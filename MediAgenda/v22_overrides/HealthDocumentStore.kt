package com.mediagenda.app.data

import android.content.Context
import android.net.Uri
import android.provider.OpenableColumns
import androidx.core.content.FileProvider
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.util.UUID

data class HealthDocument(
    val id: String,
    val name: String,
    val mimeType: String,
    val fileName: String,
    val createdAt: Long
)

/** Private, profile-specific copies of images and PDFs. */
class HealthDocumentStore(private val context: Context, profileId: String) {
    private val directory = File(context.filesDir, "saudepratica_documents/" +
        if (profileId == "legacy") "legacy" else {
            require(profileId.matches(Regex("[0-9a-fA-F-]{36}"))) { "Perfil inválido" }
            profileId
        })
    private val index = File(directory, "index.json")
    private val maxBytes = 50L * 1024L * 1024L

    init {
        if (!directory.exists() && !directory.mkdirs()) error("Não foi possível criar a pasta dos documentos")
    }

    fun all(): List<HealthDocument> {
        if (!index.exists()) return emptyList()
        val array = JSONArray(index.readText(Charsets.UTF_8))
        return (0 until array.length()).map { i ->
            val obj = array.getJSONObject(i)
            HealthDocument(
                obj.getString("id"), obj.getString("name"),
                obj.getString("mimeType"), obj.getString("fileName"),
                obj.getLong("createdAt")
            )
        }.sortedWith(compareByDescending<HealthDocument> { it.createdAt }.thenBy { it.name })
    }

    fun suggestedName(uri: Uri): String {
        val name = originalName(uri)
        return name.substringBeforeLast(".", name).ifBlank { "Documento digital" }.take(100)
    }

    private fun originalName(uri: Uri): String =
        runCatching {
            context.contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)
                ?.use { if (it.moveToFirst()) it.getString(0).orEmpty() else "" }.orEmpty()
        }.getOrDefault("")

    private fun clean(name: String): String =
        name.trim().replace(Regex("[\\p{Cntrl}]"), " ").take(100).also {
            require(it.isNotBlank()) { "Indique um nome para o documento." }
        }

    private fun mime(uri: Uri): Pair<String, String> {
        val declared = context.contentResolver.getType(uri).orEmpty().lowercase()
        val name = originalName(uri).ifBlank { uri.lastPathSegment.orEmpty() }.lowercase()
        return when {
            declared == "application/pdf" || name.endsWith(".pdf") -> "application/pdf" to ".pdf"
            declared == "image/png" || name.endsWith(".png") -> "image/png" to ".png"
            declared == "image/webp" || name.endsWith(".webp") -> "image/webp" to ".webp"
            declared == "image/heic" || name.endsWith(".heic") -> "image/heic" to ".heic"
            declared == "image/heif" || name.endsWith(".heif") -> "image/heif" to ".heif"
            declared == "image/jpeg" || name.endsWith(".jpg") || name.endsWith(".jpeg") ||
                declared == "image/*" -> "image/jpeg" to ".jpg"
            else -> throw IllegalArgumentException("Escolha um ficheiro PDF ou uma imagem.")
        }
    }

    fun add(uri: Uri, name: String): HealthDocument {
        val title = clean(name)
        val (type, extension) = mime(uri)
        val id = UUID.randomUUID().toString()
        val filename = "$id$extension"
        val destination = File(directory, filename)
        try {
            context.contentResolver.openInputStream(uri)?.use { input ->
                destination.outputStream().use { output ->
                    val buffer = ByteArray(16 * 1024)
                    var copied = 0L
                    while (true) {
                        val count = input.read(buffer)
                        if (count < 0) break
                        copied += count
                        require(copied <= maxBytes) { "O documento ultrapassa 50 MB." }
                        output.write(buffer, 0, count)
                    }
                    require(copied > 0) { "O ficheiro está vazio." }
                }
            } ?: error("Não foi possível abrir o documento.")
            val entry = HealthDocument(id, title, type, filename, System.currentTimeMillis())
            persist(all() + entry)
            return entry
        } catch (error: Exception) {
            destination.delete()
            throw error
        }
    }

    fun rename(document: HealthDocument, title: String) {
        val newName = clean(title)
        val updated = all().map { if (it.id == document.id) it.copy(name = newName) else it }
        require(updated.any { it.id == document.id }) { "Documento não encontrado." }
        persist(updated)
    }

    fun delete(document: HealthDocument) {
        persist(all().filterNot { it.id == document.id })
        file(document).delete()
    }

    private fun file(document: HealthDocument): File {
        require(Regex("[0-9a-fA-F-]{36}\\.(pdf|png|webp|heic|heif|jpg)")
            .matches(document.fileName)) { "Documento inválido" }
        return File(directory, document.fileName)
    }

    fun contentUri(document: HealthDocument): Uri =
        FileProvider.getUriForFile(context, "${context.packageName}.documents", file(document))

    private fun persist(items: List<HealthDocument>) {
        val array = JSONArray()
        items.forEach { item ->
            array.put(JSONObject()
                .put("id", item.id).put("name", item.name)
                .put("mimeType", item.mimeType).put("fileName", item.fileName)
                .put("createdAt", item.createdAt))
        }
        val output = android.util.AtomicFile(index)
        val stream = output.startWrite()
        try {
            stream.write(array.toString(2).toByteArray(Charsets.UTF_8))
            output.finishWrite(stream)
        } catch (error: Exception) {
            output.failWrite(stream)
            throw error
        }
    }
}
