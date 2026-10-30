package com.mediagenda.app

import android.content.ComponentName
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.graphics.drawable.ColorDrawable
import android.graphics.drawable.BitmapDrawable
import android.graphics.drawable.LayerDrawable
import android.content.res.Configuration
import android.content.res.ColorStateList
import androidx.core.content.ContextCompat
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import com.google.android.material.button.MaterialButton
import android.net.Uri
import android.os.Bundle
import android.text.InputType
import android.text.TextWatcher
import android.text.Editable
import android.view.Gravity
import android.view.View
import android.widget.*
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import org.json.JSONArray
import org.json.JSONObject
import java.util.Locale

/** Safe app + website shortcuts, separate from the Home dashboard. */
class ImportantShortcutsV2Activity:AppCompatActivity() {
    companion object { const val EXTRA_MANAGE="manage_shortcuts" }
    private val manage:Boolean get()=intent.getBooleanExtra(EXTRA_MANAGE,false)
    private val prefs by lazy{getSharedPreferences("saudepratica_important_shortcuts_apps_web_v2",MODE_PRIVATE)}
    private lateinit var shortcuts:JSONArray
    private lateinit var cards:LinearLayout
    private val teal=Color.rgb(0,198,190)
    private val isDark:Boolean get()=when(
        getSharedPreferences("mediagenda_ui",MODE_PRIVATE).getString("theme_mode","system")){
        "dark"->true;"light"->false
        else->(resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK)==
            Configuration.UI_MODE_NIGHT_YES
    }
    private val ink:Int get()=if(isDark)Color.rgb(245,250,251) else Color.rgb(22,39,52)
    private val muted:Int get()=if(isDark)Color.rgb(196,219,226) else Color.rgb(78,96,112)
    private val surface:Int get()=if(isDark)Color.rgb(29,44,56) else Color.WHITE
    private val border:Int get()=if(isDark)Color.rgb(74,99,111) else Color.rgb(214,224,234)
    private fun dp(x:Int)=(x*resources.displayMetrics.density+.5f).toInt()
    private fun label(s:String,size:Float=16f,bold:Boolean=false,color:Int=ink)=TextView(this).apply{
        text=s;textSize=size;setTextColor(color)
        if(bold)setTypeface(null,android.graphics.Typeface.BOLD)
        setPadding(dp(5),dp(7),dp(5),dp(7))
    }
    private fun rounded()=GradientDrawable().apply{
        setColor(surface);cornerRadius=dp(18).toFloat()
        setStroke(dp(1),border)
    }
    private fun wallpaper():android.graphics.drawable.Drawable{
        if(!isDark)return ColorDrawable(Color.rgb(245,248,250))
        val image=ContextCompat.getDrawable(this,R.drawable.saude_background)
        if(image is BitmapDrawable)image.gravity=Gravity.FILL
        return if(image!=null)LayerDrawable(arrayOf(
            image,ColorDrawable(Color.argb(112,1,14,24))))
        else ColorDrawable(Color.rgb(5,24,33))
    }
    private fun button(s:String,action:()->Unit)=MaterialButton(this).apply{
        text=s;isAllCaps=false;textSize=14f;cornerRadius=dp(16)
        backgroundTintList=ColorStateList.valueOf(Color.TRANSPARENT)
        strokeColor=ColorStateList.valueOf(teal);strokeWidth=dp(1)
        setTextColor(if(isDark)Color.rgb(147,239,229) else Color.rgb(0,110,104))
        minHeight=dp(48);setOnClickListener{action()}
    }
    override fun onCreate(savedInstanceState:Bundle?){
        super.onCreate(savedInstanceState)
        // Copy existing saved websites once; do not overwrite old preferences.
        val stored=prefs.getString("items",null)
        shortcuts=try {
            if(stored!=null)JSONArray(stored)
            else defaultItems().apply {
                val legacyPrefs=getSharedPreferences("saudepratica_important_shortcuts_v1",MODE_PRIVATE)
                val legacy=legacyPrefs.getString("links",null)
                if(!legacy.isNullOrBlank()) {
                    val oldItems=JSONArray(legacy)
                    val seen=mutableSetOf<String>()
                    for(i in 0 until oldItems.length()){
                        val item=oldItems.optJSONObject(i)?:continue
                        val name=item.optString("name").trim().take(80)
                        val url=item.optString("url").trim()
                        val parsed=runCatching{Uri.parse(url)}.getOrNull()
                        if(name.isBlank()||parsed==null||
                            parsed.scheme !in listOf("https","http")||
                            parsed.host.isNullOrBlank()||!seen.add(url))continue
                        put(JSONObject().put("kind","web")
                            .put("title",name).put("url",url))
                    }
                }
            }
        } catch(e:Exception){defaultItems()}
        if(stored==null)prefs.edit().putString("items",shortcuts.toString()).commit()
        val root=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL;background=wallpaper()
            setPadding(dp(16),dp(12),dp(16),dp(8))
        }
        val top=LinearLayout(this).apply{
            orientation=LinearLayout.HORIZONTAL;gravity=Gravity.CENTER_VERTICAL
        }
        top.addView(label("‹",34f,true,teal).apply{
            gravity=Gravity.CENTER;contentDescription="Voltar"
            isFocusable=true;setOnClickListener{finish()}
        },LinearLayout.LayoutParams(dp(42),dp(62)))
        val titles=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
        titles.addView(label("SaúdePrática",16f,true,teal))
        titles.addView(label(if(manage)"Opções · Atalhos" else "Atalhos Importantes",
            13f,false,muted))
        top.addView(titles,LinearLayout.LayoutParams(0,-2,1f))
        root.addView(top)
        val scroll=ScrollView(this).apply{clipToPadding=false}
        val body=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL;setPadding(0,dp(14),0,dp(22))
        }
        body.addView(label("🔗  Atalhos Importantes",25f,true))
        body.addView(label(if(manage)
            "Adiciona, edita e organiza aplicações ou websites."
            else "Toca num atalho para abrir a aplicação ou o website.",
            13f,false,muted))
        if(manage){
            body.addView(button("+ Atalho de aplicação"){pickApp()})
            body.addView(button("+ Atalho de website"){websiteDialog()})
        }
        cards=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
        body.addView(cards,LinearLayout.LayoutParams(-1,-2).apply{topMargin=dp(12)})
        scroll.addView(body)
        root.addView(scroll,LinearLayout.LayoutParams(-1,0,1f))
        WindowCompat.setDecorFitsSystemWindows(window,false)
        window.statusBarColor=Color.TRANSPARENT
        window.navigationBarColor=Color.TRANSPARENT
        WindowInsetsControllerCompat(window,window.decorView).apply{
            isAppearanceLightStatusBars=!isDark
            isAppearanceLightNavigationBars=!isDark
        }
        ViewCompat.setOnApplyWindowInsetsListener(root){view,insets->
            val safe=insets.getInsets(WindowInsetsCompat.Type.statusBars() or
                WindowInsetsCompat.Type.navigationBars() or
                WindowInsetsCompat.Type.displayCutout())
            view.setPadding(dp(16)+safe.left,dp(12)+safe.top,
                dp(16)+safe.right,dp(8)+safe.bottom)
            insets
        }
        setContentView(root)
        ViewCompat.requestApplyInsets(root)
        render()
    }
    private fun defaultItems()=JSONArray()
        .put(JSONObject().put("kind","app").put("title","SNS 24")
            .put("package","pt.minsaude.spms.ces"))
        .put(JSONObject().put("kind","app").put("title","IPO Lisboa")
            .put("package","com.seamlink.gatewaybox.ipolisboa"))
    private fun persist(){
        if(!prefs.edit().putString("items",shortcuts.toString()).commit())
            Toast.makeText(this,"Falha ao gravar os atalhos",Toast.LENGTH_LONG).show()
        render()
    }
    private fun list()=(0 until shortcuts.length()).mapNotNull{shortcuts.optJSONObject(it)}
    private fun render(){
        cards.removeAllViews()
        list().forEachIndexed{index,item->
            val card=LinearLayout(this).apply{
                orientation=LinearLayout.HORIZONTAL
                gravity=Gravity.CENTER_VERTICAL
                background=rounded()
                setPadding(dp(12),dp(10),dp(12),dp(10))
                isClickable=true;isFocusable=true
                contentDescription="Abrir "+item.optString("title","Atalho")
                setOnClickListener{launch(item)}
            }
            val icon=ImageView(this).apply{
                val pkg=item.optString("package")
                val drawable=if(item.optString("kind")=="app")runCatching{
                    packageManager.getApplicationIcon(pkg)
                }.getOrNull() else null
                if(drawable!=null)setImageDrawable(drawable)
                else setImageResource(android.R.drawable.ic_menu_view)
                contentDescription=null
            }
            card.addView(icon,LinearLayout.LayoutParams(dp(44),dp(44)))
            val title=item.optString("title","Atalho")
            val detail=if(item.optString("kind")=="app")"Aplicação" else "Website"
            val entry=LinearLayout(this).apply{
                orientation=LinearLayout.VERTICAL
                addView(label(title,17f,true))
                addView(label(detail,13f,false,muted))
            }
            card.addView(entry,LinearLayout.LayoutParams(0,-2,1f).apply{leftMargin=dp(12)})
            if(manage){
                val menu=button("⋮"){actions(index)}
                menu.contentDescription="Gerir "+title
                card.addView(menu,LinearLayout.LayoutParams(dp(58),dp(50)))
            }else{
                card.addView(label("›",24f,true,teal))
            }
            cards.addView(card,LinearLayout.LayoutParams(-1,-2).apply{
                bottomMargin=dp(9)
            })
        }
    }
    private fun launch(item:JSONObject){
        if(item.optString("kind")=="app"){
            val pkg=item.optString("package")
            if(pkg.isBlank())return
            val klass=item.optString("class")
            val exact=if(klass.isNotBlank())Intent(Intent.ACTION_MAIN).apply{
                addCategory(Intent.CATEGORY_LAUNCHER)
                component=ComponentName(pkg,klass)
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }else packageManager.getLaunchIntentForPackage(pkg)
            val opened=runCatching{
                if(exact==null)false else{startActivity(exact);true}
            }.getOrDefault(false)
            if(!opened)AlertDialog.Builder(this).setTitle("Aplicação não encontrada")
                .setMessage("Esta aplicação pode ter sido desinstalada. Queres abrir a página da Play Store?")
                .setNegativeButton("Cancelar",null)
                .setPositiveButton("Play Store"){_,_->
                    val uri=Uri.parse("https://play.google.com/store/apps/details?id="+Uri.encode(pkg))
                    runCatching{startActivity(Intent(Intent.ACTION_VIEW,uri))}
                }.show()
        }else{
            val uri=runCatching{Uri.parse(item.optString("url"))}.getOrNull()
            if(uri!=null&&(uri.scheme=="https"||uri.scheme=="http")&&!uri.host.isNullOrBlank()){
                runCatching{startActivity(Intent(Intent.ACTION_VIEW,uri))}
                    .onFailure{Toast.makeText(this,"Não foi possível abrir o website",Toast.LENGTH_LONG).show()}
            }
        }
    }
    private fun actions(index:Int){
        val choices=arrayOf("Abrir","Mover para cima","Mover para baixo","Editar","Eliminar")
        AlertDialog.Builder(this).setTitle(list()[index].optString("title"))
            .setItems(choices){_,action->
                when(action){
                    0->launch(list()[index])
                    1,2->{
                        val target=if(action==1)index-1 else index+1
                        val all=list().toMutableList()
                        if(target in all.indices){
                            java.util.Collections.swap(all,index,target)
                            shortcuts=JSONArray().apply{all.forEach{put(it)}}
                            persist()
                        }
                    }
                    3->if(list()[index].optString("kind")=="web")
                        websiteDialog(index) else pickApp(index)
                    4->AlertDialog.Builder(this).setTitle("Eliminar atalho?")
                        .setNegativeButton("Cancelar",null)
                        .setPositiveButton("Eliminar"){_,_->
                            shortcuts=JSONArray().apply{
                                list().forEachIndexed{i,item->if(i!=index)put(item)}
                            }
                            persist()
                        }.show()
                }
            }.show()
    }
    private fun websiteDialog(edit:Int=-1){
        val original=if(edit>=0)list()[edit] else JSONObject()
        val layout=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL;setPadding(dp(20),dp(8),dp(20),dp(8))
        }
        val title=EditText(this).apply{
            hint="Nome";setText(original.optString("title"))
            inputType=InputType.TYPE_CLASS_TEXT
        }
        val url=EditText(this).apply{
            hint="https://exemplo.pt";setText(original.optString("url"))
            inputType=InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_URI
        }
        layout.addView(title);layout.addView(url)
        val dialog=AlertDialog.Builder(this).setTitle("Atalho de website")
            .setView(layout).setNegativeButton("Cancelar",null)
            .setPositiveButton("Guardar",null).create()
        dialog.setOnShowListener{
            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener{
                val uri=runCatching{Uri.parse(url.text.toString().trim())}.getOrNull()
                if(uri==null||uri.scheme !in listOf("https","http")||uri.host.isNullOrBlank()){
                    url.error="Utiliza um endereço http:// ou https:// válido"
                    return@setOnClickListener
                }
                if(title.text.toString().isBlank()){title.error="Indica um nome";return@setOnClickListener}
                val item=JSONObject().put("kind","web")
                    .put("title",title.text.toString().trim().take(80))
                    .put("url",uri.toString())
                if(edit>=0)shortcuts.put(edit,item)else shortcuts.put(item)
                persist();dialog.dismiss()
            }
        }
        dialog.show()
    }
    private fun pickApp(edit:Int=-1){
        val launch=Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER)
        @Suppress("DEPRECATION")
        val candidates=packageManager.queryIntentActivities(launch,0)
            .filter{it.activityInfo!=null}
            .distinctBy{it.activityInfo.packageName+"/"+it.activityInfo.name}
            .sortedBy{it.loadLabel(packageManager).toString().lowercase(Locale.getDefault())}
        if(candidates.isEmpty()){
            AlertDialog.Builder(this).setMessage("O Android não disponibilizou aplicações para escolher.")
                .setPositiveButton("OK",null).show()
            return
        }
        val view=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL
            setPadding(dp(15),dp(8),dp(15),dp(8))}
        val filter=EditText(this).apply{hint="Pesquisar aplicação";isSingleLine=true}
        view.addView(filter)
        val options=ListView(this)
        view.addView(options,LinearLayout.LayoutParams(-1,dp(350)))
        val dialog=AlertDialog.Builder(this).setTitle("Escolher aplicação instalada")
            .setView(view).setNegativeButton("Cancelar",null).create()
        fun populate(query:String){
            val hits=candidates.filter{
                it.loadLabel(packageManager).toString().contains(query,ignoreCase=true)
            }
            val names=hits.map{it.loadLabel(packageManager).toString()}.toTypedArray()
            options.adapter=ArrayAdapter(this,android.R.layout.simple_list_item_1,names)
            options.setOnItemClickListener{_,_,i,_->
                val selected=hits[i]
                val item=JSONObject().put("kind","app")
                    .put("title",selected.loadLabel(packageManager).toString())
                    .put("package",selected.activityInfo.packageName)
                    .put("class",selected.activityInfo.name)
                if(edit>=0)shortcuts.put(edit,item)else shortcuts.put(item)
                persist();dialog.dismiss()
            }
        }
        filter.addTextChangedListener(object:TextWatcher{
            override fun beforeTextChanged(s:CharSequence?,start:Int,count:Int,after:Int){}
            override fun onTextChanged(s:CharSequence?,start:Int,before:Int,count:Int){
                populate(s?.toString().orEmpty())
            }
            override fun afterTextChanged(s:Editable?){}
        })
        populate("")
        dialog.show()
    }
}
