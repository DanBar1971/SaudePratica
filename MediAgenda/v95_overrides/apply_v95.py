"""SaúdePrática 1.9.77: emergency contact calling and independent hydration/agenda reminders."""
from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"

def change(path,old,new,why):
    content=path.read_text(encoding="utf-8")
    count=content.count(old)
    if count!=1:
        raise RuntimeError(f"v95 {why}: expected 1 anchor, got {count}")
    path.write_text(content.replace(old,new,1),encoding="utf-8")

manifest=root/"app/src/main/AndroidManifest.xml"
change(manifest,
       '    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />',
       '    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />\n'
       '    <uses-permission android:name="android.permission.CALL_PHONE" />',
       "permission for user-requested calls")

helper=base/"EmergencyCallHelper.kt"
helper.write_text(r'''package com.mediagenda.app

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.widget.Toast
import androidx.core.content.ContextCompat
import com.mediagenda.app.data.PersonalHealthStore

/** Always use the selected person's contact; never call a hardcoded number. */
object EmergencyCallHelper {
    fun contactNumber(activity:Activity, profileId:String):String? {
        if(profileId.isBlank())return null
        val raw=runCatching{
            PersonalHealthStore(activity,profileId).emergencyValue("contact_phone")
        }.getOrDefault("")
        val safe=raw.filter { it.isDigit() || it=='+' }
        if(!Regex("""\+?[0-9]{3,20}""").matches(safe))return null
        return safe
    }

    /** Direct CALL only after explicit hold/tap and runtime permission.
     * If Android declines permission, open the dialer instead. */
    fun place(activity:Activity,number:String,permissionGranted:Boolean) {
        val safe=number.takeIf{Regex("""\+?[0-9]{3,20}""").matches(it)}
            ?:return
        val direct=permissionGranted &&
            ContextCompat.checkSelfPermission(activity,Manifest.permission.CALL_PHONE)==
                PackageManager.PERMISSION_GRANTED
        val action=if(direct)Intent.ACTION_CALL else Intent.ACTION_DIAL
        try{
            activity.startActivity(Intent(action,Uri.fromParts("tel",safe,null)))
            if(!direct)Toast.makeText(activity,
                "Confirma a chamada no marcador do telemóvel.",
                Toast.LENGTH_LONG).show()
        }catch(ex:Exception){
            Toast.makeText(activity,
                "Não foi possível abrir a chamada. Verifica a app Telefone.",
                Toast.LENGTH_LONG).show()
        }
    }
}
''',encoding="utf-8")

main=base/"MainActivity.kt"
change(main,
'''    private val notificationPermissionLauncher = registerForActivityResult(ActivityResultContracts.RequestPermission()) { }''',
'''    private var pendingEmergencyCall:String?=null
    private val emergencyPhonePermission=registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ){granted->
        val number=pendingEmergencyCall
        pendingEmergencyCall=null
        if(number!=null)EmergencyCallHelper.place(this,number,granted)
    }
    private fun callSelectedEmergencyContact(){
        val number=EmergencyCallHelper.contactNumber(this,activeProfileId)
        if(number==null){
            MaterialAlertDialogBuilder(this)
                .setTitle("Contacto de emergência não disponível")
                .setMessage("Preenche o telefone do contacto de emergência "+
                    "na ficha do perfil selecionado antes de usar esta opção.")
                .setPositiveButton("Abrir ficha"){_,_->healthRecords("emergency")}
                .setNegativeButton("Cancelar",null).show()
            return
        }
        if(ContextCompat.checkSelfPermission(this,Manifest.permission.CALL_PHONE)
            ==PackageManager.PERMISSION_GRANTED){
            EmergencyCallHelper.place(this,number,true)
        }else{
            pendingEmergencyCall=number
            emergencyPhonePermission.launch(Manifest.permission.CALL_PHONE)
        }
    }
    private val notificationPermissionLauncher = registerForActivityResult(ActivityResultContracts.RequestPermission()) { }''',
"hold-to-call runtime permission")
change(main,
'''            DashboardModule("🆘", "Emergência", "Alergias e contactos") { healthRecords("emergency") },''',
'''            DashboardModule("🆘", "Emergência", "Abrir ficha · manter 4 s para chamar") { healthRecords("emergency") },''',
"hold hint")
change(main,
'''                card.setOnClickListener { module.action() }
                row.addView(card,''',
'''                card.setOnClickListener { module.action() }
                if(module.title=="Emergência"){
                    val handler=android.os.Handler(android.os.Looper.getMainLooper())
                    var down=false
                    var fired=false
                    val threshold=android.view.ViewConfiguration.get(this).scaledTouchSlop
                    val call=Runnable{
                        if(down && !fired){
                            fired=true
                            card.performHapticFeedback(
                                android.view.HapticFeedbackConstants.LONG_PRESS)
                            callSelectedEmergencyContact()
                        }
                    }
                    card.contentDescription="Emergência. Toque para abrir a ficha; "+
                        "mantenha premido quatro segundos para ligar ao contacto."
                    card.setOnTouchListener{_,event->
                        when(event.actionMasked){
                            android.view.MotionEvent.ACTION_DOWN->{
                                down=true;fired=false
                                handler.postDelayed(call,4000L)
                                true
                            }
                            android.view.MotionEvent.ACTION_MOVE->{
                                if(event.x < -threshold ||
                                    event.y < -threshold ||
                                    event.x > card.width+threshold ||
                                    event.y > card.height+threshold){
                                    down=false;handler.removeCallbacks(call)
                                }
                                true
                            }
                            android.view.MotionEvent.ACTION_UP->{
                                handler.removeCallbacks(call)
                                val click=down && !fired
                                down=false
                                if(click)card.performClick()
                                true
                            }
                            android.view.MotionEvent.ACTION_CANCEL->{
                                down=false;handler.removeCallbacks(call);true
                            }
                            else->false
                        }
                    }
                }
                row.addView(card,''',
"4s hold emergency action")
change(main,
'''        // Check anonymous GitHub release metadata at most once every 12 hours.
        // Never interrupt medication scheduling or require permissions.''',
'''        // Restore water/appointment alarms after upgrades, restarts or
        // interrupted medication schedule rebuilds; do not cancel medication.
        if(::repo.isInitialized && profiles.all().isNotEmpty()){
            val restore=getSharedPreferences("saudepratica_other_reminder_repair",MODE_PRIVATE)
            val now=System.currentTimeMillis()
            if(now-restore.getLong("last_repair",0L)>30L*60L*1000L){
                restore.edit().putLong("last_repair",now).apply()
                Thread{
                    runCatching{
                        com.mediagenda.app.notifications.NotificationScheduler(
                            applicationContext).refreshOtherReminders()
                    }.onFailure{
                        android.util.Log.w("SaudePraticaReminders",
                            "Rearm on resume failed",it)
                    }
                }.start()
            }
        }
        // Check anonymous GitHub release metadata at most once every 12 hours.
        // Never interrupt medication scheduling or require permissions.''',
"automatic non-medication repair")
change(main,
'''        box.addView(secondaryButton("📅 Testar notificação de agendamento"){
            testHealthNotification("appointment")
        })''',
'''        box.addView(secondaryButton("📅 Testar notificação de agendamento"){
            testHealthNotification("appointment")
        })
        box.addView(secondaryButton("💧 Testar notificação de beber água"){
            testHealthNotification("water")
        })
        box.addView(secondaryButton("🔄 Reativar avisos de água e agenda"){
            Thread{
                val ok=runCatching{
                    NotificationScheduler(applicationContext).refreshOtherReminders()
                }.isSuccess
                runOnUiThread{
                    Toast.makeText(this,if(ok)
                        "Agenda e hidratação reagendadas. Verifica se os avisos "+
                        "de água estão ativos no respetivo perfil."
                        else "Não foi possível reagendar os avisos.",
                        Toast.LENGTH_LONG).show()
                }
            }.start()
        })''',
"test and repair appointment/water")
change(main,
'''        box.addView(noteBox("Agendamento",
            "Aviso da agenda, com som normal e vibração breve. "+
            "As marcações são lembradas às 18:00 do dia anterior."))''',
'''        box.addView(noteBox("Agendamento e água",
            "Os avisos de marcações usam um canal separado dos alarmes de "+
            "medicação. A água só é avisada quando ativada no módulo Beber água, "+
            "dentro do horário escolhido e antes de atingir a meta diária. "+
            "Os botões acima testam os dois canais sem registar nenhuma toma."))''',
"notification explanation")
change(main,
'''        val med=kind=="medication"
        NotificationReceiver().onReceive(this,''',
'''        val med=kind=="medication"
        val water=kind=="water"
        NotificationReceiver().onReceive(this,''',
"water test type")
change(main,
'''                putExtra("title",if(med)"💊 Teste do alarme de medicação"
                    else "📅 Teste do aviso de agendamento")
                putExtra("body",if(med)
                    "Este é um alarme de teste: não foi registada nenhuma toma."
                    else "Este é um aviso de teste, com som mais discreto.")
                putExtra("notification_id",if(med)991501 else 991502)''',
'''                putExtra("title",when{
                    med->"💊 Teste do alarme de medicação"
                    water->"💧 Teste do aviso de beber água"
                    else->"📅 Teste do aviso de agendamento"
                })
                putExtra("body",when{
                    med->"Este é um alarme de teste: não foi registada nenhuma toma."
                    water->"Este teste não regista água. Os avisos reais "+
                        "incluem o botão Copo de água tomado."
                    else->"Este é um aviso de teste, com som mais discreto."
                })
                putExtra("demo_notice",true)
                putExtra("notification_id",if(med)991501 else if(water)991504 else 991502)''',
"water test payload")

health=base/"HealthRecordsActivity.kt"
change(health,
'''    private var pendingEmergencyPhone:EditText?=null''',
'''    private var pendingEmergencyPhone:EditText?=null
    private var pendingEmergencyDial:String?=null
    private val emergencyCallPermission=registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ){granted->
        val number=pendingEmergencyDial
        pendingEmergencyDial=null
        if(number!=null)EmergencyCallHelper.place(this,number,granted)
    }
    private fun callEmergencyPhone(){
        val number=EmergencyCallHelper.contactNumber(this,profileId)
        if(number==null){
            alert("Adiciona um telefone válido na Ficha de Emergência.")
            return
        }
        if(ContextCompat.checkSelfPermission(this,android.Manifest.permission.CALL_PHONE)
            ==android.content.pm.PackageManager.PERMISSION_GRANTED){
            EmergencyCallHelper.place(this,number,true)
        }else{
            pendingEmergencyDial=number
            emergencyCallPermission.launch(android.Manifest.permission.CALL_PHONE)
        }
    }''',
"emergency phone button")
change(health,
'''            box.addView(label(caption,14f,true))
            box.addView(label(store.emergencyValue(key).ifBlank{"Por preencher"},13f,color=muted))
            shell.addView(box);addCard(shell)''',
'''            if(key=="contact_phone"){
                val line=LinearLayout(this).apply{
                    orientation=LinearLayout.HORIZONTAL
                    gravity=Gravity.CENTER_VERTICAL
                }
                val words=LinearLayout(this).apply{
                    orientation=LinearLayout.VERTICAL
                    addView(label(caption,14f,true))
                    addView(label(store.emergencyValue(key)
                        .ifBlank{"Por preencher"},13f,color=muted))
                }
                line.addView(words,LinearLayout.LayoutParams(
                    0,ViewGroup.LayoutParams.WRAP_CONTENT,1f))
                line.addView(button("📞 CHAMAR"){callEmergencyPhone()})
                box.addView(line)
            }else{
                box.addView(label(caption,14f,true))
                box.addView(label(store.emergencyValue(key)
                    .ifBlank{"Por preencher"},13f,color=muted))
            }
            shell.addView(box);addCard(shell)''',
"call beside telephone")

scheduler=base/"notifications/NotificationScheduler.kt"
change(scheduler,
'''        cancelRegistered()
        val profiles = ProfileStore(context).all()
        profiles.forEach { profile ->
            val data = runCatching {
                val repository = DataRepository(context, profile.id)
                repository.loadMedications() to repository.loadAppointments()
            }.getOrNull() ?: return@forEach
            data.first.forEach { scheduleNextMedication(it, profile.id, profile.name, profiles.size > 1) }
            data.second.forEach { scheduleAppointment(it, profile.id, profile.name, profiles.size > 1) }
            scheduleNextWater(profile.id)
            scheduleNextPill(profile.id)
        }
    }''',
'''        // Medication failures must never starve water and appointments.
        runCatching{cancelRegistered()}.onFailure{
            android.util.Log.e("SaudePraticaReminders","Cancel old reminders",it)
        }
        val profiles = ProfileStore(context).all()
        profiles.forEach { profile ->
            val data = runCatching {
                val repository = DataRepository(context, profile.id)
                repository.loadMedications() to repository.loadAppointments()
            }.onFailure{
                android.util.Log.e("SaudePraticaReminders",
                    "Read appointments/medication for profile",it)
            }.getOrNull()
            data?.first?.forEach{ med ->
                runCatching{scheduleNextMedication(med,profile.id,
                    profile.name,profiles.size>1)}
                    .onFailure{android.util.Log.e("SaudePraticaReminders",
                        "Medication scheduling failed",it)}
            }
            data?.second?.forEach{ appointment ->
                runCatching{scheduleAppointment(appointment,profile.id,
                    profile.name,profiles.size>1)}
                    .onFailure{android.util.Log.e("SaudePraticaReminders",
                        "Appointment scheduling failed",it)}
            }
            runCatching{scheduleNextWater(profile.id)}.onFailure{
                android.util.Log.e("SaudePraticaReminders",
                    "Water scheduling failed",it)
            }
            runCatching{scheduleNextPill(profile.id)}.onFailure{
                android.util.Log.e("SaudePraticaReminders",
                    "Pill scheduling failed",it)
            }
        }
    }

    /** Re-arm non-medication reminders without cancelling ongoing alarms.
     * Used on app resume after an OS update, process death or partial rebuild.
     */
    fun refreshOtherReminders(){
        val profiles=ProfileStore(context).all()
        profiles.forEach{profile->
            runCatching{
                DataRepository(context,profile.id).loadAppointments().forEach{
                    scheduleAppointment(it,profile.id,profile.name,profiles.size>1)
                }
            }.onFailure{android.util.Log.e("SaudePraticaReminders",
                "Appointment recovery",it)}
            runCatching{scheduleNextWater(profile.id)}
                .onFailure{android.util.Log.e("SaudePraticaReminders",
                    "Water recovery",it)}
            runCatching{scheduleNextPill(profile.id)}
                .onFailure{android.util.Log.e("SaudePraticaReminders",
                    "Pill recovery",it)}
        }
    }''',
"scheduler isolation and recovery")

receiver=base/"notifications/NotificationReceiver.kt"
change(receiver,
'''            val isWater=intent.getStringExtra("reminder_kind")=="water"
            if (isWater) {''',
'''            val isWater=intent.getStringExtra("reminder_kind")=="water"
            val demoNotice=intent.getBooleanExtra("demo_notice",false)
            if (isWater && !demoNotice) {''',
"water test bypass")
change(receiver,
'''                isAppointment->"saudepratica_appointments_quiet_v1"
                isMedication->"saudepratica_medication_alarm_v3"''',
'''                isAppointment->"saudepratica_appointments_quiet_v1"
                isWater->"saudepratica_water_reminders_v2"
                isMedication->"saudepratica_medication_alarm_v3"''',
"separate water channel")
change(receiver,
'''            }else if(isMedication){
                val tone=RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM)''',
'''            }else if(isWater){
                NotificationChannel(channelId,"Beber água — lembretes",
                    NotificationManager.IMPORTANCE_DEFAULT).apply{
                    description="Lembretes opcionais de hidratação, independentes "+
                        "dos alarmes de medicação"
                    val tone=RingtoneManager.getDefaultUri(
                        RingtoneManager.TYPE_NOTIFICATION)
                    if(tone!=null)setSound(tone,AudioAttributes.Builder()
                        .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                        .setUsage(AudioAttributes.USAGE_NOTIFICATION_EVENT).build())
                    enableVibration(true)
                    vibrationPattern=longArrayOf(0,200)
                    lockscreenVisibility=android.app.Notification.VISIBILITY_PRIVATE
                }
            }else if(isMedication){
                val tone=RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM)''',
"water channel independent of medical alarms")
change(receiver,
'''                .setCategory(if(isAppointment)NotificationCompat.CATEGORY_EVENT
                    else NotificationCompat.CATEGORY_ALARM)''',
'''                .setCategory(if(isAppointment)NotificationCompat.CATEGORY_EVENT
                    else if(isWater)NotificationCompat.CATEGORY_REMINDER
                    else NotificationCompat.CATEGORY_ALARM)''',
"water notification category")
change(receiver,
'''                    else if(isMedication)NotificationCompat.PRIORITY_MAX
                    else NotificationCompat.PRIORITY_DEFAULT)''',
'''                    else if(isMedication)NotificationCompat.PRIORITY_MAX
                    else NotificationCompat.PRIORITY_DEFAULT)''',
"no op") if False else None

wellness=base/"WellnessActivity.kt"
change(wellness,
'''        card(content, "🔔 Avisos para beber água", status, "Configurar avisos") { configureWater() }''',
'''        card(content, "🔔 Avisos para beber água", status, "Configurar avisos") { configureWater() }
        card(content, "🛠️ Verificar lembretes",
            "Reativa o próximo aviso deste perfil, sem alterar as horas nem "+
            "os medicamentos.", "Reagendar água") {
            runCatching{NotificationScheduler(this).scheduleNextWater(profileId)}
                .onSuccess{Toast.makeText(this,
                    "Próximo aviso de água atualizado. Confirma as notificações do "+
                    "telemóvel e o horário configurado.",Toast.LENGTH_LONG).show()}
                .onFailure{Toast.makeText(this,
                    "Não foi possível reagendar: "+it.message,Toast.LENGTH_LONG).show()}
            showWater()
        }''',
"water self-service repair")

help=base/"SupportHelpActivity.kt"
change(help,
'''        val updateGuide=panel()''',
'''        val emergencyAndReminders=panel()
        emergencyAndReminders.addView(text(tr(
            "🆘 Emergência e avisos de água",
            "🆘 Emergency calls and water reminders",
            "🆘 Appels d'urgence et rappels d'eau",
            "🆘 Notrufkontakt und Wassererinnerungen",
            "🆘 Contactos de emergencia y avisos de agua"),18f))
        emergencyAndReminders.addView(text(tr(
            "No menu principal, mantém Emergência premido 4 segundos para ligar ao contacto guardado no perfil atual; um toque normal abre a ficha. Na Ficha de Emergência, usa CHAMAR junto do telefone. O Android pede permissão para chamadas diretas; sem permissão, abre o marcador. Em Beber água, configura e reativa os avisos. Em Opções → Notificações, testa separadamente os avisos de água e de agenda e reativa ambos sem mexer nos alarmes dos medicamentos.",
            "Hold Emergency on the home screen for 4 seconds to call the selected profile's saved contact; tap normally to open the card. In the card, use CALL beside the phone number. Android asks permission for a direct call; otherwise the dialer opens. Set water reminders under Drink water. In Options → Notifications, test water and appointment notices independently.",
            "Maintenez Urgence 4 secondes pour appeler le contact du profil actif. Un appui normal ouvre la fiche; APPELER est disponible près du numéro. Android demande l'autorisation d'appeler; sinon le clavier téléphonique s'ouvre. Testez séparément les rappels d'eau et de rendez-vous dans Options → Notifications.",
            "Notfall auf dem Startbildschirm 4 Sekunden halten, um den gespeicherten Kontakt des aktiven Profils anzurufen. Einfach antippen öffnet die Karte mit ANRUFEN. Android fordert die Anrufberechtigung an, sonst öffnet sich die Telefon-App. Wasser- und Terminerinnerungen lassen sich in Optionen → Benachrichtigungen getrennt testen.",
            "Mantén pulsado Emergencia 4 segundos para llamar al contacto guardado del perfil activo. Un toque normal abre la ficha, donde aparece LLAMAR junto al teléfono. Android pide permiso para llamar; si se deniega, abre el marcador. Prueba por separado los avisos de agua y citas en Opciones → Notificaciones."
        ),14f,muted))
        addCard(parent,emergencyAndReminders)
        val updateGuide=panel()''',
"5 language help")

gradle=root/"app/build.gradle.kts"
change(gradle,"versionCode = 86","versionCode = 87","versionCode")
change(gradle,'versionName = "1.9.76"','versionName = "1.9.77"',"versionName")
print("v1.9.77: independent water/appointment reminders and four-second emergency contact call")
