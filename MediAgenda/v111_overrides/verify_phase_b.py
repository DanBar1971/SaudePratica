"""Fail closed: Fase B alarm recovery, one patient per dose, original artwork."""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
read=lambda name:(base/"notifications"/name).read_text(encoding="utf-8")
group=read("MedicationAlarmGroup.kt")
scheduler=read("NotificationScheduler.kt")
service=read("MedicationAlarmService.kt")
snooze=read("MedicationSnoozeState.kt")
boot=read("BootReceiver.kt")
receiver=read("NotificationReceiver.kt")
history=(base/"HealthRecordsActivity.kt").read_text(encoding="utf-8")
assert "fun resetUpcoming(c:Context)" in group
assert "fun reset(c:Context)=" not in group, "destructive group reset regression"
assert "MedicationAlarmGroup.resetUpcoming(context)" in scheduler
assert "fun restore(c:Context)" in snooze
assert 'action="com.mediagenda.app.MED_ALARM_SNOOZED_FIRE"' in snooze
assert 'putExtra("profile_id",profile)' in snooze
assert 'putExtra("scheduled_at",due)' in snooze
assert 'putStringArrayListExtra("group_med_ids",ArrayList(members))' in snooze
assert "NotificationScheduler(app).scheduleAllProfiles()" in boot
assert "MedicationSnoozeState.restore(app)" in boot
assert "pending.finish()" in boot
assert "activeGroupIds=groupIds" in service
assert "activeGroupIds+activeMedication" in service
assert "MedicationAlarmCoordinator.wasHandled" in service
assert "setFullScreenIntent" in service and "setShowWhenLocked(true)" in service
assert "MedicationAlarmGroup.pending(context,profileId,scheduledDoseAt,groupIds)" in receiver
assert 'EXTRA_PROFILE_ID,profile' in service
assert 'EXTRA_CATEGORY,"intakes"' in service
assert 'if(groupIds.size<=1)' in service and 'confirm_medication_id' in service
assert "confirmScheduledIntake(medId,item.title,whenDue)" in history
assert "PersonalHealthStore(this,profileId)" in history
assert any("versionCode = "+str(n) in (root/"app/build.gradle.kts").read_text() for n in (102,103,104,105,106,107,108))
assert any('versionName = "'+v+'"' in (root/"app/build.gradle.kts").read_text() for v in ("1.9.92","1.9.93","1.9.94","1.9.95","1.9.96","1.9.97","1.9.98"))
manifest=(root/"app/src/main/AndroidManifest.xml").read_text()
for action in ("BOOT_COMPLETED","MY_PACKAGE_REPLACED","TIME_SET","TIMEZONE_CHANGED",
               "SCHEDULE_EXACT_ALARM_PERMISSION_STATE_CHANGED"):
    assert action in manifest, "missing recovery receiver for "+action
for name in ("saude_background.png","saude_icon.png","saude_splash.png"):
    p=root/"app/src/main/res/drawable-nodpi"/name
    assert p.exists() and p.stat().st_size > 1024, "missing original "+name
print("Fase B source invariants, profile navigation and original PNGs: OK")
