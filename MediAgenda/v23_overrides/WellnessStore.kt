package com.mediagenda.app.data

import android.content.Context
import java.time.LocalDate

/**
 * Optional personal settings. Nothing is shared between profiles and no
 * clinician instructions are invented by the application.
 */
class WellnessStore(context: Context, profileId: String) {
    init {
        require(profileId == "legacy" || profileId.matches(Regex("[0-9a-fA-F-]{36}"))) {
            "Perfil inválido"
        }
    }
    private val prefs = context.getSharedPreferences(
        "saudepratica_wellness_$profileId", Context.MODE_PRIVATE
    )

    fun text(key: String, fallback: String = "") =
        prefs.getString(key, fallback).orEmpty()

    fun saveText(map: Map<String, String>) {
        prefs.edit().apply {
            map.forEach { (key, value) -> putString(key, value) }
        }.apply()
    }

    val waterEnabled: Boolean get() = prefs.getBoolean("water_enabled", false)
    val waterStart: String get() = text("water_start", "09:00")
    val waterEnd: String get() = text("water_end", "20:00")
    val waterInterval: Int get() = prefs.getInt("water_interval", 120).coerceIn(30, 360)
    val glassMl: Int get() = prefs.getInt("water_glass_ml", 200).coerceIn(30, 1000)
    val optionalTargetMl: Int get() = prefs.getInt("water_target_ml", 0).coerceIn(0, 10000)

    fun saveWater(enabled: Boolean, start: String, end: String,
                  interval: Int, glass: Int, target: Int) {
        require(Regex("""^\d{2}:\d{2}$""").matches(start) &&
                Regex("""^\d{2}:\d{2}$""").matches(end)) {
            "Indique as horas no formato HH:mm."
        }
        val startTime = java.time.LocalTime.parse(start)
        val endTime = java.time.LocalTime.parse(end)
        require(endTime.isAfter(startTime)) { "A hora de fim deve ser posterior à hora de início." }
        require(interval in 30..360) { "Escolha um intervalo entre 30 e 360 minutos." }
        require(glass in 30..1000) { "O volume deve ser entre 30 e 1000 ml." }
        require(target in 0..10000) { "Objetivo inválido. Use 0 para não definir um objetivo." }
        prefs.edit()
            .putBoolean("water_enabled", enabled)
            .putString("water_start", start)
            .putString("water_end", end)
            .putInt("water_interval", interval)
            .putInt("water_glass_ml", glass)
            .putInt("water_target_ml", target)
            .apply()
    }

    fun todayMl(): Int {
        val today = LocalDate.now().toString()
        return if (prefs.getString("water_logged_date", "") == today)
            prefs.getInt("water_logged_ml", 0) else 0
    }

    fun recordGlass(): Int {
        val sum = (todayMl() + glassMl).coerceAtMost(100000)
        prefs.edit()
            .putString("water_logged_date", LocalDate.now().toString())
            .putInt("water_logged_ml", sum)
            .apply()
        return sum
    }

    fun removeLastGlass(): Int {
        val sum = (todayMl() - glassMl).coerceAtLeast(0)
        prefs.edit()
            .putString("water_logged_date", LocalDate.now().toString())
            .putInt("water_logged_ml", sum)
            .apply()
        return sum
    }
}
