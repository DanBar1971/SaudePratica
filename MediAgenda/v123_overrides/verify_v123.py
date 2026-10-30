#!/usr/bin/env python3
from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1/app')
s=(root/'src/main/java/com/mediagenda/app/MealAiActivity.kt').read_text(encoding='utf-8')
i=(root/'src/main/java/com/mediagenda/app/i18n/AppLanguage.kt').read_text(encoding='utf-8')
g=(root/'build.gradle.kts').read_text(encoding='utf-8')
for word in ['Diário de refeições','Resumo de hoje','todayDiary','loggedMeals','todayKcal',
             'todayProtein','todayCarbs','todayFat','showMealDetails(record,diary)',
             'diary.photoFile(record)','MealDiary(this,profileId)',
             '"kcal" to String.format','setOnClickListener{showMealDetails(record,diary)}',
             'reviewGeminiFoods(cached)','analyzeWithGemini()','chooseFoods(emptySet(),true)',
             'lookupBarcode(', 'MealDiary(this,profileId).add(entry,photo)']:
 assert word in s,word
assert s.count('\n        showHistory()\n')==1,'Duplicated history panel'
assert 'for(index in 0 until minOf(items.length(),16) step 2)' in s
assert 'if(picture!=null)' not in s[s.index('private fun showHistory()'):s.index('private fun showMealDetails')]
assert 'photoFile(record)' in s
assert 'meal gallery fictional' not in s
assert 'versionCode = 113' in g and 'versionName = "1.9.103"' in g
assert 'Diário de refeições\tMeal diary\tJournal des repas' in i
for word in ['foto','Proteínas','Hidratos','Gorduras']:
 assert word in i or word in s
print('PASS v1.9.103: real profile diary, photo gallery, saved macros, Gemini/manual preserved and 5-language terms')
