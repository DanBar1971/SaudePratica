"""SaúdePrática v1.9.92 — Fase B: alarm recovery and separate medication intake.
Applied after v110 (1.9.91). All substitutions are anchored, fail closed and
retain existing branded images, manifest application ID and patient databases.
"""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"

def once(path,old,new,label):
    p=base/path
    text=p.read_text(encoding="utf-8")
    count=text.count(old)
    if count!=1:
        raise RuntimeError("Fase B "+label+" expected 1 anchor; found "+str(count))
    p.write_text(text.replace(old,new,1),encoding="utf-8")

# Scheduling must only clear future-scheduling indices. Outstanding groups,
# leader identity and already shown flags must survive a reboot or app upgrade.
once("notifications/MedicationAlarmGroup.kt",
    '    fun reset(c:Context)=synchronized(lock){prefs(c).edit().clear().commit()}',
    '''    fun resetUpcoming(c:Context)=synchronized(lock){
        val p=prefs(c)
        val editor=p.edit()
        val staleBefore=System.currentTimeMillis()-14L*24*60*60*1000
        p.all.keys.forEach{key->
            if(key.startsWith("next|"))editor.remove(key)
            else if(key.startsWith("shown|") || key.startsWith("members|") ||
                key.startsWith("leader|")){
                val at=key.substringAfterLast('|').toLongOrNull()
                if(at!=null && at<staleBefore)editor.remove(key)
            }
        }
        check(editor.commit()){"Não foi possível atualizar o registo de grupos."}
    }''',"keep outstanding alarm groups")
once("notifications/NotificationScheduler.kt",
    '        MedicationAlarmGroup.reset(context)',
    '        MedicationAlarmGroup.resetUpcoming(context)',
    "reset future index only")
# Android 12+ can revoke exact-alarm access between the query and the call.
once("notifications/NotificationScheduler.kt",
    '''        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && !alarmManager.canScheduleExactAlarms()) {
            // Android may delay alarms in this fallback: show option to grant exact alarm access.
            alarmManager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, millis, pi)
        } else {
            alarmManager.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, millis, pi)
        }''',
    '''        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S &&
                !alarmManager.canScheduleExactAlarms()) {
                // Never silently drop an alarm when exact scheduling is unavailable.
                alarmManager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, millis, pi)
            } else {
                alarmManager.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, millis, pi)
            }
        } catch(e:SecurityException) {
            android.util.Log.w("SaudePraticaReminders",
                "Exact alarm permission revoked: using best-effort reminder",e)
            alarmManager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP,millis,pi)
        }''',"exact alarm permission race")

# Only one group notification, but each member retains its own pending record.
# When the alarm times out, ALL unconfirmed group members must be marked as
# having an ignored alarm; never mark any medicine as taken.
once("notifications/MedicationAlarmService.kt",
    '    private var activeScheduledAt = 0L',
    '''    private var activeScheduledAt = 0L
    private var activeGroupIds:List<String> = emptyList()''',
    "hold active group identity")
once("notifications/MedicationAlarmService.kt",
    '''                PersonalHealthStore(this,activeProfile).noteIgnoredAlarm(
                    activeMedication,activeScheduledAt)
                IntakeBadgeManager.refresh(this,activeProfile)''',
    '''                val members=(activeGroupIds+activeMedication).distinct()
                val store=PersonalHealthStore(this,activeProfile)
                members.forEach{id->
                    if(!MedicationAlarmCoordinator.wasHandled(this,activeProfile,id,
                            activeScheduledAt)){
                        store.noteIgnoredAlarm(id,activeScheduledAt)
                    }
                }
                IntakeBadgeManager.refresh(this,activeProfile)''',
    "timeout for every unconfirmed medicine")
once("notifications/MedicationAlarmService.kt",
    '''        activeProfile=profileId;activeMedication=medicationId;activeScheduledAt=scheduledAt
        currentId=intent.getIntExtra("notification_id",990100)''',
    '''        activeProfile=profileId;activeMedication=medicationId;activeScheduledAt=scheduledAt
        activeGroupIds=groupIds
        currentId=intent.getIntExtra("notification_id",990100)''',
    "set group at service start")

# Snooze persistence already exists. Re-arm its exact original-dose intents
# after reboot, app upgrade, time change or permission restoration.
snooze=base/"notifications/MedicationSnoozeState.kt"
s=snooze.read_text(encoding="utf-8")
anchor='    fun clear(c:Context,profile:String,med:String,due:Long) {'
assert s.count(anchor)==1
restore='''    /** Recover pending ten-minute snoozes after Android has discarded alarms.
     * The original dose timestamp is immutable. Never register a new intake.
     */
    fun restore(c:Context) {
        val now=System.currentTimeMillis()
        val patients=com.mediagenda.app.data.ProfileStore(c).all().map{it.id}.toSet()
        val seen=mutableSetOf<String>()
        prefs(c).all.forEach{(key,value)->
            if(!key.startsWith("snooze|"))return@forEach
            val tokens=key.split('|')
            if(tokens.size!=4)return@forEach
            val profile=tokens[1]
            val med=tokens[2]
            val due=tokens[3].toLongOrNull()?:return@forEach
            val until=value as? Long?:return@forEach
            if(profile !in patients || due<=0L || until<=0L)return@forEach
            if(until < now-24L*60*60*1000) {
                clear(c,profile,med,due)
                return@forEach
            }
            val members=com.mediagenda.app.notifications.MedicationAlarmGroup
                .members(c,profile,due).ifEmpty{listOf(med)}
            if(members.all{
                MedicationAlarmCoordinator.wasHandled(c,profile,it,due)
            }){clear(c,profile,med,due);return@forEach}
            val leader=com.mediagenda.app.notifications.MedicationAlarmGroup
                .leader(c,profile,due).ifBlank{med}
            if(!seen.add("$profile|$due"))return@forEach
            val medicine=com.mediagenda.app.data.DataRepository(c,profile)
                .loadMedications().firstOrNull{it.id==leader}?:return@forEach
            val intent=android.content.Intent(c,NotificationReceiver::class.java).apply{
                action="com.mediagenda.app.MED_ALARM_SNOOZED_FIRE"
                data=android.net.Uri.parse("saudepratica://med/$profile/$leader/$due")
                putExtra("profile_id",profile)
                putExtra("medication_id",leader)
                putExtra("scheduled_at",due)
                putExtra("reminder_kind","medication")
                putExtra("title","💊 "+medicine.medication)
                putExtra("body","Medicação adiada · confirmar em Tomas")
                putExtra("notification_id",("med|$profile|$leader").hashCode())
                putStringArrayListExtra("group_med_ids",ArrayList(members))
            }
            val pi=android.app.PendingIntent.getBroadcast(c,
                ("snoozed|$profile|$leader|$due").hashCode(),intent,
                android.app.PendingIntent.FLAG_UPDATE_CURRENT or
                    android.app.PendingIntent.FLAG_IMMUTABLE)
            val alarm=c.getSystemService(android.app.AlarmManager::class.java)
            // Past snoozes are recovered promptly but avoid a hot reboot loop.
            val fireAt=maxOf(until,now+15_000L)
            try{
                if(android.os.Build.VERSION.SDK_INT>=31 &&
                    !alarm.canScheduleExactAlarms())
                    alarm.setAndAllowWhileIdle(android.app.AlarmManager.RTC_WAKEUP,fireAt,pi)
                else alarm.setExactAndAllowWhileIdle(
                    android.app.AlarmManager.RTC_WAKEUP,fireAt,pi)
            }catch(e:SecurityException){
                alarm.setAndAllowWhileIdle(android.app.AlarmManager.RTC_WAKEUP,fireAt,pi)
            }
        }
    }

'''
snooze.write_text(s.replace(anchor,restore+anchor,1),encoding="utf-8")

# Android delivers only a short time to BroadcastReceiver. Keep the pending
# result open during disk IO, log failures and always finish. No clinic data
# or user interface may be exposed from the boot receiver.
boot=base/"notifications/BootReceiver.kt"
boot.write_text('''package com.mediagenda.app.notifications

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

/** Restore future medication, appointments, water and grouped snoozes. */
class BootReceiver:BroadcastReceiver() {
    override fun onReceive(context:Context,intent:Intent) {
        val event=intent.action.orEmpty()
        if(event !in setOf(Intent.ACTION_BOOT_COMPLETED,
                Intent.ACTION_MY_PACKAGE_REPLACED,
                Intent.ACTION_TIME_CHANGED,
                Intent.ACTION_TIMEZONE_CHANGED,
                "android.app.action.SCHEDULE_EXACT_ALARM_PERMISSION_STATE_CHANGED"))return
        val pending=goAsync()
        val app=context.applicationContext
        Thread({
            try{
                NotificationScheduler(app).scheduleAllProfiles()
                MedicationSnoozeState.restore(app)
            }catch(t:Throwable){
                android.util.Log.e("SaudePraticaReminders",
                    "Falha na recuperação de alarmes: "+event,t)
            }finally{pending.finish()}
        },"saudepratica-recover-alarms").start()
    }
}
''',encoding="utf-8")
manifest=root/"app/src/main/AndroidManifest.xml"
m=manifest.read_text(encoding="utf-8")
old='''                <action android:name="android.intent.action.MY_PACKAGE_REPLACED" />'''
new='''                <action android:name="android.intent.action.MY_PACKAGE_REPLACED" />
                <action android:name="android.intent.action.TIME_SET" />
                <action android:name="android.intent.action.TIMEZONE_CHANGED" />
                <action android:name="android.app.action.SCHEDULE_EXACT_ALARM_PERMISSION_STATE_CHANGED" />'''
assert m.count(old)==1
manifest.write_text(m.replace(old,new,1),encoding="utf-8")

gradle=root/"app/build.gradle.kts"
g=gradle.read_text(encoding="utf-8")
assert g.count("versionCode = 101")==1 and g.count('versionName = "1.9.91"')==1
gradle.write_text(g.replace("versionCode = 101","versionCode = 102",1)
    .replace('versionName = "1.9.91"','versionName = "1.9.92"',1),encoding="utf-8")
print("SaúdePrática 1.9.92: recovery, grouped alarms, individual ignored statuses, branding preserved")
