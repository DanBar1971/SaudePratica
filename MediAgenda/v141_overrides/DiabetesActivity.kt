package com.mediagenda.app

import android.app.DatePickerDialog
import android.app.TimePickerDialog
import android.content.Intent
import android.graphics.*
import android.graphics.drawable.GradientDrawable
import android.graphics.drawable.ColorDrawable
import android.graphics.drawable.BitmapDrawable
import android.graphics.drawable.LayerDrawable
import android.content.res.Configuration
import android.content.res.ColorStateList
import android.view.Gravity
import android.widget.LinearLayout
import androidx.core.content.ContextCompat
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import com.google.android.material.button.MaterialButton
import com.mediagenda.app.data.ProfileStore
import android.os.Bundle
import android.text.InputType
import android.view.View
import android.widget.*
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.security.MessageDigest
import java.text.DateFormat
import java.util.*

/** Offline diabetes diary. Not a glucose sensor, alarm or insulin dose calculator. */
class DiabetesActivity : AppCompatActivity() {
    companion object { const val EXTRA_PROFILE_ID="profile_id" }
    private lateinit var profileId:String
    private lateinit var readings:JSONArray
    private lateinit var content:LinearLayout
    private var storageFailed=false
    // Match the native Activity and Health module; follow the saved app theme.
    private val teal=Color.rgb(0,198,190)
    private val isDark:Boolean get()=when(
        getSharedPreferences("mediagenda_ui",MODE_PRIVATE).getString("theme_mode","system")){
        "dark"->true
        "light"->false
        else->(resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK)==
            Configuration.UI_MODE_NIGHT_YES
    }
    private val ink:Int get()=if(isDark)Color.rgb(245,250,251) else Color.rgb(22,39,52)
    private val muted:Int get()=if(isDark)Color.rgb(196,219,226) else Color.rgb(78,96,112)
    private val surface:Int get()=if(isDark)Color.rgb(29,44,56) else Color.WHITE
    private val border:Int get()=if(isDark)Color.rgb(74,99,111) else Color.rgb(214,224,234)
    private fun dp(x:Int)=(x*resources.displayMetrics.density+.5f).toInt()
    private fun label(s:String,size:Float=15f,bold:Boolean=false,color:Int=ink)=TextView(this).apply {
        text=s; textSize=size; setTextColor(color)
        if(bold)setTypeface(null,Typeface.BOLD)
        setPadding(dp(5),dp(7),dp(5),dp(7))
    }
    private fun rounded()=GradientDrawable().apply {
        setColor(surface);cornerRadius=dp(18).toFloat();setStroke(dp(1),border)
    }
    private fun wallpaper():android.graphics.drawable.Drawable{
        if(!isDark)return ColorDrawable(Color.rgb(245,248,250))
        val image=ContextCompat.getDrawable(this,R.drawable.saude_background)
        if(image is BitmapDrawable)image.gravity=Gravity.FILL
        return if(image!=null)LayerDrawable(arrayOf(
            image,ColorDrawable(Color.argb(112,1,14,24))))
        else ColorDrawable(Color.rgb(5,24,33))
    }
    private fun button(s:String,action:()->Unit)=MaterialButton(this).apply {
        text=s;isAllCaps=false;textSize=14f;cornerRadius=dp(16)
        backgroundTintList=ColorStateList.valueOf(Color.TRANSPARENT)
        strokeColor=ColorStateList.valueOf(teal);strokeWidth=dp(1)
        setTextColor(if(isDark)Color.rgb(147,239,229) else Color.rgb(0,110,104))
        minHeight=dp(48)
        setOnClickListener{action()}
    }
    private fun panel()=LinearLayout(this).apply {
        orientation=LinearLayout.VERTICAL;background=rounded()
        setPadding(dp(16),dp(12),dp(16),dp(14))
    }
    private fun add(view:View)=content.addView(view,LinearLayout.LayoutParams(-1,-2).apply{
        bottomMargin=dp(12)
    })
    private fun file():File{
        val key=MessageDigest.getInstance("SHA-256").digest(profileId.toByteArray())
            .joinToString(""){"%02x".format(it)}
        return File(File(filesDir,"diabetes_v1").apply{mkdirs()},key+".json")
    }
    private fun date(t:Long)=DateFormat.getDateTimeInstance(
        DateFormat.SHORT,DateFormat.SHORT,Locale("pt","PT")).format(Date(t))
    private fun entries():List<JSONObject> = (0 until readings.length())
        .mapNotNull{readings.optJSONObject(it)}.sortedByDescending{it.optLong("time")}
    override fun onCreate(savedInstanceState:Bundle?){
        super.onCreate(savedInstanceState)
        profileId=intent.getStringExtra(EXTRA_PROFILE_ID).orEmpty().ifBlank{"legacy"}
        readings=try{if(file().exists())JSONArray(file().readText())else JSONArray()}
            catch(e:Exception){storageFailed=true;JSONArray()}
        // Same full-screen wallpaper, header, insets and cards as ActivityHealthConnect.
        val person=ProfileStore(this).all().firstOrNull{it.id==profileId}
        val root=LinearLayout(this).apply {
            orientation=LinearLayout.VERTICAL
            background=wallpaper()
            setPadding(dp(16),dp(12),dp(16),dp(8))
        }
        val top=LinearLayout(this).apply {
            orientation=LinearLayout.HORIZONTAL;gravity=Gravity.CENTER_VERTICAL
        }
        top.addView(label("‹",34f,true,teal).apply{
            gravity=Gravity.CENTER;contentDescription="Voltar"
            isFocusable=true;setOnClickListener{finish()}
        },LinearLayout.LayoutParams(dp(42),dp(62)))
        val heading=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
        heading.addView(label("SaúdePrática",16f,true,teal))
        heading.addView(label("Diabetes",13f,false,muted))
        top.addView(heading,LinearLayout.LayoutParams(0,-2,1f))
        if(person!=null)top.addView(label(person.name.take(14),12f,true,teal).apply{
            setPadding(dp(10),dp(8),dp(10),dp(8));background=rounded()
        })
        root.addView(top)
        content=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(0,dp(12),0,dp(22))
        }
        val scroll=ScrollView(this).apply{clipToPadding=false;addView(content)}
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
        if(storageFailed)AlertDialog.Builder(this).setTitle("Erro de leitura")
            .setMessage("O ficheiro do diário não foi lido. Não serão gravados dados por cima até o problema ser corrigido.")
            .setPositiveButton("OK",null).show()
        render()
    }
    private fun save(){
        if(storageFailed)throw IllegalStateException("Armazenamento protegido contra sobrescrita")
        val dst=file();val tmp=File(dst.parentFile,dst.name+".tmp")
        tmp.writeText(readings.toString())
        // Files are small. Keep previous backup until successful rename.
        val bak=File(dst.parentFile,dst.name+".bak")
        if(dst.exists()&&!dst.copyTo(bak,overwrite=true).exists())
            throw IllegalStateException("Backup não criado")
        if(dst.exists()&&!dst.delete())throw IllegalStateException("Não foi possível substituir o ficheiro")
        if(!tmp.renameTo(dst)){
            if(bak.exists())bak.copyTo(dst,overwrite=true)
            throw IllegalStateException("Falha ao concluir gravação")
        }
    }
    private fun persist():Boolean{
        return try{save();render();true}catch(e:Exception){
            AlertDialog.Builder(this).setTitle("Erro de gravação")
                .setMessage(e.localizedMessage).setPositiveButton("OK",null).show()
            false
        }
    }
    private fun render(){
        content.removeAllViews()
        content.addView(label("🩸  Diabetes",25f,true))
        content.addView(label("Diário pessoal de glicemia e HbA1c",13f,false,muted),
            LinearLayout.LayoutParams(-1,-2).apply{bottomMargin=dp(16)})
        val all=entries()
        val glucose=all.filter{it.optString("type")=="glucose"}
        val hero=panel()
        val latest=glucose.firstOrNull()
        hero.addView(label(if(latest==null)"Ainda não existem medições"
          else "Última: "+latest.optString("value")+" "+latest.optString("unit")+
            " · "+date(latest.optLong("time")),19f,true))
        hero.addView(label("Não mede glicose através da câmara nem substitui um sensor ou medidor clínico.",12f))
        hero.addView(button("+ Registar glicemia"){addReading(false)})
        hero.addView(button("+ Registar HbA1c"){addReading(true)})
        add(hero)
        val last30=glucose.filter{it.optLong("time")>=
            System.currentTimeMillis()-30L*24*60*60*1000}
        val values=last30.sortedBy{it.optLong("time")}.map{
            val v=it.optDouble("value")
            if(it.optString("unit")=="mmol/L")v*18.0182 else v
        }.filter{it.isFinite()}
        val chart=panel()
        chart.addView(label("Evolução · 30 dias",18f,true))
        if(values.isNotEmpty()){
            chart.addView(label(values.size.toString()+" registos · média "+
                String.format(Locale.US,"%.0f mg/dL",values.average()),14f))
            chart.addView(GlucoseChart(values),LinearLayout.LayoutParams(-1,dp(140)))
        }else chart.addView(label("Sem dados para apresentar no gráfico.",13f))
        chart.addView(label("As médias não são HbA1c ou GMI. Os limites individuais devem ser definidos pelo médico.",12f))
        add(chart)
        val history=panel()
        history.addView(label("Histórico",18f,true))
        if(all.isEmpty())history.addView(label("Nenhum registo guardado."))
        all.take(150).forEach {r->
            val title=(if(r.optString("type")=="hba1c")"🧪 HbA1c" else "🩸 Glicemia")
            val line=label(title+" · "+r.optString("value")+" "+r.optString("unit")+
                "\n"+date(r.optLong("time"))+" · "+r.optString("context")+
                "\n"+r.optString("note"),14f)
            line.setOnLongClickListener{
                AlertDialog.Builder(this).setTitle("Eliminar registo?")
                    .setNegativeButton("Cancelar",null)
                    .setPositiveButton("Eliminar"){_,_->
                        val next=JSONArray()
                        for(i in 0 until readings.length()){
                            val item=readings.optJSONObject(i)
                            if(item!=null&&item.optString("id")!=r.optString("id"))next.put(item)
                        }
                        readings=next;persist()
                    }.show()
                true
            }
            history.addView(line)
        }
        add(history)
        add(panel().apply{
            addView(button("Partilhar histórico CSV"){share()})
            addView(label("Premir um registo continuamente para eliminar. Nesta fase os dados são locais; a sincronização e o PDF serão acrescentados depois dos testes.",12f))
        })
    }
    private fun addReading(hba:Boolean){
        val outer=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL
            setPadding(dp(18),dp(8),dp(18),dp(8))}
        val input=EditText(this).apply{
            hint=if(hba)"Resultado HbA1c" else "Valor de glicemia"
            inputType=InputType.TYPE_CLASS_NUMBER or InputType.TYPE_NUMBER_FLAG_DECIMAL
        }
        outer.addView(input)
        val units=if(hba)listOf("%","mmol/mol") else listOf("mg/dL","mmol/L")
        val unit=Spinner(this).apply{adapter=ArrayAdapter(this@DiabetesActivity,
            android.R.layout.simple_spinner_dropdown_item,units)}
        outer.addView(unit)
        val contexts=if(hba)listOf("Análise laboratorial")
            else listOf("Jejum","Antes da refeição","Depois da refeição","Ao deitar","Outro")
        val context=Spinner(this).apply{adapter=ArrayAdapter(this@DiabetesActivity,
            android.R.layout.simple_spinner_dropdown_item,contexts)}
        outer.addView(context)
        val notes=EditText(this).apply{hint="Notas (opcional)"}
        outer.addView(notes)
        var whenMs=System.currentTimeMillis()
        val timestamp=button("Data: "+date(whenMs)){}
        timestamp.setOnClickListener {
            val cal=Calendar.getInstance().apply{timeInMillis=whenMs}
            DatePickerDialog(this,{_,y,m,d->
                cal.set(y,m,d)
                TimePickerDialog(this,{_,hh,mm->
                    cal.set(Calendar.HOUR_OF_DAY,hh);cal.set(Calendar.MINUTE,mm)
                    whenMs=cal.timeInMillis;timestamp.text="Data: "+date(whenMs)
                },cal.get(Calendar.HOUR_OF_DAY),cal.get(Calendar.MINUTE),true).show()
            },cal.get(Calendar.YEAR),cal.get(Calendar.MONTH),
                cal.get(Calendar.DAY_OF_MONTH)).show()
        }
        outer.addView(timestamp)
        val dialog=AlertDialog.Builder(this)
            .setTitle(if(hba)"HbA1c laboratorial" else "Registar glicemia")
            .setView(ScrollView(this).apply{addView(outer)})
            .setNegativeButton("Cancelar",null).setPositiveButton("Guardar",null).create()
        dialog.setOnShowListener{
            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener{
                val v=input.text.toString().trim().replace(',','.').toDoubleOrNull()
                val u=unit.selectedItem.toString()
                val ok=v!=null&&v.isFinite()&&
                    (if(hba){if(u=="%")v in 2.0..25.0 else v in 0.0..260.0}
                     else {if(u=="mg/dL")v in 10.0..1200.0 else v in 0.5..67.0})
                if(!ok){input.error="Valor inválido para a unidade selecionada";return@setOnClickListener}
                if(whenMs>System.currentTimeMillis()+60000){
                    timestamp.text="Escolhe uma data que não seja futura";return@setOnClickListener
                }
                readings.put(JSONObject()
                    .put("id",UUID.randomUUID().toString())
                    .put("type",if(hba)"hba1c" else "glucose")
                    .put("value",v).put("unit",u)
                    .put("time",whenMs).put("source","manual")
                    .put("context",context.selectedItem.toString())
                    .put("note",notes.text.toString().take(500)))
                if(persist())dialog.dismiss()
            }
        }
        dialog.show()
    }
    private fun share(){
        fun quote(s:String)="\""+s.replace("\"","\"\"").replace("\n"," ")+"\""
        val csv="tipo;data;valor;unidade;contexto;origem;notas\n"+
            entries().joinToString("\n"){r->listOf("type","time","value","unit","context",
                "source","note").map{
                    quote(if(it=="time")date(r.optLong(it)) else r.optString(it))
                }.joinToString(";")}
        startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).apply{
            type="text/plain"
            putExtra(Intent.EXTRA_SUBJECT,"SaúdePrática — Diabetes CSV")
            putExtra(Intent.EXTRA_TEXT,csv)
        },"Partilhar histórico"))
    }
    private inner class GlucoseChart(val points:List<Double>):View(this@DiabetesActivity){
        private val pen=Paint(Paint.ANTI_ALIAS_FLAG)
        override fun onDraw(c:Canvas){
            super.onDraw(c)
            val low=points.minOrNull()!!.toFloat()
            val span=(points.maxOrNull()!!.toFloat()-low).coerceAtLeast(1f)
            pen.color=border;pen.strokeWidth=dp(1).toFloat()
            for(i in 1..3)c.drawLine(0f,height*i/4f,width.toFloat(),height*i/4f,pen)
            pen.color=teal;pen.strokeWidth=dp(3).toFloat();pen.style=Paint.Style.STROKE
            val path=Path()
            points.forEachIndexed{i,v->
                val x=dp(8)+(width-dp(16))*(if(points.size==1)0.5f else i.toFloat()/(points.size-1))
                val y=height-dp(8)-(height-dp(16))*((v.toFloat()-low)/span)
                if(i==0)path.moveTo(x,y)else path.lineTo(x,y)
            }
            c.drawPath(path,pen);pen.style=Paint.Style.FILL
        }
    }
}
