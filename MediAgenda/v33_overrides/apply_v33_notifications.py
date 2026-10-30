from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app/notifications")
scheduler=root/"NotificationScheduler.kt"
s=scheduler.read_text(encoding="utf-8")
start=s.index("    private fun scheduleAppointment(a: Appointment,")
end=s.index("    private fun expandOccurrences(",start)
s=s[:start]+'''    private fun scheduleAppointment(a: Appointment, profileId: String, profileName: String, multiple: Boolean) {
        if (a.done || a.date.isBlank() || a.time.isBlank()) return
        expandOccurrences(a).forEach { event ->
            // Every appointment gets a reminder at 18:00 on the previous day.
            val previousEvening=event.toLocalDate().minusDays(1).atTime(18,0)
            schedule(
                "agenda-eve|$profileId|${a.id}|$event",previousEvening,
                "📅 Marcação amanhã: " + a.activity.ifBlank{a.department},
                "Amanhã às ${event.format(DateTimeFormatter.ofPattern("HH:mm"))}" +
                    (if (a.location.isBlank()) "" else " — ${a.location}"),
                profileId=profileId,kind="appointment"
            )
            // Keep optional shorter reminders; the default 1440-minute
            // reminder is replaced by the predictable previous-evening one.
            a.remindersMinutes.distinct().filter { it>0 && it!=1440 }.forEach { mins ->
                val alarmDt=event.minusMinutes(mins.toLong())
                val whenText=when(mins){
                    120->"daqui a 2 horas"
                    60->"daqui a 1 hora"
                    else->"daqui a $mins minutos"
                }
                schedule(
                    "agenda|$profileId|${a.id}|$event|$mins",alarmDt,
                    "📅 "+a.activity.ifBlank{a.department},
                    "$whenText: ${event.format(DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm"))}" +
                        (if(a.location.isBlank())"" else " — ${a.location}"),
                    profileId=profileId,kind="appointment"
                )
            }
        }
    }

'''+s[end:]
scheduler.write_text(s,encoding="utf-8")

receiver=root/"NotificationReceiver.kt"
s=receiver.read_text(encoding="utf-8")
start=s.index('''            // New channel: Android does not let updates override user/default''')
end=s.index('''            val openApp = context.packageManager.getLaunchIntentForPackage''',start)
replacement='''            val isAppointment=intent.getStringExtra("reminder_kind")=="appointment"
            val isMedication=!medicationId.isNullOrBlank()
            val channelId=when{
                isAppointment->"saudepratica_appointments_quiet_v1"
                isMedication->"saudepratica_medication_alarm_v2"
                else->"saudepratica_other_reminders_v1"
            }
            // Channel settings survive updates: appointment alerts must use
            // a separate ID from the existing loud medication channel.
            val channel=if(isAppointment){
                NotificationChannel(channelId,"Agenda — lembretes suaves",
                    NotificationManager.IMPORTANCE_HIGH).apply{
                    description="Marcações na véspera e lembretes do próprio dia"
                    val tone=RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)
                    val attrs=AudioAttributes.Builder()
                        .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                        .setUsage(AudioAttributes.USAGE_NOTIFICATION_EVENT)
                        .build()
                    if(tone!=null)setSound(tone,attrs)
                    enableVibration(true)
                    vibrationPattern=longArrayOf(0,160)
                    enableLights(true)
                    lightColor=Color.rgb(12,200,180)
                    lockscreenVisibility=android.app.Notification.VISIBILITY_PRIVATE
                }
            }else if(isMedication){
                val tone=RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM)
                    ?:RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)
                NotificationChannel(channelId,"Alarmes de medicação — SaúdePrática",
                    NotificationManager.IMPORTANCE_HIGH).apply{
                    description="Alarmes de medicação"
                    enableVibration(true)
                    vibrationPattern=longArrayOf(0,650,300,650,300,1000)
                    enableLights(true)
                    lightColor=Color.rgb(12,200,180)
                    lockscreenVisibility=android.app.Notification.VISIBILITY_PRIVATE
                    if(tone!=null)setSound(tone,AudioAttributes.Builder()
                        .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                        .setUsage(AudioAttributes.USAGE_ALARM).build())
                }
            }else{
                NotificationChannel(channelId,"Outros lembretes de saúde",
                    NotificationManager.IMPORTANCE_DEFAULT).apply{
                    description="Hidratação e outros avisos opcionais"
                    lockscreenVisibility=android.app.Notification.VISIBILITY_PRIVATE
                }
            }
            manager.createNotificationChannel(channel)

'''
s=s[:start]+replacement+s[end:]
old='''                .setCategory(NotificationCompat.CATEGORY_ALARM)
                .setPriority(NotificationCompat.PRIORITY_MAX)'''
new='''                .setCategory(if(isAppointment)NotificationCompat.CATEGORY_EVENT
                    else NotificationCompat.CATEGORY_ALARM)
                .setPriority(if(isAppointment)NotificationCompat.PRIORITY_HIGH
                    else if(isMedication)NotificationCompat.PRIORITY_MAX
                    else NotificationCompat.PRIORITY_DEFAULT)'''
assert old in s
s=s.replace(old,new,1)
old='''            if (tapIntent != null) builder.setContentIntent(tapIntent)

            // Box photos are optional.'''
new='''            if (tapIntent != null) builder.setContentIntent(tapIntent)
            if(isAppointment){
                // Reveal an appointment to the lock screen but not clinical
                // specialties, treatments or hospital locations.
                val publicTitle=if(profileName.isBlank())
                    "SaúdePrática · Marcação"
                    else "$profileName · Lembrete de marcação"
                val redacted=NotificationCompat.Builder(context,channelId)
                    .setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
                    .setContentTitle(publicTitle)
                    .setContentText("Consulta ou exame — abre a SaúdePrática para os detalhes")
                    .setPriority(NotificationCompat.PRIORITY_HIGH)
                    .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
                    .build()
                builder.setPublicVersion(redacted)
            }

            // Box photos are optional.'''
assert old in s
s=s.replace(old,new,1)
receiver.write_text(s,encoding="utf-8")
print("Agenda reminders: 18h previous day, gentle high-importance channel, lockscreen privacy; medication alarm unchanged.")
