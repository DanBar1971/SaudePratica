"""Source-level Phase A invariants, run before assembling signed Android APK.

Real phone verification is still required for Nearby, lock screen and caregiver
behavior. This gate checks for unsafe regressions in the reconstructed sources.
"""
from pathlib import Path

project=Path("build-src/MediAgenda_Android_v1")
sync=(project/"app/src/main/java/com/mediagenda/app/sync/NearbySyncStore.kt").read_text(encoding="utf-8")
manifest=(project/"app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
gradle=(project/"app/build.gradle.kts").read_text(encoding="utf-8")
for required in [
    "private fun profileOrigin(localId:String)",
    'put("origin_device_id",origin.first)',
    'put("origin_profile_id",origin.second)',
    "profileOrigin(it.id)==(originDevice to originId)",
    'check(prefs.edit().putString("origin_${created.id}",origin)',
    'require(origins.add(origin))',
    "mergeMetadata(target(path,ids),file,path,device)",
    "NotificationScheduler(context).scheduleAllProfiles()",
]:
    assert required in sync, f"Fase A missing identity safeguard: {required}"
assert "firstOrNull{it.name.equals(name,ignoreCase=true)}" not in sync, "Unsafe name-based merge"
assert any('versionName = "'+v+'"' in gradle for v in ("1.9.91","1.9.92","1.9.93","1.9.94","1.9.95","1.9.96","1.9.97","1.9.98"))
assert any("versionCode = "+str(v) in gradle for v in (101,102,103,104,105,106,107,108))
assert 'android:icon="@drawable/saude_icon"' in manifest
for art in ["saude_background","saude_icon","saude_splash"]:
    f=project/f"app/src/main/res/drawable-nodpi/{art}.png"
    assert f.is_file() and f.stat().st_size > 1024, f"Missing original {art} PNG"
print("Fase A source and three original branding files validated")
