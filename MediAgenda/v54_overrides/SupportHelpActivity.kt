package com.mediagenda.app

import android.content.ActivityNotFoundException
import android.content.Intent
import android.content.res.ColorStateList
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.ArrayAdapter
import android.widget.EditText
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.Spinner
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.button.MaterialButton
import com.google.android.material.card.MaterialCardView
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.mediagenda.app.i18n.AppLanguage

/** Illustrated self-service guide and user-initiated email to the app author. */
class SupportHelpActivity:AppCompatActivity(){
    companion object {
        const val MODE="help_mode"
        const val HELP="help"
        const val CONTACT="contact"
        const val SUPPORT_ADDRESS="daniel.barradas@gmail.com"
        const val PAYPAL_URL="https://www.paypal.com/paypalme/djjindungo"
    }
    private val paletteBackground=Color.rgb(8,28,37)
    private val paletteCard=Color.rgb(26,48,61)
    private val light=Color.rgb(237,249,246)
    private val muted=Color.rgb(192,210,214)
    private val accent=Color.rgb(112,219,192)
    private val lang get()=AppLanguage.codes.indexOf(AppLanguage.code(this)).coerceAtLeast(0)
    private fun tr(vararg texts:String)=texts[lang]
    private fun dp(v:Int)=(v*resources.displayMetrics.density+.5f).toInt()

    override fun onCreate(savedInstanceState:Bundle?){
        super.onCreate(savedInstanceState)
        val body=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(15),dp(28),dp(15),dp(26))
            setBackgroundColor(paletteBackground)
        }
        val top=LinearLayout(this).apply{gravity=Gravity.CENTER_VERTICAL}
        top.addView(text("‹",34f),LinearLayout.LayoutParams(dp(45),dp(54)).apply{leftMargin=dp(7)}).also{
            (top.getChildAt(0) as TextView).setOnClickListener{finish()}
        }
        top.addView(text("SaúdePrática",21f),LinearLayout.LayoutParams(0,dp(54),1f))
        body.addView(top)
        if(intent.getStringExtra(MODE)==CONTACT)showContact(body)else showGuide(body)
        val scroll=ScrollView(this).apply{isFillViewport=false;addView(body)}
        setContentView(scroll)
    }
    private fun text(value:String,size:Float=16f,color:Int=light):TextView=TextView(this).apply{
        text=value;textSize=size;setTextColor(color)
        setPadding(dp(8),dp(5),dp(8),dp(7))
    }
    private fun heading(value:String):TextView=text(value,24f).apply{
        setTypeface(typeface,android.graphics.Typeface.BOLD)
    }
    private fun panel():LinearLayout=LinearLayout(this).apply{
        orientation=LinearLayout.VERTICAL
        setPadding(dp(12),dp(15),dp(12),dp(15))
    }
    private fun card(content:LinearLayout):MaterialCardView=MaterialCardView(this).apply{
        radius=dp(18).toFloat()
        strokeWidth=dp(1)
        strokeColor=Color.rgb(55,103,106)
        setCardBackgroundColor(paletteCard)
        addView(content)
    }
    private fun addCard(parent:LinearLayout,content:LinearLayout){
        parent.addView(card(content),LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT
        ).apply{topMargin=dp(10);bottomMargin=dp(6)})
    }
    private fun action(title:String,onClick:()->Unit):MaterialButton=MaterialButton(this).apply{
        text=title;isAllCaps=false;textSize=15f
        setTextColor(Color.rgb(13,44,48))
        backgroundTintList=ColorStateList.valueOf(accent)
        cornerRadius=dp(14)
        setOnClickListener{onClick()}
    }
    private fun showGuide(parent:LinearLayout){
        parent.addView(heading(tr("📖 Ajuda — como usar a aplicação",
            "📖 Help — how to use the app","📖 Aide — utiliser l’application",
            "📖 Hilfe — so funktioniert die App","📖 Ayuda — cómo usar la aplicación")))
        parent.addView(text(tr("Aprende em seis passos, com imagens simples.",
            "Learn in six simple illustrated steps.","Apprenez en six étapes illustrées.",
            "Lernen Sie in sechs bebilderten Schritten.",
            "Aprende en seis pasos con imágenes sencillas."),14f,muted))
        data class Step(val icon:Int,val title:Array<String>,val description:Array<String>)
        val steps=listOf(
            Step(R.drawable.guide_home,
                arrayOf("1. Ecrã inicial","1. Home screen","1. Accueil","1. Startseite","1. Inicio"),
                arrayOf("Escolhe um módulo, como Medicação, Agenda ou Documentos. Em Mais podes ocultar ou mostrar módulos.",
                    "Tap Medication, Appointments or Documents. Use More to show or hide modules.",
                    "Ouvrez Médicaments, Rendez-vous ou Documents. Dans Plus, choisissez les modules.",
                    "Tippen Sie auf Medikamente, Termine oder Dokumente. Unter Mehr können Sie Module ein- und ausblenden.",
                    "Abre Medicación, Agenda o Documentos. En Más puedes mostrar u ocultar módulos.")),
            Step(R.drawable.guide_med,
                arrayOf("2. Medicação e tomas","2. Medication and doses","2. Médicaments et prises","2. Medikamente und Einnahmen","2. Medicación y tomas"),
                arrayOf("Toca em + Adicionar, preenche o medicamento e a hora. Anexa a foto da embalagem. No aviso, toca em TOMEI só depois de tomares.",
                    "Tap + Add, enter the medicine and time, and add a package photo. Tap TAKEN after taking your dose.",
                    "Touchez + Ajouter, saisissez le médicament et l’heure, puis sa photo. Confirmez après la prise.",
                    "Tippen Sie auf + Hinzufügen, geben Sie Medikament und Uhrzeit ein und fügen Sie ein Packungsfoto hinzu. Erst nach der Einnahme bestätigen.",
                    "Pulsa + Añadir, indica el medicamento y la hora y añade la foto de la caja. Confirma solo después de tomarlo.")),
            Step(R.drawable.guide_calendar,
                arrayOf("3. Consultas e exames","3. Appointments and tests","3. Rendez-vous et examens","3. Termine und Untersuchungen","3. Citas y pruebas"),
                arrayOf("Na Agenda adiciona consultas, datas e horas. Vê todas as marcações no Calendário e recebe lembretes.",
                    "Add appointments, dates and times in Agenda. See them in Calendar and receive reminders.",
                    "Ajoutez les rendez-vous et les heures dans l’Agenda. Retrouvez-les dans le Calendrier.",
                    "Erfassen Sie Termine und Uhrzeiten. Alle Termine finden Sie im Kalender.",
                    "Añade citas, fechas y horas en Agenda. Consúltalas en Calendario y recibe avisos.")),
            Step(R.drawable.guide_docs,
                arrayOf("4. Fotografias e documentos","4. Photos and documents","4. Photos et documents","4. Fotos und Dokumente","4. Fotos y documentos"),
                arrayOf("Guarda documentos e exames no perfil certo. Podes fotografar ou escolher ficheiros já existentes.",
                    "Save documents and tests to the correct profile. Take a photo or choose an existing file.",
                    "Enregistrez les documents dans le bon profil. Prenez une photo ou choisissez un fichier.",
                    "Speichern Sie Dokumente im richtigen Profil. Fotografieren oder vorhandene Datei auswählen.",
                    "Guarda documentos en el perfil adecuado. Haz una foto o selecciona un archivo.")),
            Step(R.drawable.guide_sync,
                arrayOf("5. Sincronizar dois telemóveis","5. Sync two phones","5. Synchroniser deux téléphones","5. Zwei Handys synchronisieren","5. Sincronizar dos móviles"),
                arrayOf("Em Mais → Sincronização familiar, escolhe Partilhar num telemóvel e Procurar no outro. Compara e confirma os códigos antes da transferência. Faz backup antes da primeira vez.",
                    "In More → Family sync, tap Share on one phone and Search on the other. Compare the security codes. Back up first.",
                    "Dans Plus → Synchronisation familiale, choisissez Partager et Rechercher. Comparez les codes. Sauvegardez d’abord.",
                    "Unter Mehr → Familiensynchronisierung auf einem Handy Teilen, auf dem anderen Suchen wählen. Codes vergleichen. Zuvor sichern.",
                    "En Más → Sincronización familiar, pulsa Compartir en un móvil y Buscar en el otro. Compara códigos. Haz copia antes.")),
            Step(R.drawable.guide_support,
                arrayOf("6. Ajuda e segurança","6. Help and security","6. Aide et sécurité","6. Hilfe und Sicherheit","6. Ayuda y seguridad"),
                arrayOf("Usa PIN ou impressão digital para proteger a app. Em Contactar suporte podes enviar dúvidas, sugestões e erros.",
                    "Protect the app with a PIN or fingerprint. Contact Support for questions, ideas and bugs.",
                    "Protégez l’application avec un PIN ou une empreinte. Contactez le support pour vos questions et erreurs.",
                    "Schützen Sie die App mit PIN oder Fingerabdruck. Melden Sie Fragen und Fehler beim Support.",
                    "Protege la app con PIN o huella. Contacta con soporte para dudas, sugerencias o errores."))
        )
        steps.forEach{step->
            val c=panel()
            c.addView(text(step.title[lang],19f).apply{setTypeface(typeface,1)})
            c.addView(ImageView(this).apply{
                setImageResource(step.icon)
                scaleType=ImageView.ScaleType.FIT_CENTER
                adjustViewBounds=true
                contentDescription=step.title[lang]
            },LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,dp(153)))
            c.addView(text(step.description[lang],14f,muted))
            addCard(parent,c)
        }
        parent.addView(action(tr("✉ Contactar suporte","✉ Contact support","✉ Contacter le support",
            "✉ Support kontaktieren","✉ Contactar soporte")){
            startActivity(Intent(this,SupportHelpActivity::class.java).putExtra(MODE,CONTACT))
        })
        parent.addView(text(tr("As instruções são informativas e não substituem aconselhamento médico.",
            "These instructions do not replace medical advice.",
            "Ces instructions ne remplacent pas un avis médical.",
            "Diese Anleitung ersetzt keine ärztliche Beratung.",
            "Estas instrucciones no sustituyen el consejo médico."),12f,muted))
    }
    private fun field(hint:String,lines:Int=1):EditText=EditText(this).apply{
        setSingleLine(lines==1)
        this.hint=hint
        textSize=16f
        setTextColor(light);setHintTextColor(muted)
        backgroundTintList=ColorStateList.valueOf(accent)
        if(lines>1){minLines=lines;gravity=Gravity.TOP}
        setPadding(dp(9),dp(15),dp(9),dp(15))
    }
    private fun showContact(parent:LinearLayout){
        parent.addView(heading(tr("✉ Contactar o suporte","✉ Contact support",
            "✉ Contacter le support","✉ Support kontaktieren","✉ Contactar soporte")))
        parent.addView(text(tr("Podes pedir ajuda, enviar uma sugestão ou comunicar um erro.",
            "Ask for help, suggest improvements or report a bug.",
            "Demandez de l’aide, proposez une amélioration ou signalez un bug.",
            "Fragen stellen, Verbesserungen vorschlagen oder Fehler melden.",
            "Pide ayuda, sugiere mejoras o informa de un error."),14f,muted))
        val types=listOf(
            arrayOf("Pedido de ajuda","Help request","Demande d’aide","Hilfeanfrage","Solicitud de ayuda"),
            arrayOf("Sugestão para melhorar","Improvement idea","Suggestion d’amélioration","Verbesserungsvorschlag","Sugerencia de mejora"),
            arrayOf("Reportar um erro / bug","Report a bug","Signaler un bug","Fehler melden","Informar de un error"))
        val form=panel()
        form.addView(text(tr("Tipo de contacto","Message type","Type de demande",
            "Nachrichtentyp","Tipo de contacto"),14f,muted))
        val spinner=Spinner(this)
        spinner.adapter=ArrayAdapter(this,android.R.layout.simple_spinner_dropdown_item,
            types.map{it[lang]})
        form.addView(spinner)
        val who=field(tr("Nome (opcional)","Name (optional)","Nom (facultatif)",
            "Name (optional)","Nombre (opcional)"))
        val address=field(tr("Email para resposta (opcional)","Reply email (optional)",
            "Adresse pour la réponse (facultatif)","Antwort-E-Mail (optional)",
            "Email de respuesta (opcional)"))
        val description=field(tr("Escreve aqui a tua mensagem...","Write your message...",
            "Rédigez votre message...","Nachricht hier schreiben...",
            "Escribe aquí tu mensaje..."),5)
        form.addView(who);form.addView(address);form.addView(description)
        form.addView(text(tr("Não incluas PIN, número de Cartão de Cidadão, receitas nem outros dados médicos sensíveis.",
            "Do not include your PIN, ID-card number or sensitive medical information.",
            "Ne partagez pas de PIN, de numéro d’identité ou de données médicales sensibles.",
            "Keine PIN, Ausweisnummer oder sensiblen Gesundheitsdaten angeben.",
            "No incluyas PIN, DNI ni datos médicos sensibles."),13f,muted))
        form.addView(action(tr("✉ Preparar email para enviar","✉ Open email to send",
            "✉ Préparer l’email","✉ E-Mail vorbereiten","✉ Preparar correo")){
            val note=description.text.toString().trim()
            val reply=address.text.toString().trim()
            if(note.length<10){description.error=tr("Escreve pelo menos 10 caracteres.",
                "Enter at least 10 characters.","Saisissez au moins 10 caractères.",
                "Bitte mindestens 10 Zeichen eingeben.","Escribe al menos 10 caracteres.");return@action}
            if(reply.isNotBlank() && !android.util.Patterns.EMAIL_ADDRESS.matcher(reply).matches()){
                address.error=tr("Email inválido.","Invalid email.","Email incorrect.",
                    "Ungültige E-Mail.","Email inválido.");return@action
            }
            val version=runCatching{packageManager.getPackageInfo(packageName,0).versionName}
                .getOrNull().orEmpty()
            val body=buildString{
                append("Tipo: ").append(types[spinner.selectedItemPosition][0]).append("\n")
                if(who.text.isNotBlank())append("Nome: ").append(who.text).append("\n")
                if(reply.isNotEmpty())append("Responder a: ").append(reply).append("\n")
                append("\nMensagem:\n").append(note)
                append("\n\n---\nSaúdePrática ").append(version)
            }
            val subject="SaúdePrática · "+types[spinner.selectedItemPosition][0]
            val uri=Uri.parse("mailto:$SUPPORT_ADDRESS?subject="+Uri.encode(subject)+
                "&body="+Uri.encode(body))
            val intent=Intent(Intent.ACTION_SENDTO,uri)
            try{startActivity(intent)}catch(_:ActivityNotFoundException){
                Toast.makeText(this,tr("Não foi encontrada uma app de email. Endereço: $SUPPORT_ADDRESS",
                    "No email app found. Address: $SUPPORT_ADDRESS",
                    "Aucune application email. Adresse : $SUPPORT_ADDRESS",
                    "Keine E-Mail-App gefunden. Adresse: $SUPPORT_ADDRESS",
                    "No hay aplicación de correo. Dirección: $SUPPORT_ADDRESS"),Toast.LENGTH_LONG).show()
            }
        })
        addCard(parent,form)
        parent.addView(text(tr("O email só é enviado quando confirmares o envio na tua aplicação de correio.",
            "Email is only sent after you confirm in your email app.",
            "L’email est envoyé uniquement après confirmation dans votre messagerie.",
            "Die E-Mail wird erst nach Bestätigung in Ihrer E-Mail-App versendet.",
            "El correo solo se envía cuando lo confirmes en tu aplicación."),13f,muted))
    }
}