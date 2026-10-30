#!/usr/bin/env python3
"""Regression gates: no Gemini changes, safe optional audit only."""
from pathlib import Path
r=Path('build-src/MediAgenda_Android_v1/app')
p=r/'src/main/java/com/mediagenda/app/MealAiActivity.kt'
s=p.read_text(encoding='utf-8')
for needle in (
 'private fun analyzeWithGemini()',
 'MealGeminiDirect.analyze(this@MealAiActivity,jpeg)',
 'MealGeminiDirect.correct(this@MealAiActivity,jpeg,original,hint)',
 'private fun reviewGeminiFoods(response:JSONObject)',
 'val ateEverything=CheckBox(this)',
 '"consumed_all",ateEverything.isChecked',
 'historyMenuPicker=registerForActivityResult(ActivityResultContracts.OpenDocument())',
 'private fun mealVisibleKcalSum(row:JSONObject)',
 'fun menuPhotoFile(entry:JSONObject)',
 'fun attachMenuPhoto(id:String,jpeg:ByteArray)',
 'fun updateMenuReference(id:String,kcal:Double?,description:String)',
 'fun remove(id:String)',
 'val reference=row.optDouble("menu_total_kcal",0.0)',
 '"⚠ A soma das calorias na lista visível',
 'private val folder=File(context.filesDir,"saudepratica_meal_diary/$profileId")',
):assert needle in s,needle
assert 'MealDiary(this,profileId).add(record,photo)' in s
assert '"source","Gemini · revisto pelo utilizador"' in s
assert 'versionCode = 119' in (r/'build.gradle.kts').read_text()
assert 'versionName = "1.9.109"' in (r/'build.gradle.kts').read_text()
assert 'applicationId = "com.mediagenda.app.stable"' in (r/'build.gradle.kts').read_text()
lang=(r/'src/main/java/com/mediagenda/app/i18n/AppLanguage.kt').read_text()
assert '📋 Associar fotografia da ementa\t📋 Attach menu photo' in lang
for filename in ['MealGeminiClient.kt','MealGeminiDirect.kt']:
 assert (r/'src/main/java/com/mediagenda/app'/filename).is_file(),filename
print('v1.9.109 source checks passed: Gemini API preserved; optional menu audit and per-profile diary verified.')