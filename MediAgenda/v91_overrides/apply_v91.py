"""SaudePratica v1.9.73: alarms belong to active profile and show caregiver markers."""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
def change(path,old,new,why):
 s=path.read_text(encoding="utf-8")
 if s.count(old)!=1:raise RuntimeError("v91 "+why+" anchor "+str(s.count(old)))
 path.write_text(s.replace(old,new,1),encoding="utf-8")
receiver=base/"notifications/NotificationReceiver.kt"
change(receiver,'''            if(!medicationId.isNullOrBlank() && scheduledDoseAt>0L &&
                ProfileStore(context).all().any{it.id==profileId}){
                val manager=context.getSystemService(NotificationManager::class.java)''','''            if(!medicationId.isNullOrBlank() && scheduledDoseAt>0L &&
                ProfileStore(context).all().any{it.id==profileId}){
                val selected=context.getSharedPreferences(
                    "saudepratica_intake_badge_v1",Context.MODE_PRIVATE)
                    .getString("current_profile",null)
                if(!selected.isNullOrBlank() && selected!=profileId){
                    // Other profiles remain visible to the caregiver as pending
                    // but may never trigger the current patient's spoken alarm.
                    runCatching{
                        val other=DataRepository(context,profileId)
                            .loadMedications().firstOrNull{it.id==medicationId}
                        if(other!=null){
                            PersonalHealthStore(context,profileId).noteReminder(
                                other.id,other.medication.ifBlank{"Medicação"},scheduledDoseAt)
                            IntakeBadgeManager.scheduleCheck(context,profileId,
                                other.id,scheduledDoseAt)
                        }
                    }.onFailure{android.util.Log.w("SaudePraticaAlarm",
                        "Could not note other profile dose",it)}
                    return
                }
                val manager=context.getSystemService(NotificationManager::class.java)''',"silent family scheduled")
alarm=base/"notifications/MedicationAlarmService.kt"
change(alarm,'''        if(!demo && med==null){stopSelf();return START_NOT_STICKY}
        activeProfile=profileId;activeMedication=medicationId;activeScheduledAt=scheduledAt''','''        if(!demo && med==null){stopSelf();return START_NOT_STICKY}
        val selected=getSharedPreferences("saudepratica_intake_badge_v1",MODE_PRIVATE)
            .getString("current_profile",null)
        if(!demo && !selected.isNullOrBlank() && selected!=profileId){
            stopSelf();return START_NOT_STICKY
        }
        activeProfile=profileId;activeMedication=medicationId;activeScheduledAt=scheduledAt''',"service profile guard")
change(alarm,'''    private fun announce(name: String, dose: String) {
        val session''','''    private fun announce(name: String, dose: String, patient: String) {
        val session''',"voice signature")
change(alarm,'''        val words=when(locale.language){
            "en"->"Medication alarm. It is time to take $name. "+''','''        val recipient=patient.ifBlank{"SaúdePrática"}
        val words=when(locale.language){
            "en"->"Medication alarm for $recipient. It is time to take $name. "+''',"EN recipient")
change(alarm,'''            "fr"->"Alarme de médicament. Il est temps de prendre $name. "+''','''            "fr"->"Alarme de médicament pour $recipient. Il est temps de prendre $name. "+''',"FR recipient")
change(alarm,'''            "de"->"Medikamentenalarm. Es ist Zeit für $name. "+''','''            "de"->"Medikamentenalarm für $recipient. Es ist Zeit für $name. "+''',"DE recipient")
change(alarm,'''            "es"->"Alarma de medicación. Es hora de tomar $name. "+''','''            "es"->"Alarma de medicación para $recipient. Es hora de tomar $name. "+''',"ES recipient")
change(alarm,'''            else->"Alarme de medicação. Está na hora de tomar $name. "+''','''            else->"Alarme de medicação para $recipient. Está na hora de tomar $name. "+''',"PT recipient")
change(alarm,'''        if(MedicationAlarmPreferences.mode(this)!="tone")announce(drugName,doseText)''','''        if(MedicationAlarmPreferences.mode(this)!="tone")
            announce(drugName,doseText,profileName)''',"spoken profile")
main=base/"MainActivity.kt"
change(main,'''        available.forEach { profile ->
            val card=materialCard(stroke=border,bg=surface,radius=19f,elevation=1f)''','''        val caregiverId=getSharedPreferences("saudepratica_caregiver_v1",MODE_PRIVATE)
            .getString("caregiver_id",null)
        available.forEach { profile ->
            val isCaregiver=profile.id==caregiverId
            val card=materialCard(stroke=border,bg=surface,radius=19f,elevation=1f)''',"profile selection")
change(main,'''            words.addView(TextView(this).apply{
                text=profile.name
                textSize=18f''','''            words.addView(TextView(this).apply{
                text=profile.name+(if(isCaregiver)"  🤲" else "")
                textSize=18f''',"caregiver hand badge")
change(main,'''                text=fullName.ifBlank{"Abrir este perfil"}
                textSize=13f''','''                text=if(isCaregiver)
                    "🤲 Cuidador da família · "+fullName.ifBlank{"Abrir este perfil"}
                    else fullName.ifBlank{"Abrir este perfil"}
                textSize=13f''',"caregiver caption")
change(main,'''    private fun showProfileDialog(firstRun: Boolean) {
        val prefs = getSharedPreferences(profiles.preferencesFor(activeProfileId), MODE_PRIVATE)''','''    private fun showProfileDialog(firstRun: Boolean) {
        val caregiverPrefs=getSharedPreferences("saudepratica_caregiver_v1",MODE_PRIVATE)
        val caregiverCheck=android.widget.CheckBox(this).apply{
            text="🤲 Este perfil é o cuidador da família"
            isChecked=caregiverPrefs.getString("caregiver_id",null)==activeProfileId
            textSize=15f
            setPadding(dp(5),dp(8),dp(5),dp(8))
        }
        val prefs = getSharedPreferences(profiles.preferencesFor(activeProfileId), MODE_PRIVATE)''',"profile form caregiver")
change(main,'''        box.addView(noteBox("Identificação e dados pessoais",
            "Informação privada do utilizador. Preencha apenas os campos de que necessita."))''','''        box.addView(noteBox("🤲 Perfil cuidador",
            "O cuidador acompanha as tomas dos familiares neste telemóvel. "+
            "Só um perfil pode ser o cuidador de cada vez."))
        box.addView(caregiverCheck)
        box.addView(noteBox("Identificação e dados pessoais",
            "Informação privada do utilizador. Preencha apenas os campos de que necessita."))''',"profile checkbox")
change(main,'''                .putString("care_home_notes", homeNotes.edit.text.toString().trim().take(600))
                .apply()
            profileDraft = null''','''                .putString("care_home_notes", homeNotes.edit.text.toString().trim().take(600))
                .apply()
            val wasCaregiver=caregiverPrefs.getString("caregiver_id",null)==activeProfileId
            if(caregiverCheck.isChecked)
                caregiverPrefs.edit().putString("caregiver_id",activeProfileId).apply()
            else if(wasCaregiver)
                caregiverPrefs.edit().remove("caregiver_id").apply()
            profileDraft = null''',"save caregiver")
gradle=root/"app/build.gradle.kts"
change(gradle,"versionCode = 82","versionCode = 83","version code")
change(gradle,'versionName = "1.9.72"','versionName = "1.9.73"',"version name")
print("v1.9.73: patient-specific alarms and caregiver badge")
