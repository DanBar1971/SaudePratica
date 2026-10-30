"""SaúdePrática v1.9.83 hotfix: deduplicate medication alarm UI, restore drug dose,
cancel postponed alarm on any completed intake, and expose meal deletion.
Applied after v101, before graphics validation and release build.
"""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
source=Path("MediAgenda/v102_overrides")

def change(path,old,new,name):
    s=path.read_text(encoding="utf-8")
    n=s.count(old)
    if n!=1:raise RuntimeError(f"v102 {name}: expected one anchor, got {n}")
    path.write_text(s.replace(old,new,1),encoding="utf-8")

alarm=base/"notifications/MedicationAlarmService.kt"
change(alarm,
 '        const val CHANNEL = "saudepratica_fullscreen_medication_v1"',
 '        const val CHANNEL = "saudepratica_fullscreen_medication_v1"\n'
 '        const val QUIET_CHANNEL = "saudepratica_alarm_screen_visible_v1"',
 "quiet UI notification channel")
change(alarm,
 '''        if (intent?.action == ACTION_STOP) {
            silence()
            stopForeground(STOP_FOREGROUND_REMOVE)''',
 '''        if (intent?.action == ACTION_STOP) {
            val target=intent.getStringExtra("profile_id")
            if(target!=null && (target!=activeProfile ||
                intent.getStringExtra("medication_id")!=activeMedication ||
                intent.getLongExtra("scheduled_at",0L)!=activeScheduledAt))
                return START_NOT_STICKY
            silence()
            stopForeground(STOP_FOREGROUND_REMOVE)''',
 "stop only matching alarm")
change(alarm,
 '''        activeProfile=profileId;activeMedication=medicationId;activeScheduledAt=scheduledAt''',
 '''        if(!demo && MedicationAlarmCoordinator.wasConfirmed(this,profileId,
            medicationId,scheduledAt)){
            SnoozedMedicationNotice.clear(this,profileId,medicationId,scheduledAt)
            stopSelf();return START_NOT_STICKY
        }
        activeProfile=profileId;activeMedication=medicationId;activeScheduledAt=scheduledAt''',
 "check intake before playing alarm")
change(alarm,
 '''        val mgr = getSystemService(NotificationManager::class.java)
        mgr.createNotificationChannel(NotificationChannel(
            CHANNEL, "ALARMES DE MEDICAÇÃO — ecrã completo",
            NotificationManager.IMPORTANCE_HIGH).apply {''',
 '''        // When our own alarm screen is already going to open, a heads-up
        // notification would cover the drug name and dosage. Foreground service
        // still posts a notification but on a quiet, non-heads-up channel.
        val foreground=runCatching {
            val manager=getSystemService(ActivityManager::class.java)
            manager.appTasks.any{ task->
                task.taskInfo.isRunning && task.taskInfo.topActivity?.packageName==packageName
            }
        }.getOrDefault(false)
        val channelId=if(foreground)QUIET_CHANNEL else CHANNEL
        val mgr = getSystemService(NotificationManager::class.java)
        mgr.createNotificationChannel(NotificationChannel(
            channelId,
            if(foreground)"Alarme aberto na SaúdePrática" else
                "ALARMES DE MEDICAÇÃO — ecrã completo",
            if(foreground)NotificationManager.IMPORTANCE_LOW else
                NotificationManager.IMPORTANCE_HIGH).apply {''',
 "avoid banner over alarm activity")
change(alarm,
 '''            enableVibration(true)
            vibrationPattern = longArrayOf(0, 600, 350, 900)''',
 '''            enableVibration(!foreground)
            if(!foreground)vibrationPattern = longArrayOf(0, 600, 350, 900)''',
 "only channel vibration on background")
change(alarm,
 '''        val n = NotificationCompat.Builder(this, CHANNEL)
            .setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
            .setContentTitle(title)
            .setContentText("ALARME DE MEDICAÇÃO · " + doseText)
            .setStyle(NotificationCompat.BigTextStyle().bigText(
                "Alarme a tocar. Escolhe TOMEI depois de tomar ou ADIAR 10 MIN."))
            .setContentIntent(full)
            .setFullScreenIntent(full, true)''',
 '''        val n = NotificationCompat.Builder(this, channelId)
            .setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
            .setContentTitle(title)
            .setContentText("💊 "+drugName+" · Dose: "+doseText.ifBlank{"Confirmar dose"})
            .setStyle(NotificationCompat.BigTextStyle().bigText(
                "Medicamento: "+drugName+"\\nDose: "+
                doseText.ifBlank{"Confirmar dose na prescrição"}+
                "\\nEscolhe TOMEI ou ADIAR 10 MIN."))
            .setContentIntent(full)''',
 "restore title and dose in notification")
change(alarm,
 '''        if(demo)n.addAction(android.R.drawable.ic_media_pause,"PARAR TESTE",snoozePi)''',
 '''        if(!foreground)n.setFullScreenIntent(full,true)
        if(demo)n.addAction(android.R.drawable.ic_media_pause,"PARAR TESTE",snoozePi)''',
 "full-screen only when app backgrounded")
change(alarm,
 '''            n.setStyle(NotificationCompat.BigPictureStyle().bigPicture(photo)
                .bigLargeIcon(null as android.graphics.Bitmap?))''',
 '''            n.setStyle(NotificationCompat.BigPictureStyle().bigPicture(photo)
                .bigLargeIcon(null as android.graphics.Bitmap?)
                .setSummaryText(drugName+" · Dose: "+doseText.ifBlank{"Confirmar"}))''',
 "photo must retain medicine and dose")
change(alarm,
 '''        val foreground=runCatching {
            val manager=getSystemService(ActivityManager::class.java)
            manager.appTasks.any{ task->
                task.taskInfo.isRunning && task.taskInfo.topActivity?.packageName==packageName
            }
        }.getOrDefault(false)
        if(foreground){
            runCatching{startActivity(open)}''',
 '''        if(foreground){
            runCatching{startActivity(open)}''',
 "reuse foreground state")

change(alarm,
 '''        val demo=intent.getBooleanExtra(MedicationAlarmService.EXTRA_DEMO,false)
        val medicine=if(demo)null else DataRepository(this,profile).loadMedications()''',
 '''        val demo=intent.getBooleanExtra(MedicationAlarmService.EXTRA_DEMO,false)
        if(!demo && MedicationAlarmCoordinator.wasConfirmed(this,profile,medId,
            intent.getLongExtra("scheduled_at",0L))){finish();return}
        val medicine=if(demo)null else DataRepository(this,profile).loadMedications()''',
 "do not show already confirmed dose")
change(alarm,
 '''        layout.addView(label(medicine?.dose.orEmpty(),21f))''',
 '''        layout.addView(label("Dose: "+medicine?.dose.orEmpty().ifBlank{
            if(demo)"Teste" else "Confirma na prescrição"},21f))''',
 "explicit dose label")
change(alarm,
 '''                if(i.action==MedicationAlarmService.ACTION_TIMEOUT)finish()''',
 '''                if(i.action==MedicationAlarmService.ACTION_TIMEOUT)finish()
                if(i.action==MedicationAlarmCoordinator.ACTION_RESOLVED &&
                    i.getStringExtra("profile_id")==profile &&
                    i.getStringExtra("medication_id")==medId &&
                    i.getLongExtra("scheduled_at",0L)==
                        intent.getLongExtra("scheduled_at",0L))finish()''',
 "finish alarm UI after manual confirmation")
change(alarm,
 '''            IntentFilter(MedicationAlarmService.ACTION_TIMEOUT),
            ContextCompat.RECEIVER_NOT_EXPORTED)''',
 '''            IntentFilter().apply{
                addAction(MedicationAlarmService.ACTION_TIMEOUT)
                addAction(MedicationAlarmCoordinator.ACTION_RESOLVED)
            },
            ContextCompat.RECEIVER_NOT_EXPORTED)''',
 "receive resolved dose event")
change(alarm,
 '''        if (profile.isBlank() || medId.isBlank() || whenOriginal <= 0L) return
        val upcoming = Intent(context, NotificationReceiver::class.java).apply {''',
 '''        if (profile.isBlank() || medId.isBlank() || whenOriginal <= 0L) return
        if(MedicationAlarmCoordinator.wasConfirmed(context,profile,medId,whenOriginal)){
            MedicationAlarmCoordinator.resolve(context,profile,medId,whenOriginal)
            return
        }
        val upcoming = Intent(context, NotificationReceiver::class.java).apply {''',
 "reject snooze after confirmation")

recv=base/"notifications/NotificationReceiver.kt"
change(recv,
 '''            if(!medicationId.isNullOrBlank() && scheduledDoseAt>0L &&
                ProfileStore(context).all().any{it.id==profileId}){
                val selected=''', 
 '''            if(!medicationId.isNullOrBlank() && scheduledDoseAt>0L &&
                ProfileStore(context).all().any{it.id==profileId}){
                if(MedicationAlarmCoordinator.wasConfirmed(context,profileId,
                    medicationId,scheduledDoseAt)){
                    MedicationAlarmCoordinator.resolve(context,profileId,
                        medicationId,scheduledDoseAt)
                    return
                }
                val selected=''', 
 "ignore fired snooze after confirmed intake")
change(recv,
 '''                    .setContentTitle(intent.getStringExtra("title")?:"ALARME DE MEDICAÇÃO")
                    .setContentText("Tocar em TOMEI ou ADIAR 10 MIN")''',
 '''                    .setContentTitle(runCatching{
                        val med=DataRepository(context,profileId).loadMedications()
                            .firstOrNull{it.id==medicationId}
                        (profileName.ifBlank{"SaúdePrática"})+" · "+
                            (med?.medication?:intent.getStringExtra("title").orEmpty())
                    }.getOrDefault("ALARME DE MEDICAÇÃO"))
                    .setContentText(runCatching{
                        val med=DataRepository(context,profileId).loadMedications()
                            .firstOrNull{it.id==medicationId}
                        "Dose: "+med?.dose.orEmpty().ifBlank{"Confirma na prescrição"}
                    }.getOrDefault("Tocar em TOMEI ou ADIAR 10 MIN"))''',
 "fallback notification title and dose")
change(recv,
 '''                            .bigPicture(photo)
                            .bigLargeIcon(null as android.graphics.Bitmap?))''',
 '''                            .bigPicture(photo)
                            .bigLargeIcon(null as android.graphics.Bitmap?)
                            .setSummaryText(med?.medication.orEmpty()+
                                " · Dose: "+med?.dose.orEmpty()))''',
 "fallback photo summary")

store=base/"data/PersonalHealthStore.kt"
change(store,
 '''        return synchronized(intakeLock){
            val key=scheduledAt.toString()''',
 '''        val confirmed=synchronized(intakeLock){
            val key=scheduledAt.toString()''',
 "explicit confirmed result")
change(store,
 '''            confirmed
        }
    }

    /** The main medication-list Tomei button''',
 '''            confirmed
        }
        // All confirmation paths (notification, Tomas and medication list)
        // must cancel any 10-minute snooze for this original dose.
        runCatching{
            com.mediagenda.app.notifications.MedicationAlarmCoordinator.resolve(
                context,id,medicationId,scheduledAt)
        }.onFailure{android.util.Log.w("SaudePraticaAlarm",
            "Could not cancel postponed alarm",it)}
        return confirmed
    }

    /** The main medication-list Tomei button''',
 "all routes cancel snooze")
meal=base/"MealAiActivity.kt"
change(meal,
 '''            p.addView(line)
        }
    }
    private fun showMealDetails''',
 '''            p.addView(line)
            p.addView(button("🗑 Eliminar refeição de "+whenDate){
                MaterialAlertDialogBuilder(this)
                    .setTitle("Eliminar esta refeição?")
                    .setMessage("Este registo e a fotografia associada serão apagados " +
                        "apenas do perfil atual. Esta ação não pode ser anulada.")
                    .setNegativeButton("Cancelar",null)
                    .setPositiveButton("Eliminar"){_,_->
                        runCatching{diary.remove(row.getString("id"))}
                            .onSuccess{draw()}
                            .onFailure{alert(it.message?:"Erro ao eliminar refeição.")}
                    }.show()
            })
        }
    }
    private fun showMealDetails''',
 "visible delete button in meal history")
change(meal,
 '''            .setNeutralButton("Eliminar"){_,_->''',
 '''            .setNeutralButton("🗑 Eliminar refeição"){_,_->''',
 "descriptive delete action")

(base/"notifications/MedicationAlarmCoordinator.kt").write_text(
    (source/"MedicationAlarmCoordinator.kt").read_text(encoding="utf-8"),encoding="utf-8")
print("v102: cancel snoozes on all intake routes, restore name/dose, quiet visible alarm screen, meal deletion")
