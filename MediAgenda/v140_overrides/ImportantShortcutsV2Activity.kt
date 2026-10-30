package com.mediagenda.app

import android.content.ComponentName
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
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
    private val prefs by lazy{getSharedPreferences("saudepratica_important_shortcuts_apps_web_v2",MODE_PRIVATE)}
    private lateinit var shortcuts:JSONArray
    private lateinit var cards:LinearLayout
    private val accent=Color.rgb(6,113,104)
    private fun dp(x:Int)=(x*resources.displayMetrics.density+.5f).toInt()
    private fun label(s:String)=TextView(this).apply{
        text=s;textSize=16f;setTextColor(Color.rgb(21,48,54))
        setPadding(dp(10),dp(10),dp(10),dp(10))
    }
    private fun button(s:String,action:()->Unit)=Button(this).apply{
        text=s;isAllCaps=false
        backgroundTintList=android.content.res.ColorStateList.valueOf(accent)
        setTextColor(Color.WHITE);setOnClickListener{action()}
    }
    override fun onCreate(savedInstanceState:Bundle?){
        super.onCreate(savedInstanceState)
        window.statusBarColor=accent;window.navigationBarColor=accent
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
            orientation=LinearLayout.VERTICAL
            setPadding(dp(13),dp(16),dp(13),dp(16))
            val bg=androidx.core.content.ContextCompat.getDrawable(
                this@ImportantShortcutsV2Activity,R.drawable.saude_background)?.mutate()
            background=if(bg!=null)android.graphics.drawable.LayerDrawable(arrayOf(
                bg,android.graphics.drawable.ColorDrawable(Color.argb(225,242,251,250))))
                else android.graphics.drawable.ColorDrawable(Color.rgb(237,246,246))
        }
        root.addView(button("‹  Voltar"){finish()})
        root.addView(label("🔗 Atalhos Importantes").apply{textSize=24f})
        root.addView(label("Abre aplicações instaladas ou páginas web. Os atalhos podem ser organizados livremente.").apply{textSize=13f})
        root.addView(button("+ Atalho de aplicação"){pickApp()})
        root.addView(button("+ Atalho de website"){websiteDialog()})
        cards=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
        root.addView(cards)
        setContentView(ScrollView(this).apply{addView(root)})
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
                background=GradientDrawable().apply{
                    setColor(Color.rgb(253,255,255))
                    cornerRadius=dp(16).toFloat()
                    setStroke(dp(1),Color.rgb(208,231,228))
                }
                setPadding(dp(9),dp(7),dp(9),dp(7))
            }
            val icon=ImageView(this).apply{
                val pkg=item.optString("package")
                val drawable=if(item.optString("kind")=="app")runCatching{
                    packageManager.getApplicationIcon(pkg)
                }.getOrNull() else null
                if(drawable!=null)setImageDrawable(drawable)else setImageResource(
                    android.R.drawable.ic_menu_view)
            }
            card.addView(icon,LinearLayout.LayoutParams(dp(37),dp(37)))
            val title=item.optString("title","Atalho")
            val text=label(title+"\n"+if(item.optString("kind")=="app")"Aplicação" else "Website")
                .apply{setOnClickListener{launch(item)}}
            card.addView(text,LinearLayout.LayoutParams(0,-2,1f))
            val menu=button("⋮"){actions(index)}
            card.addView(menu,LinearLayout.LayoutParams(dp(56),dp(49)))
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
