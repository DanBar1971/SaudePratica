#!/usr/bin/env python3
"""Reject unsafe full-screen medication alarm and cross-profile intake regressions."""
from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app')
def source(name):
 p=root/name
 assert p.is_file(),p
 return p.read_text(encoding='utf-8')
def required(text,*words):
 for x in words: assert x in text, 'Missing invariant: '+x

app=source('SaudePraticaApplication.kt')
required(app,'if(activity is com.mediagenda.app.notifications.MedicationAlarmActivity)return',
  'authenticatedUiVisible=!requiresPin','fun isAuthenticatedUiVisible():Boolean=authenticatedUiVisible')
# Alarm action bypasses the app PIN, but all non-alarm activity gates remain.
required(app,'AppPinStore(activity).enabled()', 'activity.startActivity(Intent(activity,AppPinActivity::class.java)')
service=source('notifications/MedicationAlarmService.kt')
required(service,'setShowWhenLocked(true)','setTurnScreenOn(true)',
  'SaudePraticaApplication.isAuthenticatedUiVisible()',
  'n.setFullScreenIntent(full,true)','MedicationAlarmService.ACTION_SNOOZE',
  'IntakeActionReceiver.ACTION','startTimeout()','60_000L')
assert 'WindowManager.LayoutParams.FLAG_DISMISS_KEYGUARD' not in service.split('class MedicationAlarmActivity')[1].split('class MedicationAlarmActionReceiver')[0].replace('FLAG_DISMISS_KEYGUARD is deprecated','')
assert 'runningAppProcesses' not in service
routing=source('notifications/DeviceAlarmRouting.kt')
assert 'if (caregiver != null && caregiver in ids) return caregiver' not in routing
required(routing,'explicit(c: Context)','isLocalPatient','device_profile_id')
notif=source('notifications/NotificationReceiver.kt')
assert 'saudepratica_caregiver_notice_v1' not in notif
required(notif,'if(!DeviceAlarmRouting.isLocalPatient(context,profileId))',
    'PersonalHealthStore(context,profileId).noteReminder(',
    'MedicationAlarmService.start(context,intent)')
intakes=source('HealthRecordsActivity.kt')
assert 'Tomas atrasadas da família' not in intakes
assert 'Tomas confirmadas da família' not in intakes
required(intakes,'showIntakeHistory()', 'store.list("intakes")',
    'store.overdueIntakes()', 'Cada familiar tem as suas TOMAS no próprio perfil')
badge=source('notifications/IntakeBadgeManager.kt')
assert 'own+ProfileStore(context).all()' not in badge
required(badge,'PersonalHealthStore(context,selected).overdueIntakes().size')
main=source('MainActivity.kt')
required(main,'val lateTomas=runCatching {\n            PersonalHealthStore(this,activeProfileId)',
    '💊 $doseCount por confirmar','📅 $agendaCount próximos',
    'DeviceAlarmRouting\n                .explicit(this)==profile.id',
    '📱 Associar alarmes a este telemóvel',
    'NÃO TEM CAIXA · Só lamelas / blisters',
    'chosenPhotoMode="unboxed"')
assert 'if(caregiver)profiles.all()' not in main
manifest=Path('build-src/MediAgenda_Android_v1/app/src/main/AndroidManifest.xml').read_text(encoding='utf-8')
required(manifest,'android.permission.USE_FULL_SCREEN_INTENT',
    'android:name=".notifications.MedicationAlarmActivity"',
    'android:showWhenLocked="true"','android:turnScreenOn="true"')
print('PASS v122: alarm PIN exemption, locked FSI, correct foreground, own patient routing, isolated Tomas, per-profile badges and clear SEM CAIXA option.')
