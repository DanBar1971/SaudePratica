#!/usr/bin/env python3
"""Post-patch guardrails for v1.9.134 Health Connect snapshot persistence."""
from pathlib import Path
from re import search

app=Path("build-src/MediAgenda_Android_v1/app")
src=app/"src/main/java/com/mediagenda/app"
screen=(src/"ActivityHealthConnect.kt").read_text(encoding="utf-8")
store=(src/"data/HealthConnectSnapshotStore.kt").read_text(encoding="utf-8")
family=(src/"data/FamilyBackupStore.kt").read_text(encoding="utf-8")
gradle=(app/"build.gradle.kts").read_text(encoding="utf-8")

for snippet in (
    "day,snapshotMetricKeys[index],amount",
    'saveHealthReading(date, "total_kcal"',
    '"oxygen_percent"', '"weight_kg"', '"temperature_c"',
    '"resting_heart_bpm"', '"systolic_mmhg"', '"diastolic_mmhg"',
    '"respiratory_per_min"', "snapshotStatus=label(",
    'if (!canRead()) return',
):
    assert snippet in screen,("ActivityHealthConnect missing",snippet)

for snippet in (
    '"saudepratica_health_connect/$profileId"',
    'File(folder, "daily.json")',
    "profile_id", "schema_version", "observed_at_ms",
    "StandardCopyOption.ATOMIC_MOVE",
    "if (key !in allowedKeys", "@Synchronized",
):
    assert snippet in store,("snapshot persistence missing",snippet)

assert 'top.startsWith("saudepratica_")' in family
assert 'if (path.endsWith(".tmp")) return false' in family
assert "versionCode = 144" in gradle
assert 'versionName = "1.9.134"' in gradle
assert 'applicationId = "com.mediagenda.app.stable"' in gradle
assert "class HealthConnectSnapshotStore" in store
assert "LegacyAssistantCleanup.run(applicationContext)" in (
    src/"MainActivity.kt").read_text(encoding="utf-8")

# Never overwrite manual weight or upload Health Connect data to the network.
assert 'BodyMeasurements(this,profileId)' in screen
assert not search(r'https?://|Retrofit|OkHttpClient|HttpURLConnection',store)
assert 'family' not in store.lower() or "ZIP" in store
print("PASS: v1.9.134 HC readings saved per authorised profile and included in Android backup.")
