package com.mediagenda.app

import android.content.res.Configuration
import android.content.res.ColorStateList
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.BitmapDrawable
import android.graphics.drawable.ColorDrawable
import android.graphics.drawable.LayerDrawable
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.EditText
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
import com.mediagenda.app.data.PersonalHealthRecord
import com.mediagenda.app.data.PersonalHealthStore
import com.mediagenda.app.data.ProfileStore
import java.text.SimpleDateFormat
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.time.format.ResolverStyle
import java.util.Date
import java.util.Locale

class HealthRecordsActivity: AppCompatActivity() {
    companion object {
        const val EXTRA_PROFILE_ID="profile_id"
        const val EXTRA_CATEGORY="category"
    }
    private lateinit var profileId:String
    private lateinit var profileName:String
    private lateinit var store:PersonalHealthStore
    private lateinit var body:LinearLayout
    private var category="symptoms"
    private val teal=Color.rgb(8,168,157)
    private val dark:Boolean get()=when(getSharedPreferences("mediagenda_ui",MODE_PRIVATE)
        .getString("theme_mode","system")){
        "dark"->true;"light"->false
        else->(resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK)==Configuration.UI_MODE_NIGHT_YES
    }
    private val ink get()=if(dark)Color.rgb(241,246,250) else Color.rgb(19,34,56)
    private val muted get()=if(dark)Color.rgb(186,200,215) else Color.rgb(102,112,133)
    private val surface get()=if(dark)Color.rgb(28,41,53) else Color.WHITE
    private val border get()=if(dark)Color.rgb(54,73,89) else Color.rgb(227,232,239)
    private fun dp(n:Int)=(n*resources.displayMetrics.density+.5f).toInt()
    private fun label(value:String,size:Float=14f,bold:Boolean=false,color:Int=ink)=
        TextView(this).apply{
            text=value;textSize=size;setTextColor(color)
            if(bold)setTypeface(null,Typeface.BOLD)
        }
    private fun card()=MaterialCardView(this).apply{
        radius=dp(20).toFloat();strokeWidth=dp(1);strokeColor=border
        setCardBackgroundColor(surface);cardElevation=dp(1).toFloat()
    }
    private fun addCard(v:MaterialCardView){
        body.addView(v,LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.WRAP_CONTENT).apply{bottomMargin=dp(12)})
    }
    private fun button(value:String,clicked:()->Unit)=MaterialButton(this).apply{
        text=value;isAllCaps=false;textSize=12f
        setTextColor(teal);backgroundTintList=ColorStateList.valueOf(Color.TRANSPARENT)
        strokeColor=ColorStateList.valueOf(teal);strokeWidth=dp(1);cornerRadius=dp(18)
        setOnClickListener{clicked()}
    }
    override fun onCreate(savedInstanceState:Bundle?){
        super.onCreate(savedInstanceState)
        val people=ProfileStore(this).all()
        val person=people.firstOrNull{it.id==intent.getStringExtra(EXTRA_PROFILE_ID)}
            ?:people.singleOrNull()?:run{finish();return}
        profileId=person.id;profileName=person.name
        store=PersonalHealthStore(this,profileId)
        category=intent.getStringExtra(EXTRA_CATEGORY)
            ?.takeIf{it in setOf("symptoms","measurements","vaccines","emergency","intakes")}
            ?:"symptoms"
        val (icon,title,subtitle)=when(category){
            "symptoms"->Triple("🩺","Diário de Sintomas","Sintomas e efeitos secundários")
            "measurements"->Triple("📊","Medições de Saúde","Valores registados pelo utilizador")
            "vaccines"->Triple("💉","Vacinas","Histórico e próximas doses")
            "emergency"->Triple("🆘","Ficha de Emergência","Contactos, alergias e informação essencial")
            else->Triple("✅","Tomas confirmadas","Histórico de medicação tomada")
        }
        val wallpaper=ContextCompat.getDrawable(this,R.drawable.saude_background)
        if(wallpaper is BitmapDrawable)wallpaper.gravity=Gravity.FILL
        val root=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL;setPadding(dp(16),dp(12),dp(16),dp(8))
            background=if(dark && wallpaper!=null)LayerDrawable(arrayOf(wallpaper,
                ColorDrawable(Color.argb(105,3,14,23))))
                else ColorDrawable(if(dark)Color.rgb(3,17,26) else Color.rgb(244,247,249))
        }
        val header=LinearLayout(this).apply{
            orientation=LinearLayout.HORIZONTAL;gravity=Gravity.CENTER_VERTICAL
        }
        header.addView(label("‹",34f,color=teal).apply{
            gravity=Gravity.CENTER;contentDescription="Voltar ao Início"
            setOnClickListener{finish()}
        },LinearLayout.LayoutParams(dp(36),dp(70)))
        val heads=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
        heads.addView(label("SaúdePrática",13f,true,teal))
        heads.addView(label("$icon  $title",25f,true))
        heads.addView(label(subtitle,13f,color=muted))
        header.addView(heads,LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f))
        header.addView(label(profileName.take(12),12f,true,teal))
        root.addView(header)
        val scroll=ScrollView(this).apply{overScrollMode=View.OVER_SCROLL_NEVER}
        body=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
        scroll.addView(body)
        root.addView(scroll,LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,0,1f))
        WindowCompat.setDecorFitsSystemWindows(window,false)
        window.statusBarColor=Color.TRANSPARENT;window.navigationBarColor=Color.TRANSPARENT
        val controller=WindowInsetsControllerCompat(window,window.decorView)
        controller.isAppearanceLightStatusBars=!dark
        controller.hide(WindowInsetsCompat.Type.navigationBars())
        ViewCompat.setOnApplyWindowInsetsListener(root){view,insets->
            val safe=insets.getInsets(WindowInsetsCompat.Type.statusBars() or
                WindowInsetsCompat.Type.navigationBars() or WindowInsetsCompat.Type.displayCutout())
            view.setPadding(dp(16)+safe.left,dp(12)+safe.top,
                dp(16)+safe.right,dp(8)+safe.bottom)
            insets
        }
        setContentView(root);ViewCompat.requestApplyInsets(root)
        refresh()
    }
    private fun refresh(){
        body.removeAllViews()
        if(category=="emergency"){showEmergency();return}
        val head=LinearLayout(this).apply{
            orientation=LinearLayout.HORIZONTAL;gravity=Gravity.CENTER_VERTICAL
            setPadding(dp(3),dp(16),dp(3),dp(10))
        }
        head.addView(label("Registos",18f,true),
            LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f))
        if(category!="intakes")head.addView(button("+ Adicionar"){addRecord()})
        body.addView(head)
        val items=runCatching{store.list(category)}.getOrElse{
            alert("Erro ao ler registos: "+it.message);emptyList()
        }
        body.addView(label(items.size.toString()+" registo(s)",13f,color=muted)
            .apply{setPadding(dp(5),0,0,dp(12))})
        if(items.isEmpty()){
            val empty=LinearLayout(this).apply{
                orientation=LinearLayout.VERTICAL;gravity=Gravity.CENTER
                setPadding(dp(20),dp(30),dp(20),dp(30))
            }
            empty.addView(label("♡",35f,color=teal))
            empty.addView(label("Ainda não existem registos",17f,true))
            empty.addView(label(if(category=="intakes")
                "Aqui aparecem apenas as tomas confirmadas, não as notificações enviadas."
                else "Toque em + Adicionar para guardar informação.",13f,color=muted))
            body.addView(empty)
        }
        val date=SimpleDateFormat("dd/MM/yyyy · HH:mm",Locale("pt","PT"))
        items.forEach{item->
            val shell=card()
            val row=LinearLayout(this).apply{
                orientation=LinearLayout.HORIZONTAL;gravity=Gravity.CENTER_VERTICAL
                setPadding(dp(15),dp(14),dp(13),dp(14))
            }
            val col=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
            col.addView(label(item.title,16f,true))
            col.addView(label(date.format(Date(item.timestamp)),12f,color=muted))
            val summary=item.fields.filterKeys{it!="medication_id"}
                .values.filter{it.isNotBlank()}.joinToString(" · ")
            if(summary.isNotBlank())col.addView(label(summary.take(220),13f,color=muted))
            row.addView(col,LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f))
            row.addView(label("›",28f,color=teal))
            shell.addView(row);shell.setOnClickListener{actions(item)};addCard(shell)
        }
        val note=when(category){
            "symptoms"->"Os registos não avaliam gravidade. Sintomas intensos ou preocupantes devem ser comunicados à equipa clínica."
            "measurements"->"Valores registados manualmente. A aplicação não diagnostica nem interpreta resultados."
            "vaccines"->"Confirme a vacinação e as datas das doses com os serviços de saúde."
            else->"Uma notificação enviada não significa que a medicação foi tomada. Apenas confirmações manuais ficam neste histórico."
        }
        body.addView(label(note,12f,color=muted).apply{
            setPadding(dp(8),dp(18),dp(8),dp(25))
        })
    }
    private fun actions(item:PersonalHealthRecord){
        val info=buildString{
            append(item.title)
            append("\n\n")
            append(SimpleDateFormat("dd/MM/yyyy HH:mm",Locale("pt","PT"))
                .format(Date(item.timestamp)))
            item.fields.filterKeys{it!="medication_id"}.forEach{(key,value)->
                if(value.isNotBlank())append("\n\n"+key+": "+value)
            }
        }
        MaterialAlertDialogBuilder(this).setTitle("Detalhes")
            .setMessage(info).setNegativeButton("Fechar",null)
            .setNeutralButton("Apagar"){_,_->
                MaterialAlertDialogBuilder(this).setTitle("Apagar registo?")
                    .setMessage("O registo será apagado deste utilizador.")
                    .setPositiveButton("Apagar"){_,_->
                        runCatching{store.remove(item)}.onSuccess{refresh()}
                            .onFailure{alert(it.message?:"Erro ao apagar")}
                    }.setNegativeButton("Cancelar",null).show()
            }.show()
    }
    private fun form(title:String,entries:List<Triple<String,String,String>>,
        onSave:(Map<String,String>)->Unit) {
        val box=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(20),dp(12),dp(20),dp(15))
        }
        val fields=entries.map{(key,caption,initial)->
            box.addView(label(caption,13f,true,Color.rgb(15,100,95)))
            val edit=EditText(this).apply{
                setText(initial);textSize=15f;setTextColor(Color.rgb(20,40,51))
                setSingleLine(key !in setOf("details","notes","allergies","conditions"))
                box.addView(this)
            }
            key to edit
        }
        val scroll=ScrollView(this);scroll.addView(box)
        val dialog=MaterialAlertDialogBuilder(this)
            .setTitle(title).setView(scroll).setPositiveButton("Guardar",null)
            .setNegativeButton("Cancelar",null).show()
        dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE).setOnClickListener{
            try{
                onSave(fields.associate{it.first to it.second.text.toString().trim()})
                dialog.dismiss();refresh()
            }catch(error:Exception){
                Toast.makeText(this,error.message?:"Verifique os dados.",Toast.LENGTH_LONG).show()
            }
        }
    }
    private fun addRecord(){
        when(category){
            "symptoms"->MaterialAlertDialogBuilder(this).setTitle("Tipo de registo")
                .setItems(arrayOf("Sintoma","Possível efeito secundário")){_,choice->
                    form("Registar sintoma",listOf(
                        Triple("title","Descrição do sintoma",""),
                        Triple("severity","Intensidade de 0 a 10",""),
                        Triple("details","Notas / evolução","")
                    )){values->
                        val intensity=values["severity"].orEmpty().toIntOrNull()
                        require(intensity!=null && intensity in 0..10){"A intensidade deve ser entre 0 e 10."}
                        store.add("symptoms",values["title"].orEmpty(),
                            values.filterKeys{it!="title"}+
                            mapOf("tipo" to if(choice==0)"Sintoma" else "Possível efeito secundário"))
                    }
                }.show()
            "measurements"->{
                val types=arrayOf("Tensão arterial","Glicemia","Peso","Temperatura","Saturação")
                val units=arrayOf("mmHg","mg/dL","kg","°C","%")
                MaterialAlertDialogBuilder(this).setTitle("Tipo de medição")
                    .setItems(types){_,choice->
                        form(types[choice],listOf(
                            Triple("value",if(choice==0)"Sistólica/diastólica (ex.: 120/80)"
                                else "Valor ("+units[choice]+")",""),
                            Triple("notes","Notas","")
                        )){values->
                            val raw=values["value"].orEmpty()
                            val valid=if(choice==0)raw.split("/").let{parts->
                                parts.size==2 && parts.all{part->
                                    part.trim().toDoubleOrNull()?.let{it>0 && it.isFinite()}==true
                                }
                            }else raw.replace(",",".").toDoubleOrNull()
                                ?.let{it>=0 && it.isFinite()}==true
                            require(valid){"Introduza um valor numérico válido."}
                            store.add("measurements",types[choice],values+
                                mapOf("unidade" to units[choice]))
                        }
                    }.show()
            }
            "vaccines"->form("Registar vacina",listOf(
                Triple("title","Nome da vacina",""),
                Triple("date","Data (DD/MM/AAAA)",""),
                Triple("next","Próxima dose (opcional)",""),
                Triple("notes","Lote e observações","")
            )){values->
                fun dateValid(value:String)=runCatching{
                    LocalDate.parse(value,DateTimeFormatter.ofPattern("dd/MM/uuuu")
                        .withResolverStyle(ResolverStyle.STRICT))
                }.isSuccess
                require(dateValid(values["date"].orEmpty())){"Introduza uma data válida."}
                require(values["next"].isNullOrBlank() ||
                    dateValid(values["next"].orEmpty())){"A data da próxima dose não é válida."}
                store.add("vaccines",values["title"].orEmpty(),
                    values.filterKeys{it!="title"})
            }
        }
    }
    private fun showEmergency(){
        val fields=listOf(
            "contact_name" to "Contacto de emergência",
            "contact_phone" to "Telefone",
            "second_contact" to "Segundo contacto",
            "allergies" to "Alergias conhecidas",
            "conditions" to "Informações médicas relevantes",
            "blood_group" to "Grupo sanguíneo (se confirmado)",
            "notes" to "Outras informações"
        )
        body.addView(label("Informações de "+profileName,17f,true).apply{
            setPadding(dp(4),dp(18),0,dp(14))
        })
        fields.forEach{(key,caption)->
            val shell=card()
            val box=LinearLayout(this).apply{
                orientation=LinearLayout.VERTICAL;setPadding(dp(16),dp(13),dp(16),dp(14))
            }
            box.addView(label(caption,14f,true))
            box.addView(label(store.emergencyValue(key).ifBlank{"Por preencher"},13f,color=muted))
            shell.addView(box);addCard(shell)
        }
        body.addView(button("✎ Editar ficha"){
            form("Ficha de Emergência",fields.map{(key,caption)->
                Triple(key,caption,store.emergencyValue(key))
            }){values->store.saveEmergency(values)}
        })
        body.addView(label(
            "Dados privados na aplicação. A ficha não substitui os serviços de emergência nem aparece automaticamente no ecrã bloqueado.",
            12f,color=muted).apply{setPadding(dp(6),dp(18),dp(6),dp(25))})
    }
    private fun alert(message:String){
        MaterialAlertDialogBuilder(this).setTitle("SaúdePrática")
            .setMessage(message).setPositiveButton("OK",null).show()
    }
}
