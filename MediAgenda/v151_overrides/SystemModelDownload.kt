package com.mediagenda.app

import android.app.DownloadManager
import android.content.Context
import android.net.Uri
import android.os.Environment
import android.os.Handler
import android.os.Looper
import java.io.File
import java.io.FileOutputStream
import java.security.MessageDigest
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean

/**
 * Android's persistent, user-approved system downloader for the OPTIONAL
 * offline model. The DownloadManager owns the network connection and retries;
 * the app owns SHA-256 verification and private activation. No health records,
 * profile identifiers or user prompts are sent in this request.
 */
internal class SystemModelDownload(private val app: Context) : AutoCloseable {
    companion object {
        private const val KEY = "download_id"
        private const val PREFS = "saudepratica_ia_model_download"
        private const val FILE = "Qwen3-0.6B-Q4_K_S.gguf"
        private const val URL =
            "https://huggingface.co/unsloth/Qwen3-0.6B-GGUF/resolve/50968a4468ef4233ed78cd7c3de230dd1d61a56b/Qwen3-0.6B-Q4_K_S.gguf"
        private const val SHA256 =
            "3e5495288a45c7891d32afeb4e7a1ed58a9a22fab83f8903b561204a89aae363"
        private const val MIN_BYTES = 350_000_000L
        private const val MAX_BYTES = 450_000_000L
        const val EXPECTED_BYTES = 383_000_000L
        // During checksum verification a temporary internal copy is needed.
        const val REQUIRED_FREE_BYTES = 950_000_000L
        private val verifying = AtomicBoolean(false)
    }

    enum class Phase { NONE, WAITING, RUNNING, PAUSED, DOWNLOADED, VERIFYING, FAILED, INSTALLED }
    data class State(
        val phase: Phase,
        val bytes: Long = 0L,
        val total: Long = EXPECTED_BYTES,
        val reason: Int = 0,
        val detail: String = ""
    ) {
        val percent: Int get() =
            ((bytes.coerceAtLeast(0L) * 100L) / total.coerceAtLeast(1L)).toInt()
                .coerceIn(0, if (phase == Phase.INSTALLED) 100 else 99)
        val active: Boolean get() =
            phase in listOf(Phase.WAITING, Phase.RUNNING, Phase.PAUSED, Phase.DOWNLOADED, Phase.VERIFYING)
    }

    private val manager = app.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
    private val prefs = app.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
    private val main = Handler(Looper.getMainLooper())
    private val executor = Executors.newSingleThreadExecutor { task ->
        Thread(task, "SaudePratica-IA-Verificar-SHA256").apply { isDaemon = true }
    }
    private var closed = false
    private val modelFolder get() = File(app.filesDir, "ia-local")
    private val model get() = File(modelFolder, FILE)

    private fun id(): Long = prefs.getLong(KEY, -1L)
    private fun saveId(value: Long) = prefs.edit().putLong(KEY, value).apply()
    private fun clearId() = prefs.edit().remove(KEY).apply()

    fun snapshot(): State {
        val existing = id()
        if (existing < 0L) {
            return if (model.isFile && model.length() in MIN_BYTES..MAX_BYTES)
                State(Phase.INSTALLED, model.length(), model.length()) else State(Phase.NONE)
        }
        val cursor = try {
            manager.query(DownloadManager.Query().setFilterById(existing))
        } catch (e: Exception) {
            return State(Phase.FAILED, detail = "Não foi possível consultar o gestor de downloads.")
        }
        cursor.use { c ->
            if (c == null || !c.moveToFirst()) {
                return State(Phase.FAILED, detail = "Transferência não encontrada no Android.")
            }
            val status = c.getInt(c.getColumnIndexOrThrow(DownloadManager.COLUMN_STATUS))
            val done = c.getLong(c.getColumnIndexOrThrow(DownloadManager.COLUMN_BYTES_DOWNLOADED_SO_FAR))
            val expected = c.getLong(c.getColumnIndexOrThrow(DownloadManager.COLUMN_TOTAL_SIZE_BYTES))
            val reason = c.getInt(c.getColumnIndexOrThrow(DownloadManager.COLUMN_REASON))
            val phase = when(status) {
                DownloadManager.STATUS_PENDING -> Phase.WAITING
                DownloadManager.STATUS_RUNNING -> Phase.RUNNING
                DownloadManager.STATUS_PAUSED -> Phase.PAUSED
                DownloadManager.STATUS_SUCCESSFUL -> if (verifying.get()) Phase.VERIFYING else Phase.DOWNLOADED
                else -> Phase.FAILED
            }
            return State(phase, done.coerceAtLeast(0L),
                if (expected > 0L) expected else EXPECTED_BYTES,
                reason, if (phase == Phase.FAILED) explainError(reason) else "")
        }
    }

    private fun explainError(reason: Int): String = when(reason) {
        DownloadManager.ERROR_CANNOT_RESUME -> "A ligação foi interrompida e o servidor não permitiu continuar. Tenta novamente."
        DownloadManager.ERROR_HTTP_DATA_ERROR -> "O servidor interrompeu a transferência. Tenta novamente com Wi-Fi estável."
        DownloadManager.ERROR_INSUFFICIENT_SPACE -> "Não existe espaço de armazenamento suficiente."
        DownloadManager.ERROR_UNHANDLED_HTTP_CODE -> "O servidor devolveu um erro HTTP."
        DownloadManager.ERROR_FILE_ERROR -> "O Android não conseguiu guardar o ficheiro."
        DownloadManager.PAUSED_WAITING_FOR_NETWORK -> "A aguardar ligação à Internet."
        DownloadManager.PAUSED_WAITING_TO_RETRY -> "Ligação interrompida; o Android vai tentar novamente."
        DownloadManager.PAUSED_QUEUED_FOR_WIFI -> "A aguardar Wi-Fi para continuar."
        DownloadManager.PAUSED_UNKNOWN -> "Transferência em pausa pelo Android."
        else -> "Transferência interrompida (código $reason)."
    }

    fun statusDescription(state: State): String = when(state.phase) {
        Phase.NONE -> "IA local ainda não descarregada"
        Phase.WAITING -> "Transferência em fila no Android"
        Phase.RUNNING -> "A descarregar IA local"
        Phase.PAUSED -> explainError(state.reason)
        Phase.DOWNLOADED -> "Transferência concluída. A verificar integridade..."
        Phase.VERIFYING -> "A verificar integridade do modelo (SHA-256)..."
        Phase.FAILED -> state.detail
        Phase.INSTALLED -> "Modelo descarregado e verificado · pronto a ativar"
    }

    /** Only called by an explicit user click on Descarregar. */
    fun begin(wifiOnly: Boolean): State {
        require(!closed) { "Ecrã do assistente já fechado." }
        val current = snapshot()
        if (current.active) return current
        val external = app.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS)
            ?: error("O armazenamento de downloads do Android não está disponível.")
        check(external.usableSpace >= REQUIRED_FREE_BYTES) {
            "É necessário aproximadamente 1 GB livre para descarregar e verificar o modelo."
        }
        if (id() >= 0) {
            manager.remove(id())
            clearId()
        }
        val old = File(external, FILE)
        if (old.exists()) old.delete()
        val request = DownloadManager.Request(Uri.parse(URL))
            .setTitle("SaúdePrática · IA local leve")
            .setDescription("Modelo opcional Qwen3 0.6B · 383 MB")
            .setMimeType("application/octet-stream")
            .setDestinationInExternalFilesDir(app, Environment.DIRECTORY_DOWNLOADS, FILE)
            .setAllowedOverMetered(!wifiOnly)
            .setAllowedOverRoaming(false)
            .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
        saveId(manager.enqueue(request))
        return snapshot()
    }

    fun cancel() {
        val existing = id()
        if (existing >= 0L) manager.remove(existing)
        clearId()
    }

    /** Run after DownloadManager STATUS_SUCCESSFUL. Copy into app-private storage
     * while verifying the immutable model hash; remove the system copy afterwards. */
    fun verify(onFinished: (Result<Unit>) -> Unit) {
        if (!verifying.compareAndSet(false, true)) return
        val existing = id()
        executor.execute {
            val outcome: Result<Unit> = runCatching {
                check(existing >= 0L) { "Não existe uma transferência para validar." }
                val c = manager.query(DownloadManager.Query().setFilterById(existing))
                val completed = c?.use { cur ->
                    cur.moveToFirst() &&
                        cur.getInt(cur.getColumnIndexOrThrow(DownloadManager.COLUMN_STATUS)) ==
                            DownloadManager.STATUS_SUCCESSFUL
                } ?: false
                check(completed) { "O download ainda não terminou." }
                val downloadedUri = manager.getUriForDownloadedFile(existing)
                    ?: error("O Android não conseguiu abrir o ficheiro descarregado.")
                check(modelFolder.isDirectory || modelFolder.mkdirs()) { "Sem acesso à pasta privada da IA." }
                check(modelFolder.usableSpace >= 430_000_000L) {
                    "Precisas de mais espaço livre para verificar e instalar o modelo."
                }
                val staging = File(modelFolder, "$FILE.install")
                staging.delete()
                try {
                    val md = MessageDigest.getInstance("SHA-256")
                    var total = 0L
                    val input = app.contentResolver.openInputStream(downloadedUri)
                        ?: error("Não foi possível ler o download concluído.")
                    input.use { source ->
                        FileOutputStream(staging).use { target ->
                            val buffer = ByteArray(65536)
                            while (true) {
                                val count = source.read(buffer)
                                if (count < 0) break
                                total += count
                                check(total <= MAX_BYTES) { "O ficheiro excede o tamanho esperado." }
                                md.update(buffer, 0, count)
                                target.write(buffer, 0, count)
                            }
                            target.fd.sync()
                        }
                    }
                    check(total in MIN_BYTES..MAX_BYTES) { "O download ficou incompleto." }
                    val actual = md.digest().joinToString("") { "%02x".format(it.toInt() and 255) }
                    check(actual == SHA256) {
                        "Integridade inválida: o modelo não coincide com o ficheiro oficial."
                    }
                    if (model.exists()) check(model.delete()) { "Não foi possível substituir o modelo anterior." }
                    check(staging.renameTo(model)) { "Não foi possível finalizar a instalação." }
                } finally { staging.delete() }
            }
            if (outcome.isSuccess) {
                manager.remove(existing)
                if (id() == existing) clearId()
            } else {
                // After checksum mismatch there is no reason to preserve untrusted bits.
                val err = outcome.exceptionOrNull()?.message.orEmpty()
                if (err.contains("Integridade inválida") || err.contains("incompleto")) {
                    manager.remove(existing)
                    if (id() == existing) clearId()
                }
            }
            verifying.set(false)
            if (!closed) main.post { if (!closed) onFinished(outcome) }
        }
    }

    override fun close() {
        closed = true
        executor.shutdown()
    }
}
