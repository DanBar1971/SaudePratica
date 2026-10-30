"""SaúdePrática v1.9.100: source invariants after alarms-only patch.

Actual Android 14/HyperOS tests and Full-Screen Intent authorization still mandatory.
"""
from pathlib import Path
p=Path('build-src/MediAgenda_Android_v1')
s=p/'app/src/main/java/com/mediagenda/app'
svc=(s/'notifications/MedicationAlarmService.kt').read_text(encoding='utf-8')
rec=(s/'notifications/NotificationReceiver.kt').read_text(encoding='utf-8')
action=(s/'notifications/IntakeActionReceiver.kt').read_text(encoding='utf-8')
record=(s/'data/PersonalHealthStore.kt').read_text(encoding='utf-8')
show=(s/'HealthRecordsActivity.kt').read_text(encoding='utf-8')
manifest=(p/'app/src/main/AndroidManifest.xml').read_text(encoding='utf-8')
version=(p/'app/build.gradle.kts').read_text(encoding='utf-8')
assert 'const val CHANNEL = "saudepratica_fullscreen_medication_v2"' in svc
assert 'NotificationManager.IMPORTANCE_HIGH).apply {' in svc
assert 'n.setFullScreenIntent(full,true)' in svc and 'if(!foreground)n.setFullScreenIntent' not in svc
assert 'ActivityManager.RunningAppProcessInfo.IMPORTANCE_FOREGROUND' in svc
assert 'appTasks.any' not in svc
assert 'val takenPi=PendingIntent.getBroadcast(this' in svc
assert 'val takenPi=PendingIntent.getActivity' not in svc
assert 'putStringArrayListExtra("group_med_ids",ArrayList(groupIds))' in svc
assert 'expiryHandler.postDelayed(it,60_000L)' in svc
assert 'noteIgnoredAlarm(id,activeScheduledAt)' in svc
assert 'records.noteReminder(id,' in svc
assert '.setContentTitle("SaúdePrática · Tomas por confirmar")' in svc
assert 'if(!locked && !isFinishing)' in svc
assert 'SnoozedMedicationNotice.show(context,profile,medId,whenOriginal,delay)' not in svc
# The UI click must never launch Tomas or PIN on TOMEI; timeout may navigate.
a=svc.index('actionRow.addView(control("✓ TOMEI"')
b=svc.index('layout.addView(actionRow)',a)
clicked=svc[a:b]
assert 'sendBroadcast(Intent(this, IntakeActionReceiver::class.java)' in clicked
assert 'startActivity(' not in clicked and 'HealthRecordsActivity' not in clicked
assert 'PendingIntent.getBroadcast(context,' in rec
assert 'action=IntakeActionReceiver.ACTION' in rec
assert 'val ids=(intent.getStringArrayListExtra("group_med_ids").orEmpty()+medId)' in action
assert 'store.confirmScheduledIntake(id,' in action
assert 'if(!DeviceAlarmRouting.isLocalPatient(context,profileId))return' in action
assert 'val unanswered=list("ignored_intakes")' in record
assert 'it.fields["status"]=="no_interaction"' in record
assert 'Inclui alarmes sem resposta após 60 segundos' in show
assert 'android.permission.USE_FULL_SCREEN_INTENT' in manifest
assert 'android:showWhenLocked="true"' in manifest
assert 'versionCode = 110' in version and 'versionName = "1.9.100"' in version
assert 'com.mediagenda.app.stable' in version
for name in ['saude_icon.png','saude_splash.png','saude_background.png']:
    img=p/'app/src/main/res/drawable-nodpi'/name
    assert img.is_file() and img.stat().st_size>1024
print('v1.9.100 passed: fullscreen eligibility, two actions, intake per medicine, 60s ignored, protected Tomas, branding')
