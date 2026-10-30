package com.mediagenda.app.notifications

import android.content.Context
import com.mediagenda.app.data.ProfileStore

/**
 * The device's patient is independent of which family profile the caregiver
 * happens to be viewing. Only this patient can raise a full-screen alarm.
 */
internal object DeviceAlarmRouting {
    private const val SETTINGS = "saudepratica_device_patient_v1"
    private const val KEY = "device_profile_id"

    fun assigned(c: Context): String? {
        val ids = ProfileStore(c).all().map { it.id }.toSet()
        val explicit = c.getSharedPreferences(SETTINGS, Context.MODE_PRIVATE)
            .getString(KEY, null)
        if (explicit != null && explicit in ids) return explicit
        val caregiver = c.getSharedPreferences("saudepratica_caregiver_v1",
            Context.MODE_PRIVATE).getString("caregiver_id", null)
        if (caregiver != null && caregiver in ids) return caregiver
        val current = c.getSharedPreferences("saudepratica_intake_badge_v1",
            Context.MODE_PRIVATE).getString("current_profile", null)
        return current?.takeIf { it in ids }
    }

    fun isLocalPatient(c: Context, profileId: String): Boolean {
        val local = assigned(c)
        // Legacy installation without an association: preserve old behavior
        // rather than silencing every alarm.
        return local == null || local == profileId
    }

    fun assign(c: Context, profileId: String) {
        require(ProfileStore(c).all().any { it.id == profileId })
        check(c.getSharedPreferences(SETTINGS, Context.MODE_PRIVATE).edit()
            .putString(KEY, profileId).commit())
    }

    fun clearIfAssigned(c: Context, profileId: String) {
        val p = c.getSharedPreferences(SETTINGS, Context.MODE_PRIVATE)
        if (p.getString(KEY, null) == profileId) p.edit().remove(KEY).commit()
    }

    fun explicit(c: Context): String? =
        c.getSharedPreferences(SETTINGS, Context.MODE_PRIVATE).getString(KEY, null)
}
