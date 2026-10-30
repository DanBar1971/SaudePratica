package com.mediagenda.app

import android.content.Intent
import android.content.res.ColorStateList
import android.content.res.Configuration
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.button.MaterialButton
import com.google.android.material.card.MaterialCardView
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.mediagenda.app.data.HealthDocumentStore
import com.mediagenda.app.data.ProfileStore
import com.mediagenda.app.i18n.AppLanguage
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Locale

/** Local, profile-isolated care-home manager. Never submits data to ADSE automatically. */
class CareHomeActivity : AppCompatActivity() {
    companion object { const val EXTRA_PROFILE_ID = "saudepratica_profile_id" }
    private lateinit var profileId:String
    private lateinit var profileName:String
    private lateinit var body:LinearLayout
    private var month=Calendar.getInstance()
    private var pendingMonth=""
    private val prefs by lazy { getSharedPreferences("saudepratica_care_home_v1_" + profileId,MODE_PRIVATE) }
    private val dark get()=when(getSharedPreferences("mediagenda_ui",MODE_PRIVATE)
        .getString("theme_mode","system")){
        "dark"->true
        "light"->false
        else->(resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK)==Configuration.UI_MODE_NIGHT_YES
    }
    private val ink get()=if(dark)Color.WHITE else Color.rgb(26,42,51)
    private val muted get()=if(dark)Color.rgb(181,208,212) else Color.rgb(93,112,123)
    private val surface get()=if(dark)Color.rgb(30,46,55) else Color.WHITE
    private val accent get()=if(dark)Color.rgb(101,220,204) else Color.rgb(0,134,130)
    private val lang get()=AppLanguage.codes.indexOf(AppLanguage.code(this)).coerceIn(0,4)
    private fun tr(pt:String,en:String,fr:String,de:String,es:String)=arrayOf(pt,en,fr,de,es)[lang]
    private fun dp(n:Int)=(resources.displayMetrics.density*n+0.5f).toInt()
    private fun label(value:String,size:Float=15f,bold:Boolean=false):TextView=TextView(this).apply{
        text=value;textSize=size;setTextColor(ink)
        if(bold)setTypeface(typeface,android.graphics.Typeface.BOLD)
        setPadding(dp(2),dp(4),dp(2),dp(5))
    }
    private fun button(value:String,action:()->Unit)=MaterialButton(this).apply{
        text=value;isAllCaps=false;textSize=13f;cornerRadius=dp(12)
        strokeWidth=dp(1);strokeColor=ColorStateList.valueOf(accent)
        setTextColor(accent);backgroundTintList=ColorStateList.valueOf(surface)
        setOnClickListener{action()}
    }
    private fun vertical()=LinearLayout(this).apply{
        orientation=LinearLayout.VERTICAL
        setPadding(dp(14),dp(12),dp(14),dp(13))
    }
    private fun addCard(title:String,build:(LinearLayout)->Unit){
        val card=MaterialCardView(this).apply{
            radius=dp(16).toFloat();strokeWidth=dp(1)
            strokeColor=if(dark)Color.rgb(66,90,100) else Color.rgb(211,225,232)
            setCardBackgroundColor(surface)
        }
        val inside=vertical()
        inside.addView(label(title,18f,true))
        build(inside)
        card.addView(inside)
        body.addView(card,LinearLayout.LayoutParams(-1,-2).apply{bottomMargin=dp(12)})
    }
    private fun field(value:String,hint:String=""):EditText=EditText(this).apply{
        setSingleLine(true);setText(value);setHint(hint);textSize=15f
        setTextColor(ink);setHintTextColor(muted)
    }
    private fun notifyUser(value:String)=Toast.makeText(this,value,Toast.LENGTH_LONG).show()
    private val picker=registerForActivityResult(ActivityResultContracts.OpenDocument()){uri->
        if(uri==null)return@registerForActivityResult
        val selected=pendingMonth
        if(!selected.matches(Regex("[0-9]{4}-[0-9]{2}")))return@registerForActivityResult
        runCatching{
            val store=HealthDocumentStore(this,profileId)
            val document=store.add(uri,"Lar · Fatura "+selected)
            val item=invoice(selected)
            item.put("document_id",document.id)
            item.put("document_name",document.name)
            item.put("state","RECEBIDA")
            saveInvoice(selected,item)
        }.onSuccess{
            notifyUser("Fatura guardada também em Documentos Digitais.");render()
        }.onFailure{notifyUser("Não foi possível importar: "+(it.message?:"erro"))}
    }

    override fun onCreate(state:Bundle?){
        super.onCreate(state)
        val requested=intent.getStringExtra(EXTRA_PROFILE_ID).orEmpty()
        val profile=ProfileStore(this).all().firstOrNull{it.id==requested}
        if(profile==null){notifyUser("Escolhe primeiro um perfil válido.");finish();return}
        profileId=profile.id
        profileName=profile.name
        val root=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setBackgroundColor(if(dark)Color.rgb(9,25,34) else Color.rgb(242,248,250))
        }
        val header=LinearLayout(this).apply{
            orientation=LinearLayout.HORIZONTAL;gravity=Gravity.CENTER_VERTICAL
            setPadding(dp(14),dp(16),dp(12),dp(8))
        }
        header.addView(label("‹",35f).apply{
            gravity=Gravity.CENTER;setTextColor(accent);contentDescription="Voltar"
            setOnClickListener{finish()}
        },LinearLayout.LayoutParams(dp(48),dp(54)))
        header.addView(label("🏡 Lares e Apoio à Terceira Idade",21f,true),
            LinearLayout.LayoutParams(0,-2,1f))
        root.addView(header)
        val scroll=ScrollView(this).apply{isFillViewport=true}
        body=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(14),dp(8),dp(14),dp(35))
        }
        scroll.addView(body)
        root.addView(scroll,LinearLayout.LayoutParams(-1,0,1f))
        setContentView(root)
        render()
    }

    private fun institution()=prefs.getString("institution","").orEmpty()
    private fun valence()=prefs.getString("valence","ERPI").orEmpty()
    private fun monthKey():String=SimpleDateFormat("yyyy-MM",Locale.US).format(month.time)
    private fun monthLabel():String=SimpleDateFormat("MMMM yyyy",Locale("pt","PT")).format(month.time)
    private fun invoices()=runCatching{
        JSONObject(prefs.getString("months","{}")?:"{}")
    }.getOrElse{JSONObject()}
    private fun invoice(m:String):JSONObject=invoices().optJSONObject(m)?:JSONObject()
    private fun saveInvoice(m:String,v:JSONObject){
        val all=invoices()
        all.put(m,v)
        if(!prefs.edit().putString("months",all.toString()).commit())
            error("Não foi possível guardar a mensalidade.")
    }
    private fun changeState(value:String){
        val m=monthKey()
        val data=invoice(m)
        data.put("state",value)
        data.put("updated_at",System.currentTimeMillis())
        saveInvoice(m,data);render()
    }
    private fun openUrl(url:String){
        runCatching{startActivity(Intent(Intent.ACTION_VIEW,Uri.parse(url)))}
            .onFailure{notifyUser("Não foi possível abrir o endereço.")}
    }
    private fun call(number:String)=openUrl("tel:"+number)
    private fun email(){
        val subject="Pedido de fatura mensal do lar — "+monthLabel()
        val bodyText="Bom dia,\n\nSolicito, por favor, a fatura relativa à mensalidade de "+
            monthLabel()+", para apresentação à ADSE.\n\nCom os melhores cumprimentos."
        val mail=Uri.parse("mailto:"+Uri.encode(prefs.getString("email",
            "secretaria@apaticastanheira.pt").orEmpty()))
        val intent=Intent(Intent.ACTION_SENDTO,mail).apply{
            putExtra(Intent.EXTRA_SUBJECT,subject)
            putExtra(Intent.EXTRA_TEXT,bodyText)
        }
        runCatching{startActivity(intent)}.onFailure{
            notifyUser("Não foi encontrada aplicação de email.")
        }
    }
    private fun editInstitution(){
        val holder=vertical()
        val name=field(institution(),"Nome da instituição")
        val address=field(prefs.getString("address","").orEmpty(),"Morada")
        val phone=field(prefs.getString("phone","").orEmpty(),"Telefone")
        val email=field(prefs.getString("email","").orEmpty(),"Email")
        val website=field(prefs.getString("website","").orEmpty(),"Website")
        listOf("Instituição" to name,"Morada" to address,"Telefone" to phone,
            "Email" to email,"Site" to website).forEach{(caption,edit)->
            holder.addView(label(caption,12f));holder.addView(edit)
        }
        MaterialAlertDialogBuilder(this)
            .setTitle("Editar instituição")
            .setView(ScrollView(this).apply{addView(holder)})
            .setNeutralButton("Preencher APATI"){_,_->
                prefs.edit()
                    .putString("institution","APATI — Castanheira do Ribatejo")
                    .putString("address","Rua Palha Blanco 83, 2600-669 Castanheira do Ribatejo")
                    .putString("phone","263290281")
                    .putString("email","secretaria@apaticastanheira.pt")
                    .putString("website","https://apaticastanheira.pt/").apply()
                render()
            }
            .setPositiveButton("Guardar"){_,_->
                val clean=name.text.toString().trim().take(120)
                if(clean.isBlank()){notifyUser("Indica o nome da instituição.");return@setPositiveButton}
                prefs.edit().putString("institution",clean)
                    .putString("address",address.text.toString().trim().take(250))
                    .putString("phone",phone.text.toString().trim().take(30))
                    .putString("email",email.text.toString().trim().take(120))
                    .putString("website",website.text.toString().trim().take(250)).apply()
                render()
            }
            .setNegativeButton("Cancelar",null).show()
    }
    private fun editValence(){
        val types=arrayOf("ERPI · Residência","SAD · Apoio domiciliário","Centro de Dia")
        val codes=arrayOf("ERPI","SAD","DIA")
        MaterialAlertDialogBuilder(this)
            .setTitle("Tipo de resposta social")
            .setSingleChoiceItems(types,codes.indexOf(valence()).coerceAtLeast(0)){d,index->
                prefs.edit().putString("valence",codes[index]).apply()
                d.dismiss();render()
            }.setNegativeButton("Cancelar",null).show()
    }
    private fun editValue(key:String,title:String){
        val data=invoice(monthKey())
        val input=field(data.optString(key),"€ 0,00")
        input.inputType=android.text.InputType.TYPE_CLASS_NUMBER or
            android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL
        MaterialAlertDialogBuilder(this).setTitle(title).setView(input)
            .setPositiveButton("Guardar"){_,_->
                val raw=input.text.toString().trim().replace(',','.')
                if(raw.isNotBlank() && raw.toBigDecimalOrNull()==null){
                    notifyUser("Insere um valor numérico.");return@setPositiveButton
                }
                data.put(key,raw.take(18))
                saveInvoice(monthKey(),data);render()
            }.setNegativeButton("Cancelar",null).show()
    }
    private fun editReference(){
        val data=invoice(monthKey())
        val input=field(data.optString("adse_reference"),"Referência / data de submissão")
        MaterialAlertDialogBuilder(this).setTitle("Referência da ADSE")
            .setView(input).setPositiveButton("Guardar"){_,_->
                data.put("adse_reference",input.text.toString().trim().take(120))
                saveInvoice(monthKey(),data);render()
            }.setNegativeButton("Cancelar",null).show()
    }
    private fun notes(){
        val input=EditText(this).apply{
            setText(prefs.getString("notes",""));minLines=4;textSize=15f;setTextColor(ink)
        }
        MaterialAlertDialogBuilder(this).setTitle("Cuidados, visitas e notas")
            .setView(input).setPositiveButton("Guardar"){_,_->
                prefs.edit().putString("notes",input.text.toString().take(4000)).apply()
                render()
            }.setNegativeButton("Cancelar",null).show()
    }
    private fun stateLabel(code:String)=when(code){
        "PEDIDA"->"Fatura pedida"
        "RECEBIDA"->"Fatura recebida"
        "SUBMETIDA"->"Submetida à ADSE"
        "ANALISE"->"Em análise"
        "REEMBOLSADA"->"Reembolsada"
        "CORRIGIR"->"Precisa de correção"
        else->"Por pedir"
    }
    private fun selectState(){
        val codes=arrayOf("PENDENTE","PEDIDA","RECEBIDA","SUBMETIDA",
            "ANALISE","CORRIGIR","REEMBOLSADA")
        MaterialAlertDialogBuilder(this)
            .setTitle("Confirmar situação da mensalidade")
            .setItems(codes.map{stateLabel(it)}.toTypedArray()){_,index->
                val selected=codes[index]
                MaterialAlertDialogBuilder(this).setTitle("Confirmar estado?")
                    .setMessage("A app não consulta a ADSE. Confirma apenas o que verificaste: "+
                        stateLabel(selected)+".")
                    .setPositiveButton("Confirmar"){_,_->changeState(selected)}
                    .setNegativeButton("Cancelar",null).show()
            }.show()
    }
    private fun render(){
        body.removeAllViews()
        addCard("Perfil: "+profileName){card->
            card.addView(label("Instituição: "+institution().ifBlank{"Por configurar"},16f,true))
            card.addView(label("Valência: "+when(valence()){
                "ERPI"->"ERPI · Residência";"SAD"->"Apoio domiciliário";else->"Centro de Dia"
            },14f))
            card.addView(button("⚙ Editar instituição e contactos"){editInstitution()})
            card.addView(button("Escolher ERPI / SAD / Centro de Dia"){editValence()})
            val address=prefs.getString("address","").orEmpty()
            if(address.isNotBlank())card.addView(label(address,13f))
            val phone=prefs.getString("phone","").orEmpty()
            if(phone.matches(Regex("[+0-9 ]{6,25}")))
                card.addView(button("📞 Ligar para o lar"){call(phone.replace(" ",""))})
            val site=prefs.getString("website","").orEmpty()
            if(site.startsWith("https://"))card.addView(button("🌐 Website"){openUrl(site)})
        }
        addCard("🧾 Faturas e ADSE"){card->
            val control=LinearLayout(this).apply{gravity=Gravity.CENTER_VERTICAL}
            control.addView(button("‹"){month.add(Calendar.MONTH,-1);render()})
            control.addView(label(monthLabel().replaceFirstChar{it.uppercaseChar()},17f,true),
                LinearLayout.LayoutParams(0,-2,1f))
            control.addView(button("›"){month.add(Calendar.MONTH,1);render()})
            card.addView(control)
            val entry=invoice(monthKey())
            card.addView(label("Estado: "+stateLabel(entry.optString("state")),15f,true))
            card.addView(button("✉️ Preparar email a pedir a fatura"){
                email()
            })
            card.addView(button("✓ Confirmar que pedi a fatura"){changeState("PEDIDA")})
            card.addView(button("📎 Guardar PDF/imagem da fatura"){
                pendingMonth=monthKey()
                picker.launch(arrayOf("application/pdf","image/*"))
            })
            val documentId=entry.optString("document_id")
            if(documentId.isNotBlank())card.addView(label(
                "📂 Documento guardado: "+entry.optString("document_name"),13f))
            card.addView(button("📂 Abrir Documentos Digitais"){
                startActivity(Intent(this,DocumentsActivity::class.java)
                    .putExtra(DocumentsActivity.EXTRA_PROFILE_ID,profileId))
            })
            card.addView(button("🌐 Abrir ADSE Direta"){
                openUrl("https://adsedireta.adse.pt/")
            })
            card.addView(button("✓ Atualizar estado / reembolso"){selectState()})
            card.addView(button("Referência do processo: "+
                entry.optString("adse_reference").ifBlank{"Adicionar"}){editReference()})
            listOf("total" to "Valor faturado","paid" to "Valor pago",
                "refunded" to "Valor reembolsado").forEach{(key,name)->
                card.addView(button(name+": "+entry.optString(key).ifBlank{"—"}){editValue(key,name)})
            }
            card.addView(label("Cada mês deve ter uma única fatura para reembolso pela ADSE. "+
                "A submissão e a aprovação são confirmadas manualmente.",12f))
        }
        addCard("🤝 Apoios e documentação"){card->
            card.addView(button("Regras ADSE para Lares e Apoio Domiciliário"){
                openUrl("https://www2.adse.pt/sou-beneficiario/reembolsos/lares-e-apoio-domiciliario/")
            })
            card.addView(button("Documentos e formulários ADSE"){
                openUrl("https://www2.adse.pt/sou-beneficiario/documentos-uteis/")
            })
            card.addView(button("Simulador oficial de comparticipação"){
                openUrl("https://adsedireta.adse.pt/SimLares/")
            })
            card.addView(button("Complemento por dependência"){
                openUrl("https://www.gov.pt/servicos/obter-informacoes-sobre-o-complemento-por-dependencia")
            })
            card.addView(button("Complemento Solidário para Idosos"){
                openUrl("https://www.gov.pt/pt/servicos/pedir-o-complemento-solidario-para-idosos")
            })
            card.addView(label("Condições e valores dependem da situação e da autorização das entidades.",12f))
        }
        addCard("📅 Visitas, cuidados e notas"){card->
            card.addView(label(prefs.getString("notes","").orEmpty()
                .ifBlank{"Apontamentos sobre visitas, cuidados, roupa, equipa e assuntos a tratar."},14f))
            card.addView(button("✎ Editar notas"){notes()})
            card.addView(label("Não confirmar tomas nem cuidados clínicos sem confirmação do lar.",12f))
        }
    }
}
