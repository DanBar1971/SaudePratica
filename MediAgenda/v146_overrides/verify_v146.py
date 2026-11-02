#!/usr/bin/env python3
"""Do not certify tiny metadata-only backup or missing photos as complete."""
from pathlib import Path
from hashlib import sha256
root=Path("build-src/MediAgenda_Android_v1/app")
src=root/"src/main/java/com/mediagenda/app"
family=(src/"data/FamilyBackupStore.kt").read_text()
portable=(src/"data/PortableWindowsBackup.kt").read_text()
gradle=(root/"build.gradle.kts").read_text()
assert 'versionName = "1.9.126"' in gradle
assert "versionCode = 136" in gradle
assert 'applicationId = "com.mediagenda.app.stable"' in gradle
for t in ("DataRepository(context,person.id).ensureFiles()",
          'prefix+"medicacao.json"','prefix+"agenda.json"',
          "Fotografia do medicamento ausente do backup",
          "saudepratica_profiles_v1","diabetes_v1"):
    assert t in family,t
for t in ("data/","photo_b64","saudepratica_identity/",
          "medication_photos/","attachments.json",
          '"fotografia de medicamento"','fileHash',
          "saudepratica-encrypted-v1","AES/GCM/NoPadding"):
    assert t in portable,t
for protected in (
  "notifications/MedicationAlarmService.kt",
  "notifications/NotificationScheduler.kt",
  "notifications/MedicationAlarmCoordinator.kt",
  "notifications/DeviceAlarmRouting.kt",
):
    assert (src/protected).is_file(),protected
print("v1.9.126 Android export photo and clinical source gates passed (static).")
