#!/usr/bin/env python3
"""SaúdePrática 1.9.103: data-grounded, image-rich nutrition diary, no mocks.

Applies after v122; preserves the Gemini request/response flow, per-profile diary,
manual fallback, and the original branding/signing package ID.
"""
from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1/app')
p=root/'src/main/java/com/mediagenda/app/MealAiActivity.kt'
s=p.read_text(encoding='utf-8')
def once(old,new,label):
 global s
 assert s.count(old)==1,(label,s.count(old))
 s=s.replace(old,new,1)

# Make existing labels and controls use selected app language at construction,
# not only the Activity's GlobalLayout translation observer.
once('''        text=s; textSize=size; setTextColor(ink); if (strong) setTypeface(null,1)''',
'''        text=com.mediagenda.app.i18n.AppLanguage.t(this@MealAiActivity,s)
        textSize=size; setTextColor(ink); if (strong) setTypeface(null,1)''','localized labels')
once('''        text=s; isAllCaps=false; textSize=13f''',
'''        text=com.mediagenda.app.i18n.AppLanguage.t(this@MealAiActivity,s)
        isAllCaps=false; textSize=13f''','localized buttons')

once('''        body.addView(label("🍽️ Refeições",25f,true))''',
'''        body.addView(label("🥗 Nutrição",28f,true))''','title')

# New nutrition day dashboard uses ONLY real, locally saved meals.
needle='''        val p=panel("Nova refeição","Escolhe uma fotografia. Com Gemini, revês todos os alimentos e as porções antes de guardar.")'''
insert='''        val todayDiary=MealDiary(this,profileId).list()
        val today=java.time.LocalDate.now()
        var loggedMeals=0
        var todayKcal=0.0
        var todayProtein=0.0
        var todayCarbs=0.0
        var todayFat=0.0
        for(i in 0 until todayDiary.length()){
            val row=todayDiary.optJSONObject(i)?:continue
            val date=runCatching{java.time.Instant.ofEpochMilli(row.optLong("at"))
                .atZone(java.time.ZoneId.systemDefault()).toLocalDate()}.getOrNull()
            if(date!=today)continue
            loggedMeals++
            todayKcal+=row.optDouble("kcal",0.0).coerceAtLeast(0.0)
            todayProtein+=row.optDouble("protein_g",0.0).coerceAtLeast(0.0)
            todayCarbs+=row.optDouble("carbs_g",0.0).coerceAtLeast(0.0)
            todayFat+=row.optDouble("fat_g",0.0).coerceAtLeast(0.0)
        }
        val daily=panel("📊 Resumo de hoje",
            "Apenas refeições guardadas neste perfil; não representa todo o consumo do dia.")
        val totals=LinearLayout(this).apply {orientation=LinearLayout.HORIZONTAL}
        listOf("kcal" to String.format(Locale("pt","PT"),"%.0f",todayKcal),
            "Proteínas" to String.format(Locale("pt","PT"),"%.1f g",todayProtein),
            "Hidratos" to String.format(Locale("pt","PT"),"%.1f g",todayCarbs),
            "Gorduras" to String.format(Locale("pt","PT"),"%.1f g",todayFat)
        ).forEachIndexed{index,(name,value)->
            val tile=LinearLayout(this).apply{
                orientation=LinearLayout.VERTICAL
                setPadding(dp(4),dp(10),dp(4),dp(10))
                background=GradientDrawable().apply{
                    setColor(if(isDark)Color.rgb(16,66,67) else Color.rgb(228,248,243))
                    cornerRadius=dp(12).toFloat()
                }
                addView(label(value,if(index==0)17f else 14f,true).apply{
                    gravity=Gravity.CENTER
                    setTextColor(if(isDark)Color.rgb(127,238,215) else Color.rgb(0,96,83))
                })
                addView(label(name,11f).apply{gravity=Gravity.CENTER})
            }
            totals.addView(tile,LinearLayout.LayoutParams(0,-2,1f).apply{
                if(index>0)marginStart=dp(5)
            })
        }
        daily.addView(totals)
        daily.addView(label("$loggedMeals refeição(ões) registada(s) hoje",12f).apply{
            setTextColor(secondary)
        })
        val p=panel("Nova refeição","Escolhe uma fotografia. Com Gemini, revês todos os alimentos e as porções antes de guardar.")'''
once(needle,insert,'data-grounded daily nutrition cards')
# Diary should be near the primary action, not hidden underneath settings.
once('''        val configured=PrivateGeminiKey.read(this)!=null''',
'''        showHistory()
        val configured=PrivateGeminiKey.read(this)!=null''','history near new meal')
once('''        showHistory()
        val diary=MealDiary(this,profileId).list()''',
'''        val diary=MealDiary(this,profileId).list()''','avoid duplicate gallery')

start='''    private fun showHistory(){'''
end='''    private fun showMealDetails(row:JSONObject,diary:MealDiary){'''
assert s.count(start)==1 and s.count(end)==1
l=s.index(start);r=s.index(end,l)
new_history='''    private fun showHistory(){
        val diary=MealDiary(this,profileId)
        val items=diary.list()
        val p=panel("📸 Diário de refeições",if(items.length()==0)
            "Ainda não há refeições guardadas. A próxima fotografia fica aqui."
            else "${items.length()} refeições deste perfil. Toca num cartão para ver a fotografia e os valores.")
        if(items.length()==0)return
        // Two-column gallery, with REAL saved images only; never use sample food
        // illustrations as if the recognizer had identified a meal.
        for(index in 0 until minOf(items.length(),16) step 2){
            val rowContainer=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL}
            p.addView(rowContainer,LinearLayout.LayoutParams(-1,-2).apply{
                bottomMargin=dp(9)
            })
            for(i in index until minOf(index+2,items.length())){
                val record=items.optJSONObject(i)?:continue
                val meal=record.optString("meal","Refeição")
                val date=LocalDateTime.ofInstant(
                    java.time.Instant.ofEpochMilli(record.optLong("at")),
                    java.time.ZoneId.systemDefault())
                    .format(DateTimeFormatter.ofPattern("dd/MM · HH:mm"))
                val card=LinearLayout(this).apply{
                    orientation=LinearLayout.VERTICAL
                    setPadding(dp(8),dp(8),dp(8),dp(12))
                    background=GradientDrawable().apply{
                        setColor(if(isDark)Color.rgb(17,42,51) else Color.rgb(236,247,245))
                        cornerRadius=dp(17).toFloat()
                        setStroke(dp(1),if(isDark)Color.rgb(49,103,107) else Color.rgb(211,231,228))
                    }
                    isClickable=true
                    isFocusable=true
                    contentDescription="$meal em $date. ${record.optInt("kcal")} kcal. Abrir detalhes."
                    setOnClickListener{showMealDetails(record,diary)}
                }
                val picture=diary.photoFile(record)
                val thumb=picture?.let{
                    BitmapFactory.decodeFile(it.absolutePath,
                        BitmapFactory.Options().apply{inSampleSize=4})
                }
                if(thumb!=null){
                    card.addView(ImageView(this).apply{
                        setImageBitmap(thumb)
                        scaleType=ImageView.ScaleType.CENTER_CROP
                        background=GradientDrawable().apply{
                            setColor(Color.rgb(30,69,66));cornerRadius=dp(13).toFloat()
                        }
                        clipToOutline=true
                        contentDescription="Fotografia de $meal"
                    },LinearLayout.LayoutParams(-1,dp(128)))
                }else{
                    card.addView(TextView(this).apply{
                        text="🍽️"
                        gravity=Gravity.CENTER
                        textSize=35f
                        contentDescription="Refeição sem fotografia associada"
                        background=GradientDrawable().apply{
                            setColor(if(isDark)Color.rgb(25,70,71) else Color.rgb(208,233,230))
                            cornerRadius=dp(13).toFloat()
                        }
                    },LinearLayout.LayoutParams(-1,dp(128)))
                }
                card.addView(label(meal,14f,true).apply{maxLines=2;setPadding(0,dp(10),0,0)})
                card.addView(label(date,11f).apply{setTextColor(secondary)})
                card.addView(label("${record.optInt("kcal")} kcal",15f,true).apply{
                    setTextColor(if(isDark)Color.rgb(119,236,215) else Color.rgb(0,105,88))
                })
                val macro="P ${record.optInt("protein_g")} g  ·  H ${record.optInt("carbs_g")} g"+
                    "  ·  G ${record.optInt("fat_g")} g"
                card.addView(label(macro,10f).apply{setTextColor(secondary);maxLines=2})
                rowContainer.addView(card,LinearLayout.LayoutParams(0,-2,1f).apply{
                    if(i>index)marginStart=dp(9)
                })
            }
        }
    }
'''
s=s[:l]+new_history+s[r:]
p.write_text(s,encoding='utf-8')

# Keep package ID unchanged; bump only the version code/name.
gradle=root/'build.gradle.kts';g=gradle.read_text(encoding='utf-8')
assert g.count('versionCode = 112')==1 and g.count('versionName = "1.9.102"')==1
gradle.write_text(g.replace('versionCode = 112','versionCode = 113')
    .replace('versionName = "1.9.102"','versionName = "1.9.103"'),encoding='utf-8')
# Extend the existing five-language catalog for the redesigned nutrition view.
# User-entered food names/notes are deliberately NEVER machine translated.
lang=root/'src/main/java/com/mediagenda/app/i18n/AppLanguage.kt'
l=lang.read_text(encoding='utf-8')
entries=[
 ('Diário de refeições','Meal diary','Journal des repas','Mahlzeitentagebuch','Diario de comidas'),
 ('Resumo de hoje','Today summary','Résumé du jour','Tagesübersicht','Resumen de hoy'),
 ('Nova refeição','New meal','Nouveau repas','Neue Mahlzeit','Nueva comida'),
 ('Fotografar refeição','Photograph meal','Photographier le repas','Mahlzeit fotografieren','Fotografiar comida'),
 ('Escolher fotografia do telemóvel','Choose photo from phone','Choisir une photo du téléphone','Foto vom Handy wählen','Elegir foto del móvil'),
 ('Analisar esta refeição com Gemini','Analyze this meal with Gemini','Analyser ce repas avec Gemini','Mahlzeit mit Gemini analysieren','Analizar esta comida con Gemini'),
 ('Identificar alimentos manualmente','Identify foods manually','Identifier les aliments manuellement','Lebensmittel manuell erfassen','Identificar alimentos manualmente'),
 ('Histórico de refeições','Meal history','Historique des repas','Mahlzeitenverlauf','Historial de comidas'),
 ('Proteínas','Proteins','Protéines','Proteine','Proteínas'),
 ('Hidratos','Carbohydrates','Glucides','Kohlenhydrate','Hidratos'),
 ('Gorduras','Fats','Lipides','Fette','Grasas'),
 ('Inteligência artificial · Gemini','Gemini artificial intelligence','Intelligence artificielle · Gemini','Künstliche Intelligenz · Gemini','Inteligencia artificial · Gemini'),
 ('Outras formas de registar','Other recording methods','Autres méthodes de saisie','Weitere Erfassungsmethoden','Otras formas de registrar'),
 ('Escolher alimentos e calcular calorias','Choose foods and calculate calories','Choisir les aliments et calculer les calories','Lebensmittel wählen und Kalorien berechnen','Elegir alimentos y calcular calorías'),
 ('Registar manualmente','Record manually','Saisir manuellement','Manuell erfassen','Registrar manualmente'),
 ('Confirmar refeição','Confirm meal','Confirmer le repas','Mahlzeit bestätigen','Confirmar comida'),
 ('Guardar refeição no diário','Save meal to diary','Enregistrer le repas','Mahlzeit speichern','Guardar comida en el diario'),
 ('Tomas por confirmar','Unconfirmed doses','Prises à confirmer','Offene Einnahmen','Tomas por confirmar'),
 ('Medicamento sem caixa','Medicine without a box','Médicament sans boîte','Medikament ohne Packung','Medicamento sin caja'),
 ('Sem fotografia da caixa','No package photo','Sans photo de la boîte','Kein Packungsfoto','Sin foto de la caja'),
 ('Escolher perfil','Choose profile','Choisir le profil','Profil wählen','Elegir perfil'),
]
add='\n'.join('\t'.join(row) for row in entries)+'\n'
anchor='""".trimIndent()'
assert l.count(anchor)==1
l=l.replace(anchor,add+anchor,1)
lang.write_text(l,encoding='utf-8')

print('v1.9.103 nutrition gallery, real daily totals, selected-language labels, app ID preserved')
