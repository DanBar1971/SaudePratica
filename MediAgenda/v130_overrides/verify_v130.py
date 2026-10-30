#!/usr/bin/env python3
"""Static regression checks for 1.9.110 global dialog layout."""
from pathlib import Path
p=Path('build-src/MediAgenda_Android_v1/app')
src=p/'src/main/java/com/mediagenda/app'
files=list(src.rglob('*.kt'))
old='import com.google.android.material.dialog.MaterialAlertDialogBuilder'
ali='import com.mediagenda.app.SafeMaterialAlertDialogBuilder as MaterialAlertDialogBuilder'
assert not any(old in f.read_text(encoding='utf-8') for f in files),'An activity still has the old builder'
assert sum(ali in f.read_text(encoding='utf-8') for f in files)>=20
assert sum(f.read_text(encoding='utf-8').count('MaterialAlertDialogBuilder(') for f in files)>=180
builder=(src/'SafeMaterialAlertDialogBuilder.kt').read_text(encoding='utf-8')
for wanted in ('override fun create(): AlertDialog','orientation=LinearLayout.HORIZONTAL','parent.removeView(button)','contentDescription=fullLabel','minWidth=0','maxLines=2','View.OnLayoutChangeListener','dialog.isShowing'):
    assert wanted in builder,wanted
profile=(src/'MainActivity.kt').read_text(encoding='utf-8')
assert '(resources.displayMetrics.heightPixels*0.66f).toInt()' in profile
for item in ['footerParams()','editorFooter.addView(deleteProfileButton,footerParams())','editorFooter.addView(cancelProfileButton,footerParams())','editorFooter.addView(saveProfileButton,footerParams())']:
    assert item in profile,item
meal=(src/'MealAiActivity.kt').read_text(encoding='utf-8')
assert 'historyMenuPicker' in meal and 'Gemini' in meal
assert 'visibleDialog=MaterialAlertDialogBuilder(this)' in meal
assert '.setNeutralButton("🗑 Eliminar refeição")' in meal
assert 'setPositiveButton("Fechar",null).show()' in meal
assert 'import com.mediagenda.app.SafeMaterialAlertDialogBuilder as MaterialAlertDialogBuilder' in meal
g=(p/'build.gradle.kts').read_text()
for x in ['applicationId = "com.mediagenda.app.stable"','versionCode = 120','versionName = "1.9.110"']:
    assert x in g
print('v1.9.110 global dialog layout safety and identity OK')