from pathlib import Path

g=Path("build-src/MediAgenda_Android_v1/app/build.gradle.kts")
s=g.read_text(encoding="utf-8")
assert 'applicationId = "com.mediagenda.app.stable"' in s
assert 'versionCode = 23' in s and 'versionName = "1.9.13"' in s
g.write_text(s.replace('versionCode = 23','versionCode = 24',1)
             .replace('versionName = "1.9.13"','versionName = "1.9.14"',1),
             encoding="utf-8")
print("SaúdePrática v1.9.14: same stable app ID; user data preserved across update.")
