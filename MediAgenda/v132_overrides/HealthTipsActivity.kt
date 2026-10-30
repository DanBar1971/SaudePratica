package com.mediagenda.app

import android.os.Bundle
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.view.Gravity
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/** Archived informational cards shown on THIS device; no patient data or cloud sync. */
class HealthTipsActivity : AppCompatActivity() {
    private lateinit var body: LinearLayout
    private var catalog:List<HealthTipsManager.Tip> = emptyList()
    private val dateFormat=SimpleDateFormat("dd/MM/yyyy", Locale("pt","PT"))

    private fun dp(v:Int)=(v*resources.displayMetrics.density+0.5f).toInt()
    private fun shape(color:Int,radius:Int=17)=GradientDrawable().apply {
        setColor(color);cornerRadius=dp(radius).toFloat()
    }
    private fun title(text:String,size:Float=19f,bold:Boolean=false)=TextView(this).apply {
        this.text=text; textSize=size
        setTextColor(Color.rgb(21,45,59))
        setPadding(dp(12),dp(10),dp(12),dp(9))
        if(bold)setTypeface(null,Typeface.BOLD)
    }
    private fun action(text:String,onClick:()->Unit)=Button(this).apply{
        this.text=text;isAllCaps=false;textSize=13f
        setTextColor(Color.WHITE)
        background=shape(Color.rgb(17,125,115),13)
        setOnClickListener{onClick()}
    }
    private fun card(text:String,detail:String,onClick:()->Unit) {
        val row=LinearLayout(this).apply {
            orientation=LinearLayout.HORIZONTAL
            gravity=Gravity.CENTER_VERTICAL
            background=shape(Color.argb(241,255,255,255))
            setPadding(dp(11),dp(9),dp(11),dp(9))
            elevation=dp(2).toFloat()
            setOnClickListener{onClick()}
        }
        val columns=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
        columns.addView(title(text,16f,true))
        columns.addView(title(detail,12f))
        row.addView(columns,LinearLayout.LayoutParams(0,-2,1f))
        row.addView(title("›",27f,true))
        body.addView(row,LinearLayout.LayoutParams(-1,-2).apply {
            bottomMargin=dp(10)
        })
    }
    override fun onCreate(savedInstanceState:Bundle?) {
        super.onCreate(savedInstanceState)
        supportActionBar?.hide()
        val outer=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setBackgroundResource(R.drawable.saude_background)
        }
        val header=LinearLayout(this).apply{
            orientation=LinearLayout.HORIZONTAL
            gravity=Gravity.CENTER_VERTICAL
            setPadding(dp(9),dp(17),dp(9),dp(8))
            setBackgroundColor(Color.argb(240,241,249,248))
        }
        header.addView(action("‹ Voltar"){finish()},LinearLayout.LayoutParams(dp(92),dp(47)))
        header.addView(title("💡 Dicas e Informações",19f,true),
            LinearLayout.LayoutParams(0,-2,1f))
        outer.addView(header)
        val scroll=ScrollView(this).apply{isFillViewport=true}
        body=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(14),dp(9),dp(14),dp(26))
        }
        scroll.addView(body)
        outer.addView(scroll,LinearLayout.LayoutParams(-1,0,1f))
        setContentView(outer)
        render()
        refreshCatalog()
    }
    private fun refreshCatalog(){
        HealthTipsManager.refreshAndBrowse(this){cards->
            catalog=cards.filter{it.enabled}
            render()
        }
    }
    override fun onResume(){super.onResume();if(::body.isInitialized)render()}
    private fun render() {
        body.removeAllViews()
        body.addView(title("As informações que viste ficam guardadas neste telemóvel.",
            14f))
        val settings=LinearLayout(this).apply{
            orientation=LinearLayout.HORIZONTAL
            setPadding(0,0,0,dp(10))
        }
        val values=intArrayOf(0,1,3,7)
        val options=arrayOf("Desativadas","Todos os dias","De 3 em 3 dias","Semanalmente")
        val current=values.indexOf(HealthTipsManager.frequency(this)).coerceAtLeast(0)
        settings.addView(action("Frequência: "+options[current]){
            SafeMaterialAlertDialogBuilder(this)
                .setTitle("Apresentação automática")
                .setSingleChoiceItems(options,current){dialog,index->
                    HealthTipsManager.setFrequency(this,values[index])
                    dialog.dismiss();render()
                }
                .setNegativeButton("Cancelar",null).show()
        },LinearLayout.LayoutParams(0,dp(51),1f).apply{rightMargin=dp(7)})
        settings.addView(action("Atualizar"){refreshCatalog()},
            LinearLayout.LayoutParams(0,dp(51),0.55f))
        body.addView(settings)
        body.addView(title("Histórico de informações",20f,true))
        val history=HealthTipsManager.history(this)
        if(history.isEmpty())body.addView(title(
            "Ainda não foi apresentada nenhuma informação. As dicas lidas aparecerão aqui.",
            14f))
        else history.forEach{(tip,time)->
            card(tip.title,"Visto em "+dateFormat.format(Date(time))) {
                HealthTipsManager.openManual(this,tip)
            }
        }
        val viewed=history.map{it.first.id}.toSet()
        val available=catalog.filter{it.id !in viewed}
        if(available.isNotEmpty()){
            body.addView(title("Outras dicas disponíveis",20f,true))
            available.forEach{tip-> card(tip.title,"Toque para consultar"){
                HealthTipsManager.openManual(this,tip)
            }}
        }
    }
}
