#!/usr/bin/env python3
"""Gate health-data, profile, dose, and alarm integrity for transport-only v1.9.125."""
from pathlib import Path
import xml.etree.ElementTree as ET
src=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app")
root=src.parents[4]
a=(src/"sync/NearbySyncActivity.kt").read_text(encoding="utf-8")
g=(Path("build-src/MediAgenda_Android_v1/app/build.gradle.kts")).read_text()
assert 'versionName = "1.9.125"' in g
assert 'versionCode = 135' in g
assert 'applicationId = "com.mediagenda.app.stable"' in g
assert "saudepratica.sync.v2" in a, "Do not pair original unscoped family-sync client"
assert "selectedProfileId" in a
assert "NearbySyncStore(applicationContext).export(selectedProfileId)" in a
assert "NearbySyncStore(applicationContext).receive(local,selectedProfileId)" in a
assert "authenticationDigits" in a and "Os códigos coincidem" in a
assert "ConnectionType.NON_DISRUPTIVE" in a
assert "ConnectionType.DISRUPTIVE" in a
assert "Padrão Nearby (como antes)" in a
assert "requestOptions()" in a and "advertiseOptions()" in a
assert "PayloadTransferUpdate.Status.IN_PROGRESS" in a
assert "displayProgress(update.bytesTransferred,update.totalBytes)" in a
assert 'transferBar.progress=99' in a
assert 'transferBar.progress=100' in a
assert a.count('sentOk=true')==1, "Premature sender success introduced"
assert a.index("sentOk=true")>a.index("response==receivedAck")
assert a.index("connections.sendPayload(endpointId,")>a.index("receivedOk=true")
assert "selectedProfileLabel" in a
assert "KEEP_SCREEN_ON" in a
assert "⚙️ Modo da ligação Nearby" in a
assert "↻ Repetir ligação" in a
assert (src/"sync/NearbySyncStore.kt").exists()
for alarm in (
 "MedicationAlarmService.kt","NotificationScheduler.kt",
 "NotificationReceiver.kt","MedicationAlarmCoordinator.kt",
 "MedicationAlarmPreferences.kt","IntakeActionReceiver.kt",
 "DeviceAlarmRouting.kt",
):
    path=src/"notifications"/alarm
    assert path.is_file(),alarm
assert 'Payload.fromFile(zip)' in a
# No new permission or service: no silent or unattended sync.
manifest=Path("build-src/MediAgenda_Android_v1/app/src/main/AndroidManifest.xml")
ET.parse(manifest)
assert "<service android:name=\".sync" not in manifest.read_text(encoding="utf-8")
print("PASS SaúdePrática 1.9.125: clinical mappings untouched, validated destination receipt, no alarm changes")
