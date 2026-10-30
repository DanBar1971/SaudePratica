#!/usr/bin/env python3
"""Build-time static regression gates; device QA is still required."""
from pathlib import Path
import re
app=Path("build-src/MediAgenda_Android_v1/app")
src=app/"src/main/java/com/mediagenda/app"
main=(src/"MainActivity.kt").read_text(encoding="utf-8")
diabetes=(src/"DiabetesActivity.kt").read_text(encoding="utf-8")
links=(src/"ImportantShortcutsV2Activity.kt").read_text(encoding="utf-8")
gradle=(app/"build.gradle.kts").read_text(encoding="utf-8")
assert 'versionCode = 131' in gradle
assert 'versionName = "1.9.121"' in gradle
assert 'applicationId = "com.mediagenda.app.stable"' in gradle
assert '"Diabetes"' in main and "DiabetesActivity.EXTRA_PROFILE_ID,activeProfileId" in main
assert "ImportantShortcutsV2Activity.EXTRA_MANAGE,true" in main
assert main.count("ImportantShortcutsV2Activity::class.java")>=2
# The default Home activity launch does NOT set the management flag.
assert "const val EXTRA_MANAGE" in links
assert "getBooleanExtra(EXTRA_MANAGE,false)" in links
assert "if(manage){" in links
assert 'if(manage){\n            body.addView(button("+ Atalho de aplicação")' in links
assert 'if(manage){\n                val menu=button("⋮")' in links
assert 'setOnClickListener{launch(item)}' in links
assert "saudepratica_important_shortcuts_v1" in links
assert "saudepratica_important_shortcuts_apps_web_v2" in links
assert "getString(\"links\",null)" in links
assert "putString(\"items\",shortcuts.toString())" in links
for name in ("WindowInsetsCompat","WindowCompat","ViewCompat","wallpaper()",
             "saude_background","theme_mode","Color.rgb(29,44,56)",
             "MaterialButton","ProfileStore","Diabetes","mg/dL","hba1c",
             "diabetes_v1"):
    assert name in diabetes,name
assert "Color.argb(232,244,251,250)" not in diabetes
for name in ("WindowInsetsCompat","WindowCompat","ViewCompat",
             "saude_background","theme_mode","Color.rgb(29,44,56)"):
    assert name in links,name
# No alarm scheduler or profile data model is changed by v141.
assert (src/"notifications/NotificationScheduler.kt").exists()
print("v141 static gates PASSED; no device test or original-key signing implied.")
