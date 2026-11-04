#!/usr/bin/env python3
"""Backup-only v1.9.128 guard: UI percentage corresponds to completed bytes."""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1/app")
src=root/"src/main/java/com/mediagenda/app"
family=(src/"data/FamilyBackupStore.kt").read_text(encoding="utf-8")
portable=(src/"data/PortableWindowsBackup.kt").read_text(encoding="utf-8")
main=(src/"MainActivity.kt").read_text(encoding="utf-8")
gradle=(root/"build.gradle.kts").read_text(encoding="utf-8")
assert "val totalBytes=files.sumOf{it.second.length()}" in family
assert "count*100L/totalBytes" in family
assert "onProgress?.invoke(100)" in family
assert "FamilyBackupStore(context).export(Uri.fromFile(source),onlyProfile){pct->" in portable
assert "exported*40L/totalExport" in portable
assert "progressBar.progress=percent" in main
assert "minimumHeight=dp(54)" in main
assert 'versionName = "1.9.128"' in gradle
assert "versionCode = 138" in gradle
assert 'applicationId = "com.mediagenda.app.stable"' in gradle
assert "NotificationScheduler(this).scheduleAllProfiles()" in main
print("Verified Android v1.9.128 progress, original identity, untouched alarm scheduler")
