package com.mediagenda.app.notifications

import android.app.AlarmManager
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.net.Uri
import com.mediagenda.app.data.PersonalHealthStore

/**
 * The scheduled dose's identity is (profile UUID, medicine UUID, original alarm
 * timestamp). A snoozed PendingIntent MUST be cancelled on every intake route,
 * not only when the user presses TOMEI in the notification.
 */
internal object MedicationAlarmCoordinator {
    const val ACTION_RESOLVED="com.mediagenda.app.MEDICATION_INTAKE_RESOLVED"

    fun wasConfirmed(c:Context,profile:String,medication:String,scheduledAt:Long):Boolean {
        if(profile.isBlank()||medication.isBlank()||scheduledAt<=0)return false
        return runCatching {
            PersonalHealthStore(c,profile).list("intakes").any {
                it.fields["medication_id"]==medication &&
                    it.fields["scheduled_at"]==scheduledAt.toString()
            }
        }.getOrDefault(false)
    }

    fun resolve(c:Context,profile:String,medication:String,scheduledAt:Long) {
        if(profile.isBlank()||medication.isBlank()||scheduledAt<=0)return
        val request=("snoozed|"+profile+"|"+medication+"|"+scheduledAt).hashCode()
        val snoozed=Intent(c,NotificationReceiver::class.java).apply {
            action="com.mediagenda.app.MED_ALARM_SNOOZED_FIRE"
            data=Uri.parse("saudepratica://med/"+profile+"/"+medication+"/"+scheduledAt)
        }
        val pi=PendingIntent.getBroadcast(c,request,snoozed,
            PendingIntent.FLAG_NO_CREATE or PendingIntent.FLAG_IMMUTABLE)
        if(pi!=null) {
            c.getSystemService(AlarmManager::class.java).cancel(pi)
            pi.cancel()
        }
        SnoozedMedicationNotice.clear(c,profile,medication,scheduledAt)
        val originalId=("med|"+profile+"|"+medication).hashCode()
        c.getSystemService(NotificationManager::class.java).cancel(originalId)
        c.sendBroadcast(Intent(ACTION_RESOLVED).setPackage(c.packageName)
            .putExtra("profile_id",profile)
            .putExtra("medication_id",medication)
            .putExtra("scheduled_at",scheduledAt))
        runCatching {
            c.startService(Intent(c,MedicationAlarmService::class.java).apply {
                action=MedicationAlarmService.ACTION_STOP
                putExtra("profile_id",profile)
                putExtra("medication_id",medication)
                putExtra("scheduled_at",scheduledAt)
            })
        }
    }
}
