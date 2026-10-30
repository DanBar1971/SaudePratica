from pathlib import Path
p=Path('build-src/MediAgenda_Android_v1'); base=p/'app/src/main/java/com/mediagenda/app'
hc=(base/'ActivityHealthConnect.kt').read_text(); w=(base/'WellnessActivity.kt').read_text(); st=(base/'data/WellnessStore.kt').read_text();m=(base/'MainActivity.kt').read_text();man=(p/'app/src/main/AndroidManifest.xml').read_text(); gradle=(p/'app/build.gradle.kts').read_text()
for name in ('READ_OXYGEN_SATURATION','READ_WEIGHT','READ_RESTING_HEART_RATE','READ_BLOOD_PRESSURE','READ_RESPIRATORY_RATE'):
    assert name in hc and name in man,name
for name in ('OxygenSaturationRecord','WeightRecord','RestingHeartRateRecord','BloodPressureRecord','ReadRecordsRequestUsingFilters'):
    assert name in hc,name
assert 'BodyMeasurements(this,profileId)' in hc and 'fun addWeight(' in (base/'data/BodyMeasurements.kt').read_text()
assert 'val newTarget=(store.todayMl()+extra)' in w
assert 'fun increaseTarget(' in st and 'NotificationScheduler(this).scheduleNextWater(profileId)' in w
assert 'DashboardModule("📅", "Agenda", "Consultas e exames")' in m
assert 'showHealthcareSearchHelp()' in m
assert any('versionName = "'+v+'"' in gradle for v in ("1.9.96","1.9.97","1.9.98")) and any('versionCode = '+str(v) in gradle for v in (106,107,108))
for file in ['saude_icon.png','saude_background.png','saude_splash.png']:
    assert (p/'app/src/main/res/drawable-nodpi'/file).stat().st_size>1024
print('Fase E + descoberta Fase D + arte original: OK')