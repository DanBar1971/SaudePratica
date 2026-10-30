package com.mediagenda.app.data

import android.content.Context
import android.content.SharedPreferences
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.util.UUID

data class HealthProfile(val id: String, val name: String)

class ProfileStore(private val context: Context) {
    private val prefs: SharedPreferences =
        context.getSharedPreferences("saudepratica_profiles_v1", Context.MODE_PRIVATE)

    private fun save(profiles: List<HealthProfile>) {
        val array = JSONArray()
        profiles.forEach { array.put(JSONObject().put("id", it.id).put("name", it.name)) }
        check(prefs.edit().putString("profiles", array.toString()).commit()) {
            "Não foi possível guardar a lista de utilizadores."
        }
    }

    /** Non-destructive v1.9.1 migration: the legacy JSON files belong to
     * the original account (Regina on the existing installation).
     */
    fun all(): List<HealthProfile> {
        val raw = prefs.getString("profiles", null)
        if (raw == null) {
            val legacyPrefs = context.getSharedPreferences("mediagenda_profile", Context.MODE_PRIVATE)
            val oldName = legacyPrefs.getString("name", "").orEmpty().trim()
            val hasPreviousFiles = File(context.filesDir, "medicacao.json").exists() ||
                File(context.filesDir, "agenda.json").exists()
            val initial = if (oldName.isNotEmpty() || hasPreviousFiles) {
                listOf(HealthProfile("legacy", oldName.ifBlank { "Utilizador 1" }))
            } else emptyList()
            save(initial)
            return initial
        }
        val array = JSONArray(raw)
        return (0 until array.length()).map { i ->
            array.getJSONObject(i).let { HealthProfile(it.getString("id"), it.getString("name")) }
        }
    }

    fun create(name: String): HealthProfile {
        val cleanName = name.trim()
        require(cleanName.isNotEmpty()) { "Indique o nome do utilizador." }
        val current = all()
        require(current.none { it.name.equals(cleanName, true) }) {
            "Já existe um utilizador com este nome."
        }
        val created = HealthProfile(
            if (current.isEmpty()) "legacy" else UUID.randomUUID().toString(),
            cleanName
        )
        save(current + created)
        val profilePrefs = context.getSharedPreferences(preferencesFor(created.id), Context.MODE_PRIVATE)
        profilePrefs.edit().putString("name", cleanName).apply()
        return created
    }

    /** Delete the registry entry only after that person's files were purged. */
    fun remove(id: String) {
        val previous=all()
        require(previous.any { it.id==id }) { "Utilizador não encontrado." }
        save(previous.filterNot { it.id==id })
    }

    fun rename(id: String, newName: String) {
        val cleanName = newName.trim()
        require(cleanName.isNotEmpty()) { "O nome não pode ficar vazio." }
        val current = all()
        require(current.any { it.id == id }) { "Utilizador não encontrado." }
        require(current.none { it.id != id && it.name.equals(cleanName, true) }) {
            "Já existe um utilizador com este nome."
        }
        save(current.map { if (it.id == id) it.copy(name = cleanName) else it })
    }

    fun preferencesFor(id: String): String =
        if (id == "legacy") "mediagenda_profile" else "saudepratica_profile_$id"
}