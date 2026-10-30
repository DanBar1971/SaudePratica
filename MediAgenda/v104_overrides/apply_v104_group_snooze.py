"""Snoozed medication group safety and immediate Tomas confirmation.
Run after apply_v104.py, before the Android build.
"""
from pathlib import Path
base=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app")
def change(rel,a,b,name):
    p=base/rel
    s=p.read_text(encoding="utf-8")
    if s.count(a)!=1:raise RuntimeError("Group snooze "+name+": "+str(s.count(a)))
    p.write_text(s.replace(a,b,1),encoding="utf-8")

change("notifications/MedicationAlarmCoordinator.kt",
'''        val request=("snoozed|"+profile+"|"+medication+"|"+scheduledAt).hashCode()''',
'''        val members=MedicationAlarmGroup.members(c,profile,scheduledAt)
        // A group snooze must remain active while ANY grouped medication
        // has not been confirmed, even if the first/leader has been taken.
        if(members.size>1 && members.any{!wasConfirmed(c,profile,it,scheduledAt)})
            return
        val leader=MedicationAlarmGroup.leader(c,profile,scheduledAt)
        val alarmMedicine=if(members.size>1 && leader.isNotBlank())leader else medication
        val request=("snoozed|"+profile+"|"+alarmMedicine+"|"+scheduledAt).hashCode()''',
"preserve grouped snooze until all confirmed")
change("notifications/MedicationAlarmCoordinator.kt",
'''            data=Uri.parse("saudepratica://med/"+profile+"/"+medication+"/"+scheduledAt)''',
'''            data=Uri.parse("saudepratica://med/"+profile+"/"+alarmMedicine+"/"+scheduledAt)''',
"cancel group leader snooze")
change("notifications/MedicationAlarmCoordinator.kt",
'''        SnoozedMedicationNotice.clear(c,profile,medication,scheduledAt)''',
'''        SnoozedMedicationNotice.clear(c,profile,alarmMedicine,scheduledAt)''',
"clear group leader status")
change("notifications/MedicationAlarmCoordinator.kt",
'''                putExtra("medication_id",medication)
                putExtra("scheduled_at",scheduledAt)''',
'''                putExtra("medication_id",alarmMedicine)
                putExtra("scheduled_at",scheduledAt)''',
"stop correct member foreground session")
change("notifications/MedicationAlarmService.kt",
'''        val name=runCatching{
            DataRepository(context,profile).loadMedications()
                .firstOrNull{it.id==medication}?.medication
        }.getOrNull().orEmpty().ifBlank{"Medicação"}''',
'''        val linked=MedicationAlarmGroup.members(context,profile,scheduledAt)
        val name=if(linked.size>1)linked.size.toString()+" medicamentos"
        else runCatching{
            DataRepository(context,profile).loadMedications()
                .firstOrNull{it.id==medication}?.medication
        }.getOrNull().orEmpty().ifBlank{"Medicação"}''',
"group postponed label")

change("notifications/MedicationAlarmService.kt",
'''            startActivity(Intent(this,com.mediagenda.app.HealthRecordsActivity::class.java).apply{
                putExtra(com.mediagenda.app.HealthRecordsActivity.EXTRA_PROFILE_ID,profile)
                putExtra(com.mediagenda.app.HealthRecordsActivity.EXTRA_CATEGORY,"intakes")
                putExtra("stop_alarm_id",intent.getIntExtra("notification_id",0))
            })''',
'''            startActivity(Intent(this,com.mediagenda.app.HealthRecordsActivity::class.java).apply{
                if(groupIds.size<=1){
                    action="com.mediagenda.app.MEDICATION_OPEN_TOMAS"
                    putExtra("confirm_medication_id",medId)
                }
                putExtra("alarm_medication_id",medId)
                putExtra("alarm_scheduled_at",intent.getLongExtra("scheduled_at",0L))
                putExtra(com.mediagenda.app.HealthRecordsActivity.EXTRA_PROFILE_ID,profile)
                putExtra(com.mediagenda.app.HealthRecordsActivity.EXTRA_CATEGORY,"intakes")
                putExtra("stop_alarm_id",intent.getIntExtra("notification_id",0))
            })''',
"single TOMEI always visible as confirmed inside opened Tomas")
print("group snooze leader and individual confirmations protected")
