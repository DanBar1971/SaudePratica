#!/usr/bin/env python3
"""Android 1.9.127 portable backup acceptance gates for CI.
Static + compiled source checks; real device round-trip is separate.
"""
from pathlib import Path
from hashlib import sha256
app=Path("build-src/MediAgenda_Android_v1/app")
src=app/"src/main/java/com/mediagenda/app"
get=lambda s:(src/s).read_text(encoding="utf-8")
gradle=(app/"build.gradle.kts").read_text()
family=get("data/FamilyBackupStore.kt")
portable=get("data/PortableWindowsBackup.kt")
restore=get("data/PortableWindowsClinicalRestore.kt")
main=get("MainActivity.kt")
assert 'versionName = "1.9.127"' in gradle
assert 'versionCode = 137' in gradle
assert 'applicationId = "com.mediagenda.app.stable"' in gradle
assert 'fun export(destination:Uri,onlyProfile:String?=null)' in family
assert 'val files=paths(onlyProfile)' in family
assert 'fun export(destination:Uri,password:CharArray,onlyProfile:String?=null)' in portable
assert 'FamilyBackupStore(context).export(Uri.fromFile(source),onlyProfile)' in portable
assert 'profiles=ProfileStore(context).all()' in portable
assert 'filter{onlyProfile==null||it.id==onlyProfile}' in portable
assert 'put("scope",if(onlyProfile==null)"family" else "profile")' in portable
assert 'val source=preview.decrypted' not in restore
assert 'fun restore(preview:PortableWindowsBackup.Preview,expected:Plan,recoveryPassword:CharArray)' in restore
assert 'val safety=File.createTempFile("pre_restore_",".spbackup",recoveryDir)' in restore
assert 'sp_recovery_private' in restore
assert 'PortableWindowsBackup(context).export(Uri.fromFile(safety)' in restore
assert 'PortableWindowsBackup(context).restoreOriginal(verified,0)' in restore
assert 'rollbackPassword=recoveryPassword.copyOf()' in restore
assert 'recoveryPassword.fill(0.toChar())' in restore
assert 'photos' in portable and 'photo_b64' in restore
assert 'fun chooseWindowsExport(onlyProfile:String?=null)' in main
assert '"Backup .spbackup · Família"' in main
assert '"Backup .spbackup · Perfil"' in main
assert '"Restaurar .spbackup · Família ou Perfil"' in main
backup=main[main.index('"backup" -> {'):main.index('"apoio" -> {')]
for deleted in ("Backup completo da família","Restaurar backup completo",
    '"Exportar JSON"','"Importar JSON"','"Exportar para Excel"'):
    assert deleted not in backup,deleted
assert 'PortableWindowsClinicalRestore(this).inspect(preview)' in main
assert 'PortableWindowsClinicalRestore(this).restore(' in main
assert 'preview,plan,password' in main
assert 'recoveryPassword.fill(0.toChar())' in main
assert 'NotificationScheduler(this).scheduleAllProfiles()' in main
for file in ("notifications/MedicationAlarmService.kt",
 "notifications/NotificationScheduler.kt",
 "notifications/MedicationAlarmCoordinator.kt",
 "notifications/IntakeActionReceiver.kt"):
    assert (src/file).exists(),file
print("PASS: two .spbackup scopes and confirmed edited-Windows import wiring.")
