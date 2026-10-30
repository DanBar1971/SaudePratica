"""SaúdePrática 1.9.67: single intake selector, one medication alarm channel and installability checks."""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
def change(file,old,new,why):
    s=file.read_text(encoding="utf8")
    if s.count(old)!=1:
        raise RuntimeError(f"v1.9.67 {why}: expected 1 match, got {s.count(old)}")
    file.write_text(s.replace(old,new,1),encoding="utf8")

main=base/"MainActivity.kt"
# There are three separate 'intake' UI elements for the same concept.
# Keep the real selector only; preserve underlying m.time for old data imports.
change(main,'        val timeText = input("Momento da toma (ex.: Jejum / Deitar)", m.time)\n',
       '','remove redundant legacy time entry')
change(main,'        val chosenPatternText=input("Tipo de toma prescrito",patterns.first{it.second==chosenPattern}.first)\n        chosenPatternText.edit.isEnabled=false\n',
       '','remove redundant read-only type entry')
change(main,'                    chosenPatternText.edit.setText(patterns[index].first)\n',
       '','remove duplicate field update')
change(main,'        listOf(name,dose,indication,timeText).forEach{box.addView(it.container)}',
       '        listOf(name,dose,indication).forEach{box.addView(it.container)}',
       'remove old moment text box')
change(main,'        box.addView(chosenPatternText.container)\n',
       '','remove read-only duplicate box')
change(main,'dosePatternButton=secondaryButton("Alterar tipo de toma"){',
       'dosePatternButton=secondaryButton("Tipo de toma prescrito: "+patterns.first{it.second==chosenPattern}.first){',
       'single selector text')
change(main,'dosePatternButton.text="Alterar tipo de toma"',
       'dosePatternButton.text="Tipo de toma prescrito: "+patterns[index].first',
       'update single selector')
change(main,'m.indication=indication.edit.text.toString().trim(); m.time=timeText.edit.text.toString().trim()',
       'm.indication=indication.edit.text.toString().trim()',
       'preserve legacy time data')
# Explain schedules in one short sentence, rather than a large paragraph.
change(main,'''        box.addView(noteBox("Horário prescrito", "Confirma com a prescrição a hora inicial. " +
            "4/6/12 horas calculam avisos consecutivos. Jejum, almoço, jantar e deitar " +
            "usam a hora indicada; às refeições é preciso indicar todas as horas. " +
            "SOS não cria alarmes: regista a toma quando acontecer."))''',
       '''        box.addView(noteBox("Horário prescrito",
            "Confirma as horas na prescrição. SOS não emite alarmes."))''',
       'compact schedule help')

receiver=base/"notifications/NotificationReceiver.kt"
# Full-screen notifications are posted by the broadcast too. The foreground
# service upgrades that same notification id and provides looping audio.
# This avoids an orphaned notification if Android rejects starting the service.
anchor='            val isMedication=!medicationId.isNullOrBlank() ||\n                intent.getStringExtra("reminder_kind")=="medication"'
new=anchor+'''
            val scheduledDoseAt=intent.getLongExtra("scheduled_at",0L)
            if(!medicationId.isNullOrBlank() && scheduledDoseAt>0L &&
                ProfileStore(context).all().any{it.id==profileId}){
                val manager=context.getSystemService(NotificationManager::class.java)
                val alarmId=intent.getIntExtra("notification_id",991501)
                val channel=com.mediagenda.app.notifications.MedicationAlarmService.CHANNEL
                manager.createNotificationChannel(android.app.NotificationChannel(
                    channel,"ALARMES DE MEDICAÇÃO — ecrã completo",
                    NotificationManager.IMPORTANCE_HIGH).apply {
                    description="Alarme persistente até TOMEI ou ADIAR"
                    setSound(null,null)
                    enableVibration(true)
                    lockscreenVisibility=android.app.Notification.VISIBILITY_PRIVATE
                })
                // Delete only obsolete medication channels. Appointments, water
                // reminders and confirmation channels are deliberately retained.
                listOf("saudepratica_medication_alarm_v2",
                    "saudepratica_medication_alarm_v3").forEach{
                    manager.deleteNotificationChannel(it)
                }
                val open=Intent(context,MedicationAlarmActivity::class.java).apply{
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or
                        Intent.FLAG_ACTIVITY_CLEAR_TOP)
                    putExtras(intent)
                }
                val full=PendingIntent.getActivity(context,alarmId,open,
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
                val snooze=Intent(context,MedicationAlarmActionReceiver::class.java).apply{
                    action=MedicationAlarmService.ACTION_SNOOZE
                    putExtras(intent)
                    data=android.net.Uri.parse(
                        "saudepratica://snooze/$profileId/$medicationId/$scheduledDoseAt")
                }
                val confirm=Intent(context,IntakeActionReceiver::class.java).apply{
                    action=IntakeActionReceiver.ACTION
                    putExtra("profile_id",profileId)
                    putExtra("medication_id",medicationId)
                    putExtra("scheduled_at",scheduledDoseAt)
                    putExtra("notification_id",alarmId)
                }
                val n=NotificationCompat.Builder(context,channel)
                    .setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
                    .setContentTitle(intent.getStringExtra("title")?:"ALARME DE MEDICAÇÃO")
                    .setContentText("Tocar em TOMEI ou ADIAR 10 MIN")
                    .setCategory(NotificationCompat.CATEGORY_ALARM)
                    .setPriority(NotificationCompat.PRIORITY_MAX)
                    .setFullScreenIntent(full,true)
                    .setContentIntent(full)
                    .setAutoCancel(false).setOngoing(true)
                    .addAction(android.R.drawable.ic_media_pause,"ADIAR 10 MIN",
                        PendingIntent.getBroadcast(context,
                            ("snooze|$profileId|$medicationId|$scheduledDoseAt").hashCode(),
                            snooze,PendingIntent.FLAG_UPDATE_CURRENT or
                                PendingIntent.FLAG_IMMUTABLE))
                    .addAction(android.R.drawable.checkbox_on_background,"✓ TOMEI",
                        PendingIntent.getBroadcast(context,
                            ("taken|$profileId|$medicationId|$scheduledDoseAt").hashCode(),
                            confirm,PendingIntent.FLAG_UPDATE_CURRENT or
                                PendingIntent.FLAG_IMMUTABLE))
                runCatching{
                    val med=DataRepository(context,profileId).loadMedications()
                        .firstOrNull{it.id==medicationId}
                    val photos=med?.images.orEmpty()
                    MedicationPhotoLoader.load(context,photos,780)?.let{photo->
                        n.setLargeIcon(photo)
                        n.setStyle(NotificationCompat.BigPictureStyle()
                            .bigPicture(photo)
                            .bigLargeIcon(null as android.graphics.Bitmap?))
                    }
                    if(med!=null){
                        PersonalHealthStore(context,profileId)
                            .noteReminder(med.id,med.medication.ifBlank{"Medicação"},scheduledDoseAt)
                        IntakeBadgeManager.scheduleCheck(context,profileId,med.id,scheduledDoseAt)
                    }
                }
                manager.notify(alarmId,n.build())
                runCatching{MedicationAlarmService.start(context,intent)}
                    .onFailure{android.util.Log.e("SaudePraticaAlarm",
                        "Alarm service blocked; full screen notification remains",it)}
                return
            }'''
change(receiver,anchor,new,"alarm with safe full-screen fallback")
# Avoid endless new alarm notifications if user taps TOMEI and backend recording fails.
# Service already has a foreground notification and reuses the id.

build=root/"app/build.gradle.kts"
change(build,'versionCode = 76','versionCode = 77','versionCode')
change(build,'versionName = "1.9.66"','versionName = "1.9.67"','versionName')
print("v1.9.67: one intake type control, no obsolete medication channels, full-screen fallback, upgrade version")
