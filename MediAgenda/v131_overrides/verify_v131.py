#!/usr/bin/env python3
"""Safe visual and hydration regression checks; no medical/Gemini changes."""
from pathlib import Path
app=Path('build-src/MediAgenda_Android_v1/app')
base=app/'src/main/java/com/mediagenda/app'
read=lambda p:(base/p).read_text(encoding='utf-8')
style=read('SafeMaterialAlertDialogBuilder.kt'); water=read('WellnessActivity.kt'); main=read('MainActivity.kt')
gradle=(app/'build.gradle.kts').read_text(encoding='utf-8')
assert 'versionCode = 121' in gradle and 'versionName = "1.9.111"' in gradle
assert 'applicationId = "com.mediagenda.app.stable"' in gradle
for token in ('Color.rgb(59,49,53)','Color.rgb(31,50,72)','Color.rgb(21,129,119)',
    'styleEmbeddedGroups(win.decorView)','actionButtons.forEach(::styleButton)',
    'Tone.DANGER','Tone.CANCEL','Tone.ACCEPT','parent.removeView(button)',
    'row.addView(button,LinearLayout.LayoutParams(0,dp(context,50),1f)'):
    assert token in style, token
for label in ('"eliminar"','"apagar"','"cancelar"','"fechar"'):
    assert label in style
assert 'setOnClickListener' not in style and 'setOnShowListener' in style  or 'setOnClickListener' not in style
assert 'val options=arrayOf("＋ 250 ml","＋ 500 ml","＋ 750 ml","＋ 1000 ml","＋ 1500 ml")' in water
assert 'MaterialAlertDialogBuilder(this).setTitle("Escolhe quanto acrescentar ao objetivo de hoje")\n                .setItems(options)' in water
assert '.setMessage("Só altera o objetivo. Confirma que não tens restrições de líquidos.")' not in water
assert 'store.increaseTarget(extra)' in water and 'NotificationScheduler(this).scheduleNextWater(profileId)' in water
assert 'editorFooter.addView(deleteProfileButton,footerParams())' in main
assert 'editorFooter.addView(cancelProfileButton,footerParams())' in main
assert 'editorFooter.addView(saveProfileButton,footerParams())' in main
assert read('MealAiActivity.kt') and read('data/WellnessStore.kt')
print('v1.9.111 regression gates passed: semantic pill buttons and hydration choices, stable app identity')