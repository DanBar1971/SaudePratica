"""SaúdePrática v1.9.63 — overdue medication counter and strict profile identity sync."""
from pathlib import Path
import subprocess
root=Path('build-src/MediAgenda_Android_v1')
main=root/'app/src/main'
patch=Path('MediAgenda/v81_overrides/source-changes.patch').resolve()
subprocess.run(['patch','--batch','--forward','-p1','--input',str(patch)],cwd=main,check=True)
build=root/'app/build.gradle.kts'
s=build.read_text(encoding='utf8')
assert s.count('versionCode = 72')==1 and s.count('versionName = "1.9.62"')==1
build.write_text(s.replace('versionCode = 72','versionCode = 73').replace('versionName = "1.9.62"','versionName = "1.9.63"'),encoding='utf8')
sync=(main/'java/com/mediagenda/app/sync/NearbySyncStore.kt').read_text()
assert 'firstOrNull{it.name.equals(name,ignoreCase=true)}' not in sync
assert 'receiverProfile(device,remote,name,store)' in sync
assert 'mergePreferences(localId' in sync
assert (main/'java/com/mediagenda/app/notifications/IntakeBadgeManager.kt').exists()
print('v1.9.63: sync profile identity isolated, late-dose badge, delete confirmed doses, Help updated')