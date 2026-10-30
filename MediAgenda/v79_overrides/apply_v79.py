"""SaúdePrática 1.9.61: dose schedules, pause/resume, manual doses, facilities, certificates."""
from pathlib import Path
import subprocess
root=Path('build-src/MediAgenda_Android_v1')
src=root/'app/src/main/java/com/mediagenda/app'
app=root/'app'
patch=Path('MediAgenda/v79_overrides/source-changes.patch').resolve()
subprocess.run(['patch','--batch','--forward','-p1','--input',str(patch)],cwd=app,check=True)
gradle=app/'build.gradle.kts'
s=gradle.read_text(encoding='utf8')
assert s.count('versionCode = 70')==1 and s.count('versionName = "1.9.60"')==1
s=s.replace('versionCode = 70','versionCode = 71').replace('versionName = "1.9.60"','versionName = "1.9.61"')
gradle.write_text(s,encoding='utf8')
main=(src/'MainActivity.kt').read_text()
assert 'observations_by_unit' in main and 'suspendedFrom' in main and 'expiry.edit' in main
repo=(src/'data/DataRepository.kt').read_text()
assert 'dose_pattern' in repo and 'expiry_date' in repo
print('v1.9.61: medication interval schedules, suspension, SOS, manual intake, multi-facility observations, appointments and certificates')