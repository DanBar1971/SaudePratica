"""SaúdePrática v1.9.81 — honest offline food suggestions and meal-photo history.

No private images or API keys are bundled. Keep existing meal files, profile
IDs, app identity, graphics, and all existing Android data intact.
"""
from pathlib import Path

root=Path('build-src/MediAgenda_Android_v1')
base=root/'app/src/main/java/com/mediagenda/app'
meal=base/'MealAiActivity.kt'
s=meal.read_text(encoding='utf-8')

def replace(old,new,name):
    global s
    n=s.count(old)
    if n!=1:
        raise RuntimeError(f'1.9.81 {name}: expected one anchor, got {n}')
    s=s.replace(old,new,1)

# The offline Google AIY Food-V1 model is a SINGLE DISH classifier. Displaying
# Tafelspitz and Saugerbraten as if these are identified ingredients is incorrect.
# Never save an unrecognized label as a dish with a fabricated 0-kcal result.
start=s.index('    private fun showDishSuggestions(guesses:List<FoodDishClassifier.Guess>) {')
end=s.index('    /** Searchable selection instead of a huge list',start)
s=s[:start]+'''    private fun showDishSuggestions(guesses:List<FoodDishClassifier.Guess>) {
        // This single-dish model is unsuitable for full trays containing many
        // foods. Only expose a class when it maps to our local nutrition table
        // and clears the minimum score; labels are never treated as facts.
        val candidates=guesses.filter { it.score >= 0.25f }
            .mapNotNull { g -> matchedFood(g.dish)?.let { food -> food to g.score } }
            .distinctBy { it.first.name }.take(3)
        val holder=LinearLayout(this).apply {
            orientation=LinearLayout.VERTICAL
            setPadding(dp(16),dp(8),dp(16),dp(10))
        }
        holder.addView(label("O modelo offline reconhece um prato de cada vez e não " +
            "identifica com segurança refeições completas, como carne com arroz, " +
            "batatas, legumes, sopa e sobremesa. Confirma todos os alimentos e " +
            "as porções antes de calcular calorias.",14f))
        val dialog=MaterialAlertDialogBuilder(this)
            .setTitle("🥘 Refeição com vários alimentos")
            .setView(ScrollView(this).apply {addView(holder)})
            .setNegativeButton("Cancelar",null).create()
        holder.addView(button("🥗 Escolher todos os alimentos da fotografia") {
            dialog.dismiss();chooseFoods(emptySet(),true)
        })
        if(candidates.isNotEmpty()) {
            holder.addView(label("Sugestões parciais e não confirmadas:",13f,true))
            candidates.forEach { (food,_) ->
                holder.addView(button("Adicionar ${food.name} (confirmar porção)") {
                    dialog.dismiss();chooseFoods(setOf(food.name),true)
                })
            }
        } else {
            holder.addView(label("Não encontrei resultados suficientemente " +
                "fiáveis. Não vou inventar pratos nem indicar 0 kcal.",13f))
        }
        dialog.show()
    }
''' +s[end:]

replace('''        p.addView(button("🥗 Calcular por alimentos e porções") { chooseFoods(emptySet(), false) })''',
'''        p.addView(button("🥗 Selecionar vários alimentos e calcular kcal") {
            chooseFoods(emptySet(), photo!=null)
        })''','multi-food shortcut')
replace('''            p.addView(button("✨ Identificar prato na fotografia") { detectOffline() })''',
'''            p.addView(button("✨ Sugestões offline (apenas um prato)") { detectOffline() })''','truthful classifier button')
replace('''"Reconhecimento local de pratos com modelo alimentar especializado. As calorias dependem dos alimentos e dos gramas confirmados por ti."''',
'''"O reconhecimento offline sugere apenas tipos de pratos. Para refeições completas, seleciona todos os alimentos, confirma as porções e calcula kcal."''',
    'recognition limitations')

# Portuguese foods frequently served in the same meal should be searchable.
replace('''        Food("Carne de porco",242.0,27.0,0.0,14.0,150,listOf("Pork")),''',
'''        Food("Carne de porco",242.0,27.0,0.0,14.0,150,listOf("Pork")),
        Food("Lombo de porco assado",195.0,28.0,0.0,8.0,160,listOf("Pork loin")),
        Food("Esparregado",90.0,2.5,9.0,4.5,100,listOf("Spinach")),
        Food("Molho de carne",95.0,2.0,5.0,7.0,35,listOf("Gravy")),''','portuguese savory food')
replace('''        Food("Bolo simples",350.0,5.0,50.0,14.0,100,listOf("Cake")),''',
'''        Food("Bolo simples",350.0,5.0,50.0,14.0,100,listOf("Cake")),
        Food("Bolo de iogurte",340.0,6.0,47.0,14.0,85,listOf("Yogurt cake")),''',
        'yogurt cake')
replace('''        Food("Salada de alface e tomate",23.0,1.3,3.8,0.3,120,listOf("Salad")),''',
'''        Food("Salada de alface e tomate",23.0,1.3,3.8,0.3,120,listOf("Salad")),
        Food("Salada mista sem molho",27.0,1.0,4.8,0.2,100,listOf("Mixed salad")),''',
        'mixed salad')

# Every photo already saved in private MealDiary is linked by UUID filename, but
# the former history dialog never read those files. Reveal thumbnails and the
# original photo; support attaching photos to older manually-added entries.
replace('''    private var pendingPhoto: File? = null''',
'''    private var pendingPhoto: File? = null
    private var historyPhotoEntryId: String? = null
    private val historyPhotoPicker=registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        val id=historyPhotoEntryId
        historyPhotoEntryId=null
        if(uri==null || id.isNullOrBlank())return@registerForActivityResult
        runCatching {
            val bitmap=contentResolver.openInputStream(uri)?.use {
                BitmapFactory.decodeStream(it)
            } ?: error("Fotografia ilegível")
            val factor=minOf(1.0,1280.0/maxOf(bitmap.width,bitmap.height).toDouble())
            val scaled=if(factor<1.0)Bitmap.createScaledBitmap(bitmap,
                (bitmap.width*factor).toInt().coerceAtLeast(1),
                (bitmap.height*factor).toInt().coerceAtLeast(1),true) else bitmap
            val out=java.io.ByteArrayOutputStream()
            check(scaled.compress(Bitmap.CompressFormat.JPEG,83,out))
            if(scaled!==bitmap)scaled.recycle()
            bitmap.recycle()
            check(out.size() in 500..2_500_000) {"Fotografia demasiado grande ou inválida"}
            check(MealDiary(this,profileId).attachPhoto(id,out.toByteArray())) {
                "Refeição não encontrada neste perfil"
            }
        }.onSuccess {Toast.makeText(this,"Fotografia associada à refeição.",Toast.LENGTH_LONG).show();draw()}
         .onFailure {alert("Erro ao guardar fotografia: ${it.message}")}
    }''', 'import historic photo')

start=s.index('    private fun showHistory(){')
end=s.index('    private fun alert(s:String)',start)
s=s[:start]+'''    private fun showHistory(){
        val diary=MealDiary(this,profileId)
        val items=diary.list()
        val p=panel("Histórico de refeições",if(items.length()==0)
            "Ainda não há refeições guardadas." else "${items.length()} refeições neste perfil. Toque para ver a fotografia e os valores.")
        for(i in 0 until minOf(items.length(),40)){
            val row=items.getJSONObject(i)
            val name=row.optString("meal","Refeição")
            val whenDate=LocalDateTime.ofInstant(java.time.Instant.ofEpochMilli(row.optLong("at")),
                java.time.ZoneId.systemDefault()).format(DateTimeFormatter.ofPattern("dd/MM · HH:mm"))
            val picture=diary.photoFile(row)
            val line=LinearLayout(this).apply {orientation=LinearLayout.HORIZONTAL
                gravity=Gravity.CENTER_VERTICAL}
            if(picture!=null){
                val thumb=BitmapFactory.decodeFile(picture.absolutePath,
                    BitmapFactory.Options().apply{inSampleSize=8})
                if(thumb!=null)line.addView(ImageView(this).apply {
                    setImageBitmap(thumb);scaleType=ImageView.ScaleType.CENTER_CROP
                    contentDescription="Foto de $name em $whenDate"
                },LinearLayout.LayoutParams(dp(66),dp(66)).apply{marginEnd=dp(8)})
            }
            line.addView(button("${if(picture!=null)"📷 " else ""}$whenDate · $name · ${row.optInt("kcal")} kcal") {
                showMealDetails(row,diary)
            },LinearLayout.LayoutParams(0,dp(65),1f))
            p.addView(line)
        }
    }
    private fun showMealDetails(row:JSONObject,diary:MealDiary){
        val holder=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL
            setPadding(dp(14),dp(8),dp(14),dp(12))}
        val picture=diary.photoFile(row)
        if(picture!=null){
            val bmp=BitmapFactory.decodeFile(picture.absolutePath,
                BitmapFactory.Options().apply{inSampleSize=2})
            if(bmp!=null)holder.addView(ImageView(this).apply {
                setImageBitmap(bmp);scaleType=ImageView.ScaleType.FIT_CENTER
                adjustViewBounds=true;contentDescription="Fotografia da refeição"
            },LinearLayout.LayoutParams(-1,dp(220)))
        } else holder.addView(label("Sem fotografia guardada neste registo.",13f))
        holder.addView(label("${row.optString("foods")}\\n\\nEnergia: " +
            "${row.optDouble("kcal")} kcal\\nProteínas: ${row.optDouble("protein_g")} g" +
            "\\nHidratos: ${row.optDouble("carbs_g")} g" +
            "\\nGorduras: ${row.optDouble("fat_g")} g" +
            "\\n\\n${row.optString("note")}",14f))
        val content=ScrollView(this).apply{addView(holder)}
        MaterialAlertDialogBuilder(this).setTitle(row.optString("meal","Refeição"))
            .setView(content)
            .setNegativeButton("📷 Associar foto"){_,_->
                historyPhotoEntryId=row.optString("id")
                historyPhotoPicker.launch(arrayOf("image/jpeg","image/png","image/webp"))
            }
            .setNeutralButton("Eliminar"){_,_->
                MaterialAlertDialogBuilder(this).setTitle("Eliminar esta refeição?")
                    .setPositiveButton("Eliminar"){_,_->diary.remove(row.getString("id"));draw()}
                    .setNegativeButton("Cancelar",null).show()
            }.setPositiveButton("Fechar",null).show()
    }
''' +s[end:]

replace('''    fun add(entry:JSONObject,photo:ByteArray?){''',
'''    fun photoFile(entry:JSONObject): File? {
        val name=entry.optString("photo")
        if(!name.matches(Regex("[0-9a-fA-F-]{36}\\\\.jpg")))return null
        return File(folder,name).takeIf{it.isFile && it.length() in 500..3_000_000}
    }
    fun attachPhoto(id:String,jpeg:ByteArray):Boolean {
        if(!id.matches(Regex("[0-9a-fA-F-]{36}")))return false
        if(jpeg.size !in 500..2_500_000)return false
        val items=list()
        var changed=false
        for(i in 0 until items.length()){
            val row=items.optJSONObject(i)?:continue
            if(row.optString("id")==id){
                val name="$id.jpg"
                File(folder,name).writeBytes(jpeg)
                row.put("photo",name)
                changed=true
                break
            }
        }
        if(changed)persist(items)
        return changed
    }
    fun add(entry:JSONObject,photo:ByteArray?){''','private photo access and attach')
meal.write_text(s,encoding='utf-8')

gradle=root/'app/build.gradle.kts'
g=gradle.read_text(encoding='utf-8')
assert g.count('versionCode = 90')==1 and g.count('versionName = "1.9.80"')==1
g=g.replace('versionCode = 90','versionCode = 91',1)
g=g.replace('versionName = "1.9.80"','versionName = "1.9.81"',1)
gradle.write_text(g,encoding='utf-8')
print('v1.9.81: no unsupported Tafelspitz auto result, PT foods, image history & retroactive attachment')