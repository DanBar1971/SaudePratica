package com.mediagenda.app.notifications

import android.content.Context

/**
 * Temporary display state for a postponed dose (profile + medicine + original
 * due instant). Not a confirmation, prescription change or new alarm identity.
 */
internal object MedicationSnoozeState {
    private const val PREFS="saudepratica_snooze_status_v1"
    private fun key(profile:String,med:String,due:Long)="snooze|$profile|$med|$due"
    private fun prefs(c:Context)=c.getSharedPreferences(PREFS,Context.MODE_PRIVATE)
    fun until(c:Context,profile:String,med:String,due:Long):Long {
        if(profile.isBlank()||med.isBlank()||due<=0L)return 0L
        return prefs(c).getLong(key(profile,med,due),0L)
    }
    fun save(c:Context,profile:String,med:String,due:Long,until:Long) {
        if(profile.isBlank()||med.isBlank()||due<=0L||until<=0L)return
        check(prefs(c).edit().putLong(key(profile,med,due),until).commit()){
            "Não foi possível guardar o adiamento."
        }
    }
    fun clear(c:Context,profile:String,med:String,due:Long) {
        if(profile.isNotBlank()&&med.isNotBlank()&&due>0L)
            prefs(c).edit().remove(key(profile,med,due)).apply()
    }
}
