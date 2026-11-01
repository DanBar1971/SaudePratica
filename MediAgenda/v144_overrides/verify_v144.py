#!/usr/bin/env python3
"""Static acceptance tests for NON-INVASIVE alarm permission diagnostics."""
from pathlib import Path
import xml.etree.ElementTree as ET

root=Path("build-src/MediAgenda_Android_v1/app")
src=root/"src/main/java/com/mediagenda/app"
gradle=(root/"build.gradle.kts").read_text()
manifest=(root/"src/main/AndroidManifest.xml").read_text()
main=(src/"MainActivity.kt").read_text()
panel=(src/"AlarmPermissionsActivity.kt").read_text()
help=(src/"SupportHelpActivity.kt").read_text()
assert 'versionName = "1.9.124"' in gradle
assert "versionCode = 134" in gradle
assert 'applicationId = "com.mediagenda.app.stable"' in gradle
ET.fromstring(manifest)
assert 'android:name=".AlarmPermissionsActivity"' in manifest
assert 'android:exported="false"' in manifest
for perm in ("POST_NOTIFICATIONS","USE_FULL_SCREEN_INTENT","SCHEDULE_EXACT_ALARM"):
    assert perm in manifest,perm
assert '"Permissões e alarmes do telemóvel"' in main
assert 'Intent(this,AlarmPermissionsActivity::class.java)' in main
assert 'box.addView(infoCard("🔔", "Notificações",' in main
for fragment in (
    "canUseFullScreenIntent()",
    "ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT",
    "ACTION_APP_NOTIFICATION_SETTINGS",
    "ACTION_CHANNEL_NOTIFICATION_SETTINGS",
    "EXTRA_CHANNEL_ID",
    "canScheduleExactAlarms()",
    "ACTION_REQUEST_SCHEDULE_EXACT_ALARM",
    "isIgnoringBatteryOptimizations(packageName)",
    "ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS",
    "ACTION_APPLICATION_DETAILS_SETTINGS",
    "NotificationManagerCompat.from(this)",
    "EXTRA_APP_PACKAGE",
    "Mostrar no ecrã bloqueado",
    "Abrir novas janelas em segundo plano",
    "Início automático",
    "MedicationAlarmService.CHANNEL",
    'getString("theme_mode","system")',
    "override fun onResume()",
):
    assert fragment in panel,fragment
# No permissions granted silently and no direct background alarm launch.
for forbidden in ("MedicationAlarmService.start(","setFullScreenIntent(",
                  "NotificationScheduler(","scheduleAllProfiles(",
                  "ACTION_MANAGE_OVERLAY_PERMISSION",
                  "REQUEST_IGNORE_BATTERY_OPTIMIZATIONS",
                  "setShowWhenLocked(","NotificationManager.IMPORTANCE_HIGH).apply"):
    assert forbidden not in panel,forbidden
assert "alarmPermissionsGuide" in help
assert "phon" in help.lower() or "alarme" in help
assert (src/"notifications/MedicationAlarmService.kt").exists()
assert (src/"notifications/NotificationScheduler.kt").exists()
print("PASS Android v1.9.124: settings only, original alarm engine untouched.")
