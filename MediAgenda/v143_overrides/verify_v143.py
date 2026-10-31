#!/usr/bin/env python3
"""Static safety and interoperability gates for Android v1.9.123."""
from pathlib import Path
import re
app=Path("build-src/MediAgenda_Android_v1/app")
src=app/"src/main/java/com/mediagenda/app"
def read(p):return (src/p).read_text(encoding="utf-8")
gradle=(app/"build.gradle.kts").read_text(encoding="utf-8")
assert 'versionName = "1.9.123"' in gradle
assert 'versionCode = 133' in gradle
assert 'applicationId = "com.mediagenda.app.stable"' in gradle
fam=read("data/FamilyBackupStore.kt")
assert '"diabetes_v1"' in fam
assert "storedTops()" in fam
assert "forbiddenTop" in fam
assert "data/"+'"' not in fam  # no arbitrary extension to raw paths
assert "saudepratica_app_pin_v1" in fam
assert "backup.json" in fam and "sha256" in fam
assert "850L*1024*1024" in fam
bridge=read("data/PortableWindowsBackup.kt")
for word in ("SAUDEPRATICA-BACKUP-V1", "PBKDF2WithHmacSHA256",
             "AES/GCM/NoPadding","600_000","AES-256-GCM",
             "saudepratica-encrypted-v1","saudepratica-portable-v1",
             "android_archives.json","attachments.json","profile.json",
             "medicacao.json","agenda.json","fileHash",
             "cipher.doFinal()","updateAAD","FamilyBackupStore(context).restore",
             "maxZip=220L*1024*1024"):
    assert word in bridge,word
assert "fun restoreOriginal" in bridge
assert "ProfileStore(context).all()" in bridge
assert "finally{source.delete();password.fill" in bridge
assert "finally{password.fill" in bridge
main=read("MainActivity.kt")
assert "windowsBackupExport" in main and "windowsBackupImport" in main
assert "chooseWindowsExport()" in main
assert "inspectWindowsBackup(uri,pwd)" in main
assert "confirmRestoreWindowsOriginal" in main
assert "ATENÇÃO: vais substituir TODOS" in main
assert "As alterações feitas no Windows NÃO serão aplicadas." in main
assert "exportFamilyZip" in main and "restoreFamilyZip" in main
assert "NotificationScheduler(this).scheduleAllProfiles()" in main
assert (src/"notifications/MedicationAlarmService.kt").is_file()
print("PASS: v1.9.123 encryption contract, complete clinical backup, no false sync.")
