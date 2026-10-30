package com.mediagenda.app.notifications

import android.content.Context
import com.mediagenda.app.data.DataRepository
import com.mediagenda.app.data.PersonalHealthStore
import com.mediagenda.app.data.ProfileStore

/**
 * One visible medication alarm for every exact (profile ID, scheduled instant).
 * Each medicine still has a separate pending intake and confirmation.
 */
internal object MedicationAlarmGroup {
    private const val STORE="saudepratica_med_alarm_groups_v1"
    private val lock=Any()
    private fun prefs(c:Context)=c.getSharedPreferences(STORE,Context.MODE_PRIVATE)
    fun reset(c:Context)=synchronized(lock){prefs(c).edit().clear().commit()}
    fun record(c:Context,profile:String,med:String,at:Long){
        if(at<=0L||profile.isBlank()||med.isBlank())return
        synchronized(lock) {
            prefs(c).edit().putLong("next|"+profile+"|"+med,at).commit()
        }
    }
    fun members(c:Context,profile:String,at:Long):List<String> =
        prefs(c).getString("members|"+profile+"|"+at,null)
            ?.split('|')?.filter{it.isNotBlank()}.orEmpty()
    fun leader(c:Context,profile:String,at:Long):String =
        prefs(c).getString("leader|"+profile+"|"+at,"").orEmpty()
    fun due(c:Context,profile:String,at:Long,current:String):List<String> {
        if(ProfileStore(c).all().none{it.id==profile}||at<=0L)return listOf(current)
        val snapshot=prefs(c).getString("members|"+profile+"|"+at,null)
        if(!snapshot.isNullOrBlank())return snapshot.split('|').distinct()
        val scheduled=prefs(c).all.filter{(key,value)->
            key.startsWith("next|"+profile+"|") && value==at
        }.keys.map{it.removePrefix("next|"+profile+"|")}
        val existing=DataRepository(c,profile).loadMedications().map{it.id}.toSet()
        return (scheduled+current).distinct().filter{it in existing}.sorted()
    }
    fun claim(c:Context,profile:String,at:Long,ids:List<String>,leader:String):Boolean=synchronized(lock){
        val key="shown|"+profile+"|"+at
        val p=prefs(c)
        if(p.getBoolean(key,false))false
        else p.edit().putBoolean(key,true)
            .putString("members|"+profile+"|"+at,ids.joinToString("|"))
            .putString("leader|"+profile+"|"+at,leader).commit()
    }
    fun pending(c:Context,profile:String,at:Long,ids:List<String>){
        val data=DataRepository(c,profile).loadMedications().associateBy{it.id}
        val store=PersonalHealthStore(c,profile)
        ids.distinct().forEach{ id->
            if(!MedicationAlarmCoordinator.wasConfirmed(c,profile,id,at)){
                val m=data[id]?:return@forEach
                store.noteReminder(id,m.medication.ifBlank{"Medicamento"},at)
                IntakeBadgeManager.scheduleCheck(c,profile,id,at)
            }
        }
    }
    fun outstanding(c:Context,profile:String,at:Long,ids:List<String>):List<String> =
        ids.filter { !MedicationAlarmCoordinator.wasConfirmed(c,profile,it,at) }
}
