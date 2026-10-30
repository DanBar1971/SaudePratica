package com.mediagenda.app

import android.graphics.Color
import android.os.Bundle
import android.view.Gravity
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.mediagenda.app.i18n.AppLanguage
import java.text.Normalizer
import java.util.Locale

/** Private, offline guidance assistant. This is rule-based help, not clinical AI. */
class SmartHelpActivity: AppCompatActivity() {
    private lateinit var transcript:LinearLayout
    private lateinit var scroller:ScrollView
    private lateinit var question:EditText
    private lateinit var quickChoices:LinearLayout
    private val locale get()=AppLanguage.code(this)
    private val darkBg=Color.rgb(9,28,37)
    private val surface=Color.rgb(26,45,55)
    private val accent=Color.rgb(14,130,118)
    private val pale=Color.rgb(238,249,245)
    private fun dp(n:Int)=(n*resources.displayMetrics.density+.5f).toInt()
    private fun text(pt:String,en:String,fr:String,de:String,es:String):String=when(locale){
        "en"->en;"fr"->fr;"de"->de;"es"->es;else->pt
    }
    private fun rounded(color:Int,radius:Int=16):android.graphics.drawable.GradientDrawable=
        android.graphics.drawable.GradientDrawable().apply{
            setColor(color);cornerRadius=dp(radius).toFloat()
        }
    private fun smartButton(label:String,primary:Boolean=false,action:()->Unit):
        com.google.android.material.button.MaterialButton =
        com.google.android.material.button.MaterialButton(this).apply{
            text=label
            isAllCaps=false
            textSize=14f
            minHeight=dp(43)
            cornerRadius=dp(14)
            insetTop=0;insetBottom=0
            setTextColor(if(primary)Color.WHITE else pale)
            backgroundTintList=android.content.res.ColorStateList.valueOf(
                if(primary)accent else Color.rgb(37,70,77))
            setOnClickListener{action()}
        }
    override fun onCreate(savedInstanceState:Bundle?){
        super.onCreate(savedInstanceState)
        title=text("Ajuda inteligente","Smart help","Aide intelligente",
            "Intelligente Hilfe","Ayuda inteligente")
        // Always handle the keyboard with IME insets: OEMs differ on adjustResize.
        androidx.core.view.WindowCompat.setDecorFitsSystemWindows(window,false)
        window.setSoftInputMode(android.view.WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE)
        window.statusBarColor=darkBg
        window.navigationBarColor=darkBg
        val outer=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setBackgroundColor(darkBg)
        }
        val header=LinearLayout(this).apply{
            orientation=LinearLayout.HORIZONTAL
            gravity=Gravity.CENTER_VERTICAL
        }
        val back=TextView(this).apply{
            text="‹";textSize=38f
            gravity=Gravity.CENTER
            setTextColor(Color.rgb(96,217,201))
            contentDescription=text("Voltar à SaúdePrática","Back","Retour",
                "Zurück","Volver")
            isClickable=true;isFocusable=true
            setOnClickListener{finish()}
        }
        header.addView(back,LinearLayout.LayoutParams(dp(43),dp(52)))
        header.addView(TextView(this).apply{
            this.text=text("✨ Ajuda inteligente","✨ Smart help","✨ Aide intelligente",
                "✨ Intelligente Hilfe","✨ Ayuda inteligente")
            textSize=23f;setTextColor(Color.WHITE)
            setTypeface(typeface,android.graphics.Typeface.BOLD)
        },LinearLayout.LayoutParams(0,-2,1f))
        outer.addView(header)
        outer.addView(TextView(this).apply{
            this.text=text(
                "Funciona offline. Perguntas sobre a aplicação, sem transmitir dados médicos.",
                "Offline app guidance. No medical data are transmitted.",
                "Aide hors ligne, sans transmission de données médicales.",
                "Offline-Hilfe ohne Übertragung medizinischer Daten.",
                "Ayuda sin conexión, sin enviar datos médicos.")
            textSize=13f;setTextColor(Color.rgb(189,207,212))
            setPadding(dp(7),dp(5),dp(6),dp(9))
        })
        scroller=ScrollView(this).apply{
            isFillViewport=true
            clipToPadding=false
        }
        transcript=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(3),dp(10),dp(3),dp(14))
        }
        scroller.addView(transcript)
        outer.addView(scroller,LinearLayout.LayoutParams(-1,0,1f))
        quickChoices=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
        fun quick(value:String){
            quickChoices.addView(smartButton(value){ask(value)},
                LinearLayout.LayoutParams(-1,dp(45)).apply{bottomMargin=dp(5)})
        }
        quick(text("Como fotografar a caixa?","How to scan a medicine box?",
            "Comment scanner une boîte ?","Wie Arzneipackung scannen?",
            "¿Cómo escanear una caja?"))
        quick(text("Como registar uma toma?","How do I confirm a dose?",
            "Comment confirmer une prise ?","Wie Einnahme bestätigen?",
            "¿Cómo confirmar una toma?"))
        quick(text("Como sincronizar os telemóveis?","How do I sync two phones?",
            "Comment synchroniser deux téléphones ?","Wie zwei Handys synchronisieren?",
            "¿Cómo sincronizar dos móviles?"))
        outer.addView(quickChoices)
        val bar=LinearLayout(this).apply{
            orientation=LinearLayout.HORIZONTAL
            gravity=Gravity.CENTER_VERTICAL
            setPadding(dp(7),dp(6),dp(7),dp(4))
            background=rounded(surface,18)
        }
        question=EditText(this).apply{
            hint=text("Escreve aqui a tua pergunta…","Type your question here…",
                "Écrivez votre question ici…","Frage hier eingeben…",
                "Escribe tu pregunta aquí…")
            textSize=15f
            setTextColor(Color.WHITE)
            setHintTextColor(Color.rgb(189,207,212))
            minLines=1;maxLines=3
            inputType=android.text.InputType.TYPE_CLASS_TEXT or
                android.text.InputType.TYPE_TEXT_FLAG_CAP_SENTENCES or
                android.text.InputType.TYPE_TEXT_FLAG_MULTI_LINE
            imeOptions=android.view.inputmethod.EditorInfo.IME_ACTION_SEND
            background=null
        }
        bar.addView(question,LinearLayout.LayoutParams(0,-2,1f))
        bar.addView(smartButton("➤",true){
            val value=question.text.toString().trim()
            if(value.isNotBlank())ask(value)
        },LinearLayout.LayoutParams(dp(65),dp(50)))
        outer.addView(bar)
        setContentView(outer)
        // Keep the composer ABOVE the Xiaomi/Android IME instead of under it.
        androidx.core.view.ViewCompat.setOnApplyWindowInsetsListener(outer){_,insets->
            val top=insets.getInsets(
                androidx.core.view.WindowInsetsCompat.Type.statusBars()).top
            val bottom=insets.getInsets(
                androidx.core.view.WindowInsetsCompat.Type.navigationBars()).bottom
            val keyboard=insets.isVisible(
                androidx.core.view.WindowInsetsCompat.Type.ime())
            val keyboardBottom=insets.getInsets(
                androidx.core.view.WindowInsetsCompat.Type.ime()).bottom
            outer.setPadding(dp(10),top+dp(5),dp(10),
                (if(keyboard)keyboardBottom else bottom)+dp(10))
            quickChoices.visibility=if(keyboard)android.view.View.GONE else android.view.View.VISIBLE
            if(keyboard){scroller.post{scroller.fullScroll(ScrollView.FOCUS_DOWN)}}
            insets
        }
        androidx.core.view.ViewCompat.requestApplyInsets(outer)
        postBubble(false,text(
            "Olá! Pergunta-me como usar a medicação, as tomas, as consultas, os documentos ou a sincronização.",
            "Hello! Ask how to manage medication, doses, appointments, documents or syncing.",
            "Bonjour ! Posez une question sur les médicaments, les prises, les rendez-vous ou la synchronisation.",
            "Hallo! Frag mich zur Medikation, Einnahmen, Terminen oder Synchronisierung.",
            "¡Hola! Pregunta por medicamentos, tomas, citas o sincronización."))
    }
    private fun postBubble(user:Boolean,message:String){
        val bubble=TextView(this).apply{
            text=(if(user)"👤  " else "✨  ")+message
            textSize=15f
            setTextColor(if(user)Color.rgb(9,44,39) else pale)
            background=rounded(if(user)Color.rgb(176,235,221) else surface,14)
            setPadding(dp(13),dp(12),dp(13),dp(12))
            layoutParams=LinearLayout.LayoutParams(-1,-2).apply{
                bottomMargin=dp(10)
                leftMargin=if(user)dp(35) else 0
                rightMargin=if(user)0 else dp(30)
            }
            gravity=if(user)Gravity.END else Gravity.START
            setTextIsSelectable(true)
        }
        transcript.addView(bubble)
        scroller.post{scroller.fullScroll(ScrollView.FOCUS_DOWN)}
    }
    private fun normalize(s:String):String=Normalizer.normalize(
        s.lowercase(Locale.ROOT),Normalizer.Form.NFD)
        .replace(Regex("\\p{Mn}+"),"")
    private fun ask(value:String){
        question.text.clear();postBubble(true,value)
        val q=normalize(value)
        val response=when {
            listOf("dose","toma","tomei","pill","taken","prise","einnahme","pastilla").any{q.contains(it)}->text(
                "Vai a Tomas. Os avisos ficam 'Por confirmar' até tocares em ✓ TOMEI na notificação ou confirmares a toma no módulo. Nunca confirmes um comprimido que não tomaste.",
                "Open Doses. Reminders remain Pending until you tap ✓ TAKEN on the notification or confirm in the app. Never confirm a dose you did not take.",
                "Ouvrez Prises. Les rappels restent en attente jusqu'à la confirmation dans l'application ou la notification.",
                "Öffne Einnahmen. Erinnerungen bleiben offen, bis du sie in der App oder Benachrichtigung bestätigst.",
                "Abre Tomas. Los avisos siguen pendientes hasta que confirmes en la aplicación o notificación.")
            listOf("fotograf","caixa","medic","scan","medicine","boite","pack","caja","arznei","ocr").any{q.contains(it)}->text(
                "Vai a Medicação → + Adicionar → ✨ Reconhecer caixa por fotografia. Escolhe uma imagem ou fotografa a frente da embalagem. Confirma sempre nome e dose antes de guardar. Para apenas guardar a fotografia, abre a ficha e usa 'Anexar foto da embalagem', sem OCR.",
                "Go to Medication → Add → Recognize medicine box from photo. Check name and strength before saving. To keep a photo without recognition, use Attach package photo in the medication record.",
                "Médicaments → Ajouter → Reconnaître une boîte par photo. Vérifiez nom et dosage. Vous pouvez aussi joindre simplement la photo sans OCR.",
                "Medikamente → Hinzufügen → Packung aus Foto erkennen. Name und Stärke vor dem Speichern prüfen. Das Foto kann auch ohne OCR angehängt werden.",
                "Medicación → Añadir → Reconocer caja por foto. Comprueba nombre y dosis. También puedes adjuntar una foto sin OCR.")
            listOf("sincron","sync","bluetooth","wifi","telefone","phone","handy","movil","telefono").any{q.contains(it)}->text(
                "Em ambos os telemóveis abre Mais → Sincronização familiar. Num toca PARTILHAR, no outro PROCURAR. Confirma os códigos iguais. Faz primeiro um backup em cada telemóvel.",
                "On both phones open More → Family sync. Tap SHARE on one and SEARCH on the other. Check matching pairing codes. Make a backup on each phone first.",
                "Sur les deux téléphones : Plus → Synchronisation familiale. PARTAGER sur l'un, RECHERCHER sur l'autre, puis comparer les codes. Sauvegardez d'abord.",
                "Auf beiden Handys: Mehr → Familiensynchronisierung. Ein Gerät TEILEN, das andere SUCHEN. Codes vergleichen und zuvor sichern.",
                "En ambos móviles: Más → Sincronización familiar. COMPARTIR en uno y BUSCAR en otro. Compara los códigos y realiza copias antes.")
            listOf("consulta","appointment","rendez","termin","cita","exame").any{q.contains(it)}->text(
                "Abre Marcações → + Adicionar. Podes fotografar uma convocatória, importar o documento ou preencher a data e hora manualmente. Confirma tudo antes de guardar.",
                "Open Appointments → Add. Photograph a letter, import a document or enter the date and time manually. Review before saving.",
                "Rendez-vous → Ajouter. Photographiez la convocation, importez le document ou saisissez la date et l'heure.",
                "Termine → Hinzufügen. Einladung fotografieren, Dokument importieren oder Datum und Uhrzeit selbst eingeben.",
                "Citas → Añadir. Fotografía la carta, importa el documento o escribe fecha y hora.")
            listOf("document","pdf","analise","analyse","lab","bericht","informe").any{q.contains(it)}->text(
                "Em Documentos podes importar PDFs e fotografias. Em Análises podes guardar exames e resultados. Confirma o perfil antes de guardar.",
                "In Documents you can import PDFs and photos. In Lab Results you can save tests. Check the profile first.",
                "Dans Documents, importez des PDF et photos. Dans Analyses, gardez les examens. Vérifiez le profil.",
                "Unter Dokumente lassen sich PDFs und Fotos hinzufügen. Laborwerte separat speichern; Profil prüfen.",
                "En Documentos importa PDF y fotos. En Análisis guarda resultados y comprueba el perfil.")
            listOf("backup","copia","sauvegarde","sicherung","guardar dados").any{q.contains(it)}->text(
                "Mais → Backup completo da família → Criar ZIP. Guarda o ZIP num local seguro: contém informações de saúde e não está encriptado.",
                "More → Complete family backup → Create ZIP. Store it securely: it includes medical information and is not encrypted.",
                "Plus → Sauvegarde familiale complète → Créer ZIP. Conservez-le en sécurité : il n'est pas chiffré.",
                "Mehr → Vollständiges Familien-Backup → ZIP erstellen. Sicher aufbewahren: unverschlüsselt.",
                "Más → Copia familiar completa → Crear ZIP. Guárdalo con seguridad: no está cifrado.")
            listOf("contact","apoio","suporte","support","bug","erro","fehler","error","aide").any{q.contains(it)}->text(
                "Mais → Contactar suporte. Escolhe Ajuda, Sugestão ou Bug, descreve o problema e confirma o envio no teu email. Não anexes documentos médicos sem necessidade.",
                "More → Contact support. Select Help, Suggestion or Bug, describe it, then send from your email. Avoid unnecessary medical data.",
                "Plus → Contacter le support. Choisissez le type de demande, décrivez-la et envoyez par e-mail, sans données médicales inutiles.",
                "Mehr → Support kontaktieren. Typ auswählen, Problem beschreiben und E-Mail senden. Keine unnötigen Gesundheitsdaten.",
                "Más → Contactar soporte. Selecciona el tipo, describe el problema y envía desde tu correo. Evita datos médicos innecesarios.")
            listOf("acerca","about","versao","version","info app","informacoes da app").any{q.contains(it)}->text(
                "Abre Mais e desliza até Acerca da SaúdePrática, onde tens a versão e os detalhes da aplicação.",
                "Open More and scroll to About SaúdePrática to see the app version and details.",
                "Ouvrez Plus, puis À propos de SaúdePrática pour voir la version.",
                "Öffne Mehr und anschließend Über SaúdePrática für die App-Version.",
                "Abre Más y entra en Acerca de SaúdePrática para consultar la versión.")
            else ->text(
                "Ainda não tenho uma resposta para isso. Experimenta perguntar sobre fotografias de medicamentos, tomas, consultas, documentos, sincronização ou backups. Também tens Mais → Ajuda.",
                "I don't have a specific answer yet. Try asking about medication photos, doses, appointments, syncing or backups. See More → Help.",
                "Je n'ai pas encore cette réponse. Essayez médicaments, prises, rendez-vous ou synchronisation. Voir Plus → Aide.",
                "Dazu habe ich noch keine Antwort. Frag nach Medikamenten, Einnahmen, Terminen oder Sync. Siehe Mehr → Hilfe.",
                "Todavía no tengo esa respuesta. Prueba medicación, tomas, citas o sincronización. Consulta Más → Ayuda.")
        }
        postBubble(false,response)
    }
}