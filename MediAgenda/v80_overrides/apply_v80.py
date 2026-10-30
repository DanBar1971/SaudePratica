"""SaúdePrática v1.9.62 — search healthcare units by Distrito > Concelho, optional GPS.
Uses a full 308-municipality name index; actual establishment suggestions remain non-exhaustive.
"""
from pathlib import Path
import json, shutil, subprocess
root=Path('build-src/MediAgenda_Android_v1')
app=root/'app'
patch=Path('MediAgenda/v80_overrides/source-changes.patch').resolve()
subprocess.run(['patch','--batch','--forward','-p1','--input',str(patch)],cwd=app,check=True)
municipalities=Path('MediAgenda/v80_overrides/portugal_distritos_concelhos.json')
data=json.loads(municipalities.read_text(encoding='utf-8'))['districts']
assert len(data)==20 and sum(len(municipalities) for municipalities in data.values())==308
assert 'Vila Franca de Xira' in data['Lisboa']
assets=app/'src/main/assets';assets.mkdir(parents=True,exist_ok=True)
shutil.copy2(municipalities,assets/'portugal_distritos_concelhos.json')
src=app/'src/main/java/com/mediagenda/app'
main=(src/'MainActivity.kt').read_text(encoding='utf-8')
assert 'chooseHealthcareDistrict' in main and 'chooseHealthcareByGps' in main
catalog=(src/'HealthcareCatalog.kt').read_text(encoding='utf-8')
assert 'Hospital de Vila Franca de Xira (ULS Estuário do Tejo)' in catalog
gradle=app/'build.gradle.kts';s=gradle.read_text(encoding='utf-8')
assert s.count('versionCode = 71')==1 and s.count('versionName = "1.9.61"')==1
s=s.replace('versionCode = 71','versionCode = 72').replace('versionName = "1.9.61"','versionName = "1.9.62"')
gradle.write_text(s,encoding='utf-8')
print('v1.9.62: Distrito → Concelho → Unidade, optional location, Hospital Vila Franca de Xira, Help updated PT EN FR DE ES')