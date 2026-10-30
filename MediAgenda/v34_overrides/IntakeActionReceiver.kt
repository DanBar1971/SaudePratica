package com.mediagenda.app.notifications

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import com.mediagenda.app.data.DataRepository
import com.mediagenda.app.data.PersonalHealthStore
import com.mediagenda.app.data.ProfileStore

/**
 * "✓ Tomei" action for a real medication alarm. Confirmations are registered
 * for the exact medicine and user, never for synthetic/test notifications.
 */
class IntakeActionReceiver:BroadcastReceiver() {
    companion object {
        const val ACTION="com.mediagenda.app.CONFIRM_INTAKE"
    }
    override fun onReceive(context:Context,intent:Intent) {
        if(intent.action!=ACTION)return
        val profileId=intent.getStringExtra("profile_id").orEmpty()
        val medId=intent.getStringExtra("medication_id").orEmpty()
        val scheduledAt=intent.getLongExtra("scheduled_at",0L)
        val notificationId=intent.getIntExtra("notification_id",0)
        val now=System.currentTimeMillis()
        if(scheduledAt<=0L || scheduledAt>now+300000 ||
            scheduledAt<now-48L*60*60*1000)return
        val owner=ProfileStore(context).all().firstOrNull{it.id==profileId}?:return
        val med=DataRepository(context,profileId).loadMedications()
            .firstOrNull{it.id==medId}?:return
        val store=PersonalHealthStore(context,profileId)
        // Handle double taps or replay of a previously delivered alert.
        val already=store.list("intakes").any{
            it.fields["medication_id"]==medId &&
            it.fields["scheduled_at"]==scheduledAt.toString()
        }
        if(!already){
            try {
                store.add("intakes",med.medication.ifBlank{"Medicação"},
                    mapOf("medication_id" to medId,
                        "scheduled_at" to scheduledAt.toString(),
                        "source" to "notification"))
            }catch(_:Exception){
                // Never claim that the dose was logged after a write error.
                return
            }
        }
        val manager=context.getSystemService(NotificationManager::class.java)
        val channelId="saudepratica_intake_confirmation_v1"
        if(Build.VERSION.SDK_INT>=Build.VERSION_CODES.O){
            manager.createNotificationChannel(NotificationChannel(channelId,
                "Confirmações de tomas",NotificationManager.IMPORTANCE_LOW).apply{
                description="Confirmações sem alarme sonoro"
                enableVibration(false)
            })
        }
        val open=context.packageManager.getLaunchIntentForPackage(context.packageName)
        val tap=open?.let {
            PendingIntent.getActivity(context,notificationId,it,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        }
        if(Build.VERSION.SDK_INT>=33 && ContextCompat.checkSelfPermission(
            context,Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED
        )return
        val complete=NotificationCompat.Builder(context,channelId)
            .setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
            .setContentTitle(owner.name+" · ✓ Toma registada")
            .setContentText(med.medication.ifBlank{"Medicação"}+
                " — registada no histórico de tomas.")
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setVisibility(NotificationCompat.VISIBILITY_PRIVATE)
            .setAutoCancel(true)
        if(tap!=null)complete.setContentIntent(tap)
        manager.cancel(notificationId)
        manager.notify(notificationId,complete.build())
    }
}
