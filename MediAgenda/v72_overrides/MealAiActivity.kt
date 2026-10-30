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
import android.util.Base64
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
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import java.util.Locale
import java.util.UUID

/** Food estimation from a photograph is advisory, not a clinical calculation.
 * Every entry requires human review. A configured HTTPS proxy holds the actual AI API key.
 */
class MealAiActivity : AppCompatActivity() {
    companion object { const val EXTRA_PROFILE_ID = "profile_id" }
    private lateinit var profileId: String
    private lateinit var body: LinearLayout
    private var photo: ByteArray? = null
    private var pendingPhoto: File? = null
    private var busy = false
    private val settings by lazy { MealAiSettings(this) }
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
        val p=panel("Fotografar e analisar", "A IA estima alimentos, porções e nutrientes. Confirma e corrige antes de guardar; a foto não permite uma medição exata.")
        p.addView(button("📷 Fotografar refeição") { capture() })
        p.addView(button("🖼️ Escolher imagem") { gallery.launch(arrayOf("image/jpeg","image/png","image/webp")) })
        p.addView(button("✎ Registar refeição manualmente") { editAndSave(null) })
        photo?.let { jpeg ->
            val preview=ImageView(this).apply {scaleType=ImageView.ScaleType.FIT_CENTER
                adjustViewBounds=true;setImageBitmap(BitmapFactory.decodeByteArray(jpeg,0,jpeg.size)) }
            p.addView(preview,LinearLayout.LayoutParams(-1,dp(210)))
            p.addView(button("✨ Analisar com IA") { analyze() })
        }
        if(!settings.configured()) {
            val q=panel("Análise online ainda não configurada",
                "Para analisar fotografias com IA é necessário um serviço HTTPS privado. A chave da IA nunca fica na APK. Também podes guardar refeições manualmente.")
            q.addView(button("⚙ Configurar serviço de IA") { configure() })
        } else panel("Ligação de IA configurada", "As fotografias só são enviadas após tocares em Analisar e confirmares.")
            .addView(button("⚙ Alterar ligação") {configure()})
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
    private fun analyze(){
        val jpeg=photo ?: return
        if(!settings.configured()) {alert("Configura primeiro o endereço do serviço de IA. Podes guardar a refeição manualmente sem ligação.");return}
        MaterialAlertDialogBuilder(this).setTitle("Enviar fotografia para análise?")
            .setMessage("A fotografia será enviada ao serviço de IA configurado. Não serão enviados o nome, perfil, medicação nem outros dados clínicos. A resposta é uma estimativa, não um diagnóstico.")
            .setNegativeButton("Cancelar",null).setPositiveButton("Enviar e analisar") { _,_ ->
                busy=true
                val msg=panel("A analisar…","A fotografia está a ser enviada por HTTPS. Não feches este ecrã.")
                Thread {
                    val response=runCatching {
                        val url=URL(settings.endpoint())
                        check(url.protocol=="https") {"Só é permitido HTTPS"}
                        val connection=url.openConnection() as HttpURLConnection
                        connection.instanceFollowRedirects=false
                        connection.requestMethod="POST";connection.connectTimeout=15000;connection.readTimeout=45000
                        connection.setRequestProperty("Content-Type","application/json; charset=utf-8")
                        connection.setRequestProperty("Authorization","Bearer ${settings.token()}")
                        connection.doOutput=true
                        val payload=JSONObject().put("image_mime","image/jpeg")
                            .put("image_base64", Base64.encodeToString(jpeg,Base64.NO_WRAP))
                            .put("language","pt-PT")
                        try {
                            connection.outputStream.use {it.write(payload.toString().toByteArray(Charsets.UTF_8))}
                            val code=connection.responseCode
                            val output=(if(code in 200..299) connection.inputStream else connection.errorStream)
                                ?.bufferedReader()?.use {it.readText().take(30000)}.orEmpty()
                            check(code==200){"Serviço devolveu HTTP $code: ${output.take(150)}"}
                            val obj=JSONObject(output)
                            check(obj.has("foods") && obj.has("total_kcal")){"Formato de resposta de IA inválido"}
                            obj
                        }finally{connection.disconnect()}
                    }
                    runOnUiThread {
                        busy=false
                        body.removeView(msg)
                        response.onSuccess {editAndSave(it)}.onFailure {alert("Não foi possível analisar a refeição: ${it.message}")}
                    }
                }.start()
            }.show()
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
            f.optString("name") + " — "+ f.optInt("grams",0) +" g"
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
    private fun configure(){
        val url=input("Endereço HTTPS da API de IA",settings.endpoint())
        val token=input("Token de acesso ao servidor", "")
        token.inputType=android.text.InputType.TYPE_CLASS_TEXT or android.text.InputType.TYPE_TEXT_VARIATION_PASSWORD
        val p=LinearLayout(this).apply {orientation=LinearLayout.VERTICAL;setPadding(dp(16),0,dp(16),0)}
        p.addView(label("Utiliza um serviço privado compatível (ex.: Cloudflare Worker). Nunca introduzas aqui a chave da OpenAI; esta fica no servidor.",13f))
        p.addView(url);p.addView(token)
        val d=MaterialAlertDialogBuilder(this).setTitle("Configurar análise por IA")
            .setView(p).setNegativeButton("Cancelar",null)
            .setNeutralButton("Desligar"){_,_-> settings.clear(); draw()}
            .setPositiveButton("Guardar",null).show()
        d.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE).setOnClickListener {
            try {settings.save(url.text.toString(),token.text.toString());d.dismiss();draw()}
            catch(e:Exception){url.error=e.message ?: "Endereço inválido"}
        }
    }
    private fun alert(s:String){MaterialAlertDialogBuilder(this).setTitle("SaúdePrática")
        .setMessage(s).setPositiveButton("OK",null).show()}
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

/** Android KeyStore encrypts the proxy access token at rest; the OpenAI key is never on-device. */
private class MealAiSettings(private val context:android.content.Context){
    private val prefs=context.getSharedPreferences("sp_meal_ai_proxy",android.content.Context.MODE_PRIVATE)
    private val alias="saudepratica_meal_proxy_access_v1"
    fun endpoint()=prefs.getString("endpoint","").orEmpty()
    fun token():String = runCatching {
        val pair=prefs.getString("token_enc","").orEmpty().split(":")
        if(pair.size!=2)return@runCatching ""
        val ks=java.security.KeyStore.getInstance("AndroidKeyStore").apply {load(null)}
        val cipher=javax.crypto.Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(javax.crypto.Cipher.DECRYPT_MODE,ks.getKey(alias,null),
            javax.crypto.spec.GCMParameterSpec(128,Base64.decode(pair[0],Base64.NO_WRAP)))
        String(cipher.doFinal(Base64.decode(pair[1],Base64.NO_WRAP)), Charsets.UTF_8)
    }.getOrDefault("")
    fun configured()=endpoint().startsWith("https://") && token().isNotBlank()
    fun save(url:String, password:String){
        val target=url.trim()
        val parsed=java.net.URI(target)
        require(parsed.scheme=="https" && !parsed.host.isNullOrBlank() && parsed.userInfo==null && parsed.fragment==null){"Usa um endereço HTTPS válido"}
        require(password.length in 12..512){"Indica o token do servidor (mínimo de 12 caracteres)"}
        val keyStore=java.security.KeyStore.getInstance("AndroidKeyStore").apply {load(null)}
        if(!keyStore.containsAlias(alias)){
            val generator=javax.crypto.KeyGenerator.getInstance("AES","AndroidKeyStore")
            generator.init(android.security.keystore.KeyGenParameterSpec.Builder(alias,
                android.security.keystore.KeyProperties.PURPOSE_ENCRYPT or android.security.keystore.KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(android.security.keystore.KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(android.security.keystore.KeyProperties.ENCRYPTION_PADDING_NONE).build())
            generator.generateKey()
        }
        val c=javax.crypto.Cipher.getInstance("AES/GCM/NoPadding")
        c.init(javax.crypto.Cipher.ENCRYPT_MODE,keyStore.getKey(alias,null))
        val secret=Base64.encodeToString(c.iv,Base64.NO_WRAP)+":"+
            Base64.encodeToString(c.doFinal(password.toByteArray()),Base64.NO_WRAP)
        prefs.edit().putString("endpoint",target).putString("token_enc",secret).apply()
    }
    fun clear(){prefs.edit().clear().apply()}
}