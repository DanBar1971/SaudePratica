"""SaúdePrática 1.9.97: Gemini handling, exact alarm visibility, no regression in TOMEI."""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
main=(base/"MainActivity.kt").read_text(encoding="utf-8")
meal=(base/"MealAiActivity.kt").read_text(encoding="utf-8")
gemini=(base/"MealGeminiDirect.kt").read_text(encoding="utf-8")
sched=(base/"notifications/NotificationScheduler.kt").read_text(encoding="utf-8")
recv=(base/"notifications/NotificationReceiver.kt").read_text(encoding="utf-8")
service=(base/"notifications/MedicationAlarmService.kt").read_text(encoding="utf-8")
assert '"Gemini · API Key e teste"' in main
assert "EXTRA_OPEN_GEMINI_SETTINGS" in main and "EXTRA_OPEN_GEMINI_SETTINGS" in meal
assert "configurarGemini()" in meal
assert "canScheduleExactAlarms()" in main
assert "Autorizar alarmes exatos no Android" in main
assert "Diagnóstico do último alarme" in main
assert 'getSharedPreferences("saudepratica_alarm_timing_v1"' in recv
assert 'putLong("scheduled",intended)' in recv and 'putLong("received",System.currentTimeMillis())' in recv
assert 'intent.action!="com.mediagenda.app.MED_ALARM_SNOOZED_FIRE"' in recv
assert 'listOf("gemini-3.8-flash","gemini-3.8-flash",' in gemini
assert '"gemini-3.6-flash"' in gemini
assert "Thread.sleep(if(attempt==0)1200L else 2500L)" in gemini
assert 'X-goog-api-key' in gemini
assert 'setExactAndAllowWhileIdle' in sched
assert 'setAndAllowWhileIdle' in sched
# Do not change the route which is confirmed working on the phone.
assert 'putExtra(com.mediagenda.app.HealthRecordsActivity.EXTRA_CATEGORY,"intakes")' in recv
assert 'EXTRA_PROFILE_ID,profileId' in recv
assert 'setFullScreenIntent' in recv and 'setFullScreenIntent' in service
v=(root/"app/build.gradle.kts").read_text()
assert any('versionCode = '+str(code) in v for code in (107,108)) and any('versionName = "'+name+'"' in v for name in ("1.9.97","1.9.98"))
for name in ("saude_icon.png","saude_splash.png","saude_background.png"):
    p=root/"app/src/main/res/drawable-nodpi"/name
    assert p.exists() and p.stat().st_size>1024,name
print("1.9.97: Gemini retry, key settings, exact alarm timing, TOMEI route and artwork OK")
