#!/usr/bin/env python3
"""v1.9.119: a signed Android transition release to the canonical GitHub repository."""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1/app")
src=root/"src/main/java/com/mediagenda/app"
old="DanBar1971/AndroidAppDev"
new="DanBar1971/SaudePratica"
changed=[]
for path in src.rglob("*.kt"):
    text=path.read_text(encoding="utf-8")
    if old in text:
        path.write_text(text.replace(old,new),encoding="utf-8")
        changed.append(path.name)
assert "SaudePraticaUpdateChecker.kt" in changed,changed
assert "InAppUpdateInstaller.kt" in changed,changed
assert "SessionApkUpdater.kt" in changed,changed
build=root/"build.gradle.kts"
s=build.read_text(encoding="utf-8")
assert s.count("versionCode = 128")==1
assert s.count('versionName = "1.9.118"')==1
s=s.replace("versionCode = 128","versionCode = 129",1)
s=s.replace('versionName = "1.9.118"','versionName = "1.9.119"',1)
build.write_text(s,encoding="utf-8")
print("Transition to official release API, download URL verification and fallback links:",changed)
