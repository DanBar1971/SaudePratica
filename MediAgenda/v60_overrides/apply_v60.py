from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
file=root/"app/src/main/java/com/mediagenda/app/sync/NearbySyncActivity.kt"
file.write_text(Path("MediAgenda/v60_overrides/NearbySyncActivity.kt").read_text(encoding="utf-8"),encoding="utf-8")
gradle=root/"app/build.gradle.kts"
s=gradle.read_text(encoding="utf-8")
assert s.count("versionCode = 50")==1 and s.count('versionName = "1.9.40"')==1
gradle.write_text(s.replace("versionCode = 50","versionCode = 51",1)
    .replace('versionName = "1.9.40"','versionName = "1.9.41"',1),encoding="utf-8")
print("v1.9.41: Nearby asUri() private-cache import, Xiaomi coarse location runtime permission")
