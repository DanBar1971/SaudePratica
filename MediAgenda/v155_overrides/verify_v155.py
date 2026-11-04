from pathlib import Path
app=Path("build-src/MediAgenda_Android_v1/app")
src=app/"src/main/java/com/mediagenda/app"
main=(src/"MainActivity.kt").read_text(encoding="utf-8")
portable=(src/"data/PortableWindowsBackup.kt").read_text(encoding="utf-8")
gradle=(app/"build.gradle.kts").read_text(encoding="utf-8")
for phrase in ("backupPinInput","TYPE_CLASS_NUMBER","InputFilter.LengthFilter(4)",
               "usesLegacyPassword(uri)","Backup completo com PIN",
               "Restaurar ZIP antigo (sem PIN)"):
    assert phrase in main,phrase
for phrase in ("saudepratica-encrypted-pin-v2","saudepratica-encrypted-v1",
               "1200000","600000","AES/GCM/NoPadding",
               "PBKDF2WithHmacSHA256"):
    assert phrase in portable,phrase
assert "versionCode = 145" in gradle
assert 'versionName = "1.9.135"' in gradle
print("PASS: Android 1.9.135 PIN backup contracts")
