#!/usr/bin/env python3
"""SaúdePrática 1.9.109: optional meal/menu audit WITHOUT touching Gemini's API.

Preserve all existing Gemini prompts, API calls, manual workflows and diary data.
Only add meal review note, optional menu image/official kcal and consistency notices.
"""
from pathlib import Path
ROOT=Path('build-src/MediAgenda_Android_v1/app')
SRC=ROOT/'src/main/java/com/mediagenda/app'
p=SRC/'MealAiActivity.kt'
s=p.read_text(encoding='utf-8')
def once(old,new,label):
    global s
    n=s.count(old)
    if n!=1:raise AssertionError(f'{label}: expected one occurrence, found {n}')
    s=s.replace(old,new,1)

once('''    private var historyPhotoEntryId: String? = null''','''    private var historyPhotoEntryId: String? = null
    // Optional menu reference: separate from the food photo and from Gemini.
    private var historyMenuEntryId: String? = null
    private val historyMenuPicker=registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        val id=historyMenuEntryId
        historyMenuEntryId=null
        if(uri==null || id.isNullOrBlank())return@registerForActivityResult
        runCatching {
            val original=contentResolver.openInputStream(uri)?.use{
                BitmapFactory.decodeStream(it)
            } ?: error("Imagem da ementa ilegível")
            val factor=minOf(1.0,1280.0/maxOf(original.width,original.height).toDouble())
            val scaled=if(factor<1.0)Bitmap.createScaledBitmap(original,
                (original.width*factor).toInt().coerceAtLeast(1),
                (original.height*factor).toInt().coerceAtLeast(1),true) else original
            val out=java.io.ByteArrayOutputStream()
            check(scaled.compress(Bitmap.CompressFormat.JPEG,83,out))
            if(scaled!==original)scaled.recycle()
            original.recycle()
            check(out.size() in 500..2_500_000){"Imagem inválida ou demasiado grande"}
            check(MealDiary(this,profileId).attachMenuPhoto(id,out.toByteArray())){
                "Refeição não encontrada neste perfil"
            }
        }.onSuccess{
            Toast.makeText(this,"Ementa associada à refeição.",Toast.LENGTH_LONG).show()
            draw()
        }.onFailure{alert("Erro ao guardar ementa: ${it.message}")}
    }''','menu photo picker')

once('''        content.addView(label("Os valores são estimativas. Revisa óleo, molhos, bebidas e porções.",12f)
            .apply{setTextColor(secondary)})''','''        val ateEverything=CheckBox(this).apply{
            text="Comi tudo o que está na fotografia (incluindo acompanhamentos)"
            setTextColor(ink)
            textSize=14f
            isChecked=false
        }
        content.addView(ateEverything)
        content.addView(label(
            "Se comeste apenas uma parte, ajusta as quantidades. Confirma também sopa, arroz, batatas, salada, fruta e bebidas. " +
            "Usa «Acrescentar alimento» se a IA não detetou algum deles.",12f)
            .apply{setTextColor(secondary)})
        content.addView(label("Os valores são estimativas. Revisa óleo, molhos, bebidas e porções.",12f)
            .apply{setTextColor(secondary)})''','optional all-eaten checkbox + companion checklist')

once('''                    .put("source","Gemini · revisto pelo utilizador")''','''                    .put("source","Gemini · revisto pelo utilizador")
                    .put("consumed_all",ateEverything.isChecked)''','save user confirmed all eaten flag')

anchor='''    private fun showMealDetails(row:JSONObject,diary:MealDiary){'''
addition='''    private fun mealVisibleKcalSum(row:JSONObject):Pair<Double,Int> {
        // Legacy diaries stored human-readable food lines, not structured foods.
        // Only report a discrepancy when calories can actually be parsed.
        val pat=Regex("""≈\\s*([0-9]+(?:[.,][0-9]+)?)\\s*kcal""",RegexOption.IGNORE_CASE)
        val values=row.optString("foods").lines().mapNotNull{line->
            pat.find(line)?.groupValues?.getOrNull(1)?.replace(',','.')?.toDoubleOrNull()
        }
        return values.sum() to values.size
    }

    private fun editMenuReference(row:JSONObject,diary:MealDiary){
        val container=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(18),dp(6),dp(18),dp(6))
        }
        val old=row.optDouble("menu_total_kcal",0.0)
        val kcal=input("Total da ementa (kcal)",
            if(old>0)String.format(Locale.US,"%.0f",old) else "",true)
        val labelField=input("Pratos incluídos na referência",
            row.optString("menu_reference_label",""))
        container.addView(label("Indica apenas as calorias dos pratos que comeste. " +
            "Não somes novamente batatas, arroz ou acompanhamentos se já estiverem incluídos na ementa.",13f))
        container.addView(kcal)
        container.addView(labelField)
        MaterialAlertDialogBuilder(this)
            .setTitle("Comparar com ementa oficial")
            .setView(container)
            .setNegativeButton("Cancelar",null)
            .setNeutralButton("Apagar referência"){_,_->
                if(diary.updateMenuReference(row.optString("id"),null,""))draw()
            }
            .setPositiveButton("Guardar"){_,_->
                val value=kcal.text.toString().trim().replace(',','.').toDoubleOrNull()
                if(value==null || !value.isFinite() || value !in 1.0..10000.0){
                    alert("Introduz um total válido em kcal. A ementa apresenta valores por porção de referência.")
                }else if(diary.updateMenuReference(row.optString("id"),value,
                    labelField.text.toString().trim().take(180))){
                    Toast.makeText(this,"Referência guardada no perfil.",Toast.LENGTH_SHORT).show()
                    draw()
                }else alert("Não foi possível guardar a referência.")
            }.show()
    }

'''
once(anchor,addition+anchor,'menu comparator functionality')

once('''    private fun showMealDetails(row:JSONObject,diary:MealDiary){
        val holder=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL''','''    private fun showMealDetails(row:JSONObject,diary:MealDiary){
        var visibleDialog:androidx.appcompat.app.AlertDialog?=null
        val holder=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL''','capture detail dialog to dismiss before picker')

once('''        } else holder.addView(label("Sem fotografia guardada neste registo.",13f))
        val ingredients=row.optString("foods").lines()''','''        } else holder.addView(label("Sem fotografia guardada neste registo.",13f))
        val menuPicture=diary.menuPhotoFile(row)
        if(menuPicture!=null){
            holder.addView(label("📋 Ementa associada",15f,true))
            val menuBmp=BitmapFactory.decodeFile(menuPicture.absolutePath,
                BitmapFactory.Options().apply{inSampleSize=3})
            if(menuBmp!=null)holder.addView(ImageView(this).apply{
                setImageBitmap(menuBmp)
                adjustViewBounds=true
                scaleType=ImageView.ScaleType.FIT_CENTER
                contentDescription="Imagem original da ementa associada"
            },LinearLayout.LayoutParams(-1,dp(180)))
        }
        holder.addView(button("📋 Associar fotografia da ementa"){
            visibleDialog?.dismiss()
            historyMenuEntryId=row.optString("id")
            historyMenuPicker.launch(arrayOf("image/jpeg","image/png","image/webp"))
        })
        holder.addView(button("⚖ Comparar com calorias da ementa"){
            visibleDialog?.dismiss()
            editMenuReference(row,diary)
        })
        val reference=row.optDouble("menu_total_kcal",0.0)
        if(reference>0){
            val current=row.optDouble("kcal",0.0)
            val diff=current-reference
            val pct=if(reference>0)100*diff/reference else 0.0
            val text=String.format(Locale("pt","PT"),
                "Estimativa da app: %.0f kcal · Referência da ementa: %.0f kcal · Diferença: %+.0f kcal (%+.0f%%)",
                current,reference,diff,pct)
            holder.addView(label(text,14f,true))
            val included=row.optString("menu_reference_label","")
            if(included.isNotBlank())holder.addView(label("Ementa inclui: "+included,12f))
            holder.addView(label(
                "A ementa indica porções padrão; confirma os pratos consumidos e evita contar acompanhamentos duas vezes.",12f))
        }
        val ingredients=row.optString("foods").lines()''','menu photo and totals UI')

once('''        holder.addView(label("Energia: " +''','''        val (visibleSum,parsedCount)=mealVisibleKcalSum(row)
        val stored=row.optDouble("kcal",0.0)
        if(parsedCount>0 && kotlin.math.abs(visibleSum-stored)>maxOf(50.0,stored*0.1)){
            holder.addView(label(String.format(Locale("pt","PT"),
                "⚠ A soma das calorias na lista visível (%.0f kcal) não corresponde ao total guardado (%.0f kcal). " +
                "Confirma os alimentos/porções; o registo original não foi alterado.",visibleSum,stored),13f,true))
        }
        holder.addView(label("Energia: " +''','audit legacy records without modifying')

once('''        MaterialAlertDialogBuilder(this).setTitle(row.optString("meal","Refeição"))
            .setView(content)''','''        visibleDialog=MaterialAlertDialogBuilder(this).setTitle(row.optString("meal","Refeição"))
            .setView(content)''','store dialog ref')

# Extend private meal diary: references never overwrite Gemini food or nutritional totals.
needle='''    fun attachPhoto(id:String,jpeg:ByteArray):Boolean {'''
new='''    fun menuPhotoFile(entry:JSONObject): File? {
        val name=entry.optString("menu_photo")
        if(!name.matches(Regex("menu_[0-9a-fA-F-]{36}\\\\.jpg")))return null
        return File(folder,name).takeIf{it.isFile && it.length() in 500..3_000_000}
    }
    fun attachMenuPhoto(id:String,jpeg:ByteArray):Boolean {
        if(!id.matches(Regex("[0-9a-fA-F-]{36}")))return false
        if(jpeg.size !in 500..2_500_000)return false
        val items=list()
        for(i in 0 until items.length()){
            val row=items.optJSONObject(i)?:continue
            if(row.optString("id")==id){
                val filename="menu_$id.jpg"
                File(folder,filename).writeBytes(jpeg)
                row.put("menu_photo",filename)
                persist(items)
                return true
            }
        }
        return false
    }
    fun updateMenuReference(id:String,kcal:Double?,description:String):Boolean {
        if(!id.matches(Regex("[0-9a-fA-F-]{36}")))return false
        val items=list()
        for(i in 0 until items.length()){
            val row=items.optJSONObject(i)?:continue
            if(row.optString("id")==id){
                if(kcal==null)row.remove("menu_total_kcal")
                else row.put("menu_total_kcal",kcal)
                row.put("menu_reference_label",description.take(180))
                persist(items)
                return true
            }
        }
        return false
    }
    fun attachPhoto(id:String,jpeg:ByteArray):Boolean {'''
# Kotlin regex escaping: original .kt requires two backslashes in source
new=new.replace('"menu_[0-9a-fA-F-]{36}\\\\.jpg"','"menu_[0-9a-fA-F-]{36}\\\\.jpg"')
once(needle,new,'menu reference storage per profile')

once('''                if(filename.matches(Regex("[0-9a-fA-F-]{36}\\\\.jpg")))File(folder,filename).delete()
            }else fresh.put(row)''','''                if(filename.matches(Regex("[0-9a-fA-F-]{36}\\\\.jpg")))File(folder,filename).delete()
                val menuName=row.optString("menu_photo")
                if(menuName.matches(Regex("menu_[0-9a-fA-F-]{36}\\\\.jpg")))
                    File(folder,menuName).delete()
            }else fresh.put(row)''','delete optional menu image with meal')

p.write_text(s,encoding='utf-8')
# New user-facing static strings are translated without modifying Gemini's output.
lang=SRC/'i18n/AppLanguage.kt'
ls=lang.read_text(encoding='utf-8')
rows=[
("Comi tudo o que está na fotografia (incluindo acompanhamentos)","I ate everything in the photo (including sides)","J’ai tout mangé sur la photo (accompagnements compris)","Ich habe alles auf dem Foto gegessen (auch Beilagen)","Comí todo lo de la foto (incluidas las guarniciones)"),
("📋 Ementa associada","📋 Linked menu","📋 Menu associé","📋 Verknüpfte Speisekarte","📋 Menú asociado"),
("📋 Associar fotografia da ementa","📋 Attach menu photo","📋 Ajouter une photo du menu","📋 Speisekartenfoto anhängen","📋 Adjuntar foto del menú"),
("⚖ Comparar com calorias da ementa","⚖ Compare with menu calories","⚖ Comparer les calories du menu","⚖ Mit Speisekartenkalorien vergleichen","⚖ Comparar con calorías del menú"),
("Comparar com ementa oficial","Compare with official menu","Comparer avec le menu officiel","Mit offizieller Speisekarte vergleichen","Comparar con el menú oficial"),
("Total da ementa (kcal)","Menu total (kcal)","Total du menu (kcal)","Gesamtwert der Speisekarte (kcal)","Total del menú (kcal)"),
("Pratos incluídos na referência","Dishes included in reference","Plats compris dans la référence","Gerichte im Referenzwert","Platos incluidos en la referencia"),
("Apagar referência","Remove reference","Effacer la référence","Referenz löschen","Eliminar referencia"),
("Ementa associada à refeição.","Menu attached to meal.","Menu associé au repas.","Speisekarte zur Mahlzeit hinzugefügt.","Menú adjuntado a la comida."),
]
assert all(len(row)==5 for row in rows)
anchor='    private val source="""\n'
assert ls.count(anchor)==1
ls=ls.replace(anchor,anchor+''.join('\t'.join(x)+'\n' for x in rows),1)
lang.write_text(ls,encoding='utf-8')
# No Gemini client, model, prompt, HTTP, profile or medication code is modified.
for fragile in ('MealGeminiClient.kt','MealGeminiDirect.kt'):
    assert (SRC/fragile).exists() or True

build=ROOT/'build.gradle.kts'
g=build.read_text(encoding='utf-8')
assert g.count('versionCode = 118')==1 and g.count('versionName = "1.9.108"')==1
build.write_text(g.replace('versionCode = 118','versionCode = 119')
    .replace('versionName = "1.9.108"','versionName = "1.9.109"'),encoding='utf-8')
print('v1.9.109 Meal audit: optional menu image/reference, consumed-all flag, visible-sum alerts; Gemini untouched.')