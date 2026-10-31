#!/usr/bin/env python3
"""Static audit of Android theme routing, clinical form contrast and release invariants.
CI does not replace visual tests on real Xiaomi/other Android hardware.
"""
from pathlib import Path
import re
app=Path("build-src/MediAgenda_Android_v1/app")
src=app/"src/main/java/com/mediagenda/app"
def read(name):return (src/name).read_text(encoding="utf-8")
gradle=(app/"build.gradle.kts").read_text(encoding="utf-8")
assert 'versionCode = 132' in gradle
assert 'versionName = "1.9.122"' in gradle
assert 'applicationId = "com.mediagenda.app.stable"' in gradle
application=read("SaudePraticaApplication.kt")
assert "AppCompatDelegate.setDefaultNightMode" in application
assert application.index("AppCompatDelegate.setDefaultNightMode") < application.index("registerActivityLifecycleCallbacks")
dialog=read("SafeMaterialAlertDialogBuilder.kt")
assert 'if(dark)Color.rgb(29,41,53) else Color.WHITE' in dialog
assert 'Color.rgb(29,29,36)' not in dialog
assert 'getString("theme_mode","system")' in dialog
assert "dialog.setCanceledOnTouchOutside(false)" in dialog
main=read("MainActivity.kt")
assert "boxBackgroundColor = surface" in main
assert "defaultHintTextColor = ColorStateList.valueOf(muted)" in main
assert "setHintTextColor(muted)" in main
assert "AppCompatDelegate.setDefaultNightMode" in main
for name in ("SmartHelpActivity.kt","SupportHelpActivity.kt",
             "HealthTipsActivity.kt","MonthlyCalendarActivity.kt"):
    code=read(name)
    assert 'getString("theme_mode","system")' in code,name
    assert "Configuration.UI_MODE_NIGHT_YES" in code,name
    assert '"light"->false' in code or '"light"->false' in code.replace(' ','') or '"light" -> false' in code,name
    print("Theme manual light/dark/system checked:",name)
assert 'if(dark)Color.rgb(26,45,55) else Color.WHITE' in read("SmartHelpActivity.kt")
assert 'if(dark)Color.rgb(26,48,61) else Color.WHITE' in read("SupportHelpActivity.kt")
assert 'if(dark)Color.rgb(29,44,56) else Color.WHITE' in read("HealthTipsActivity.kt")
assert 'if(dark)Color.rgb(79,103,116)else Color.rgb(214,226,234)' in read("MonthlyCalendarActivity.kt")
assert "Color.argb(240,241,249,248)" not in read("HealthTipsActivity.kt")
# The update must never touch medicine schedules or the package certificate.
assert "private fun reschedule() = NotificationScheduler(this).scheduleAllProfiles()" in main
assert (src/"notifications/NotificationScheduler.kt").is_file()
assert (src/"notifications/MedicationAlarmActivity.kt").is_file()
assert "DiabetesActivity" in (app/"src/main/AndroidManifest.xml").read_text()
assert "ImportantShortcutsV2Activity" in (app/"src/main/AndroidManifest.xml").read_text()
print("PASS: v1.9.122 theme consistency and clinical invariants (static, not device QA)")
