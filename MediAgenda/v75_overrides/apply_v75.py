from pathlib import Path
import subprocess
root=Path('build-src/MediAgenda_Android_v1')
src=root/'app/src/main/java/com/mediagenda/app'
patch=Path('MediAgenda/v75_overrides/source-changes.patch').resolve()
subprocess.run(['patch','--batch','--forward','-p0','--input',str(patch)],cwd=src,check=True)
gradle=root/'app/build.gradle.kts'
s=gradle.read_text(encoding='utf-8')
assert s.count('versionCode = 66')==1
assert s.count('versionName = "1.9.56"')==1
s=s.replace('versionCode = 66','versionCode = 67').replace('versionName = "1.9.56"','versionName = "1.9.57"')
gradle.write_text(s,encoding='utf-8')
main=(src/'MainActivity.kt').read_text(encoding='utf-8')
help=(src/'SupportHelpActivity.kt').read_text(encoding='utf-8')
assert 'showOptionsGroup("perfis")' in main and 'showOptionsGroup("backup")' in main
assert 'Modo Sénior' in main and 'Aprende em nove passos' in help
print('v1.9.57: Opções grouped by purpose, profiles naming, Modo Sénior, backups, and Help updated in five languages')