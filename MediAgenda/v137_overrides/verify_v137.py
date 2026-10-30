#!/usr/bin/env python3
"""Focused UI safety gates for SaúdePrática v1.9.117."""
from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1/app")
base=root/"src/main/java/com/mediagenda/app"
s=(base/"SafeMaterialAlertDialogBuilder.kt").read_text(encoding="utf-8")
gradle=(root/"build.gradle.kts").read_text(encoding="utf-8")
main=(base/"MainActivity.kt").read_text(encoding="utf-8")
scheduler=(base/"notifications/NotificationScheduler.kt").read_text(encoding="utf-8")
receiver=(base/"notifications/NotificationReceiver.kt").read_text(encoding="utf-8")
alarm=(base/"notifications/MedicationAlarmService.kt").read_text(encoding="utf-8")

assert 'val hydrationEditor=listOf("hidrata", "hydrat", "wasser", "trink")' in s
assert 'val fullEditor=hydrationEditor || formTitle=="editar perfil"' in s
assert 'button.maxLines=3' in s
assert 'ViewGroup.LayoutParams.WRAP_CONTENT,1f' in s
assert 'button.minimumHeight=scaledMinHeight' in s
assert 'dialog.setCanceledOnTouchOutside(false)' in s
assert 'dialog.setCancelable(false)' in s
assert 'win.setLayout(ViewGroup.LayoutParams.MATCH_PARENT,' in s
assert 'WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE' in s
assert 'versionCode = 127' in gradle and 'versionName = "1.9.117"' in gradle

# Non-invasive verification of existing Android exact-alarm fallback/diagnostics.
# No runtime alarm component is modified by apply_v137.
assert 'setExactAndAllowWhileIdle' in scheduler
assert 'setAndAllowWhileIdle' in scheduler
assert 'canScheduleExactAlarms()' in scheduler
assert '"saudepratica_alarm_timing_v1"' in receiver
assert 'Diagnóstico do último alarme de medicação' in main
assert 'ACTION_TIMEOUT' in alarm
print("v1.9.117 safety gates OK. Device-specific font/keyboard and exact alarm timing still require real-phone tests.")
