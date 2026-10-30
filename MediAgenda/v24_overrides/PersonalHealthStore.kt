package com.mediagenda.app.data

import android.content.Context
import android.util.AtomicFile
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.util.UUID

/** Local, non-cloud medical journal; namespaced by profile. */
data class PersonalHealthRecord(
    val id: String,
    val kind: String,
    val title: String,
    val timestamp: Long,
    val fields: Map<String, String>
)

class PersonalHealthStore(private val context: Context, profileId: String) {
    private val id = profileId.also {
        require(it == "legacy" || it.matches(Regex("[0-9a-fA-F-]{36}")))
    }
    private val folder = File(context.filesDir, "saudepratica_health/$id").apply {
        if (!exists()) require(mkdirs()) { "Não foi possível preparar os registos." }
    }
    private val file = File(folder, "records.json")
    private val emergency = context.getSharedPreferences("saudepratica_emergency_$id", Context.MODE_PRIVATE)
    private val allowed = setOf("symptoms", "measurements", "vaccines", "intakes")

    fun list(kind: String): List<PersonalHealthRecord> {
        require(kind in allowed)
        if (!file.exists()) return emptyList()
        val arr = JSONArray(file.readText(Charsets.UTF_8))
        val records = mutableListOf<PersonalHealthRecord>()
        for (i in 0 until arr.length()) {
            val o = arr.optJSONObject(i) ?: continue
            if (o.optString("kind") != kind) continue
            val map = mutableMapOf<String, String>()
            val properties = o.optJSONObject("fields") ?: JSONObject()
            val keys = properties.keys()
            while (keys.hasNext()) {
                val key = keys.next()
                map[key] = properties.optString(key)
            }
            records += PersonalHealthRecord(
                o.optString("id"), kind, o.optString("title"),
                o.optLong("timestamp"), map
            )
        }
        return records.sortedByDescending { it.timestamp }
    }

    private fun all(): List<PersonalHealthRecord> =
        allowed.flatMap { list(it) }

    private fun write(records: List<PersonalHealthRecord>) {
        val arr = JSONArray()
        records.forEach { item ->
            arr.put(JSONObject()
                .put("id", item.id).put("kind", item.kind)
                .put("title", item.title).put("timestamp", item.timestamp)
                .put("fields", JSONObject(item.fields)))
        }
        val atomic = AtomicFile(file)
        val stream = atomic.startWrite()
        try {
            stream.write(arr.toString(2).toByteArray(Charsets.UTF_8))
            atomic.finishWrite(stream)
        } catch (error: Exception) {
            atomic.failWrite(stream)
            throw error
        }
    }

    fun add(kind: String, title: String, fields: Map<String, String>,
            timestamp: Long = System.currentTimeMillis()): PersonalHealthRecord {
        require(kind in allowed) { "Registo inválido." }
        require(title.isNotBlank()) { "Indique uma descrição." }
        val safe = fields.mapValues { it.value.trim().take(1000) }
        val newItem = PersonalHealthRecord(UUID.randomUUID().toString(),
            kind, title.trim().take(160), timestamp, safe)
        write(all() + newItem)
        return newItem
    }

    fun remove(item: PersonalHealthRecord) {
        require(item.kind in allowed)
        write(all().filterNot { it.id == item.id })
    }

    fun emergencyValue(key: String) = emergency.getString(key, "").orEmpty()
    fun saveEmergency(values: Map<String, String>) {
        val permitted = setOf("contact_name", "contact_phone", "second_contact", "allergies",
            "conditions", "notes", "blood_group")
        val editor = emergency.edit()
        values.forEach { (key, value) ->
            require(key in permitted) { "Campo inválido." }
            editor.putString(key, value.trim().take(2000))
        }
        require(editor.commit()) { "Não foi possível guardar a ficha." }
    }

    fun latestIntakeFor(medicationId: String): Long? =
        list("intakes").firstOrNull { it.fields["medication_id"] == medicationId }?.timestamp

    /** A confirmation is a log entry, never an instruction to take a dose. */
    fun confirmIntake(medicationId: String, name: String): PersonalHealthRecord {
        require(medicationId.isNotBlank()) { "Medicamento inválido." }
        return add("intakes", name, mapOf("medication_id" to medicationId))
    }
}
