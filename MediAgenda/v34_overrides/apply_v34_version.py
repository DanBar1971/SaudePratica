from pathlib import Path

g=Path("build-src/MediAgenda_Android_v1/app/build.gradle.kts")
s=g.read_text(encoding="utf-8")
assert 'applicationId = "com.mediagenda.app.stable"' in s
assert 'versionCode = 24' in s and 'versionName = "1.9.14"' in s
g.write_text(s.replace('versionCode = 24','versionCode = 25',1)
    .replace('versionName = "1.9.14"','versionName = "1.9.15"',1),
    encoding="utf-8")
print("SaúdePrática v1.9.15: same applicationId, keeps installed data.")
