"""v1.9.71: make scheduled medication alarms audible independently of foreground service."""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
def change(path,old,new,label):
 s=path.read_text()
 if s.count(old)!=1:raise RuntimeError(f"v89 {label}: expected 1 anchor got {s.count(old)}")
 path.write_text(s.replace(old,new,1))
p=base/"notifications/NotificationReceiver.kt"
change(p,'''                val channel=com.mediagenda.app.notifications.MedicationAlarmService.CHANNEL
                manager.createNotificationChannel(android.app.NotificationChannel(
                    channel,"ALARMES DE MEDICAÇÃO — ecrã completo",
                    NotificationManager.IMPORTANCE_HIGH).apply {
                    description="Alarme persistente até TOMEI ou ADIAR"
                    setSound(null,null)
                    enableVibration(true)
                    lockscreenVisibility=android.app.Notification.VISIBILITY_PRIVATE
                })''','''                // New channel ID is essential: Android persists channel sound
                // settings across APK updates. The old channel was SILENT.
                // If Android refuses to start the foreground service from a
                // scheduled broadcast, this channel MUST still ring audibly.
                val channel="saudepratica_scheduled_alarm_audible_v1"
                manager.createNotificationChannel(android.app.NotificationChannel(
                    channel,"Alarmes programados de medicação",
                    NotificationManager.IMPORTANCE_HIGH).apply {
                    description="Alarme audível mesmo quando o serviço de voz não arranca"
                    val tone=RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM)
                        ?:RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)
                    if(tone!=null)setSound(tone,AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_ALARM)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build())
                    enableVibration(true)
                    vibrationPattern=longArrayOf(0,750,350,750,350,750)
                    lockscreenVisibility=android.app.Notification.VISIBILITY_PRIVATE
                })''',"audible scheduled fallback")
change(p,'''                manager.notify(alarmId,n.build())
                runCatching{MedicationAlarmService.start(context,intent)}
                    .onFailure{android.util.Log.e("SaudePraticaAlarm",
                        "Alarm service blocked; full screen notification remains",it)}
                return''','''                // Start service before publishing fallback notification. The
                // service may be blocked on some Android/HyperOS builds.
                // Keep the audible fallback instead of silently failing.
                runCatching{MedicationAlarmService.start(context,intent)}
                    .onFailure{android.util.Log.e("SaudePraticaAlarm",
                        "Scheduled service blocked; audible fallback",it)}
                manager.notify(alarmId,n.build())
                return''',"start order")
# The foreground service must not remove the fallback audible notification.
# It uses the same id on its own channel. The sound stops when the notification
# is replaced; voice and ringtone continue through the foreground service.
p=base/"notifications/MedicationAlarmService.kt"
change(p,'''        try {
            startForeground(currentId, n.build())''','''        try {
            startForeground(currentId, n.build())''',"foreground") if False else None
p=root/"app/build.gradle.kts"
change(p,"versionCode = 80","versionCode = 81","version")
change(p,'versionName = "1.9.70"','versionName = "1.9.71"',"name")
print("v1.9.71 audible scheduled alarms")
