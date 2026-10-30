"""SaúdePrática 1.9.78: Important Shortcuts with locally saved URLs and website icons."""
from pathlib import Path

base=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app")
root=Path("build-src/MediAgenda_Android_v1")

def change(path,old,new,label):
 s=path.read_text(encoding="utf-8")
 n=s.count(old)
 if n!=1:raise RuntimeError("v96 "+label+" anchor "+str(n))
 path.write_text(s.replace(old,new,1),encoding="utf-8")

activity=r'''package com.mediagenda.app

import android.content.Intent
import android.content.res.Configuration
import android.content.res.ColorStateList
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.BitmapDrawable
import android.graphics.drawable.ColorDrawable
import android.graphics.drawable.GradientDrawable
import android.graphics.drawable.LayerDrawable
import android.net.Uri
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.EditText
import android.widget.FrameLayout
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import com.google.android.material.button.MaterialButton
import com.google.android.material.card.MaterialCardView
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.mediagenda.app.i18n.AppLanguage
import org.json.JSONArray
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.security.MessageDigest
import java.util.UUID

/** Personal link list independent of health profiles; no WebView is used. */
class ImportantShortcutsActivity:AppCompatActivity(){
    companion object{const val EXTRA_MANAGE="manage_shortcuts"}
    private data class Link(val id:String,val name:String,val url:String)
    private val prefs by lazy{getSharedPreferences("saudepratica_important_shortcuts_v1",MODE_PRIVATE)}
    private val dark get()=when(getSharedPreferences("mediagenda_ui",MODE_PRIVATE)
        .getString("theme_mode","system")){
            "dark"->true
            "light"->false
            else->(resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK)==
                Configuration.UI_MODE_NIGHT_YES
        }
    private val ink get()=if(dark)Color.rgb(243,251,250)else Color.rgb(20,36,48)
    private val muted get()=if(dark)Color.rgb(184,207,217)else Color.rgb(94,113,121)
    private val surface get()=if(dark)Color.rgb(29,44,56)else Color.WHITE
    private val border get()=if(dark)Color.rgb(62,95,104)else Color.rgb(213,230,235)
    private val accent get()=if(dark)Color.rgb(100,220,204)else Color.rgb(0,143,135)
    private val lang get()=AppLanguage.codes.indexOf(AppLanguage.code(this)).coerceIn(0,4)
    private fun tr(pt:String,en:String,fr:String,de:String,es:String)=
        arrayOf(pt,en,fr,de,es)[lang]
    private fun dp(n:Int)=(n*resources.displayMetrics.density+0.5f).toInt()
    private lateinit var body:LinearLayout
    private var manage=false
    private val cache by lazy{File(cacheDir,"shortcuts-icons-v1").apply{mkdirs()}}
    private fun text(value:String,size:Float=15f,bold:Boolean=false,color:Int=ink)=
        TextView(this).apply{
            text=value;textSize=size;setTextColor(color)
            if(bold)setTypeface(typeface,Typeface.BOLD)
        }
    private fun bg(color:Int)=GradientDrawable().apply{
        setColor(color);cornerRadius=dp(14).toFloat()
    }
    private fun button(title:String,click:()->Unit)=MaterialButton(this).apply{
        text=title;isAllCaps=false;textSize=13f;cornerRadius=dp(13)
        setTextColor(accent)
        strokeWidth=dp(1)
        strokeColor=ColorStateList.valueOf(accent)
        backgroundTintList=ColorStateList.valueOf(surface)
        setOnClickListener{click()}
    }

    override fun onCreate(state:Bundle?){
        super.onCreate(state)
        manage=intent.getBooleanExtra(EXTRA_MANAGE,false)
        val backdrop=ContextCompat.getDrawable(this,R.drawable.saude_background)
        if(backdrop is BitmapDrawable)backdrop.gravity=Gravity.FILL
        val root=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            background=if(dark && backdrop!=null)
                LayerDrawable(arrayOf(backdrop,
                    ColorDrawable(Color.argb(126,0,16,24))))
                else ColorDrawable(if(dark)Color.rgb(5,22,32)
                    else Color.rgb(244,249,250))
        }
        val header=LinearLayout(this).apply{
            orientation=LinearLayout.HORIZONTAL
            gravity=Gravity.CENTER_VERTICAL
            setPadding(dp(12),dp(7),dp(10),dp(10))
        }
        header.addView(text("‹",35f,color=accent).apply{
            gravity=Gravity.CENTER
            contentDescription="Voltar"
            setOnClickListener{finish()}
        },LinearLayout.LayoutParams(dp(42),dp(64)))
        val head=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
        head.addView(text("SaúdePrática",13f,true,accent))
        head.addView(text(tr("🔗 Atalhos Importantes","🔗 Important Shortcuts",
            "🔗 Raccourcis importants","🔗 Wichtige Links",
            "🔗 Enlaces importantes"),22f,true))
        head.addView(text(tr("Páginas web no navegador do telemóvel",
            "Websites in your default browser",
            "Sites dans votre navigateur",
            "Webseiten im Standardbrowser",
            "Webs en el navegador predeterminado"),12f,color=muted))
        header.addView(head,LinearLayout.LayoutParams(0,-2,1f))
        root.addView(header)
        val scroll=ScrollView(this).apply{overScrollMode=View.OVER_SCROLL_NEVER}
        body=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(16),dp(10),dp(16),dp(28))
        }
        scroll.addView(body)
        root.addView(scroll,LinearLayout.LayoutParams(-1,0,1f))
        WindowCompat.setDecorFitsSystemWindows(window,false)
        window.statusBarColor=Color.TRANSPARENT
        window.navigationBarColor=Color.TRANSPARENT
        WindowInsetsControllerCompat(window,window.decorView).apply{
            isAppearanceLightStatusBars=!dark
            isAppearanceLightNavigationBars=!dark
        }
        ViewCompat.setOnApplyWindowInsetsListener(root){view,insets->
            val safe=insets.getInsets(WindowInsetsCompat.Type.statusBars() or
                WindowInsetsCompat.Type.navigationBars() or
                WindowInsetsCompat.Type.displayCutout())
            view.setPadding(safe.left,safe.top,safe.right,safe.bottom);insets
        }
        setContentView(root)
        ViewCompat.requestApplyInsets(root)
        render()
    }

    private fun normalized(input:String):String?{
        val value=input.trim()
        if(value.length>1500)return null
        val uri=runCatching{Uri.parse(value)}.getOrNull()?:return null
        if(uri.scheme !in listOf("https","http"))return null
        val host=uri.host.orEmpty()
        if(host.isBlank() || host.contains(" ") || host.contains("@"))return null
        if(runCatching{java.net.URI(value).rawUserInfo!=null}.getOrDefault(true))return null
        return value
    }
    private fun defaults()=listOf(
        Link("adse-default","ADSE Direta","https://adsedireta.adse.pt/"),
        Link("cga-default","CGA Direta","https://cgadirecta.cga.pt/"),
        Link("irs-default","Portal das Finanças · IRS","https://irs.portaldasfinancas.gov.pt/"),
        Link("apati-default","APATI Castanheira","https://apaticastanheira.pt/")
    )
    private fun save(items:List<Link>){
        val arr=JSONArray()
        items.forEach{arr.put(JSONObject().put("id",it.id)
            .put("name",it.name).put("url",it.url))}
        prefs.edit().putString("links",arr.toString()).apply()
    }
    private fun read():MutableList<Link>{
        if(!prefs.contains("links")){
            val result=defaults().toMutableList()
            save(result)
            return result
        }
        return runCatching{
            val arr=JSONArray(prefs.getString("links","[]")?:"[]")
            val result=mutableListOf<Link>()
            for(i in 0 until arr.length()){
                val obj=arr.optJSONObject(i)?:continue
                val url=normalized(obj.optString("url"))?:continue
                val name=obj.optString("name").trim()
                if(name.isNotEmpty())result.add(Link(
                    obj.optString("id").ifBlank{UUID.randomUUID().toString()},
                    name.take(85),url))
            }
            result
        }.getOrElse{mutableListOf()}
    }

    private fun render(){
        body.removeAllViews()
        val list=read()
        body.addView(text(
            if(manage)tr("Gerir os teus links","Manage your links",
                "Gérer vos liens","Links verwalten","Gestionar enlaces")
            else tr("Os teus atalhos","Your shortcuts",
                "Vos raccourcis","Deine Links","Tus enlaces"),19f,true).apply{
                setPadding(dp(5),0,0,dp(7))
            })
        body.addView(text(tr("Toca num link para abrir no navegador. Os ícones surgem automaticamente.",
            "Tap a link to open the browser. Icons appear automatically.",
            "Touchez un lien pour ouvrir le navigateur. Les icônes se chargent.",
            "Link antippen und Browser öffnen. Icons erscheinen automatisch.",
            "Toca un enlace para abrir el navegador. Los iconos aparecen solos."),
            13f,color=muted).apply{setPadding(dp(5),0,dp(5),dp(15))})
        list.forEach{renderEntry(it)}
        if(list.isEmpty())body.addView(text(tr("Ainda não existem links.","No links yet.",
            "Aucun lien.","Noch keine Links.","Aún no hay enlaces."),
            15f,color=muted))
        val action=if(manage)
            tr("＋ Adicionar atalho","＋ Add shortcut","＋ Ajouter un lien",
                "＋ Link hinzufügen","＋ Añadir enlace")
        else tr("⚙ Gerir e adicionar atalhos","⚙ Manage shortcuts",
            "⚙ Gérer les raccourcis","⚙ Links verwalten",
            "⚙ Gestionar enlaces")
        body.addView(button(action){
            if(manage)edit(null) else{manage=true;render()}
        },LinearLayout.LayoutParams(-1,dp(58)).apply{topMargin=dp(11)})
        if(manage)body.addView(button(tr("✓ Concluir","✓ Done",
            "✓ Terminé","✓ Fertig","✓ Terminado")){
            manage=false;render()
        },LinearLayout.LayoutParams(-1,dp(53)).apply{topMargin=dp(9)})
        body.addView(text(tr(
            "Os links ficam guardados neste telemóvel. Alguns sites exigem autenticação.",
            "Links are stored on this phone. Some sites require sign-in.",
            "Les liens restent sur cet appareil. Certains sites nécessitent une connexion.",
            "Die Links bleiben auf dem Telefon. Einige Seiten benötigen eine Anmeldung.",
            "Los enlaces se guardan en este teléfono. Algunos sitios requieren acceso."),
            12f,color=muted).apply{setPadding(dp(5),dp(17),0,0)})
    }

    private fun renderEntry(link:Link){
        val card=MaterialCardView(this).apply{
            radius=dp(18).toFloat()
            strokeWidth=dp(1)
            strokeColor=border
            setCardBackgroundColor(surface)
            isClickable=!manage
        }
        val row=LinearLayout(this).apply{
            orientation=LinearLayout.HORIZONTAL
            gravity=Gravity.CENTER_VERTICAL
            setPadding(dp(12),dp(13),dp(9),dp(13))
        }
        val frame=FrameLayout(this).apply{
            background=bg(if(dark)Color.rgb(34,77,79)else Color.rgb(222,243,240))
        }
        frame.addView(text("🌐",29f).apply{gravity=Gravity.CENTER},
            FrameLayout.LayoutParams(-1,-1))
        val icon=ImageView(this).apply{
            scaleType=ImageView.ScaleType.FIT_CENTER
            contentDescription="Favicon "+link.name
            visibility=View.GONE
            setPadding(dp(5),dp(5),dp(5),dp(5))
        }
        frame.addView(icon,FrameLayout.LayoutParams(-1,-1))
        row.addView(frame,LinearLayout.LayoutParams(dp(55),dp(55)))
        favicon(link.url,icon)
        val words=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(12),0,dp(4),0)
        }
        words.addView(text(link.name,15.5f,true))
        words.addView(text(Uri.parse(link.url).host.orEmpty()
            .removePrefix("www."),12f,color=muted))
        row.addView(words,LinearLayout.LayoutParams(0,-2,1f))
        if(manage){
            row.addView(button("✎"){edit(link)},
                LinearLayout.LayoutParams(dp(55),dp(48)))
            row.addView(button("✕"){remove(link)},
                LinearLayout.LayoutParams(dp(53),dp(48)))
        }else{
            row.addView(text("›",29f,color=accent))
            card.contentDescription=link.name+" · "+link.url
            card.setOnClickListener{open(link.url)}
        }
        card.addView(row)
        body.addView(card,LinearLayout.LayoutParams(-1,-2)
            .apply{bottomMargin=dp(11)})
    }

    private fun open(raw:String){
        val url=normalized(raw)?:return
        try{
            startActivity(Intent(Intent.ACTION_VIEW,Uri.parse(url))
                .addCategory(Intent.CATEGORY_BROWSABLE))
        }catch(_:Exception){
            Toast.makeText(this,tr("Não foi possível abrir o navegador.",
                "Could not open the browser.","Impossible d'ouvrir le navigateur.",
                "Browser konnte nicht geöffnet werden.","No se pudo abrir el navegador."),
                Toast.LENGTH_LONG).show()
        }
    }
    private fun edit(item:Link?){
        val form=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(19),dp(10),dp(19),dp(7))
        }
        val title=EditText(this).apply{
            setSingleLine(true)
            hint=tr("Nome do atalho","Shortcut name","Nom du lien","Linkname","Nombre")
            setText(item?.name.orEmpty())
        }
        val address=EditText(this).apply{
            setSingleLine(true)
            hint="https://..."
            inputType=android.text.InputType.TYPE_CLASS_TEXT or
                android.text.InputType.TYPE_TEXT_VARIATION_URI
            setText(item?.url.orEmpty())
        }
        form.addView(text(tr("Nome","Name","Nom","Name","Nombre"),13f,true,accent))
        form.addView(title)
        form.addView(text("URL",13f,true,accent))
        form.addView(address)
        val dialog=MaterialAlertDialogBuilder(this)
            .setTitle(if(item==null)
                tr("Adicionar atalho","Add shortcut","Ajouter un lien",
                    "Link hinzufügen","Añadir enlace")
                else tr("Editar atalho","Edit shortcut","Modifier le lien",
                    "Link bearbeiten","Editar enlace"))
            .setView(form)
            .setNegativeButton(tr("Cancelar","Cancel","Annuler",
                "Abbrechen","Cancelar"),null)
            .setPositiveButton(tr("Guardar","Save","Enregistrer",
                "Speichern","Guardar"),null).create()
        dialog.setOnShowListener{
            dialog.getButton(-1).setOnClickListener{
                val name=title.text.toString().trim()
                val url=normalized(address.text.toString())
                when{
                    name.isBlank()->title.error=tr("Indica um nome","Enter a name",
                        "Saisissez un nom","Name eingeben","Escribe un nombre")
                    name.length>85->title.error="Máximo: 85"
                    url==null->address.error=tr(
                        "Introduz um URL válido http:// ou https://",
                        "Enter a valid http:// or https:// URL",
                        "Saisissez un lien valide","Gültige Webadresse eingeben",
                        "Introduce un URL válido")
                    else->{
                        val list=read()
                        if(item==null)list.add(Link(UUID.randomUUID().toString(),name,url))
                        else{
                            val index=list.indexOfFirst{it.id==item.id}
                            if(index>=0)list[index]=item.copy(name=name,url=url)
                        }
                        save(list);dialog.dismiss();render()
                    }
                }
            }
        }
        dialog.show()
    }
    private fun remove(link:Link){
        MaterialAlertDialogBuilder(this)
            .setTitle(tr("Apagar atalho?","Delete shortcut?",
                "Supprimer le lien ?","Link löschen?","¿Eliminar enlace?"))
            .setMessage(link.name+"\n"+link.url+
                "\n\n"+tr("O site não será apagado.","The website will not be deleted.",
                    "Le site ne sera pas supprimé.","Die Webseite bleibt bestehen.",
                    "El sitio web no se eliminará."))
            .setNegativeButton(tr("Cancelar","Cancel","Annuler","Abbrechen","Cancelar"),null)
            .setPositiveButton(tr("Apagar","Delete","Supprimer","Löschen","Eliminar")){_,_->
                save(read().filter{it.id!=link.id});render()
            }.show()
    }

    /** Background retrieval: site-native PNG then Google fallback PNG.
     * Only the website hostname is sent in Google's favicon fallback query. */
    private fun favicon(raw:String,view:ImageView){
        val host=Uri.parse(raw).host?.lowercase()?:return
        val digest=MessageDigest.getInstance("SHA-256")
            .digest(host.toByteArray(Charsets.UTF_8))
            .joinToString(""){"%02x".format(it.toInt() and 255)}
        val local=File(cache,digest+".png")
        val cached=if(local.isFile)runCatching{
            BitmapFactory.decodeFile(local.path)
        }.getOrNull() else null
        if(cached!=null){
            view.setImageBitmap(cached);view.visibility=View.VISIBLE
            return
        }
        Thread({
            var found:Bitmap?=null
            val candidates=listOf(
                "https://"+host+"/apple-touch-icon.png",
                "https://"+host+"/favicon.png",
                "https://www.google.com/s2/favicons?domain="+
                    URLEncoder.encode(host,"UTF-8")+"&sz=64")
            for(address in candidates){
                val bitmap=runCatching{
                    val connection=URL(address).openConnection() as HttpURLConnection
                    connection.connectTimeout=2800
                    connection.readTimeout=2800
                    connection.instanceFollowRedirects=false
                    try{
                        if(connection.responseCode!=200)return@runCatching null
                        val output=ByteArrayOutputStream()
                        connection.inputStream.use{stream->
                            val buffer=ByteArray(4096)
                            while(output.size()<120_000){
                                val read=stream.read(buffer,0,
                                    minOf(buffer.size,120_000-output.size()))
                                if(read<=0)break
                                output.write(buffer,0,read)
                            }
                        }
                        val bytes=output.toByteArray()
                        BitmapFactory.decodeByteArray(bytes,0,bytes.size)
                    }finally{connection.disconnect()}
                }.getOrNull()
                if(bitmap!=null){found=bitmap;break}
            }
            val bmp=found
            if(bmp!=null){
                val scaled=Bitmap.createScaledBitmap(bmp,72,72,true)
                runCatching{local.outputStream().use{
                    scaled.compress(Bitmap.CompressFormat.PNG,95,it)
                }}
                runOnUiThread{
                    if(!isFinishing && !isDestroyed){
                        view.setImageBitmap(scaled)
                        view.visibility=View.VISIBLE
                    }
                }
            }
        },"SaudeShortcutsIcon").start()
    }
}
'''
(base/"ImportantShortcutsActivity.kt").write_text(activity,encoding="utf-8")

manifest=root/"app/src/main/AndroidManifest.xml"
change(manifest,
'''        <activity android:name=".SupportHelpActivity" android:exported="false" />''',
'''        <activity android:name=".SupportHelpActivity" android:exported="false" />
        <activity android:name=".ImportantShortcutsActivity" android:exported="false" />''',
"manifest")
main=base/"MainActivity.kt"
change(main,'''        "Despesas de Saúde"
    )
    private fun dashboardPrefs()''',
'''        "Despesas de Saúde","Atalhos Importantes"
    )
    private fun dashboardPrefs()''',"checklist")
change(main,
'''            DashboardModule("🏨", "IPO Lisboa", "Abrir aplicação IPO Lisboa") { openIpoLisboa() },
            DashboardModule("⚙", "Opções", "Perfis, backups e acessibilidade") { showDataTools() }''',
'''            DashboardModule("🏨", "IPO Lisboa", "Abrir aplicação IPO Lisboa") { openIpoLisboa() },
            DashboardModule("🔗", "Atalhos Importantes", "ADSE, CGA, IRS e outros links") {
                startActivity(Intent(this,ImportantShortcutsActivity::class.java))
            },
            DashboardModule("⚙", "Opções", "Perfis, backups e acessibilidade") { showDataTools() }''',"home module")
change(main,
'''        box.addView(infoCard("🎨", "Aspeto e idioma", "Tema, idioma e módulos do ecrã inicial") {
            showOptionsGroup("personalizacao")
        })''',
'''        box.addView(infoCard("🎨", "Aspeto e idioma", "Tema, idioma e módulos do ecrã inicial") {
            showOptionsGroup("personalizacao")
        })
        box.addView(infoCard("🔗", "Atalhos Importantes",
            "Adicionar, editar e apagar links web · ADSE, CGA, IRS e APATI") {
            startActivity(Intent(this,ImportantShortcutsActivity::class.java)
                .putExtra(ImportantShortcutsActivity.EXTRA_MANAGE,true))
        })''',"settings manager")
help=base/"SupportHelpActivity.kt"
change(help,'''        val emergencyAndReminders=panel()''',
'''        val shortcutGuide=panel()
        shortcutGuide.addView(text(tr(
            "🔗 Atalhos Importantes","🔗 Important Shortcuts",
            "🔗 Raccourcis importants","🔗 Wichtige Links",
            "🔗 Enlaces importantes"),18f))
        shortcutGuide.addView(text(tr(
            "Abre Atalhos Importantes no ecrã inicial. Um toque abre o site no navegador predefinido. Em Opções → Atalhos Importantes podes adicionar, editar ou apagar links. Já inclui ADSE Direta, CGA Direta, IRS e APATI Castanheira. Os favicons são carregados em segundo plano; como alternativa pode ser usado o serviço de ícones da Google. Os atalhos ficam guardados neste telemóvel.",
            "Open Important Shortcuts from Home. Tap a link to open your default browser. In Options → Important Shortcuts you can add, edit or delete links. ADSE, CGA, IRS and APATI are preloaded. Favicons load in the background, using Google's favicon service if needed. Links stay on this phone.",
            "Ouvrez Raccourcis importants depuis l'accueil. Touchez un lien pour ouvrir le navigateur. Dans Options vous pouvez ajouter, modifier ou supprimer les liens. ADSE, CGA, IRS et APATI sont inclus. Les icônes sont chargées en arrière-plan et gardées en cache.",
            "Wichtige Links vom Startbildschirm öffnen. Tippen öffnet den Standardbrowser. Unter Optionen lassen sich Links hinzufügen, ändern und löschen. ADSE, CGA, IRS und APATI sind enthalten. Favicons werden im Hintergrund geladen.",
            "Abre Enlaces importantes desde Inicio. Toca un enlace para abrir el navegador. En Opciones puedes añadir, editar y eliminar enlaces. ADSE, CGA, IRS y APATI están incluidos. Los iconos se descargan en segundo plano."
        ),14f,muted))
        addCard(parent,shortcutGuide)
        val emergencyAndReminders=panel()''',"help 5 languages")
gradle=root/"app/build.gradle.kts"
change(gradle,"versionCode = 87","versionCode = 88","version code")
change(gradle,'versionName = "1.9.77"','versionName = "1.9.78"',"version name")
print("v1.9.78: important shortcuts + favicon cache + settings + help")
