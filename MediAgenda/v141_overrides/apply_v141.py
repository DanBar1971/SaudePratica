#!/usr/bin/env python3
"""SaúdePrática v1.9.121: consistent Diabetes UI and read-only Home shortcuts."""
from pathlib import Path
from shutil import copyfile

APP=Path("build-src/MediAgenda_Android_v1/app")
SRC=APP/"src/main/java/com/mediagenda/app"
OV=Path("MediAgenda/v141_overrides")

for file in ("DiabetesActivity.kt","ImportantShortcutsV2Activity.kt"):
    assert (SRC/file).exists(),file
    copyfile(OV/file,SRC/file)

# Home launches viewer (no editing); Options explicitly opens manage mode.
main=SRC/"MainActivity.kt"
s=main.read_text(encoding="utf-8")
anchor='''        box.addView(infoCard("🔗", "Atalhos Importantes",
            "Aplicações instaladas e websites · organizar atalhos") {
            startActivity(Intent(this,ImportantShortcutsV2Activity::class.java))
        })'''
replacement='''        box.addView(infoCard("🔗", "Atalhos Importantes",
            "Aplicações instaladas e websites · organizar atalhos") {
            startActivity(Intent(this,ImportantShortcutsV2Activity::class.java)
                .putExtra(ImportantShortcutsV2Activity.EXTRA_MANAGE,true))
        })'''
assert s.count(anchor)==1,("Options shortcut route",s.count(anchor))
s=s.replace(anchor,replacement,1)
assert s.count('Intent(this,ImportantShortcutsV2Activity::class.java)')>=1
# Legacy website-only data and the view-only dashboard remain untouched.
main.write_text(s,encoding="utf-8")

gradle=APP/"build.gradle.kts"
g=gradle.read_text(encoding="utf-8")
assert g.count("versionCode = 130")==1
assert g.count('versionName = "1.9.120"')==1
g=g.replace("versionCode = 130","versionCode = 131",1)
g=g.replace('versionName = "1.9.120"','versionName = "1.9.121"',1)
gradle.write_text(g,encoding="utf-8")
print("v1.9.121 applied: theme-matched Diabetes + view-only Home / manage Options.")
