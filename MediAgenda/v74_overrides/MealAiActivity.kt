package com.mediagenda.app

import android.content.Intent
import android.content.res.ColorStateList
import android.content.res.Configuration
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Color
import android.graphics.Matrix
import android.graphics.drawable.BitmapDrawable
import android.graphics.drawable.ColorDrawable
import android.graphics.drawable.GradientDrawable
import android.graphics.drawable.LayerDrawable
import android.net.Uri
import android.os.Bundle
import android.provider.MediaStore
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.EditText
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import com.google.android.material.button.MaterialButton
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.mediagenda.app.data.ProfileStore
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.label.ImageLabeling
import com.google.mlkit.vision.label.defaults.ImageLabelerOptions
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import java.util.Locale
import java.util.UUID

/** Offline meal recognition, local nutrition reference, and per-profile private diary.
 * Labels may be broad or wrong; no data leaves the phone and users verify every item/portion.
 */
class MealAiActivity : AppCompatActivity() {
    companion object { const val EXTRA_PROFILE_ID = "profile_id" }
    private lateinit var profileId: String
    private lateinit var body: LinearLayout
    private var photo: ByteArray? = null
    private var pendingPhoto: File? = null
    private var busy = false
    private val isDark get() = when (getSharedPreferences("mediagenda_ui", MODE_PRIVATE).getString("theme_mode", "system")) {
        "dark" -> true; "light" -> false
        else -> (resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK) == Configuration.UI_MODE_NIGHT_YES
    }
    private val ink get() = if (isDark) Color.WHITE else Color.rgb(20, 34, 48)
    private val secondary get() = if (isDark) Color.rgb(195, 216, 223) else Color.rgb(84, 103, 115)
    private val teal = Color.rgb(0, 193, 182)
    private fun dp(n: Int) = (resources.displayMetrics.density * n + .5f).toInt()
    private fun label(s: String, size: Float = 14f, strong: Boolean = false): TextView = TextView(this).apply {
        text=s; textSize=size; setTextColor(ink); if (strong) setTypeface(null,1)
        setPadding(0, dp(4), 0, dp(5))
    }
    private fun button(s: String, action: () -> Unit): MaterialButton = MaterialButton(this).apply {
        text=s; isAllCaps=false; textSize=13f
        strokeColor=ColorStateList.valueOf(teal); strokeWidth=dp(1)
        backgroundTintList=ColorStateList.valueOf(Color.TRANSPARENT)
        setTextColor(if(isDark) Color.rgb(147,238,226) else Color.rgb(0,114,107))
        cornerRadius=dp(14); setOnClickListener { if(!busy) action() }
    }
    private fun panel(title: String, description: String = ""): LinearLayout {
        val outer = LinearLayout(this).apply {
            orientation=LinearLayout.VERTICAL
            background=GradientDrawable().apply {setColor(if(isDark) Color.rgb(29,44,56) else Color.WHITE)
                cornerRadius=dp(18).toFloat(); setStroke(dp(1),if(isDark)Color.rgb(74,99,111) else Color.rgb(215,224,233))}
            setPadding(dp(16),dp(12),dp(16),dp(13))
        }
        outer.addView(label(title, 18f, true))
        if(description.isNotBlank()) outer.addView(label(description,13f).apply { setTextColor(secondary) })
        body.addView(outer,LinearLayout.LayoutParams(-1,-2).apply {bottomMargin=dp(12)})
        return outer
    }
    private val camera = registerForActivityResult(ActivityResultContracts.TakePicture()) { ok ->
        val f = pendingPhoto; pendingPhoto=null
        if(ok && f != null) useImage(Uri.fromFile(f)) else f?.delete()
    }
    private val gallery = registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if(uri != null) useImage(uri)
    }
    override fun onCreate(state: Bundle?) {
        super.onCreate(state)
        val id=intent.getStringExtra(EXTRA_PROFILE_ID).orEmpty()
        if(ProfileStore(this).all().none { it.id == id }) {finish();return}
        profileId=id
        val root=LinearLayout(this).apply { orientation=LinearLayout.VERTICAL
            setPadding(dp(16),dp(10),dp(16),dp(10))
            val bg=ContextCompat.getDrawable(this@MealAiActivity,R.drawable.saude_background)
            if (isDark && bg != null) { if(bg is BitmapDrawable)bg.gravity=Gravity.FILL
                background=LayerDrawable(arrayOf(bg, ColorDrawable(Color.argb(100,1,14,24))))
            } else setBackgroundColor(Color.rgb(245,248,250))
        }
        root.addView(label("‹  SaúdePrática  /  Nutrição",19f,true).apply {
            setTextColor(teal); setOnClickListener { finish() }
        })
        val scroll=ScrollView(this)
        body=LinearLayout(this).apply {orientation=LinearLayout.VERTICAL;setPadding(0,dp(10),0,dp(28))}
        scroll.addView(body);root.addView(scroll,LinearLayout.LayoutParams(-1,0,1f))
        WindowCompat.setDecorFitsSystemWindows(window,false)
        window.statusBarColor=Color.TRANSPARENT;window.navigationBarColor=Color.TRANSPARENT
        WindowInsetsControllerCompat(window,window.decorView).apply {
            isAppearanceLightStatusBars=!isDark;isAppearanceLightNavigationBars=!isDark
        }
        ViewCompat.setOnApplyWindowInsetsListener(root) { v,insets ->
            val safe=insets.getInsets(WindowInsetsCompat.Type.statusBars() or WindowInsetsCompat.Type.navigationBars() or WindowInsetsCompat.Type.displayCutout())
            v.setPadding(dp(16)+safe.left,dp(10)+safe.top,dp(16)+safe.right,dp(10)+safe.bottom)
            insets
        }
        setContentView(root);ViewCompat.requestApplyInsets(root)
        draw()
    }
    private fun draw() {
        body.removeAllViews()
        body.addView(label("🍽️ Diário de refeições",25f,true))
        val p=panel("Refeições e calorias · offline", "Identificação local de alimentos com ML Kit. Os valores são estimativas por porção, não medições: confirma sempre antes de guardar.")
        p.addView(button("📷 Fotografar refeição") { capture() })
        p.addView(button("🖼️ Escolher imagem") { gallery.launch(arrayOf("image/jpeg","image/png","image/webp")) })
        p.addView(button("🥗 Calcular por alimentos e porções") { chooseFoods(emptySet(), false) })
        p.addView(button("✎ Registar refeição manualmente") { editAndSave(null) })
        photo?.let { jpeg ->
            val preview=ImageView(this).apply {scaleType=ImageView.ScaleType.FIT_CENTER
                adjustViewBounds=true;setImageBitmap(BitmapFactory.decodeByteArray(jpeg,0,jpeg.size)) }
            p.addView(preview,LinearLayout.LayoutParams(-1,dp(210)))
            p.addView(button("✨ Identificar alimentos no telemóvel") { detectOffline() })
        }
        panel("Privacidade · reconhecimento local",
            "Não precisa de Internet, conta ou chave API. O modelo ML Kit está incluído na app e a " +
            "fotografia não é enviada a servidores. Em pratos mistos, pode apenas reconhecer " +
            "que há comida e não identificar os ingredientes. Nesses casos, escolhe-os na lista. " +
            "As calorias dependem dos gramas e dos ingredientes que confirmares.")
        showHistory()
    }
    private fun capture() {
        try {
            val dir=File(cacheDir,"saudepratica_document_scans").apply {mkdirs()}
            val file=File.createTempFile("meal_", ".jpg",dir)
            pendingPhoto=file
            camera.launch(FileProvider.getUriForFile(this,"$packageName.documents",file))
        }catch(e:Exception){alert("Não foi possível abrir a câmara: ${e.message}")}
    }
    private fun useImage(uri:Uri) {
        try {
            val bitmap=contentResolver.openInputStream(uri)?.use { stream ->
                BitmapFactory.decodeStream(stream)
            } ?: error("Fotografia ilegível")
            val factor=minOf(1.0,1280.0/maxOf(bitmap.width,bitmap.height).toDouble())
            val output=if(factor<1.0) Bitmap.createScaledBitmap(bitmap,(bitmap.width*factor).toInt().coerceAtLeast(1),
                (bitmap.height*factor).toInt().coerceAtLeast(1),true) else bitmap
            val mem=java.io.ByteArrayOutputStream()
            check(output.compress(Bitmap.CompressFormat.JPEG,83,mem)) {"Erro ao preparar imagem"}
            if(output!==bitmap)output.recycle();bitmap.recycle()
            check(mem.size() in 500..2_500_000) {"Imagem muito grande ou vazia"}
            photo=mem.toByteArray();draw()
        }catch(e:Exception){alert("Erro ao importar fotografia: ${e.message}")}
        finally { pendingPhoto?.delete();pendingPhoto=null }
    }
    /** Base image-labeling is generic, not food-specific; candidates are only suggestions. */
    private fun detectOffline() {
        val bytes=photo ?: return
        if (busy) return
        busy=true
        val bitmap=BitmapFactory.decodeByteArray(bytes,0,bytes.size)
        if(bitmap==null){busy=false;alert("Não foi possível ler a fotografia.");return}
        val labeler=ImageLabeling.getClient(
            ImageLabelerOptions.Builder().setConfidenceThreshold(0.62f).build())
        try {
            labeler.process(InputImage.fromBitmap(bitmap,0))
                .addOnSuccessListener { labels ->
                    val matches=FoodReference.items.filter { food ->
                        labels.any { label ->
                            label.confidence>=0.68f && food.hints.any { hint ->
                                label.text.equals(hint,ignoreCase=true)
                            }
                        }
                    }.map { it.name }.toSet()
                    if(matches.isEmpty()) {
                        Toast.makeText(this,
                            "Não foi possível distinguir alimentos. Escolhe-os na lista.",
                            Toast.LENGTH_LONG).show()
                    }
                    chooseFoods(matches,true)
                }.addOnFailureListener { error ->
                    alert("Não foi possível fazer o reconhecimento offline. " +
                        "Podes selecionar os alimentos manualmente. ${error.localizedMessage.orEmpty()}")
                }.addOnCompleteListener {
                    bitmap.recycle();labeler.close();busy=false
                }
        }catch(e:Exception){
            bitmap.recycle();labeler.close();busy=false
            alert("Erro no reconhecimento offline: ${e.localizedMessage}")
        }
    }
    private fun chooseFoods(suggestions: Set<String>, withPhoto: Boolean) {
        val choices=FoodReference.items.sortedWith(compareByDescending<FoodReference.Food> {
            it.name in suggestions
        }.thenBy { it.name })
        val picked=BooleanArray(choices.size){choices[it].name in suggestions}
        val title=if(withPhoto) "Confirmar alimentos do prato" else "Escolher alimentos da refeição"
        MaterialAlertDialogBuilder(this).setTitle(title)
            .setMultiChoiceItems(choices.map{it.name}.toTypedArray(),picked) { _,which,checked ->
                picked[which]=checked
            }.setNegativeButton("Cancelar",null)
            .setPositiveButton("Indicar porções",null)
            .show().also { dialog ->
                dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE).setOnClickListener {
                    val chosen=choices.filterIndexed{index,_->picked[index]}
                    if(chosen.isEmpty()) {
                        Toast.makeText(this,"Escolhe pelo menos um alimento.",Toast.LENGTH_LONG).show()
                    } else {dialog.dismiss();enterPortions(chosen)}
                }
            }
    }
    private fun enterPortions(foods:List<FoodReference.Food>) {
        val fields=LinearLayout(this).apply {
            orientation=LinearLayout.VERTICAL;setPadding(dp(16),dp(5),dp(16),dp(8))
        }
        fields.addView(label("Indica os gramas aproximados de cada alimento. Os valores " +
            "incluem apenas os ingredientes selecionados; adiciona azeite, molhos e bebidas se existirem.",13f))
        val amounts=foods.map { food ->
            val input=input("${food.name} (gramas)",food.portion.toString(),true)
            fields.addView(input)
            food to input
        }
        val scroll=ScrollView(this).apply {addView(fields)}
        val dialog=MaterialAlertDialogBuilder(this)
            .setTitle("Porções da refeição")
            .setView(scroll).setNegativeButton("Cancelar",null)
            .setPositiveButton("Calcular calorias",null).show()
        dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE).setOnClickListener {
            try {
                var calories=0.0;var protein=0.0;var carbs=0.0;var fat=0.0
                val list=JSONArray()
                for((food,field) in amounts){
                    val grams=field.text.toString().replace(',','.').toDoubleOrNull()
                    require(grams!=null && grams>0.0 && grams<=3000.0){"Indica gramas válidos para ${food.name}."}
                    val multiplier=grams/100.0
                    val kcal=food.kcal*multiplier
                    calories+=kcal;protein+=food.protein*multiplier
                    carbs+=food.carbs*multiplier;fat+=food.fat*multiplier
                    list.put(JSONObject().put("name",food.name)
                        .put("grams",kotlin.math.round(grams).toInt())
                        .put("kcal",kotlin.math.round(kcal).toInt()))
                }
                require(calories<=10000.0){"Confirma as quantidades indicadas."}
                val result=JSONObject().put("foods",list).put("total_kcal",calories)
                    .put("protein_g",protein).put("carbs_g",carbs).put("fat_g",fat)
                    .put("uncertainty_note", "Estimativa offline por tabelas médias/100 g. " +
                        "As quantidades e a confeção podem alterar bastante os valores.")
                dialog.dismiss();editAndSave(result)
            }catch(e:Exception){Toast.makeText(this,e.message ?: "Quantidade inválida",Toast.LENGTH_LONG).show()}
        }
    }
    private fun input(title:String, initial:String, numerical:Boolean=false): EditText {
        return EditText(this).apply {hint=title;setSingleLine(!title.contains("Alimentos"))
            setText(initial);textSize=16f
            if(numerical)inputType=android.text.InputType.TYPE_CLASS_NUMBER or android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL
        }
    }
    private fun editAndSave(result:JSONObject?) {
        val foods=result?.optJSONArray("foods") ?: JSONArray()
        val foodText=(0 until foods.length()).joinToString("\n") { i ->
            val f=foods.optJSONObject(i) ?: JSONObject()
            f.optString("name") + " — "+ f.optInt("grams",0) +" g (≈" + f.optInt("kcal",0) + " kcal)"
        }
        val names=input("Alimentos e porções (editável)",foodText)
        val kcal=input("Energia (kcal)",result?.optDouble("total_kcal",0.0)?.takeIf{it>0}?.let{String.format(Locale.US,"%.0f",it)} ?: "",true)
        val protein=input("Proteínas (g)",result?.optDouble("protein_g",0.0)?.let{String.format(Locale.US,"%.1f",it)} ?: "",true)
        val carbs=input("Hidratos (g)",result?.optDouble("carbs_g",0.0)?.let{String.format(Locale.US,"%.1f",it)} ?: "",true)
        val fat=input("Gordura (g)",result?.optDouble("fat_g",0.0)?.let{String.format(Locale.US,"%.1f",it)} ?: "",true)
        val type=input("Tipo de refeição","Almoço")
        val note=input("Observações",result?.optString("uncertainty_note","") ?: "")
        val fields=LinearLayout(this).apply {orientation=LinearLayout.VERTICAL;setPadding(dp(14),0,dp(14),0)}
        fields.addView(label("Revê todas as quantidades antes de guardar. Óleo, molhos e ingredientes escondidos podem alterar muito as calorias.",13f))
        listOf(type,names,kcal,protein,carbs,fat,note).forEach { fields.addView(it) }
        val scroll=ScrollView(this).apply {addView(fields)}
        val dialog=MaterialAlertDialogBuilder(this).setTitle("Confirmar refeição")
            .setView(scroll).setNegativeButton("Cancelar",null).setPositiveButton("Guardar",null).show()
        dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE).setOnClickListener {
            try {
                fun numeric(v:EditText)=v.text.toString().trim().replace(',','.').toDoubleOrNull() ?: 0.0
                val energy=numeric(kcal)
                require(energy in 0.0..10000.0){"Indica um valor de kcal válido"}
                require(names.text.toString().isNotBlank()){ "Indica pelo menos um alimento" }
                val entry=JSONObject().put("id",UUID.randomUUID().toString())
                    .put("at",System.currentTimeMillis()).put("meal",type.text.toString().take(80))
                    .put("foods",names.text.toString().take(1200))
                    .put("kcal",energy).put("protein_g",numeric(protein).coerceIn(0.0,1000.0))
                    .put("carbs_g",numeric(carbs).coerceIn(0.0,1000.0)).put("fat_g",numeric(fat).coerceIn(0.0,1000.0))
                    .put("note",note.text.toString().take(500)).put("estimated",result!=null)
                MealDiary(this,profileId).add(entry,photo)
                Toast.makeText(this,"Refeição guardada neste perfil.",Toast.LENGTH_LONG).show()
                dialog.dismiss();photo=null;draw()
            }catch(e:Exception){alert("Não foi possível guardar: ${e.message}")}
        }
    }
    private fun showHistory(){
        val diary=MealDiary(this,profileId)
        val items=diary.list()
        val p=panel("Histórico de refeições", if(items.length()==0) "Ainda não há refeições guardadas." else "${items.length()} refeições neste perfil.")
        for(i in 0 until minOf(items.length(),40)) {
            val row=items.getJSONObject(i)
            val name=row.optString("meal","Refeição")
            val whenDate=LocalDateTime.ofInstant(java.time.Instant.ofEpochMilli(row.optLong("at")),java.time.ZoneId.systemDefault())
                .format(DateTimeFormatter.ofPattern("dd/MM · HH:mm"))
            p.addView(button("$whenDate · $name · ${row.optInt("kcal")} kcal") {
                MaterialAlertDialogBuilder(this).setTitle(name)
                    .setMessage("${row.optString("foods")}\n\nEnergia: ${row.optDouble("kcal")} kcal\nProteínas: ${row.optDouble("protein_g")} g\nHidratos: ${row.optDouble("carbs_g")} g\nGorduras: ${row.optDouble("fat_g")} g\n\n${row.optString("note")}")
                    .setNeutralButton("Eliminar") { _,_ ->
                        MaterialAlertDialogBuilder(this).setTitle("Eliminar esta refeição?")
                            .setPositiveButton("Eliminar") { _,_ ->diary.remove(row.getString("id"));draw()}
                            .setNegativeButton("Cancelar",null).show()
                    }.setPositiveButton("Fechar",null).show()
            })
        }
    }
    private fun alert(s:String){MaterialAlertDialogBuilder(this).setTitle("SaúdePrática")
        .setMessage(s).setPositiveButton("OK",null).show()}
}


/** Approximate cooked-food reference (per 100 g), strictly indicative and editable. */
private object FoodReference {
    data class Food(val name:String,val kcal:Double,val protein:Double,val carbs:Double,
        val fat:Double,val portion:Int,val hints:List<String> = emptyList())
    val items=listOf(
        Food("Arroz cozido",130.0,2.7,28.0,0.3,150,listOf("Rice")),
        Food("Batata cozida",87.0,1.9,20.0,0.1,150,listOf("Potato")),
        Food("Batata frita",312.0,3.4,41.0,15.0,120,listOf("French fries","Fried food")),
        Food("Massa cozida",157.0,5.8,30.9,0.9,150,listOf("Pasta","Noodle")),
        Food("Frango grelhado",165.0,31.0,0.0,3.6,150,listOf("Chicken")),
        Food("Bife de vaca grelhado",217.0,26.0,0.0,12.0,150,listOf("Beef","Steak")),
        Food("Carne de porco",242.0,27.0,0.0,14.0,150,listOf("Pork")),
        Food("Salmão grelhado",206.0,22.0,0.0,12.0,150,listOf("Salmon")),
        Food("Peixe branco cozido",100.0,22.0,0.0,1.0,150,listOf("Fish")),
        Food("Atum ao natural",116.0,26.0,0.0,1.0,100,listOf("Tuna")),
        Food("Ovo cozido",155.0,13.0,1.1,11.0,55,listOf("Egg")),
        Food("Salada de alface e tomate",23.0,1.3,3.8,0.3,120,listOf("Salad")),
        Food("Brócolos cozidos",35.0,2.4,7.2,0.4,120,listOf("Broccoli")),
        Food("Legumes cozidos",45.0,2.0,8.0,0.5,150,listOf("Vegetable")),
        Food("Sopa de legumes",45.0,1.5,7.0,1.0,250,listOf("Soup")),
        Food("Pão branco",265.0,9.0,49.0,3.2,50,listOf("Bread")),
        Food("Pão integral",247.0,13.0,41.0,4.2,50),
        Food("Queijo flamengo",356.0,25.0,2.0,27.0,30,listOf("Cheese")),
        Food("Iogurte natural",63.0,3.5,4.7,3.3,125,listOf("Yogurt")),
        Food("Leite meio-gordo",47.0,3.4,4.8,1.6,200,listOf("Milk")),
        Food("Maçã",52.0,0.3,14.0,0.2,150,listOf("Apple")),
        Food("Banana",89.0,1.1,23.0,0.3,120,listOf("Banana")),
        Food("Laranja",47.0,0.9,12.0,0.1,150,listOf("Orange")),
        Food("Morangos",32.0,0.7,7.7,0.3,150,listOf("Strawberry")),
        Food("Pizza",266.0,11.0,33.0,10.0,200,listOf("Pizza")),
        Food("Hambúrguer",260.0,14.0,25.0,12.0,180,listOf("Hamburger")),
        Food("Sanduíche",240.0,10.0,29.0,9.0,180,listOf("Sandwich")),
        Food("Bolo simples",350.0,5.0,50.0,14.0,100,listOf("Cake")),
        Food("Bolachas",480.0,6.0,65.0,22.0,50,listOf("Cookie","Biscuit")),
        Food("Chocolate",546.0,5.0,61.0,31.0,30,listOf("Chocolate")),
        Food("Azeite",884.0,0.0,0.0,100.0,10,listOf("Olive oil")),
        Food("Manteiga",717.0,0.9,0.1,81.0,10,listOf("Butter")),
        Food("Molho de tomate",60.0,1.5,10.0,1.5,40,listOf("Tomato sauce")),
        Food("Feijão cozido",127.0,8.7,23.0,0.5,120,listOf("Bean")),
        Food("Grão-de-bico cozido",164.0,8.9,27.4,2.6,120,listOf("Chickpea")),
        Food("Água",0.0,0.0,0.0,0.0,200,listOf("Water")),
        Food("Refrigerante normal",42.0,0.0,10.5,0.0,330,listOf("Soft drink","Soda")),
        Food("Sumo de laranja",45.0,0.7,10.4,0.2,200,listOf("Juice"))
    )
}

private class MealDiary(context:android.content.Context, profileId:String) {
    private val folder=File(context.filesDir,"saudepratica_meal_diary/$profileId").apply {mkdirs()}
    private val index=File(folder,"meals.json")
    fun list(): JSONArray = runCatching {JSONArray(index.readText(Charsets.UTF_8))}.getOrDefault(JSONArray())
    fun add(entry:JSONObject,photo:ByteArray?){
        val name="${entry.getString("id")}.jpg"
        if(photo!=null) File(folder,name).writeBytes(photo)
        entry.put("photo",if(photo!=null)name else "")
        val previous=list();val fresh=JSONArray().put(entry)
        for(i in 0 until previous.length())fresh.put(previous.getJSONObject(i))
        persist(fresh)
    }
    fun remove(id:String){
        val fresh=JSONArray();val old=list()
        for(i in 0 until old.length()){
            val row=old.getJSONObject(i)
            if(row.optString("id")==id){val filename=row.optString("photo")
                if(filename.matches(Regex("[0-9a-fA-F-]{36}\\.jpg")))File(folder,filename).delete()
            }else fresh.put(row)
        }
        persist(fresh)
    }
    private fun persist(value:JSONArray){
        val temp=File(folder,"meals.tmp");temp.writeText(value.toString(),Charsets.UTF_8)
        check(temp.renameTo(index) || runCatching {temp.copyTo(index,true);temp.delete();true}.getOrDefault(false)) {
            "Erro a guardar o diário" }
    }
}