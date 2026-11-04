package com.mediagenda.app.data

import android.content.Context
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.nio.file.Files
import java.nio.file.StandardCopyOption
import java.time.LocalDate

/**
 * Local, profile-scoped Health Connect snapshot.
 *
 * Health Connect keeps ownership of the original records. We only retain
 * the aggregate/last measurements the user is authorised to see when they
 * update Atividade e Saúde. The family ZIP already includes the
 * "saudepratica_*" directories under filesDir, including this one.
 *
 * Missing or denied metrics are not persisted as zero. Windows can import
 * this versioned JSON without guessing clinical measurements.
 */
class HealthConnectSnapshotStore(context: Context, private val profileId: String) {
    private val folder = File(context.filesDir, "saudepratica_health_connect/$profileId")
    private val file = File(folder, "daily.json")
    private val allowedKeys = setOf(
        "steps", "distance_km", "active_kcal", "sleep_minutes",
        "heart_bpm", "total_kcal", "weight_kg", "oxygen_percent",
        "resting_heart_bpm", "systolic_mmhg", "diastolic_mmhg",
        "respiratory_per_min", "temperature_c"
    )

    init {
        require(profileId == "legacy" || Regex("[0-9a-fA-F-]{36}").matches(profileId)) {
            "Identificador de perfil inválido"
        }
    }

    /** Returns false on a local storage error; it never uploads any data. */
    @Synchronized
    fun record(day: LocalDate, key: String, value: Double, observedAt: Long? = null): Boolean {
        if (key !in allowedKeys || !value.isFinite() || value < 0.0 ||
            value > 10_000_000.0 || day.isAfter(LocalDate.now().plusDays(1))) {
            return false
        }
        return runCatching {
            folder.mkdirs()
            require(folder.isDirectory)
            val root = if (file.exists()) {
                require(file.length() in 1..2_000_000L)
                JSONObject(file.readText(Charsets.UTF_8))
            } else {
                JSONObject().put("schema_version", 1)
                    .put("source", "health_connect")
                    .put("profile_id", profileId)
            }
            require(root.optInt("schema_version") == 1)
            require(root.optString("profile_id") == profileId)
            val days = root.optJSONObject("days") ?: JSONObject().also { root.put("days", it) }
            val daily = days.optJSONObject(day.toString()) ?: JSONObject().also {
                days.put(day.toString(), it)
            }
            val reading = JSONObject()
                .put("value", value)
                .put("captured_at_ms", System.currentTimeMillis())
            if (observedAt != null && observedAt > 0L) {
                reading.put("observed_at_ms", observedAt)
            }
            daily.put(key, reading)
            root.put("updated_at_ms", System.currentTimeMillis())
            val bytes = root.toString().toByteArray(Charsets.UTF_8)
            require(bytes.size < 2_000_000)
            val pending = File(folder, "daily.json.tmp")
            try {
                FileOutputStream(pending).use { stream ->
                    stream.write(bytes)
                    stream.fd.sync()
                }
                try {
                    Files.move(pending.toPath(), file.toPath(),
                        StandardCopyOption.REPLACE_EXISTING,
                        StandardCopyOption.ATOMIC_MOVE)
                } catch (_: java.nio.file.AtomicMoveNotSupportedException) {
                    Files.move(pending.toPath(), file.toPath(),
                        StandardCopyOption.REPLACE_EXISTING)
                }
            } finally {
                if (pending.exists()) pending.delete()
            }
            true
        }.getOrDefault(false)
    }
}
