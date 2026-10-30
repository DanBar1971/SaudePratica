"""SaúdePrática 1.9.69: timed alarm, preferences, safe demo, ignored doses."""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
def change(p,a,b,label):
 s=p.read_text()
 if s.count(a)!=1:raise RuntimeError(f"v87 {label}: expected 1 anchor, found {s.count(a)}")
 p.write_text(s.replace(a,b,1))
(base/"notifications/MedicationAlarmPreferences.kt").write_text("""package com.mediagenda.app.notifications
import android.content.Context
import com.mediagenda.app.i18n.AppLanguage
import java.util.Locale
object MedicationAlarmPreferences {
 fun settings(c:Context)=c.getSharedPreferences("saudepratica_alarm_settings_v1",Context.MODE_PRIVATE)
 fun mode(c:Context)=settings(c).getString("mode","both")?:"both"
 fun vibration(c:Context)=settings(c).getBoolean("vibration",true)
 fun voice(c:Context)=settings(c).getString("voice","system")?:"system"
 fun seconds(c:Context)=settings(c).getInt("seconds",60).coerceIn(30,120).toLong()
 fun language(c:Context):Locale {
  val chosen=settings(c).getString("language","auto")?:"auto"
  return when(if(chosen=="auto")AppLanguage.code(c) else chosen){
   "en"->Locale.ENGLISH;"fr"->Locale.FRENCH;"de"->Locale.GERMAN
   "es"->Locale("es","ES");else->Locale("pt","PT")
  }
 }
}
""")
p=base/"notifications/MedicationAlarmService.kt"
change(p,"import com.mediagenda.app.data.ProfileStore","import com.mediagenda.app.data.ProfileStore\nimport com.mediagenda.app.data.PersonalHealthStore","import")
change(p,'        const val ACTION_SNOOZE = "com.mediagenda.app.MED_ALARM_SNOOZE"','''        const val ACTION_SNOOZE = "com.mediagenda.app.MED_ALARM_SNOOZE"
        const val ACTION_TIMEOUT = "com.mediagenda.app.MED_ALARM_TIMEOUT"
        const val EXTRA_DEMO = "alarm_demo"''',"actions")
change(p,"    private var speechSession = 0",'''    private var speechSession = 0
    private var activeProfile = ""
    private var activeMedication = ""
    private var activeScheduledAt = 0L
    private var demo = false
    private var expiry: Runnable? = null
    private val expiryHandler = Handler(Looper.getMainLooper())
    private fun timeoutAlarm() {
        if(!demo && activeProfile.isNotBlank() && activeMedication.isNotBlank() &&
            activeScheduledAt>0L) {
            runCatching {
                PersonalHealthStore(this,activeProfile).noteIgnoredAlarm(
                    activeMedication,activeScheduledAt)
                IntakeBadgeManager.refresh(this,activeProfile)
            }.onFailure{android.util.Log.e("SaudePraticaAlarm","Ignored log",it)}
        }
        sendBroadcast(Intent(ACTION_TIMEOUT).setPackage(packageName))
        silence()
        getSystemService(NotificationManager::class.java).cancel(currentId)
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }
    private fun startTimeout() {
        expiry?.let{expiryHandler.removeCallbacks(it)}
        expiry=Runnable{timeoutAlarm()}.also{
            expiryHandler.postDelayed(it,MedicationAlarmPreferences.seconds(this)*1000L)
        }
    }''',"timeout")
change(p,'''        val words = "Alarme de medicação. Está na hora de tomar $name. " +
            (if(dose.isNotBlank()) "Dose: $dose. " else "") +
            "Por favor, confirme a toma na SaúdePrática."''','''        val locale=MedicationAlarmPreferences.language(this)
        val words=when(locale.language){
            "en"->"Medication alarm. It is time to take $name. "+
                (if(dose.isNotBlank())"Dose: $dose. " else "")+"Please confirm your dose."
            "fr"->"Alarme de médicament. Il est temps de prendre $name. "+
                (if(dose.isNotBlank())"Dose : $dose. " else "")+"Veuillez confirmer la prise."
            "de"->"Medikamentenalarm. Es ist Zeit für $name. "+
                (if(dose.isNotBlank())"Dosis: $dose. " else "")+"Bitte bestätigen Sie die Einnahme."
            "es"->"Alarma de medicación. Es hora de tomar $name. "+
                (if(dose.isNotBlank())"Dosis: $dose. " else "")+"Confirma la toma."
            else->"Alarme de medicação. Está na hora de tomar $name. "+
                (if(dose.isNotBlank())"Dose: $dose. " else "")+
                "Por favor, confirme a toma na SaúdePrática."
        }''',"spoken translations")
change(p,'                val portuguese = Locale("pt", "PT")\n                val result = engine.setLanguage(portuguese)','''                val preferred=MedicationAlarmPreferences.language(this@MedicationAlarmService)
                val result=engine.setLanguage(preferred)''',"locale")
change(p,"                engine.setSpeechRate(0.87f)",'''                val preference=MedicationAlarmPreferences.voice(this@MedicationAlarmService)
                if(preference!="system"){
                    val voices=engine.voices.orEmpty().filter{
                        it.locale.language==preferred.language && !it.isNetworkConnectionRequired
                    }
                    val match=voices.firstOrNull{v->
                        val label=v.name.lowercase(Locale.ROOT)
                        if(preference=="female")
                            listOf("female","woman","fem","mulher").any{label.contains(it)}
                        else listOf("male","man","masc","homem").any{label.contains(it)}
                    }
                    if(match!=null)engine.voice=match
                }
                engine.setSpeechRate(0.87f)''',"voice preference")
change(p,'''                runCatching { player?.stop(); player?.release() }
                player = null
                repeatSpeech = repeat''','''                if(MedicationAlarmPreferences.mode(this@MedicationAlarmService)=="voice"){
                    runCatching { player?.stop(); player?.release() }
                    player=null
                }
                repeatSpeech=repeat''',"ringtone + voice")
change(p,'        val profileId = intent.getStringExtra("profile_id").orEmpty()','''        demo=intent.getBooleanExtra(EXTRA_DEMO,false)
        val profileId=intent.getStringExtra("profile_id").orEmpty()''',"demo")
change(p,'''        if (profileId.isBlank() || medicationId.isBlank() || scheduledAt <= 0L ||
            ProfileStore(this).all().none { it.id == profileId }) {''','''        if ((!demo && (profileId.isBlank() || medicationId.isBlank() || scheduledAt<=0L)) ||
            ProfileStore(this).all().none{it.id==profileId}) {''',"demo validation")
change(p,'''        val med = DataRepository(this, profileId).loadMedications().firstOrNull {
            it.id == medicationId
        } ?: run { stopSelf(); return START_NOT_STICKY }
        currentId = intent.getIntExtra("notification_id", 990100)''','''        val med=if(demo)null else DataRepository(this,profileId).loadMedications()
            .firstOrNull{it.id==medicationId}
        if(!demo && med==null){stopSelf();return START_NOT_STICKY}
        activeProfile=profileId;activeMedication=medicationId;activeScheduledAt=scheduledAt
        currentId=intent.getIntExtra("notification_id",990100)''',"demo medicine")
change(p,'        val title = (profileName.ifBlank { "SaúdePrática" }) + " · " + med.medication','''        val drugName=med?.medication?:"Medicamento de teste"
        val doseText=med?.dose.orEmpty()
        val title=(profileName.ifBlank{"SaúdePrática"})+" · "+drugName''',"name")
change(p,'            .setContentText("ALARME DE MEDICAÇÃO · " + med.dose)','            .setContentText("ALARME DE MEDICAÇÃO · " + doseText)',"dose")
change(p,'''            .addAction(android.R.drawable.ic_media_pause, "ADIAR 10 MIN", snoozePi)
            .addAction(android.R.drawable.checkbox_on_background, "✓ TOMEI", takenPi)
        MedicationPhotoLoader.load(this, med.images, 780)?.let { photo ->''','''        if(demo)n.addAction(android.R.drawable.ic_media_pause,"PARAR TESTE",snoozePi)
        else{
            n.addAction(android.R.drawable.ic_media_pause,"ADIAR 10 MIN",snoozePi)
            n.addAction(android.R.drawable.checkbox_on_background,"✓ TOMEI",takenPi)
        }
        med?.let{MedicationPhotoLoader.load(this,it.images,780)}?.let{photo->''',"demo actions and photo")
change(p,'        announce(med.medication, med.dose)','''        startTimeout()
        if(MedicationAlarmPreferences.mode(this)!="tone")announce(drugName,doseText)''',"voice mode and timer")
change(p,'        try {\n            val pattern = longArrayOf(0, 750, 400, 750, 900)','''        if(MedicationAlarmPreferences.vibration(this))try {
            val pattern = longArrayOf(0, 750, 400, 750, 900)''',"vibration")
change(p,"    private fun silence() {\n        ++speechSession",'''    private fun silence() {
        expiry?.let{expiryHandler.removeCallbacks(it)}
        expiry=null
        ++speechSession''',"silence expiry")
change(p,"class MedicationAlarmActivity : Activity() {\n    private fun dp",'''class MedicationAlarmActivity : Activity() {
    private var timeoutListener:BroadcastReceiver?=null
    override fun onDestroy(){
        timeoutListener?.let{runCatching{unregisterReceiver(it)}}
        super.onDestroy()
    }
    private fun dp''',"activity receiver")
change(p,'        val medicine = DataRepository(this, profile).loadMedications().firstOrNull { it.id == medId }','''        val demo=intent.getBooleanExtra(MedicationAlarmService.EXTRA_DEMO,false)
        val medicine=if(demo)null else DataRepository(this,profile).loadMedications()
            .firstOrNull{it.id==medId}''',"activity demo")
change(p,'        layout.addView(label(medicine?.medication ?: "Medicação", 29f))','''        layout.addView(label(medicine?.medication?:if(demo)"Medicamento de teste" else "Medicação",29f))''',"activity name")
change(p,'        layout.addView(label("O alarme só termina quando escolheres uma ação.", 17f))','''        layout.addView(label("O alarme termina após "+
            MedicationAlarmPreferences.seconds(this)+
            " segundos. Sem resposta, fica por confirmar.",17f))''',"activity explanation")
change(p,'        layout.addView(control("ADIAR 10 MIN", Color.rgb(42, 89, 111)) {','''        val timeoutReceiver=object:BroadcastReceiver(){
            override fun onReceive(c:Context,i:Intent){
                if(i.action==MedicationAlarmService.ACTION_TIMEOUT)finish()
            }
        }
        ContextCompat.registerReceiver(this,timeoutReceiver,
            IntentFilter(MedicationAlarmService.ACTION_TIMEOUT),
            ContextCompat.RECEIVER_NOT_EXPORTED)
        timeoutListener=timeoutReceiver
        layout.addView(control(if(demo)"PARAR TESTE" else "ADIAR 10 MIN",
            Color.rgb(42,89,111)){
            if(demo){
                MedicationAlarmService.stop(this,intent.getIntExtra("notification_id",0))
                finish();return@control
            }''',"activity stop demo")
change(p,'        layout.addView(control("✓ TOMEI", Color.rgb(0, 125, 102)) {','''        if(!demo)layout.addView(control("✓ TOMEI",Color.rgb(0,125,102)){''',"activity no demo confirm")
change(p,'        if (profile.isBlank() || medId.isBlank() || whenOriginal <= 0L) return','''        if(intent.getBooleanExtra(MedicationAlarmService.EXTRA_DEMO,false)){
            MedicationAlarmService.stop(context,intent.getIntExtra("notification_id",0));return
        }
        if (profile.isBlank() || medId.isBlank() || whenOriginal <= 0L) return''',"demo snooze")
p=base/"data/PersonalHealthStore.kt"
change(p,'"intakes", "pending_intakes", "deleted_intakes")','"intakes", "pending_intakes", "deleted_intakes", "ignored_intakes")',"ignored kind")
change(p,'    /** An unconfirmed reminder becomes overdue after a 15-minute grace period.','''    fun noteIgnoredAlarm(medicationId:String,scheduledAt:Long){
        if(medicationId.isBlank()||scheduledAt<=0L)return
        synchronized(intakeLock){
            val key=scheduledAt.toString()
            if(list("intakes").any{it.fields["medication_id"]==medicationId &&
                it.fields["scheduled_at"]==key})return
            if(list("ignored_intakes").any{it.fields["medication_id"]==medicationId &&
                it.fields["scheduled_at"]==key})return
            add("ignored_intakes","Alarme ignorado",mapOf(
                "medication_id" to medicationId,"scheduled_at" to key,
                "status" to "no_interaction"))
        }
    }
    fun ignoredAlarmKeys():Set<String> = list("ignored_intakes").map{
        it.fields["medication_id"].orEmpty()+"|"+it.fields["scheduled_at"].orEmpty()
    }.toSet()

    /** An unconfirmed reminder becomes overdue after a 15-minute grace period.''',"ignored log")
p=base/"HealthRecordsActivity.kt"
change(p,'        val checked=confirmed.mapNotNull{','''        val ignoredKeys=store.ignoredAlarmKeys()
        val checked=confirmed.mapNotNull{''',"ignored lookup")
change(p,'                column.addView(label("⚠️ Por confirmar desde "+whenText,13f,','''                val ignored=PersonalHealthStore(this,person.id).ignoredAlarmKeys()
                if(item.fields["medication_id"].orEmpty()+"|"+due in ignored)
                    column.addView(label("🔕 Alarme ignorado — sem resposta",13f,
                        color=Color.rgb(255,171,105)))
                column.addView(label("⚠️ Por confirmar desde "+whenText,13f,''',"caregiver status")
change(p,'            column.addView(label(if(item.id in overdue) "⚠️ Atrasada · por confirmar"','''            if(item.fields["medication_id"].orEmpty()+"|"+whenDue in ignoredKeys)
                column.addView(label("🔕 Alarme ignorado — toma por confirmar",12f,
                    color=Color.rgb(255,171,105)))
            column.addView(label(if(item.id in overdue) "⚠️ Atrasada · por confirmar"''',"patient status")
p=base/"MainActivity.kt"
change(p,'        box.addView(secondaryButton("💊 Testar alarme de medicação"){\n            testHealthNotification("medication")','''        box.addView(secondaryButton("💊 Testar alarme de medicação"){
            testRealMedicationAlarm()''',"real test")
change(p,'''        box.addView(noteBox("Medicação",
            "Alarme forte, separado das notificações da agenda. "+
            "Nos avisos reais, expande a notificação e toca em ✓ TOMEI "+
            "depois de tomares. O teste usa ✓ TOMEI (TESTE) sem registar medicação."))''','''        box.addView(noteBox("Medicação",
            "O teste abre o ecrã real sem registar tomas. Sem resposta, "+
            "o alarme pára e fica por confirmar."))
        box.addView(secondaryButton("⚙ Configurar alarmes: som, voz e idioma"){
            showMedicationAlarmSettings()
        })''',"settings button")
change(p,'    private fun testHealthNotification(kind:String){','''    private fun showMedicationAlarmSettings(){
        val p=com.mediagenda.app.notifications.MedicationAlarmPreferences.settings(this)
        val modes=arrayOf("Toque","Toque + voz","Apenas voz")
        val modeKeys=arrayOf("tone","both","voice")
        val langs=arrayOf("Automático (idioma da app)","Português","English",
            "Français","Deutsch","Español")
        val langKeys=arrayOf("auto","pt","en","fr","de","es")
        val voices=arrayOf("Predefinida Android","Feminina","Masculina")
        val voiceKeys=arrayOf("system","female","male")
        val durations=arrayOf("30 segundos","60 segundos","120 segundos")
        val durationKeys=intArrayOf(30,60,120)
        val box=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(20),dp(8),dp(20),0)
        }
        fun selector(title:String,options:Array<String>,selected:Int,onPick:(Int)->Unit){
            val index=selected.coerceIn(0,options.lastIndex)
            val button=secondaryButton(title+" · "+options[index]){}
            button.setOnClickListener{
                MaterialAlertDialogBuilder(this).setTitle(title)
                    .setSingleChoiceItems(options,index){d,i->
                        onPick(i);d.dismiss();showMedicationAlarmSettings()
                    }.setNegativeButton("Cancelar",null).show()
            }
            box.addView(button)
        }
        selector("Som",modes,modeKeys.indexOf(p.getString("mode","both"))){
            p.edit().putString("mode",modeKeys[it]).apply()
        }
        box.addView(android.widget.CheckBox(this).apply{
            text="Vibração durante o alarme"
            isChecked=p.getBoolean("vibration",true)
            setOnCheckedChangeListener{_,value->
                p.edit().putBoolean("vibration",value).apply()
            }
        })
        selector("Idioma",langs,langKeys.indexOf(p.getString("language","auto"))){
            p.edit().putString("language",langKeys[it]).apply()
        }
        selector("Voz",voices,voiceKeys.indexOf(p.getString("voice","system"))){
            p.edit().putString("voice",voiceKeys[it]).apply()
        }
        selector("Duração",durations,durationKeys.indexOf(p.getInt("seconds",60))){
            p.edit().putInt("seconds",durationKeys[it]).apply()
        }
        MaterialAlertDialogBuilder(this).setTitle("⚙ Alarme de medicação")
            .setView(box).setPositiveButton("Concluído",null).show()
    }
    private fun testRealMedicationAlarm(){
        if(Build.VERSION.SDK_INT>=33 &&
            ContextCompat.checkSelfPermission(this,Manifest.permission.POST_NOTIFICATIONS)
                !=PackageManager.PERMISSION_GRANTED){
            requestNotificationPermission()
            Toast.makeText(this,"Autoriza as notificações e repete o teste.",
                Toast.LENGTH_LONG).show()
            return
        }
        val demo=Intent(this,com.mediagenda.app.notifications.MedicationAlarmActivity::class.java).apply{
            putExtra("profile_id",activeProfileId)
            putExtra("medication_id","demo")
            putExtra("scheduled_at",System.currentTimeMillis())
            putExtra("notification_id",991503)
            putExtra(com.mediagenda.app.notifications.MedicationAlarmService.EXTRA_DEMO,true)
        }
        com.mediagenda.app.notifications.MedicationAlarmService.start(this,demo)
        startActivity(demo)
    }

    private fun testHealthNotification(kind:String){''',"settings UI")
p=root/"app/build.gradle.kts"
change(p,"versionCode = 78","versionCode = 79","code")
change(p,'versionName = "1.9.68"','versionName = "1.9.69"',"name")
print("SaúdePrática 1.9.69 applied")
exec(compile(Path("MediAgenda/v88_overrides/apply_v88.py").read_text(encoding="utf-8"),"MediAgenda/v88_overrides/apply_v88.py","exec"))
