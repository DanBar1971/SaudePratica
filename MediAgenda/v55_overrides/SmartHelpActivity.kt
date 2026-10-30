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
    private val locale get()=AppLanguage.code(this)
    private val darkBg=Color.rgb(8,28,37)
    private val pale=Color.rgb(238,249,245)
    private fun dp(n:Int)=(n*resources.displayMetrics.density+.5f).toInt()
    private fun text(pt:String,en:String,fr:String,de:String,es:String):String=when(locale){
        "en"->en;"fr"->fr;"de"->de;"es"->es;else->pt
    }
    override fun onCreate(savedInstanceState:Bundle?){
        super.onCreate(savedInstanceState)
        val outer=LinearLayout(this).apply {
            orientation=LinearLayout.VERTICAL
            setPadding(dp(14),dp(28),dp(14),dp(14))
            setBackgroundColor(darkBg)
        }
        outer.addView(TextView(this).apply {
            this.text=text("✨ Ajuda inteligente","✨ Smart help","✨ Aide intelligente",
                "✨ Intelligente Hilfe","✨ Ayuda inteligente")
            textSize=23f;setTextColor(Color.WHITE)
        })
        outer.addView(TextView(this).apply {
            this.text=text(
                "Funciona offline. Respostas sobre a aplicação, sem enviar perguntas nem dados médicos.",
                "Works offline. App guidance only; no questions or medical data are sent.",
                "Hors ligne. Aide sur l'application, sans transmission de données médicales.",
                "Offline. App-Hilfe ohne Übertragung medizinischer Daten.",
                "Sin conexión. Ayuda sobre la app sin enviar datos médicos.")
            textSize=12f;setTextColor(Color.LTGRAY)
            setPadding(0,dp(9),0,dp(10))
        })
        scroller=ScrollView(this)
        transcript=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(0,dp(10),0,dp(12))
        }
        scroller.addView(transcript)
        outer.addView(scroller,LinearLayout.LayoutParams(-1,0,1f))
        val suggestions=LinearLayout(this).apply { orientation=LinearLayout.VERTICAL }
        fun quick(value:String){
            suggestions.addView(Button(this).apply{
                text=value;isAllCaps=false
                setOnClickListener{ask(value)}
            })
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
        outer.addView(suggestions)
        question=EditText(this).apply{
            hint=text("Escreve uma pergunta sobre a app…","Ask about the app…",
                "Posez une question sur l'application…","Frage zur App eingeben…",
                "Pregunta sobre la app…")
            setTextColor(Color.WHITE);setHintTextColor(Color.LTGRAY)
            maxLines=2
        }
        outer.addView(question)
        outer.addView(Button(this).apply{
            text=text("Perguntar","Ask","Demander","Fragen","Preguntar")
            setOnClickListener{val value=question.text.toString().trim();if(value.isNotBlank())ask(value)}
        })
        setContentView(outer)
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
            textSize=15f;setTextColor(if(user)darkBg else pale)
            setBackgroundColor(if(user)Color.rgb(176,235,221)else Color.rgb(26,57,66))
            setPadding(dp(13),dp(12),dp(13),dp(12))
            layoutParams=LinearLayout.LayoutParams(-1,-2).apply{bottomMargin=dp(8)}
            gravity=if(user)Gravity.END else Gravity.START
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