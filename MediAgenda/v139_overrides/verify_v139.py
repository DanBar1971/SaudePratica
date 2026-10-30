#!/usr/bin/env python3
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1/app")
src=root/"src/main/java/com/mediagenda/app"
paths=["SaudePraticaUpdateChecker.kt","InAppUpdateInstaller.kt","SessionApkUpdater.kt"]
for name in paths:
    s=(src/name).read_text(encoding="utf-8")
    assert "DanBar1971/SaudePratica" in s,name
    assert "DanBar1971/AndroidAppDev" not in s,name
    print("Verified canonical update source:",name)
s=(src/"SaudePraticaUpdateChecker.kt").read_text(encoding="utf8")
assert "https://api.github.com/repos/DanBar1971/SaudePratica/releases/latest" in s
installer=(src/"InAppUpdateInstaller.kt").read_text(encoding="utf8")
assert "DanBar1971/SaudePratica/releases/download/" in installer
g=(root/"build.gradle.kts").read_text(encoding="utf8")
assert "versionCode = 129" in g and 'versionName = "1.9.119"' in g
scheduler=(src/"notifications/NotificationScheduler.kt").read_text(encoding="utf8")
assert "setExactAndAllowWhileIdle" in scheduler and "canScheduleExactAlarms()" in scheduler
print("v1.9.119 URL-only transition verified, alarms unchanged.")
