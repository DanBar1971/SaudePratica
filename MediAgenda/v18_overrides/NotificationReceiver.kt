package com.mediagenda.app.notifications

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.media.AudioAttributes
import android.media.RingtoneManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat

class NotificationReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val medicationId = intent.getStringExtra("medication_id")
        try {
            if (Build.VERSION.SDK_INT >= 33 &&
                ContextCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED) return

            val title = intent.getStringExtra("title") ?: "SaúdePrática"
            val body = intent.getStringExtra("body") ?: "Aviso de medicação"
            val id = intent.getIntExtra("notification_id", title.hashCode())
            val manager = context.getSystemService(NotificationManager::class.java)

            // New channel: Android does not let updates override user/default
            // sound settings of an already-created notification channel.
            val channelId = "saudepratica_medication_alarm_v2"
            val sound = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM)
                ?: RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)
            val audio = AudioAttributes.Builder()
                .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                .setUsage(AudioAttributes.USAGE_ALARM)
                .build()
            val channel = NotificationChannel(
                channelId, "Alarmes de medicação — SaúdePrática",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Avisos importantes de medicação e lembretes de saúde"
                enableVibration(true)
                vibrationPattern = longArrayOf(0, 650, 300, 650, 300, 1000)
                enableLights(true)
                lightColor = Color.rgb(12, 200, 180)
                lockscreenVisibility = android.app.Notification.VISIBILITY_PRIVATE
                if (sound != null) setSound(sound, audio)
            }
            manager.createNotificationChannel(channel)

            val openApp = context.packageManager.getLaunchIntentForPackage(context.packageName)
            val tapIntent = openApp?.let {
                PendingIntent.getActivity(
                    context, id, it,
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
                )
            }

            val builder = NotificationCompat.Builder(context, channelId)
                .setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
                .setContentTitle(title)
                .setContentText(body)
                .setStyle(NotificationCompat.BigTextStyle().bigText(body))
                .setCategory(NotificationCompat.CATEGORY_ALARM)
                .setPriority(NotificationCompat.PRIORITY_MAX)
                .setVisibility(NotificationCompat.VISIBILITY_PRIVATE)
                .setColor(Color.rgb(0, 174, 151))
                .setTicker(title + " — " + body)
                .setAutoCancel(true)
            if (tapIntent != null) builder.setContentIntent(tapIntent)
            manager.notify(id, builder.build())
        } finally {
            // Preserve one next alarm for each recurring medication.
            if (!medicationId.isNullOrBlank()) {
                runCatching {
                    NotificationScheduler(context).scheduleNextMedicationById(medicationId)
                }
            }
        }
    }
}
