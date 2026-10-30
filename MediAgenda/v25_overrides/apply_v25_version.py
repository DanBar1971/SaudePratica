from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
gradle=root/"app/build.gradle.kts"
text=gradle.read_text(encoding="utf-8")
assert 'applicationId = "com.mediagenda.app.stable"' in text, "Application ID must not change"
assert 'versionCode = 15' in text and 'versionName = "1.9.5"' in text
text=text.replace('versionCode = 15','versionCode = 16',1)
text=text.replace('versionName = "1.9.5"','versionName = "1.9.6"',1)
gradle.write_text(text,encoding="utf-8")
print("SaúdePrática v1.9.6: incremental update, stable application ID")
