package com.mediagenda.app.i18n

import android.app.Activity
import android.content.Context
import android.view.View
import android.view.ViewGroup
import android.view.ViewTreeObserver
import android.widget.EditText
import android.widget.TextView
import com.google.android.material.textfield.TextInputLayout

/** Selected UI language; never translates text entered by the user. */
object AppLanguage {
    val codes=listOf("pt","en","fr","de","es")
    val names=listOf("Português","English","Français","Deutsch","Español")
    private const val PREFS="saudepratica_language_v1"
    fun code(context:Context):String {
        val saved=context.getSharedPreferences(PREFS,Context.MODE_PRIVATE)
            .getString("language","pt").orEmpty()
        return if(saved in codes)saved else "pt"
    }
    fun chosenName(context:Context):String=names[codes.indexOf(code(context))]
    fun choose(context:Context,value:String){
        require(value in codes)
        check(context.getSharedPreferences(PREFS,Context.MODE_PRIVATE)
            .edit().putString("language",value).commit())
    }
    private val source="""
Início	Home	Accueil	Startseite	Inicio
Medicação	Medication	Médicaments	Medikation	Medicación
Tomas	Doses	Prises	Einnahmen	Tomas
Agenda	Appointments	Rendez-vous	Termine	Agenda
Calendário	Calendar	Calendrier	Kalender	Calendario
Documentos	Documents	Documents	Dokumente	Documentos
Situação Clínica	Medical history	Situation clinique	Gesundheitsakte	Situación clínica
Despesas de Saúde	Health expenses	Dépenses de santé	Gesundheitskosten	Gastos sanitarios
Beber água	Drink water	Boire de l’eau	Wasser trinken	Beber agua
Ciclo Menstrual	Menstrual cycle	Cycle menstruel	Menstruationszyklus	Ciclo menstrual
Nutrição	Nutrition	Nutrition	Ernährung	Nutrición
Saúde Visual	Eye health	Santé visuelle	Augengesundheit	Salud visual
Sintomas	Symptoms	Symptômes	Symptome	Síntomas
Medições	Measurements	Mesures	Messwerte	Mediciones
Vacinas	Vaccines	Vaccins	Impfungen	Vacunas
Emergência	Emergency	Urgence	Notfall	Emergencia
Farmácias	Pharmacies	Pharmacies	Apotheken	Farmacias
Mais	More	Plus	Mehr	Más
Tomas e avisos	Doses and reminders	Prises et rappels	Einnahmen und Erinnerungen	Tomas y avisos
Pendentes e confirmadas	Pending and confirmed	En attente et confirmées	Offen und bestätigt	Pendientes y confirmadas
Consultas e exames	Appointments and tests	Consultations et examens	Termine und Untersuchungen	Consultas y pruebas
Vista mensal e marcações	Calendar and appointments	Calendrier et rendez-vous	Kalender und Termine	Calendario y citas
PDFs e imagens	PDFs and images	PDF et images	PDFs und Bilder	PDF e imágenes
Medicina do Trabalho	Occupational medicine	Médecine du travail	Arbeitsmedizin	Medicina del trabajo
Faturas, receitas e IRS	Invoices, prescriptions and tax	Factures, ordonnances et impôts	Rechnungen, Rezepte und Steuern	Facturas, recetas e impuestos
Hidratação	Hydration	Hydratation	Flüssigkeitszufuhr	Hidratación
Período e pílula	Period and pill	Règles et pilule	Periode und Pille	Periodo y píldora
Plano alimentar e restrições	Meal plan and restrictions	Repas et restrictions	Ernährungsplan und Einschränkungen	Plan de alimentación y restricciones
Graduação e receita óptica	Vision and prescription	Vision et ordonnance	Sehstärke und Sehhilfe	Graduación y receta óptica
Diário e efeitos secundários	Journal and side effects	Journal et effets secondaires	Tagebuch und Nebenwirkungen	Diario y efectos secundarios
Tensão, glicemia e mais	Blood pressure, glucose and more	Tension, glycémie et plus	Blutdruck, Blutzucker und mehr	Tensión, glucemia y más
Histórico de vacinação	Vaccination history	Historique vaccinal	Impfverlauf	Historial de vacunación
Alergias e contactos	Allergies and contacts	Allergies et contacts	Allergien und Kontakte	Alergias y contactos
Perto de mim e serviço	Nearby and on duty	À proximité et de garde	In der Nähe und Notdienst	Cercanas y de guardia
Aplicação oficial de saúde	Official health app	Application officielle de santé	Offizielle Gesundheits-App	Aplicación oficial de salud
Abrir aplicação IPO Lisboa	Open IPO Lisboa app	Ouvrir l’app IPO Lisboa	IPO-Lissabon-App öffnen	Abrir aplicación IPO Lisboa
Utilizadores e opções	Users and settings	Utilisateurs et options	Benutzer und Einstellungen	Usuarios y opciones
Perfil, cópias de segurança e exportação	Profile, backups and exports	Profil, sauvegardes et exportation	Profil, Sicherungen und Export	Perfil, copias y exportación
Perfil atual	Current profile	Profil actuel	Aktuelles Profil	Perfil actual
Definir nome do perfil	Set profile name	Définir le nom du profil	Profilnamen festlegen	Definir nombre del perfil
Escolher utilizador	Choose user	Choisir un utilisateur	Benutzer auswählen	Elegir usuario
Adicionar utilizador	Add user	Ajouter un utilisateur	Benutzer hinzufügen	Añadir usuario
Escolher módulos do Início	Choose Home modules	Choisir les modules d’accueil	Startseitenmodule auswählen	Elegir módulos de Inicio
Selecionar com checklist o que aparece no menu principal	Select Home menu items	Choisir les éléments du menu principal	Hauptmenüelemente auswählen	Elegir qué aparece en el menú
Aspeto da aplicação	App appearance	Apparence de l’application	App-Darstellung	Aspecto de la aplicación
Escolha entre automático, claro e escuro.	Choose automatic, light or dark.	Automatique, clair ou sombre.	Automatisch, hell oder dunkel.	Automático, claro u oscuro.
PIN de acesso	Access PIN	Code PIN d’accès	Zugangs-PIN	PIN de acceso
Ativado · PIN de 4 dígitos	Enabled · 4-digit PIN	Activé · PIN à 4 chiffres	Aktiv · vierstellige PIN	Activado · PIN de 4 dígitos
Desativado · a aplicação abre sem pedir PIN	Disabled · no PIN required	Désactivé · pas de PIN requis	Deaktiviert · keine PIN nötig	Desactivado · sin PIN
Notificações	Notifications	Notifications	Benachrichtigungen	Notificaciones
Testar avisos de agendamentos e alarmes de medicação	Test appointment and medication alerts	Tester les rappels de rendez-vous et médicaments	Termin- und Medikamentenalarme testen	Probar avisos de citas y medicación
Sincronização familiar (Bluetooth / Wi-Fi)	Family sync (Bluetooth / Wi-Fi)	Synchronisation familiale (Bluetooth / Wi-Fi)	Familiensynchronisierung (Bluetooth / WLAN)	Sincronización familiar (Bluetooth / Wi-Fi)
Trocar dados com outro telemóvel SaúdePrática, sem apagar registos	Sync with another SaúdePrática phone, without deleting records	Échanger avec un autre téléphone sans effacer les données	Mit anderem SaúdePrática-Handy ohne Datenverlust synchronisieren	Sincronizar con otro móvil sin borrar registros
Backup completo da família	Full family backup	Sauvegarde familiale complète	Vollständige Familiensicherung	Copia familiar completa
Exportar ZIP com utilizadores, dados, fotos, PDFs e exames	Export ZIP with users, data, photos, PDFs and tests	Exporter profils, données, photos, PDF et examens	ZIP mit Benutzern, Daten, Fotos und Befunden exportieren	Exportar ZIP con usuarios, datos, fotos y pruebas
Restaurar backup completo	Restore full backup	Restaurer la sauvegarde complète	Vollständige Sicherung wiederherstellen	Restaurar copia completa
Importar ZIP num novo telemóvel; substitui os dados atuais	Import ZIP to another phone; replaces current data	Importer ZIP ; remplace les données actuelles	ZIP importieren; ersetzt aktuelle Daten	Importar ZIP; sustituye los datos actuales
Importar JSON	Import JSON	Importer JSON	JSON importieren	Importar JSON
Exportar JSON	Export JSON	Exporter JSON	JSON exportieren	Exportar JSON
Importa medicação, agenda ou um backup completo.	Import medication, appointments or a full backup.	Importer médicaments, rendez-vous ou sauvegarde.	Medikamente, Termine oder Backup importieren.	Importa medicación, citas o una copia completa.
Guarde os ficheiros de medicação e agenda separadamente.	Save medication and appointment files separately.	Enregistrer médicaments et rendez-vous séparément.	Medikamente und Termine getrennt speichern.	Guardar por separado medicación y citas.
Backup do utilizador atual	Current user backup	Sauvegarde du profil actuel	Sicherung des aktuellen Benutzers	Copia del usuario actual
Cria um JSON com medicação e agenda deste perfil.	Create JSON with this profile’s medication and appointments.	Créer un JSON du profil avec médicaments et rendez-vous.	JSON mit Medikamenten und Terminen dieses Profils erstellen.	Crear JSON con medicación y citas del perfil.
Exportar para Excel	Export to Excel	Exporter vers Excel	Nach Excel exportieren	Exportar a Excel
Gera CSV UTF-8 com separador ';' para abrir no Excel.	Creates a CSV for Excel.	Crée un CSV pour Excel.	Erstellt eine CSV für Excel.	Crea CSV para Excel.
Acerca	About	À propos	Über die App	Acerca de
SaúdePrática — versão, autor e contacto	SaúdePrática — version, author and contact	SaúdePrática — version, auteur et contact	SaúdePrática — Version, Autor und Kontakt	SaúdePrática — versión, autor y contacto
Organize a terapêutica e os avisos	Organize medication and reminders	Organisez médicaments et rappels	Medikamente und Erinnerungen organisieren	Organiza la medicación y los avisos
Medicamentos	Medicines	Médicaments	Medikamente	Medicamentos
Ordenar:	Sort:	Trier :	Sortieren:	Ordenar:
Ainda não há medicação	No medication yet	Aucun médicament	Noch keine Medikamente	Todavía no hay medicación
Adicionar	Add	Ajouter	Hinzufügen	Añadir
Cancelar	Cancel	Annuler	Abbrechen	Cancelar
Guardar	Save	Enregistrer	Speichern	Guardar
Voltar	Back	Retour	Zurück	Volver
Sair	Exit	Quitter	Beenden	Salir
Confirmar	Confirm	Confirmer	Bestätigen	Confirmar
Eliminar	Delete	Supprimer	Löschen	Eliminar
Apagar	Delete	Supprimer	Löschen	Borrar
Editar	Edit	Modifier	Bearbeiten	Editar
Detalhes	Details	Détails	Details	Detalles
Nome	Name	Nom	Name	Nombre
Dose	Dose	Dose	Dosis	Dosis
Hora	Time	Heure	Uhrzeit	Hora
Data	Date	Date	Datum	Fecha
Escolher início	Choose start	Choisir le début	Beginn wählen	Elegir inicio
Escolher fim	Choose end	Choisir la fin	Ende wählen	Elegir fin
Escolher dias da semana	Choose weekdays	Choisir les jours de la semaine	Wochentage wählen	Elegir días de la semana
Adicionar data	Add date	Ajouter une date	Datum hinzufügen	Añadir fecha
Editar medicação	Edit medication	Modifier le médicament	Medikament bearbeiten	Editar medicación
Sem indicação	No indication	Sans indication	Keine Angabe	Sin indicación
Tomei	Taken	Pris	Eingenommen	Tomado
Tomas por confirmar	Doses to confirm	Prises à confirmer	Offene Einnahmen	Tomas por confirmar
Tomas confirmadas	Confirmed doses	Prises confirmées	Bestätigte Einnahmen	Tomas confirmadas
Registos	Records	Enregistrements	Einträge	Registros
Não existem tomas pendentes.	No pending doses.	Aucune prise en attente.	Keine offenen Einnahmen.	No hay tomas pendientes.
Nenhuma toma confirmada.	No confirmed doses.	Aucune prise confirmée.	Keine bestätigten Einnahmen.	No hay tomas confirmadas.
Confirmar toma	Confirm dose	Confirmer la prise	Einnahme bestätigen	Confirmar toma
Sim, tomei	Yes, I took it	Oui, je l’ai pris	Ja, eingenommen	Sí, la tomé
Marcações	Appointments	Rendez-vous	Termine	Citas
Agenda vazia	No appointments	Aucun rendez-vous	Keine Termine	Agenda vacía
Concluído	Completed	Terminé	Abgeschlossen	Completado
Pendente	Pending	En attente	Ausstehend	Pendiente
Hoje	Today	Aujourd’hui	Heute	Hoy
Amanhã	Tomorrow	Demain	Morgen	Mañana
Esta semana	This week	Cette semaine	Diese Woche	Esta semana
Módulos do ecrã principal	Home screen modules	Modules de l’accueil	Startseitenmodule	Módulos de la pantalla principal
Automático (seguir o telemóvel)	Automatic (follow phone)	Automatique (selon le téléphone)	Automatisch (wie das Handy)	Automático (seguir móvil)
Claro	Light	Clair	Hell	Claro
Escuro	Dark	Sombre	Dunkel	Oscuro
Utilizador	User	Utilisateur	Benutzer	Usuario
Utilizadores	Users	Utilisateurs	Benutzer	Usuarios
Abrir	Open	Ouvrir	Öffnen	Abrir
Fechar	Close	Fermer	Schließen	Cerrar
Partilhar	Share	Partager	Teilen	Compartir
Pesquisar	Search	Rechercher	Suchen	Buscar
Fotografias guardadas	Saved photos	Photos enregistrées	Gespeicherte Fotos	Fotos guardadas
Fotografia da embalagem	Package photo	Photo de l’emballage	Packungsfoto	Foto del envase
Ver imagem da embalagem	View package image	Voir l’image de la boîte	Packungsbild ansehen	Ver imagen del envase
Notificações de medicação	Medication notifications	Rappels de médicaments	Medikamentenmeldungen	Notificaciones de medicación
Perfil	Profile	Profil	Profil	Perfil
Mudar utilizador	Switch user	Changer d’utilisateur	Benutzer wechseln	Cambiar usuario
Ativar PIN	Enable PIN	Activer le PIN	PIN aktivieren	Activar PIN
Introduz o PIN	Enter PIN	Saisir le PIN	PIN eingeben	Introduce el PIN
Confirmar PIN atual	Confirm current PIN	Confirmer le PIN actuel	Aktuelle PIN bestätigen	Confirmar PIN actual
PIN ativado	PIN enabled	PIN activé	PIN aktiviert	PIN activado
Alterar PIN	Change PIN	Changer le PIN	PIN ändern	Cambiar PIN
Desativar PIN	Disable PIN	Désactiver le PIN	PIN deaktivieren	Desactivar PIN
Ativar impressão digital	Enable fingerprint	Activer l’empreinte digitale	Fingerabdruck aktivieren	Activar huella digital
Desbloquear com impressão digital	Unlock with fingerprint	Déverrouiller par empreinte	Mit Fingerabdruck entsperren	Desbloquear con huella
Entrar	Sign in	Entrer	Anmelden	Entrar
Sincronização familiar	Family synchronization	Synchronisation familiale	Familiensynchronisierung	Sincronización familiar
Desligar	Disconnect	Déconnecter	Trennen	Desconectar
PROCURAR	SEARCH	RECHERCHER	SUCHEN	BUSCAR
PARTILHAR	SHARE	PARTAGER	TEILEN	COMPARTIR
Códigos iguais	Codes match	Codes identiques	Codes stimmen überein	Códigos iguales
Recusar	Reject	Refuser	Ablehnen	Rechazar
Documentos clínicos	Medical documents	Documents médicaux	Medizinische Dokumente	Documentos clínicos
Análises clínicas	Lab results	Analyses médicales	Laborergebnisse	Análisis clínicos
Medicação e tomas	Medication and doses	Médicaments et prises	Medikamente und Einnahmen	Medicación y tomas
Fotografias das embalagens	Package photos	Photos des boîtes	Packungsfotos	Fotos de los envases
Dados pessoais e de identificação	Personal and identity data	Données personnelles et identité	Personen- und Ausweisdaten	Datos personales y de identidad
Idiomas	Languages	Langues	Sprachen	Idiomas
Escolher idioma da aplicação	Choose app language	Choisir la langue de l’application	App-Sprache auswählen	Elegir idioma de la aplicación
Português	Portuguese	Portugais	Portugiesisch	Portugués
Inglês	English	Anglais	Englisch	Inglés
Francês	French	Français	Französisch	Francés
Alemão	German	Allemand	Deutsch	Alemán
Espanhol	Spanish	Espagnol	Spanisch	Español
Ajuda	Help	Aide	Hilfe	Ayuda
Como usar a SaúdePrática, passo a passo	Learn SaúdePrática, step by step	Apprendre SaúdePrática pas à pas	SaúdePrática Schritt für Schritt	Aprende SaúdePrática paso a paso
Contactar suporte	Contact support	Contacter le support	Support kontaktieren	Contactar soporte
Pedir ajuda, sugerir melhorias ou comunicar erros	Ask for help, suggest improvements or report bugs	Demander de l’aide, suggérer des améliorations ou signaler des bugs	Hilfe, Verbesserungsvorschläge oder Fehler melden	Pedir ayuda, sugerir mejoras o informar errores
Apoiar o autor 🍺	Support the author 🍺	Soutenir l’auteur 🍺	Autor unterstützen 🍺	Apoyar al autor 🍺
Oferecer uma cerveja via PayPal (opcional)	Buy the author a beer via PayPal (optional)	Offrir une bière via PayPal (facultatif)	Dem Autor via PayPal ein Bier spendieren (freiwillig)	Invitar a una cerveza por PayPal (opcional)
""".trimIndent()
    private val catalog:Map<String,List<String>> by lazy {
        source.lines().mapNotNull { row ->
            val split=row.split('\t')
            if(split.size==5)split[0] to split.drop(1) else null
        }.toMap()
    }
    fun t(context:Context,input:String):String{
        val lang=codes.indexOf(code(context))
        if(lang<=0||input.isBlank())return input
        val exact=catalog[input]?.get(lang-1)
        if(exact!=null)return exact
        val components=input.trimStart()
        val prefix=input.substring(0,input.length-components.length)
        catalog[components]?.get(lang-1)?.let{return prefix+it}
        // Preserve pictograms while translating the short labels that follow.
        val match=Regex("""^([^\p{L}\p{N}]{1,5}\s*)(.+)$""").matchEntire(input)
        if(match!=null){
            val name=match.groupValues[2]
            catalog[name]?.get(lang-1)?.let{return match.groupValues[1]+it}
        }
        return input
    }
    private val attached=java.util.WeakHashMap<Activity,Boolean>()
    fun attach(activity:Activity){
        val root=activity.window.decorView
        if(attached.contains(activity))return
        attached[activity]=true
        val observer=root.viewTreeObserver
        observer.addOnGlobalLayoutListener(object:ViewTreeObserver.OnGlobalLayoutListener{
            override fun onGlobalLayout(){
                if(!activity.isFinishing && code(activity)!="pt")
                    translateTree(activity,root)
            }
        })
    }
    private fun translateTree(context:Context,view:View){
        if(view is TextInputLayout){
            val hint=view.hint?.toString()
            if(hint!=null){
                val t=t(context,hint)
                if(t!=hint)view.hint=t
            }
        }
        if(view is TextView){
            if(view !is EditText){
                val old=view.text?.toString().orEmpty()
                val translated=t(context,old)
                if(translated!=old)view.text=translated
            }
            if(view.hint!=null){
                val h=view.hint.toString()
                val n=t(context,h)
                if(n!=h)view.hint=n
            }
        }
        if(view is ViewGroup){
            for(i in 0 until view.childCount)translateTree(context,view.getChildAt(i))
        }
    }
}