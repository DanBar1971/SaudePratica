"""SaúdePrática v1.9.85 — group medicines due at exactly the same time, by patient ID.

Keep the original single-pill photo alarm; grouped alarms open per-pill Tomas
without silently confirming every drug. Each scheduled medicine remains distinct.
"""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
src=Path("MediAgenda/v104_overrides")
def change(rel,old,new,label):
    f=base/rel
    s=f.read_text(encoding="utf-8")
    n=s.count(old)
    if n!=1:raise RuntimeError("v104 "+label+": anchor count "+str(n))
    f.write_text(s.replace(old,new,1),encoding="utf-8")

(base/"notifications/MedicationAlarmGroup.kt").write_text(
    (src/"MedicationAlarmGroup.kt").read_text(encoding="utf-8"),encoding="utf-8")

change("notifications/NotificationScheduler.kt",
    "        val profiles = ProfileStore(context).all()\n        profiles.forEach { profile ->",
    "        MedicationAlarmGroup.reset(context)\n        val profiles = ProfileStore(context).all()\n        profiles.forEach { profile ->",
    "group scheduler reset")
change("notifications/NotificationScheduler.kt",
    '        val dose=if(m.dose.isBlank())"" else',
    '''        MedicationAlarmGroup.record(context,profileId,m.id,
            next.atZone(zone).toInstant().toEpochMilli())
        val dose=if(m.dose.isBlank())"" else''',"record upcoming grouped slots")

change("notifications/NotificationReceiver.kt",
'''                if(MedicationAlarmCoordinator.wasConfirmed(context,profileId,
                    medicationId,scheduledDoseAt)){''',
'''                val groupIds=if(intent.hasExtra("group_med_ids"))
                    intent.getStringArrayListExtra("group_med_ids").orEmpty().distinct()
                else MedicationAlarmGroup.due(context,profileId,scheduledDoseAt,medicationId)
                if(groupIds.size>1){
                    MedicationAlarmGroup.pending(context,profileId,scheduledDoseAt,groupIds)
                    if(MedicationAlarmGroup.outstanding(context,profileId,scheduledDoseAt,
                            groupIds).isEmpty())return
                    if(intent.action!="com.mediagenda.app.MED_ALARM_SNOOZED_FIRE" &&
                        !MedicationAlarmGroup.claim(context,profileId,scheduledDoseAt,groupIds,medicationId))return
                    intent.putStringArrayListExtra("group_med_ids",ArrayList(groupIds))
                }else if(MedicationAlarmCoordinator.wasConfirmed(context,profileId,
                    medicationId,scheduledDoseAt)){''',"group receiver dispatch and per-pill record")

change("notifications/NotificationReceiver.kt",
'''                    .setContentTitle(runCatching{
                        val med=DataRepository(context,profileId).loadMedications()''',
'''                    .setContentTitle(if(groupIds.size>1)
                        profileName+" · "+groupIds.size+" medicamentos"
                        else runCatching{
                        val med=DataRepository(context,profileId).loadMedications()''',
"fallback group title")
change("notifications/NotificationReceiver.kt",
'''                val confirm=Intent(context,IntakeActionReceiver::class.java).apply{
                    action=IntakeActionReceiver.ACTION
                    putExtra("profile_id",profileId)
                    putExtra("medication_id",medicationId)
                    putExtra("scheduled_at",scheduledDoseAt)
                    putExtra("notification_id",alarmId)
                }''',
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
                }''',"fallback opens patient profile")
change("notifications/NotificationReceiver.kt",
'''                        PendingIntent.getBroadcast(context,
                            ("taken|$profileId|$medicationId|$scheduledDoseAt").hashCode(),
                            confirm,PendingIntent.FLAG_UPDATE_CURRENT or''',
'''                        PendingIntent.getActivity(context,
                            ("taken|$profileId|$medicationId|$scheduledDoseAt").hashCode(),
                            confirm,PendingIntent.FLAG_UPDATE_CURRENT or''',
"fallback TOMEI action opens Tomas")
change("notifications/NotificationReceiver.kt",
'''                    MedicationPhotoLoader.load(context,photos,780)?.let{photo->''',
'''                    if(groupIds.size<=1)MedicationPhotoLoader.load(context,photos,780)?.let{photo->''',
"fallback group no photo")
change("notifications/NotificationReceiver.kt",
'''                    if(med!=null){
                        PersonalHealthStore(context,profileId)
                            .noteReminder(med.id,med.medication.ifBlank{"Medicação"},scheduledDoseAt)''',
'''                    if(groupIds.size>1){
                        val byId=DataRepository(context,profileId)
                            .loadMedications().associateBy{it.id}
                        n.setStyle(NotificationCompat.InboxStyle().also{style->
                            groupIds.forEach{id->
                                byId[id]?.let{m->
                                    style.addLine(m.medication+" · "+m.dose.ifBlank{"Dose por confirmar"})
                                }
                            }
                        })
                    }
                    if(med!=null){
                        PersonalHealthStore(context,profileId)''',"group fallback list")

change("notifications/MedicationAlarmService.kt",
'''        if (intent?.action == ACTION_STOP) {
            val target=intent.getStringExtra("profile_id")''',
'''        if (intent?.action == ACTION_STOP) {
            val notification=intent.getIntExtra("notification_id",0)
            if(notification!=0 && notification!=currentId)return START_NOT_STICKY
            val target=intent.getStringExtra("profile_id")''',"stop matching foreground notification")
change("notifications/MedicationAlarmService.kt",
'''        if(!demo && MedicationAlarmCoordinator.wasConfirmed(this,profileId,
            medicationId,scheduledAt)){''',
'''        val groupIds=intent.getStringArrayListExtra("group_med_ids").orEmpty().distinct()
        if(!demo && (if(groupIds.size>1)
            MedicationAlarmGroup.outstanding(this,profileId,scheduledAt,groupIds).isEmpty()
            else MedicationAlarmCoordinator.wasConfirmed(this,profileId,
                medicationId,scheduledAt))){''',"group active if any outstanding")

change("notifications/MedicationAlarmService.kt",
'''        val drugName=med?.medication?:"Medicamento de teste"
        val doseText=med?.dose.orEmpty()''',
'''        val groupMeds=if(groupIds.size>1)DataRepository(this,profileId)
            .loadMedications().filter{it.id in groupIds} else emptyList()
        val drugName=if(groupMeds.size>1)groupMeds.size.toString()+" medicamentos"
            else med?.medication?:"Medicamento de teste"
        val doseText=if(groupMeds.size>1)"" else med?.dose.orEmpty()''',
"grouped notification title")

change("notifications/MedicationAlarmService.kt",
'''        val takenPi = PendingIntent.getBroadcast(this,
            ("taken|$profileId|$medicationId|$scheduledAt").hashCode(), taken,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)''',
'''        val review=Intent(this,com.mediagenda.app.HealthRecordsActivity::class.java).apply {
            action="com.mediagenda.app.MEDICATION_OPEN_TOMAS"
            data=Uri.parse("saudepratica://tomas/"+profileId+"/"+medicationId+"/"+scheduledAt)
            putExtra(com.mediagenda.app.HealthRecordsActivity.EXTRA_PROFILE_ID,profileId)
            putExtra(com.mediagenda.app.HealthRecordsActivity.EXTRA_CATEGORY,"intakes")
            putExtra("stop_alarm_id",currentId)
            putExtra("alarm_medication_id",medicationId)
            putExtra("alarm_scheduled_at",scheduledAt)
            if(groupMeds.size<=1)putExtra("confirm_medication_id",medicationId)
        }
        val takenPi=PendingIntent.getActivity(this,
            ("taken|$profileId|$medicationId|$scheduledAt").hashCode(),review,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)''',
"direct Tomas notification action")
change("notifications/MedicationAlarmService.kt",
'''        if(demo)n.addAction(android.R.drawable.ic_media_pause,"PARAR TESTE",snoozePi)''',
'''        if(groupMeds.size>1){
            n.setContentText("Confirma cada medicamento em Tomas")
            n.setStyle(NotificationCompat.InboxStyle().also{style->
                groupMeds.forEach{m->
                    style.addLine(m.medication+" · "+m.dose.ifBlank{"Dose por confirmar"})
                }
            })
        }
        if(demo)n.addAction(android.R.drawable.ic_media_pause,"PARAR TESTE",snoozePi)''',
"summary without boxes")
change("notifications/MedicationAlarmService.kt",
'''        med?.let{MedicationPhotoLoader.load(this,it.images,780)}?.let{photo->''',
'''        if(groupMeds.size<=1)
        med?.let{MedicationPhotoLoader.load(this,it.images,780)}?.let{photo->''',
"photos remain single-only")

change("notifications/MedicationAlarmService.kt",
'''        val demo=intent.getBooleanExtra(MedicationAlarmService.EXTRA_DEMO,false)
        if(!demo && MedicationAlarmCoordinator.wasConfirmed(this,profile,medId,''',
'''        val demo=intent.getBooleanExtra(MedicationAlarmService.EXTRA_DEMO,false)
        val groupIds=intent.getStringArrayListExtra("group_med_ids").orEmpty()
        if(!demo && groupIds.size<=1 &&
            MedicationAlarmCoordinator.wasConfirmed(this,profile,medId,''',
"activity group guard")
change("notifications/MedicationAlarmService.kt",
'''        layout.addView(label(medicine?.medication?:
            if(demo)"Medicamento de teste" else "Medicação",29f))''',
'''        if(groupIds.size>1){
            val medicines=DataRepository(this,profile).loadMedications().associateBy{it.id}
            layout.addView(label("Medicamentos programados para esta hora",20f))
            groupIds.forEach{member->
                medicines[member]?.let{m->
                    val taken=MedicationAlarmCoordinator.wasConfirmed(this,profile,member,
                        intent.getLongExtra("scheduled_at",0L))
                    layout.addView(label((if(taken)"✓ " else "☐ ")+m.medication+
                        " · "+m.dose.ifBlank{"Confirma na prescrição"},19f))
                }
            }
            layout.addView(label("Confirma cada toma individualmente na aplicação.",14f))
        }else{
        layout.addView(label(medicine?.medication?:
            if(demo)"Medicamento de teste" else "Medicação",29f))''',"group list activity")
change("notifications/MedicationAlarmService.kt",
'''        layout.addView(label("O alarme termina após "+
            MedicationAlarmPreferences.seconds(this)+''',
'''        }
        layout.addView(label("O alarme termina após "+
            MedicationAlarmPreferences.seconds(this)+''',"close single visual block")
change("notifications/MedicationAlarmService.kt",
'''                if(i.action==MedicationAlarmCoordinator.ACTION_RESOLVED &&
                    i.getStringExtra("profile_id")==profile &&
                    i.getStringExtra("medication_id")==medId &&
                    i.getLongExtra("scheduled_at",0L)==
                        intent.getLongExtra("scheduled_at",0L))finish()''',
'''                if(i.action==MedicationAlarmCoordinator.ACTION_RESOLVED &&
                    i.getStringExtra("profile_id")==profile &&
                    i.getLongExtra("scheduled_at",0L)==
                        intent.getLongExtra("scheduled_at",0L) &&
                    (if(groupIds.size>1)
                        MedicationAlarmGroup.outstanding(this@MedicationAlarmActivity,
                            profile,intent.getLongExtra("scheduled_at",0L),
                            groupIds).isEmpty()
                     else i.getStringExtra("medication_id")==medId))finish()''',
"do not dismiss group while other doses pending")
change("notifications/MedicationAlarmService.kt",
'''            sendBroadcast(Intent(this, IntakeActionReceiver::class.java).apply {
                action = IntakeActionReceiver.ACTION
                putExtra("profile_id", profile)
                putExtra("medication_id", medId)
                putExtra("scheduled_at", intent.getLongExtra("scheduled_at", 0L))
                putExtra("notification_id", intent.getIntExtra("notification_id", 0))
            })
            finish()''',
'''            if(groupIds.size<=1){
                sendBroadcast(Intent(this, IntakeActionReceiver::class.java).apply {
                    action = IntakeActionReceiver.ACTION
                    putExtra("profile_id", profile)
                    putExtra("medication_id", medId)
                    putExtra("scheduled_at", intent.getLongExtra("scheduled_at", 0L))
                    putExtra("notification_id", intent.getIntExtra("notification_id", 0))
                })
            }else MedicationAlarmService.stop(this,intent.getIntExtra("notification_id",0))
            startActivity(Intent(this,com.mediagenda.app.HealthRecordsActivity::class.java).apply{
                putExtra(com.mediagenda.app.HealthRecordsActivity.EXTRA_PROFILE_ID,profile)
                putExtra(com.mediagenda.app.HealthRecordsActivity.EXTRA_CATEGORY,"intakes")
                putExtra("stop_alarm_id",intent.getIntExtra("notification_id",0))
            })
            finish()''',
"TOMEI button to per-user Tomas; group never auto-confirms")

change("HealthRecordsActivity.kt",
'''        store=PersonalHealthStore(this,profileId)
        category=intent.getStringExtra(EXTRA_CATEGORY)''',
'''        store=PersonalHealthStore(this,profileId)
        if(intent.action=="com.mediagenda.app.MEDICATION_OPEN_TOMAS"){
            val medId=intent.getStringExtra("alarm_medication_id").orEmpty()
            val at=intent.getLongExtra("alarm_scheduled_at",0L)
            val stopId=intent.getIntExtra("stop_alarm_id",0)
            if(stopId!=0)com.mediagenda.app.notifications.MedicationAlarmService.stop(
                this,stopId)
            val toConfirm=intent.getStringExtra("confirm_medication_id").orEmpty()
            val now=System.currentTimeMillis()
            if(medId==toConfirm && medId.isNotBlank() &&
                at in (now-48L*60*60*1000)..(now+300_000L)) {
                val med=DataRepository(this,profileId).loadMedications()
                    .firstOrNull{it.id==medId}
                if(med!=null)runCatching{
                    store.confirmScheduledIntake(medId,
                        med.medication.ifBlank{"Medicação"},at)
                }
            }
        }
        category=intent.getStringExtra(EXTRA_CATEGORY)''',
"review Tomas profile; individual confirmation only")

build=root/"app/build.gradle.kts"
s=build.read_text(encoding="utf-8")
assert s.count("versionCode = 94")==1 and s.count('versionName = "1.9.84"')==1
build.write_text(s.replace("versionCode = 94","versionCode = 95",1)
    .replace('versionName = "1.9.84"','versionName = "1.9.85"',1),
    encoding="utf-8")
print("v1.9.85: group alarm by profile/time; no photos for groups; individually confirm doses")
