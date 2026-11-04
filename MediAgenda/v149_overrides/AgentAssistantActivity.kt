package com.mediagenda.app

import android.app.Activity
import android.content.Intent
import android.content.res.Configuration
import android.graphics.Color
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.google.android.material.button.MaterialButton
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.mlkit.genai.common.DownloadStatus
import com.google.mlkit.genai.common.FeatureStatus
import com.google.mlkit.genai.prompt.Generation
import com.google.mlkit.genai.prompt.GenerativeModel
import com.mediagenda.app.data.DataRepository
import com.mediagenda.app.data.ProfileStore
import com.mediagenda.app.model.AppointmentStatus
import kotlinx.coroutines.launch
import java.text.Normalizer
import java.time.LocalDate
import java.time.LocalDateTime
import java.time.LocalTime
import java.util.Locale

/**
 * A profile-scoped assistant: native read tools and proposed drafts NEVER write
 * health data. Gemini Nano is an optional on-device text generator for questions
 * not covered by tools. Its responses are NEVER interpreted as database commands.
 * Reminder delivery remains with existing Android notifications, not the LLM.
 */
class AgentAssistantActivity : AppCompatActivity() {
    companion object {
        const val EXTRA_PROFILE_ID = "saude_agent_profile"
        const val EXTRA_ACTION = "saude_agent_draft_action"
        const val EXTRA_NAME = "saude_agent_draft_name"
        const val EXTRA_DOSE = "saude_agent_draft_dose"
        const val EXTRA_DATE = "saude_agent_draft_date"
        const val EXTRA_TIME = "saude_agent_draft_time"
        const val EXTRA_ACTIVITY = "saude_agent_draft_activity"
        const val ACTION_MEDICATION = "prepare_medication"
        const val ACTION_APPOINTMENT = "prepare_appointment"
    }

    private var profileId = ""
    private var profileName = ""
    private lateinit var log: LinearLayout
    private lateinit var scroll: ScrollView
    private lateinit var input: EditText
    private lateinit var status: TextView
    private var model: GenerativeModel? = null
    private var modelReady = false
    private var modelAvailableToDownload = false
    private var busy = false
    private val prefs by lazy { getSharedPreferences("mediagenda_ui", MODE_PRIVATE) }
    private val dark get() = when(prefs.getString("theme_mode","system")) {
        "dark" -> true
        "light" -> false
        else -> (resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK) ==
            Configuration.UI_MODE_NIGHT_YES
    }
    private val bg get() = if(dark) Color.rgb(9,28,37) else Color.rgb(245,248,250)
    private val surface get() = if(dark) Color.rgb(26,45,55) else Color.WHITE
    private val fg get() = if(dark) Color.WHITE else Color.rgb(20,40,49)
    private val secondary get() = if(dark) Color.rgb(191,212,215) else Color.rgb(76,95,105)
    private val accent = Color.rgb(9,124,114)
    private fun dp(n:Int)=(n*resources.displayMetrics.density+0.5f).toInt()
    private fun rounded(color:Int)=android.graphics.drawable.GradientDrawable().apply {
        setColor(color);cornerRadius=dp(14).toFloat()
    }
    private fun localized(pt:String,en:String,fr:String,de:String,es:String):String =
        when(com.mediagenda.app.i18n.AppLanguage.code(this)) {
            "en"->en;"fr"->fr;"de"->de;"es"->es;else->pt
        }

    override fun onCreate(savedInstanceState:Bundle?) {
        super.onCreate(savedInstanceState)
        // This Activity is internal only (android:exported=false); the caller
        // must be an already unlocked MainActivity with an active profile.
        val selected = intent.getStringExtra(EXTRA_PROFILE_ID).orEmpty()
        val actual = ProfileStore(this).all().firstOrNull { it.id==selected }
        if(actual==null || selected.isBlank()) { finish(); return }
        profileId=actual.id;profileName=actual.name
        title=localized("Assistente SaúdePrática","SaúdePrática Assistant",
            "Assistant SaúdePrática","SaúdePrática Assistent","Asistente SaúdePrática")
        val outer=LinearLayout(this).apply {
            orientation=LinearLayout.VERTICAL
            setBackgroundColor(bg)
            setPadding(dp(12),dp(12),dp(12),dp(15))
        }
        val titleRow=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL;gravity=Gravity.CENTER_VERTICAL}
        titleRow.addView(button("‹") {finish()},LinearLayout.LayoutParams(dp(56),dp(50)))
        titleRow.addView(TextView(this).apply{
            text="✨ "+title
            textSize=20f;setTextColor(fg)
            setTypeface(typeface,android.graphics.Typeface.BOLD)
        },LinearLayout.LayoutParams(0,-2,1f))
        outer.addView(titleRow)
        status=TextView(this).apply {
            textSize=12f;setTextColor(secondary)
            setPadding(dp(4),dp(7),dp(4),dp(10))
            text=localized("Perfil: ","Profile: ","Profil : ","Profil: ","Perfil: ")+profileName+
                " · Assistência guiada offline"
        }
        outer.addView(status)
        scroll=ScrollView(this)
        log=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL;setPadding(dp(4),dp(4),dp(4),dp(12))}
        scroll.addView(log)
        outer.addView(scroll,LinearLayout.LayoutParams(-1,0,1f))
        val shortcuts=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
        val one=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL}
        one.addView(button(localized("Próximas consultas","Appointments","Rendez-vous",
            "Termine","Citas")){readAgenda()},LinearLayout.LayoutParams(0,dp(54),1f))
        one.addView(button(localized("Ver medicação","Medications","Médicaments",
            "Medikamente","Medicamentos")){readMedication()},LinearLayout.LayoutParams(0,dp(54),1f))
        shortcuts.addView(one)
        val two=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL}
        two.addView(button(localized("+ Consulta","+ Appointment","+ RDV",
            "+ Termin","+ Cita")){offerAppointment("")},LinearLayout.LayoutParams(0,dp(54),1f))
        two.addView(button(localized("+ Medicação","+ Medication","+ Médicament",
            "+ Medikament","+ Medicación")){offerMedication("")},LinearLayout.LayoutParams(0,dp(54),1f))
        shortcuts.addView(two)
        val three=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL}
        three.addView(button(localized("Ajuda clássica","Classic help","Aide classique",
            "Klassische Hilfe","Ayuda clásica")){
            startActivity(Intent(this,SmartHelpActivity::class.java))
        },LinearLayout.LayoutParams(0,dp(48),1f))
        three.addView(button(localized("IA local","Local AI","IA locale",
            "Lokale KI","IA local")){manageLocalModel()},LinearLayout.LayoutParams(0,dp(48),1f))
        shortcuts.addView(three)
        outer.addView(shortcuts)
        val composer=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL;gravity=Gravity.CENTER_VERTICAL}
        input=EditText(this).apply{
            hint=localized("Pergunta ou pede uma ação…","Ask or request an action…",
                "Posez une question…","Frage oder Aktion…","Pregunta o acción…")
            setTextColor(fg);setHintTextColor(secondary)
            textSize=15f;minLines=1;maxLines=3
            background=rounded(surface)
            setPadding(dp(14),dp(9),dp(14),dp(9))
        }
        composer.addView(input,LinearLayout.LayoutParams(0,dp(54),1f))
        composer.addView(button("➤"){
            val value=input.text.toString().trim()
            if(value.isNotEmpty()){input.text.clear();ask(value)}
        },LinearLayout.LayoutParams(dp(62),dp(54)))
        outer.addView(composer)
        setContentView(outer)
        window.setSoftInputMode(android.view.WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE)
        bubble(false,localized(
            "Olá! Podes perguntar pelos teus agendamentos e medicamentos. Também preparo fichas para confirmares antes de guardar. Os alarmes continuam a funcionar independentemente da IA.",
            "Hello! I can read your appointments and medications and open drafts for your approval. Alarms remain independent of AI.",
            "Bonjour ! Je peux consulter vos rendez-vous et médicaments et préparer des fiches à confirmer.",
            "Hallo! Ich kann Termine und Medikamente anzeigen und Entwürfe zur Bestätigung öffnen.",
            "¡Hola! Puedo consultar tus citas y medicación, y preparar fichas para confirmar."))
        lifecycleScope.launch { checkModel() }
    }
    private fun button(label:String,action:()->Unit):MaterialButton=MaterialButton(this).apply {
        text=label;isAllCaps=false;textSize=12f;minHeight=dp(46)
        setOnClickListener{action()}
    }
    private fun bubble(user:Boolean,message:String){
        if(isFinishing || isDestroyed)return
        val card=TextView(this).apply{
            text=(if(user)"👤  " else "✨  ")+message
            setTextColor(if(user)Color.rgb(6,46,40) else fg)
            textSize=15f;setPadding(dp(14),dp(13),dp(14),dp(13))
            background=rounded(if(user)Color.rgb(183,237,220) else surface)
        }
        log.addView(card,LinearLayout.LayoutParams(-1,-2).apply{
            bottomMargin=dp(9);leftMargin=if(user)dp(35) else 0
            rightMargin=if(user)0 else dp(24)
        })
        scroll.post{scroll.fullScroll(View.FOCUS_DOWN)}
    }
    private fun normalized(value:String):String=Normalizer.normalize(
        value.lowercase(Locale.ROOT),Normalizer.Form.NFD).replace(Regex("\\p{Mn}+"),"")
    private fun currentRepo():DataRepository? {
        // Re-validate the exact profile before EVERY read; no cross-profile queries.
        if(profileId.isBlank() || ProfileStore(this).all().none{it.id==profileId})return null
        return DataRepository(this,profileId)
    }
    private fun readAgenda(){
        val repo=currentRepo()
        if(repo==null){bubble(false,"Perfil indisponível. Volta a selecionar o perfil.");return}
        val now=LocalDateTime.now()
        val pending=runCatching{
            repo.loadAppointments().filter{a->
                !a.cancelled && !AppointmentStatus.completed(a,now) &&
                    (runCatching{LocalDate.parse(a.date)}.getOrNull()?.let{!it.isBefore(now.toLocalDate())}==true)
            }.sortedWith(compareBy({it.date},{it.time})).take(8)
        }.getOrElse{bubble(false,"Não foi possível consultar os agendamentos deste perfil.");return}
        if(pending.isEmpty()){bubble(false,"Não há agendamentos futuros registados neste perfil.");return}
        bubble(false, "Próximas marcações de "+profileName+":\n"+
            pending.joinToString("\n"){a->
                "• "+a.date+" "+a.time+" · "+
                    (a.activity.ifBlank{a.specialty.ifBlank{a.type}})+
                    (if(a.location.isBlank())"" else " · "+a.location)
            })
    }
    private fun readMedication(){
        val repo=currentRepo()
        if(repo==null){bubble(false,"Perfil indisponível. Volta a selecionar o perfil.");return}
        val meds=runCatching{repo.loadMedications()}.getOrElse{
            bubble(false,"Não foi possível consultar a medicação deste perfil.");return
        }
        if(meds.isEmpty()){bubble(false,"Este perfil não tem medicamentos registados.");return}
        bubble(false,"Medicação de "+profileName+" ("+meds.size+"):\n"+
            meds.take(12).joinToString("\n"){m->
                "• "+m.medication+" "+m.dose+
                    (if(m.suspendedFrom.isNotBlank())" · SUSPENSA" else "")+
                    (if(m.doseTimes.isNotBlank())" · "+m.doseTimes else
                        if(m.time.isNotBlank())" · "+m.time else "")
            }+(if(meds.size>12)"\n… e mais "+(meds.size-12)+" registos." else "")+
            "\nOs horários são os registados na aplicação, não uma recomendação de doses.")
    }
    private fun parseDate(text:String):String{
        val iso=Regex("""\b\d{4}-\d{2}-\d{2}\b""").find(text)?.value
        if(iso!=null)return runCatching{LocalDate.parse(iso).toString()}.getOrDefault("")
        val local=Regex("""\b(\d{1,2})/(\d{1,2})/(\d{4})\b""").find(text)
        if(local!=null){
            val x=local.groupValues
            return runCatching{LocalDate.of(x[3].toInt(),x[2].toInt(),x[1].toInt()).toString()}.getOrDefault("")
        }
        return if(normalized(text).contains("amanha"))LocalDate.now().plusDays(1).toString()
            else if(normalized(text).contains("hoje"))LocalDate.now().toString() else ""
    }
    private fun parseTime(text:String):String {
        val hit=Regex("""\b([01]?\d|2[0-3])[:h]([0-5]\d)\b""").find(text)?:return ""
        return hit.groupValues[1].padStart(2,'0')+":"+hit.groupValues[2]
    }
    private fun offerAppointment(value:String){
        val date=parseDate(value);val time=parseTime(value)
        val desc=value.trim().take(150)
        MaterialAlertDialogBuilder(this).setTitle("Preparar nova consulta")
            .setMessage("Vou abrir uma ficha para "+profileName+
                ". A data, hora, local e lembretes têm de ser revistos antes de guardar.")
            .setPositiveButton("Rever ficha"){_,_->
                if(currentRepo()==null){bubble(false,"O perfil deixou de estar disponível.");return@setPositiveButton}
                val result=Intent().putExtra(EXTRA_ACTION,ACTION_APPOINTMENT)
                    .putExtra(EXTRA_PROFILE_ID,profileId)
                    .putExtra(EXTRA_DATE,date)
                    .putExtra(EXTRA_TIME,time)
                    .putExtra(EXTRA_ACTIVITY,desc)
                setResult(Activity.RESULT_OK,result);finish()
            }.setNegativeButton("Cancelar",null).show()
    }
    private fun offerMedication(value:String){
        val dose=Regex("""(?i)\b\d+(?:[.,]\d+)?\s*(?:mg|g|ml|mcg|µg|ui)\b""")
            .find(value)?.value.orEmpty()
        val clean=value.replace(Regex("""(?i)^.*?\b(?:adicionar|criar|registar|registrar)\s+(?:uma?\s+)?(?:nova?\s+)?(?:medicacao|medicamento|medication|medicine)?\s*"""),"")
            .replace(dose,"").trim(' ','.',',',';').take(80)
        MaterialAlertDialogBuilder(this).setTitle("Preparar nova medicação")
            .setMessage("Vou abrir a ficha de "+profileName+
                (if(clean.isNotBlank())" para "+clean else "")+
                ". Confirma o nome, dose, posologia, horários e prescrição. "+
                "O agente não recomenda nem inicia tratamentos.")
            .setPositiveButton("Rever ficha"){_,_->
                if(currentRepo()==null){bubble(false,"O perfil deixou de estar disponível.");return@setPositiveButton}
                val result=Intent().putExtra(EXTRA_ACTION,ACTION_MEDICATION)
                    .putExtra(EXTRA_PROFILE_ID,profileId)
                    .putExtra(EXTRA_NAME,clean)
                    .putExtra(EXTRA_DOSE,dose)
                setResult(Activity.RESULT_OK,result);finish()
            }.setNegativeButton("Cancelar",null).show()
    }
    private fun ask(value:String){
        bubble(true,value)
        val q=normalized(value)
        val wantsNew=listOf("adicionar","acrescentar","criar","registar","registrar",
            "add ","create ","ajouter","hinzufugen","anadir").any{q.contains(it)}
        val med=listOf("medic","farmaco","remedio","comprimido","medicine","drug",
            "medikament").any{q.contains(it)}
        val apt=listOf("consulta","marcacao","agendamento","appointment",
            "rendez-vous","termin","cita","exame").any{q.contains(it)}
        when {
            wantsNew && med -> offerMedication(value)
            wantsNew && apt -> offerAppointment(value)
            apt -> readAgenda()
            med -> readMedication()
            q.contains("ajuda") || q.contains("help") -> {
                bubble(false,"Podes abrir a Ajuda clássica no botão inferior.")
            }
            modelReady -> generateLocal(value)
            else -> bubble(false,
                "Posso consultar a medicação e os agendamentos deste perfil e preparar fichas para validares. "+
                "Neste dispositivo, as outras perguntas usam a Ajuda clássica enquanto a IA local não estiver disponível.")
        }
    }
    private suspend fun checkModel(){
        try{
            val client=Generation.getClient()
            model=client
            when(client.checkStatus()){
                FeatureStatus.AVAILABLE -> {
                    modelReady=true;status.text="Perfil: "+profileName+" · IA Gemini Nano local disponível"
                }
                FeatureStatus.DOWNLOADABLE -> {
                    modelAvailableToDownload=true
                    status.text="Perfil: "+profileName+" · IA local opcional por instalar"
                }
                FeatureStatus.DOWNLOADING -> {
                    status.text="Perfil: "+profileName+" · IA local a descarregar no dispositivo"
                }
                else -> {
                    status.text="Perfil: "+profileName+" · Assistência guiada offline (IA indisponível)"
                }
            }
        }catch(_:Exception){
            status.text="Perfil: "+profileName+" · Assistência guiada offline (IA indisponível)"
        }
    }
    private fun manageLocalModel(){
        if(modelReady){bubble(false,"A IA generativa local está disponível neste telemóvel.");return}
        if(!modelAvailableToDownload){
            bubble(false,"Gemini Nano não está disponível neste telemóvel. "+
                "As consultas de registos e fichas guiadas continuam a funcionar sem IA.")
            return
        }
        MaterialAlertDialogBuilder(this).setTitle("Instalar IA local gratuita?")
            .setMessage("O Android descarregará o modelo Gemini Nano através do AICore. "+
                "Pode utilizar bastante espaço e rede Wi-Fi. Os registos de saúde não são enviados para um servidor da aplicação.")
            .setPositiveButton("Descarregar"){_,_->
                lifecycleScope.launch {
                    try{
                        model?.download()?.collect{item->
                            when(item){
                                DownloadStatus.DownloadCompleted -> {
                                    modelAvailableToDownload=false
                                    checkModel()
                                    bubble(false,"Modelo descarregado. Já podes conversar com a IA local.")
                                }
                                is DownloadStatus.DownloadFailed -> bubble(false,
                                    "Falha ao descarregar a IA. Podes continuar com a assistência guiada.")
                                is DownloadStatus.DownloadProgress -> status.text=
                                    "Perfil: "+profileName+" · A descarregar modelo local..."
                                is DownloadStatus.DownloadStarted -> status.text=
                                    "Perfil: "+profileName+" · Download da IA iniciado"
                            }
                        }
                    }catch(_:Exception){bubble(false,"Não foi possível descarregar o modelo neste equipamento.")}
                }
            }.setNegativeButton("Cancelar",null).show()
    }
    private fun generateLocal(question:String){
        if(busy)return
        val client=model?:return
        busy=true
        status.text="Perfil: "+profileName+" · IA local a responder..."
        lifecycleScope.launch {
            try{
                // Never ask the LLM to write records, and never add clinical
                // records to the prompt. Native actions are classified above.
                val prompt="És um assistente de utilização da app SaúdePrática. "+
                    "Responde em português de Portugal, em até 100 palavras. "+
                    "Não diagnoses nem recomendes doses, mudanças de medicação ou tratamentos. "+
                    "Se a pergunta envolver uma ação clínica, indica a ficha e confirmação humana. "+
                    "Se não souberes algo sobre a app, diz que não sabes. Pergunta: "+
                    question.take(500)
                val response=client.generateContent(prompt)
                bubble(false,response.candidates.firstOrNull()?.text?.take(2000).orEmpty().ifBlank{
                    "A IA local não conseguiu responder. Usa a Ajuda clássica."
                })
            }catch(_:Exception){
                bubble(false,"A IA local não conseguiu responder. Os registos e a Ajuda clássica continuam disponíveis.")
            }finally{
                busy=false
                status.text="Perfil: "+profileName+" · "+(if(modelReady)"IA local disponível" else "Assistência guiada offline")
            }
        }
    }
    override fun onDestroy(){
        model?.close();model=null
        super.onDestroy()
    }
}
