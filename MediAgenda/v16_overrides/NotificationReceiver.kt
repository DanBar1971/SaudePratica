package com.mediagenda.app.notifications

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
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

            val title = intent.getStringExtra("title") ?: "MediAgenda"
            val body = intent.getStringExtra("body") ?: "Aviso"
            val id = intent.getIntExtra("notification_id", title.hashCode())
            val manager = context.getSystemService(NotificationManager::class.java)
            val channelId = "mediagenda_reminders"
            manager.createNotificationChannel(
                NotificationChannel(
                    channelId, "Avisos MediAgenda", NotificationManager.IMPORTANCE_HIGH
                )
            )
            val notification = NotificationCompat.Builder(context, channelId)
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentTitle(title)
                .setContentText(body)
                .setStyle(NotificationCompat.BigTextStyle().bigText(body))
                .setPriority(NotificationCompat.PRIORITY_HIGH)
                .setAutoCancel(true)
                .build()
            manager.notify(id, notification)
        } finally {
            if (!medicationId.isNullOrBlank()) {
                runCatching { NotificationScheduler(context).scheduleNextMedicationById(medicationId) }
            }
        }
    }
}
