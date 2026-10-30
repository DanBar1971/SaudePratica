from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1")
ocr=root/"app/src/main/java/com/mediagenda/app/ocr/ProfileCitizenCardOcr.kt"
ocr.write_text(Path("MediAgenda/v29_overrides/ProfileCitizenCardOcr.kt").read_text(encoding="utf-8"),encoding="utf-8")

gradle=root/"app/build.gradle.kts"
s=gradle.read_text(encoding="utf-8")
assert 'applicationId = "com.mediagenda.app.stable"' in s, "App identity cannot change"
assert 'versionCode = 19' in s and 'versionName = "1.9.9"' in s
s=s.replace('versionCode = 19','versionCode = 20',1)
s=s.replace('versionName = "1.9.9"','versionName = "1.9.10"',1)
gradle.write_text(s,encoding="utf-8")
print("SaúdePrática v1.9.10: CC fields and review OCR included; same app ID.")
