"""SaudePratica v1.9.100: correct fullscreen medication alarm flows.

Apply after all earlier source overlays. No edits to patient identifiers, clinical
sync, other notification categories, UI artwork, or signer identity.
"""
from pathlib import Path

root=Path('build-src/MediAgenda_Android_v1')
base=root/'app/src/main/java/com/mediagenda/app'

def change(rel,old,new,label):
    f=base/rel
    s=f.read_text(encoding='utf-8')
    n=s.count(old)
    if n!=1:raise RuntimeError(f'v119 {label}: anchor {n}, path {rel}')
    f.write_text(s.replace(old,new,1),encoding='utf-8')

service='notifications/MedicationAlarmService.kt'
change(service,'const val CHANNEL = "saudepratica_fullscreen_medication_v1"',
    'const val CHANNEL = "saudepratica_fullscreen_medication_v2"',
    'new HIGH channel to avoid old persisted quiet settings')

# Never mistake the existence of a running activity *task* for a visible screen:
# ActivityManager.appTasks.topActivity can point to a background task.
start='''        // When our own alarm screen is already going to open, a heads-up
        // notification would cover the drug name and dosage. Foreground service
        // still posts a notification but on a quiet, non-heads-up channel.
        // A background Activity may still be the appTasks.topActivity when
        // Android's KEYGUARD is showing. Treat that as LOCKED, not foreground.
'''
end='''        val mgr = getSystemService(NotificationManager::class.java)
'''
p=base/service;s=p.read_text(encoding='utf-8')
assert s.count(start)==1 and s.count(end)==1
p1=s.index(start);p2=s.index(end,p1)
s=s[:p1]+'''        // Android 14+ deliberately shows a heads-up instead of auto-launching
        // an FSI while UNLOCKED and our activity is not already visible. Never
        // suppress the FSI or use a quiet channel merely because appTasks is
        // running in the background.
        val locked=runCatching{
            getSystemService(android.app.KeyguardManager::class.java).isKeyguardLocked
        }.getOrDefault(false)
        val interactive=runCatching{
            getSystemService(android.os.PowerManager::class.java).isInteractive
        }.getOrDefault(true)
        val foreground=(!locked && interactive && runCatching{
            getSystemService(ActivityManager::class.java).runningAppProcesses
                ?.any{it.pid==android.os.Process.myPid() &&
                    it.importance==ActivityManager.RunningAppProcessInfo.IMPORTANCE_FOREGROUND}
                ?:false
        }.getOrDefault(false))
        val fsiAllowed=runCatching{
            if(android.os.Build.VERSION.SDK_INT>=34)
                getSystemService(NotificationManager::class.java)
                    .canUseFullScreenIntent()
            else true
        }.getOrDefault(false)
        android.util.Log.i("SaudePraticaAlarm",
            "fullscreen request: locked=$locked interactive=$interactive "+
                "activityVisible=$foreground fsiAllowed=$fsiAllowed")
'''+s[p2:]
p.write_text(s,encoding='utf-8')
change(service,
'''            if(foreground)"Alarme aberto na SaúdePrática" else
                "ALARMES DE MEDICAÇÃO — ecrã completo",
            if(foreground)NotificationManager.IMPORTANCE_LOW else
                NotificationManager.IMPORTANCE_HIGH).apply {''',
'''            "ALARMES DE MEDICAÇÃO — ecrã completo",
            NotificationManager.IMPORTANCE_HIGH).apply {''','always HIGH importance')
change(service,
'''            enableVibration(!foreground)
            if(!foreground)vibrationPattern = longArrayOf(0, 600, 350, 900)
''',
'''            enableVibration(true)
            vibrationPattern = longArrayOf(0, 600, 350, 900)
''', 'always vibration')
change(service,'val channelId=if(foreground)QUIET_CHANNEL else CHANNEL',
       'val channelId=CHANNEL', 'use HIGH notification channel') if 'val channelId=if(foreground)QUIET_CHANNEL else CHANNEL' in (base/service).read_text() else None
change(service,
'''        fun stop(context: Context, id: Int) {
            context.startService(Intent(context, MedicationAlarmService::class.java).apply {
                action = ACTION_STOP
                putExtra("notification_id", id)
            })
        }''',
'''        fun stop(context: Context, id: Int) {
            runCatching{
                context.startService(Intent(context, MedicationAlarmService::class.java).apply{
                    action = ACTION_STOP
                    putExtra("notification_id", id)
                })
            }.onFailure{android.util.Log.w("SaudePraticaAlarm",
                "Cannot stop inactive service from background",it)}
        }''', 'safe STOP when service not running')

# New code no longer assigns channelId in above section; insert it explicitly.
change(service,'        val mgr = getSystemService(NotificationManager::class.java)',
'''        val channelId=CHANNEL
        val mgr = getSystemService(NotificationManager::class.java)''','set channel')
change(service,'        if(!foreground)n.setFullScreenIntent(full,true)',
       '        n.setFullScreenIntent(full,true)', 'never remove FSI when app might be background')
change(service,'                "\\nEscolhe TOMEI ou ADIAR 10 MIN."))',
       '                "\\nEscolhe TOMEI ou ADIAR 10M."))', 'alarm label')
change(service,
'''        val taken = Intent(this, IntakeActionReceiver::class.java).apply {
            action = IntakeActionReceiver.ACTION
            putExtra("profile_id", profileId)
            putExtra("medication_id", medicationId)
            putExtra("scheduled_at", scheduledAt)
            putExtra("notification_id", currentId)
        }''',
'''        val taken = Intent(this, IntakeActionReceiver::class.java).apply {
            action = IntakeActionReceiver.ACTION
            data = Uri.parse("saudepratica://taken/$profileId/$medicationId/$scheduledAt")
            putExtra("profile_id", profileId)
            putExtra("medication_id", medicationId)
            putExtra("scheduled_at", scheduledAt)
            putExtra("notification_id", currentId)
            putStringArrayListExtra("group_med_ids",ArrayList(groupIds))
        }''','direct TOMEI action with group identity')
# Remove activity-based taken path and ensure notification action uses broadcast.
p=base/service;s=p.read_text()
a=s.index('        val review=Intent(this,com.mediagenda.app.HealthRecordsActivity::class.java).apply {')
b=s.index('        val snoozePi = PendingIntent.getBroadcast(',a)
s=s[:a]+'''        val takenPi=PendingIntent.getBroadcast(this,
            ("taken|$profileId|$medicationId|$scheduledAt").hashCode(),taken,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
'''+s[b:]
p.write_text(s)
change(service,'''        if(groupMeds.size>1){
            n.setContentText("Confirma cada medicamento em Tomas")''',
       '''        if(groupMeds.size>1){
            n.setContentText("TOMEI confirma todas as doses desta hora")''',
       'group TOMEI semantics')
# Real dose must exist in Tomas even if Android shows no notification or the
# patient does not react before timeout; one independent record per medicine.
change(service,
'''        activeProfile=profileId;activeMedication=medicationId;activeScheduledAt=scheduledAt
        activeGroupIds=groupIds''',
'''        // Register each grouped medication as unconfirmed before the alarm
        // is displayed. A TOMEI click will resolve each record atomically.
        runCatching{
            val available=DataRepository(this,profileId).loadMedications().associateBy{it.id}
            val records=PersonalHealthStore(this,profileId)
            (groupIds+medicationId).distinct().forEach{id->
                if(!MedicationAlarmCoordinator.wasHandled(this,profileId,id,scheduledAt))
                    available[id]?.let{records.noteReminder(id,
                        it.medication.ifBlank{"Medicação"},scheduledAt)}
            }
        }.onFailure{android.util.Log.e("SaudePraticaAlarm","Pending alarm storage",it)}
        activeProfile=profileId;activeMedication=medicationId;activeScheduledAt=scheduledAt
        activeGroupIds=groupIds''', 'register every pending group medicine')
change(service,'"Por favor, confirme a toma na SaúdePrática."',
       '"Por favor, confirme a toma no ecrã do alarme."',
       'speech instruction uses alarm buttons, no app navigation')
# 60 seconds is the requested fixed duration; no silent login on tap.
change(service,'expiryHandler.postDelayed(it,MedicationAlarmPreferences.seconds(this)*1000L)',
       'expiryHandler.postDelayed(it,60_000L)', 'exact 60-second timeout')
change(service,
'''        sendBroadcast(Intent(ACTION_TIMEOUT).setPackage(packageName))
        silence()''',
'''        if(!demo && activeProfile.isNotBlank()){
            // Explicitly retain a secure Tomas shortcut after auto-dismiss.
            // Do not start a clinical Activity from a background service;
            // Android 10+ restricts this and the screen may still be locked.
            runCatching{
                val manager=getSystemService(NotificationManager::class.java)
                val channel="saudepratica_alarm_unanswered_v1"
                manager.createNotificationChannel(NotificationChannel(channel,
                    "Tomas com alarme sem resposta",
                    NotificationManager.IMPORTANCE_DEFAULT).apply{
                    setSound(null,null);enableVibration(false)
                    lockscreenVisibility=Notification.VISIBILITY_PRIVATE
                })
                val review=Intent(this,
                    com.mediagenda.app.HealthRecordsActivity::class.java).apply{
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or
                        Intent.FLAG_ACTIVITY_CLEAR_TOP)
                    putExtra(com.mediagenda.app.HealthRecordsActivity.EXTRA_PROFILE_ID,
                        activeProfile)
                    putExtra(com.mediagenda.app.HealthRecordsActivity.EXTRA_CATEGORY,
                        "intakes")
                }
                val pi=PendingIntent.getActivity(this,
                    ("unanswered|$activeProfile|$activeScheduledAt").hashCode(),review,
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
                val quantity=(activeGroupIds+activeMedication).distinct().size
                manager.notify(("unanswered|$activeProfile|$activeScheduledAt").hashCode(),
                    NotificationCompat.Builder(this,channel)
                        .setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
                        .setContentTitle("SaúdePrática · Tomas por confirmar")
                        .setContentText(if(quantity>1)"$quantity medicamentos sem resposta"
                            else "Alarme sem resposta · confirmar em Tomas")
                        .setContentIntent(pi).setAutoCancel(true)
                        .setVisibility(NotificationCompat.VISIBILITY_PRIVATE)
                        .build())
            }.onFailure{android.util.Log.e("SaudePraticaAlarm",
                "Unanswered alarm shortcut",it)}
        }
        sendBroadcast(Intent(ACTION_TIMEOUT).setPackage(packageName)
            .putExtra("profile_id",activeProfile)
            .putExtra("scheduled_at",activeScheduledAt))
        silence()''', 'timeout opens safe review path')
change(service,
'''            layout.addView(label("Confirma cada toma individualmente na aplicação.",14f))''',
'''            layout.addView(label("TOMEI confirma todos os medicamentos desta hora.",14f))''',
       'group checkbox meaning')
change(service,
'''        layout.addView(label("O alarme termina após "+
            MedicationAlarmPreferences.seconds(this)+
            " segundos. Sem resposta, fica por confirmar.",13f))''',
'''        layout.addView(label("O alarme termina após 60 segundos. "+
            "Sem resposta, a toma fica por confirmar.",13f))''',
       'visible exact 60-second timeout')
change(service,
'''        if(!demo){
            actionRow.addView(View(this).apply{''',
'''        if(!demo){
            actionRow.addView(View(this).apply{''',
       'n/a') if False else None
p=base/service;s=p.read_text()
a=s.index('            actionRow.addView(control("✓ TOMEI",Color.rgb(0,132,108)){')
b=s.index('        })}\n        layout.addView(actionRow)',a)
s=s[:a]+'''            actionRow.addView(control("✓ TOMEI",Color.rgb(0,132,108)){
                // Confirm on a background receiver; never navigate to the app
                // or launch PIN just because the user pressed TOMEI.
                sendBroadcast(Intent(this, IntakeActionReceiver::class.java).apply{
                    action=IntakeActionReceiver.ACTION
                    data=Uri.parse("saudepratica://taken/$profile/$medId/"+
                        intent.getLongExtra("scheduled_at",0L))
                    putExtra("profile_id",profile)
                    putExtra("medication_id",medId)
                    putExtra("scheduled_at",intent.getLongExtra("scheduled_at",0L))
                    putExtra("notification_id",intent.getIntExtra("notification_id",0))
                    putStringArrayListExtra("group_med_ids",ArrayList(groupIds))
                })
                finish()
'''+s[b:]
p.write_text(s)
# Timeout inside visible alarm UI opens Tomas only when unlocked. On the
# lockscreen the user gets a private notification to tap *after* unlocking.
change(service,
'''                if(i.action==MedicationAlarmService.ACTION_TIMEOUT)finish()''',
'''                if(i.action==MedicationAlarmService.ACTION_TIMEOUT &&
                    i.getStringExtra("profile_id")==profile &&
                    i.getLongExtra("scheduled_at",0L)==
                        intent.getLongExtra("scheduled_at",0L)){
                    val locked=getSystemService(android.app.KeyguardManager::class.java)
                        .isKeyguardLocked
                    if(!locked && !isFinishing){
                        startActivity(Intent(this@MedicationAlarmActivity,
                            com.mediagenda.app.HealthRecordsActivity::class.java).apply{
                            putExtra(com.mediagenda.app.HealthRecordsActivity.EXTRA_PROFILE_ID,
                                profile)
                            putExtra(com.mediagenda.app.HealthRecordsActivity.EXTRA_CATEGORY,
                                "intakes")
                        })
                    }
                    finish()
                }''','timeout visible activity navigation only while unlocked')
# Snooze must be silent and close, without a second status popup.
change(service,'        SnoozedMedicationNotice.show(context,profile,medId,whenOriginal,delay)',
       '''        SnoozedMedicationNotice.clear(context,profile,medId,whenOriginal)
        context.getSystemService(NotificationManager::class.java)
            .cancel(intent.getIntExtra("notification_id",0))''',
       'quiet snooze has no extra notification')

# Direct notification TOMEI is a broadcast (even when foreground service
# could not start). This prevents Activity/login navigation.
receiver='notifications/NotificationReceiver.kt'
change(receiver,
'''                val confirm=Intent(context,com.mediagenda.app.HealthRecordsActivity::class.java).apply {
                    action="com.mediagenda.app.MEDICATION_OPEN_TOMAS"
                    data=android.net.Uri.parse("saudepratica://tomas/"+profileId+"/"+
                        medicationId+"/"+scheduledDoseAt)
                    putExtra(com.mediagenda.app.HealthRecordsActivity.EXTRA_PROFILE_ID,profileId)
                    putExtra(com.mediagenda.app.HealthRecordsActivity.EXTRA_CATEGORY,"intakes")
                    putExtra("stop_alarm_id",alarmId)
                    putExtra("alarm_medication_id",medicationId)
                    putExtra("alarm_scheduled_at",scheduledDoseAt)
                    if(groupIds.size<=1)putExtra("confirm_medication_id",medicationId)
                }''',
'''                val confirm=Intent(context,IntakeActionReceiver::class.java).apply {
                    action=IntakeActionReceiver.ACTION
                    data=android.net.Uri.parse("saudepratica://taken/"+profileId+"/"+
                        medicationId+"/"+scheduledDoseAt)
                    putExtra("profile_id",profileId)
                    putExtra("medication_id",medicationId)
                    putExtra("scheduled_at",scheduledDoseAt)
                    putExtra("notification_id",alarmId)
                    putStringArrayListExtra("group_med_ids",ArrayList(groupIds))
                }''','fallback TOMEI direct broadcast')
change(receiver,
'''                        PendingIntent.getActivity(context,
                            ("taken|$profileId|$medicationId|$scheduledDoseAt").hashCode(),
                            confirm,PendingIntent.FLAG_UPDATE_CURRENT or
                                PendingIntent.FLAG_IMMUTABLE))''',
'''                        PendingIntent.getBroadcast(context,
                            ("taken|$profileId|$medicationId|$scheduledDoseAt").hashCode(),
                            confirm,PendingIntent.FLAG_UPDATE_CURRENT or
                                PendingIntent.FLAG_IMMUTABLE))''','fallback notification broadcast Pi')

# One explicit TOMEI click on a group produces independent checked records,
# never silently marks an unattended dose taken.
intake='notifications/IntakeActionReceiver.kt'
p=base/intake;s=p.read_text(encoding='utf-8')
a=s.index('        val owner=ProfileStore(context).all().firstOrNull{it.id==profileId}?:return')
b=s.index('        val manager=context.getSystemService(NotificationManager::class.java)',a)
new='''        val owner=ProfileStore(context).all().firstOrNull{it.id==profileId}?:return
        if(!DeviceAlarmRouting.isLocalPatient(context,profileId))return
        val meds=DataRepository(context,profileId).loadMedications().associateBy{it.id}
        val ids=(intent.getStringArrayListExtra("group_med_ids").orEmpty()+medId)
            .filter{it.isNotBlank()}.distinct()
        if(ids.isEmpty() || ids.any{it !in meds})return
        val store=PersonalHealthStore(context,profileId)
        // Replays and duplicate taps are safe: confirmScheduledIntake is idempotent
        // per profile + medication + original scheduled time.
        try {
            ids.forEach{id->
                val med=meds.getValue(id)
                store.confirmScheduledIntake(id,med.medication.ifBlank{"Medicação"},
                    scheduledAt)
            }
        }catch(e:Exception){
            android.util.Log.e("SaudePratica","Could not confirm grouped dose",e)
            return
        }
        MedicationAlarmService.stop(context,notificationId)
        ids.forEach{SnoozedMedicationNotice.clear(context,profileId,it,scheduledAt)}
        IntakeBadgeManager.refresh(context,profileId)
'''
s=s[:a]+new+s[b:]
s=s.replace('''            .setContentText(med.medication.ifBlank{"Medicação"}+
                " — registada no histórico de tomas.")''',
'''            .setContentText(if(ids.size>1)
                "${ids.size} tomas individuais registadas no histórico."
                else meds.getValue(medId).medication.ifBlank{"Medicação"}+
                    " — registada no histórico de tomas.")''')
p.write_text(s)

# An ignored *alarm* becomes a pending case immediately at timeout, rather than
# hiding it until the ordinary 15-minute late-dose threshold.
records='data/PersonalHealthStore.kt'
change(records,
'''        return list("pending_intakes").filter{
            val time=it.fields["scheduled_at"]?.toLongOrNull()?:it.timestamp
            time>0L && time<=now-15L*60_000L &&''',
'''        val unanswered=list("ignored_intakes").filter{
            it.fields["status"]=="no_interaction"
        }.map{it.fields["medication_id"].orEmpty()+"|"+
            it.fields["scheduled_at"].orEmpty()}.toSet()
        return list("pending_intakes").filter{
            val time=it.fields["scheduled_at"]?.toLongOrNull()?:it.timestamp
            val medId=it.fields["medication_id"].orEmpty()
            // While ADIAR 10M is still active, do not show a new overdue
            // banner even after the original dose is >15 minutes old.
            val snoozedUntil=com.mediagenda.app.notifications.MedicationSnoozeState
                .until(context,id,medId,time)
            time>0L && snoozedUntil<=now &&
                (time<=now-15L*60_000L ||
                (medId+"|"+time) in unanswered) &&''',
       'badge overdue immediately when actual alarm timed out')
change('HealthRecordsActivity.kt',
'''        body.addView(label("Avisos há mais de 15 minutos sem confirmação. Isto não prova que a dose foi esquecida.",
            12f,color=muted).apply{setPadding(dp(5),0,0,dp(10))})''',
'''        body.addView(label("Inclui alarmes sem resposta após 60 segundos e avisos " +
            "sem confirmação há mais de 15 minutos. Isto não prova que a dose foi esquecida.",
            12f,color=muted).apply{setPadding(dp(5),0,0,dp(10))})''',
       'explain missed alarm immediately')

# App version advances, no new package/certificate or patient schema.
gradle=root/'app/build.gradle.kts';g=gradle.read_text(encoding='utf-8')
assert g.count('versionCode = 109')==1 and g.count('versionName = "1.9.99"')==1
for a,b in [('versionCode = 109','versionCode = 110'),
 ('versionName = "1.9.99"','versionName = "1.9.100"')]:g=g.replace(a,b,1)
gradle.write_text(g,encoding='utf-8')
print('1.9.100: always high-priority FSI; 2 actions; taken w/o login; 10m quiet snooze; 60s unconfirmed Tomas.')
