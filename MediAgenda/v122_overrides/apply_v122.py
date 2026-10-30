#!/usr/bin/env python3
"""Safe source-only patch v122: alarm PIN, patient ownership and per-profile badges.
Apply only after v121 profile changes to v1.9.102. Does not modify medications,
alarm due times, stored personal records or the original Android signing identity.
"""
from pathlib import Path
import re

ROOT = Path('build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app')
assert ROOT.exists(), 'Build source not reconstructed; refusing to patch'

def read(path):
    f = ROOT / path
    assert f.is_file(), f'Missing source {f}'
    return f.read_text(encoding='utf-8')

def write(path, before, after):
    assert before != after, f'No change to {path}'
    (ROOT / path).write_text(after, encoding='utf-8')
    print('Patched', path)

def once(s, old, new, hint):
    assert s.count(old)==1, f'Unexpected source around {hint}: {s.count(old)} occurrences'
    return s.replace(old,new,1)

p='SaudePraticaApplication.kt'
s=read(p)
s=once(s,'class SaudePraticaApplication:Application(), Application.ActivityLifecycleCallbacks {\n    private var started=0',
'''class SaudePraticaApplication:Application(), Application.ActivityLifecycleCallbacks {
    private var started=0
    companion object {
        // Count only an actual resumed, authorised UI window. Foreground audio
        // services make a process "foreground" but do NOT make a screen visible.
        @Volatile private var authenticatedUiVisible=false
        fun isAuthenticatedUiVisible():Boolean=authenticatedUiVisible
    }''','app visible signal')
old='''        AppLanguage.attach(activity)
        if(activity is AppPinActivity || activity is SplashActivity)return
        if(AppPinStore(activity).enabled() &&
            !AppPinSession.unlocked && !AppPinSession.gateRequested) {
            AppPinSession.gateRequested=true
            activity.startActivity(Intent(activity,AppPinActivity::class.java)
                .putExtra(AppPinActivity.FROM_SPLASH,false))
        }
    }
    override fun onActivityPaused(activity:Activity){}'''
new='''        AppLanguage.attach(activity)
        // Critical: a real scheduled alarm is a standalone lock-screen UI.
        // Do not launch our PIN Activity on top of ADIAR / TOMEI, even after
        // Android killed the original process or the alarm was postponed.
        if(activity is com.mediagenda.app.notifications.MedicationAlarmActivity)return
        if(activity is AppPinActivity || activity is SplashActivity)return
        val requiresPin=AppPinStore(activity).enabled() && !AppPinSession.unlocked
        authenticatedUiVisible=!requiresPin
        if(requiresPin && !AppPinSession.gateRequested) {
            AppPinSession.gateRequested=true
            activity.startActivity(Intent(activity,AppPinActivity::class.java)
                .putExtra(AppPinActivity.FROM_SPLASH,false))
        }
    }
    override fun onActivityPaused(activity:Activity){
        if(activity !is com.mediagenda.app.notifications.MedicationAlarmActivity)
            authenticatedUiVisible=false
    }'''
s=once(s,old,new,'global PIN gate')
write(p,read(p),s)

p='notifications/MedicationAlarmService.kt'
s=read(p)
old='''        val foreground=(!locked && interactive && runCatching{
            getSystemService(ActivityManager::class.java).runningAppProcesses
                ?.any{it.pid==android.os.Process.myPid() &&
                    it.importance==ActivityManager.RunningAppProcessInfo.IMPORTANCE_FOREGROUND}
                ?:false
        }.getOrDefault(false))'''
new='''        val foreground=(!locked && interactive &&
            com.mediagenda.app.SaudePraticaApplication.isAuthenticatedUiVisible())'''
s=once(s,old,new,'real foreground versus foreground alarm service')
old='''        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON or
            WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED or
            WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON or
            WindowManager.LayoutParams.FLAG_DISMISS_KEYGUARD)'''
new='''        // setShowWhenLocked/setTurnScreenOn are already called above.
        // FLAG_DISMISS_KEYGUARD is deprecated and can provoke Xiaomi's PIN UI.
        // Never dismiss the phone lock: show only the two alarm actions on top.
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)'''
s=once(s,old,new,'do not dismiss Android keyguard')
write(p,read(p),s)

p='notifications/DeviceAlarmRouting.kt'
s=read(p)
old='''        val caregiver = c.getSharedPreferences("saudepratica_caregiver_v1",
            Context.MODE_PRIVATE).getString("caregiver_id", null)
        if (caregiver != null && caregiver in ids) return caregiver
'''
s=once(s,old,'''        // A caregiver is not implicitly the owner of this phone's alarms.
        // Family members never trigger a full-screen alarm here merely because
        // this profile manages their appointments or overdue notifications.
''','remove caregiver-as-local-patient')
write(p,read(p),s)

p='notifications/IntakeBadgeManager.kt'
s=read(p)
old='''        if(profileId!=null && selected!=profileId &&
            prefs(context).getString("current_profile",null)!=
                context.getSharedPreferences("saudepratica_caregiver_v1",
                    Context.MODE_PRIVATE).getString("caregiver_id",null))return'''
s=once(s,old,'''        if(profileId!=null && selected!=profileId)return''','only selected profile badge')
old='''                val own=PersonalHealthStore(context,selected).overdueIntakes().size
                val caregiver=context.getSharedPreferences("saudepratica_caregiver_v1",
                    Context.MODE_PRIVATE).getString("caregiver_id",null)
                if(caregiver==selected) own+ProfileStore(context).all()
                    .filter{it.id!=selected}.sumOf{
                        PersonalHealthStore(context,it.id).overdueIntakes().size
                    } else own'''
s=once(s,old,'''                // Android badge is scoped strictly to the selected patient.
                // Aggregation for caregivers belongs on the chooser, never Tomas.
                PersonalHealthStore(context,selected).overdueIntakes().size''','badge no caregiver aggregation')
write(p,read(p),s)

p='notifications/NotificationReceiver.kt'
s=read(p)
pat=r'''                if\(!DeviceAlarmRouting\.isLocalPatient\(context,profileId\)\)\{.*?\n                \}\n                val manager=context\.getSystemService\(NotificationManager::class\.java\)'''
match=list(re.finditer(pat,s,flags=re.S))
assert len(match)==1, f'Nonlocal caregiver branch not found: {len(match)}'
new='''                if(!DeviceAlarmRouting.isLocalPatient(context,profileId)){
                    // Keep the due reminder in the correct person's private
                    // store, but do NOT post another family's medication banner
                    // to the current device or wake its full-screen alarm.
                    runCatching{
                        val other=DataRepository(context,profileId)
                            .loadMedications().firstOrNull{it.id==medicationId}
                        if(other!=null){
                            PersonalHealthStore(context,profileId).noteReminder(
                                other.id,other.medication.ifBlank{"Medicação"},scheduledDoseAt)
                            IntakeBadgeManager.scheduleCheck(context,profileId,
                                other.id,scheduledDoseAt)
                        }
                    }.onFailure{android.util.Log.e("SaudePraticaAlarm",
                        "Unable to record other profile reminder",it)}
                    return
                }
                val manager=context.getSystemService(NotificationManager::class.java)'''
s=s[:match[0].start()]+new+s[match[0].end():]
write(p,read(p),s)

p='HealthRecordsActivity.kt'
s=read(p)
start='''        val caregiverId=getSharedPreferences("saudepratica_caregiver_v1",MODE_PRIVATE)
            .getString("caregiver_id",null)
        if(caregiverId==profileId){'''
end='''        val format=SimpleDateFormat("dd/MM/yyyy · HH:mm",Locale("pt","PT"))'''
assert s.count(start)==1 and s.count(end)>=1
head=s.index(start);tail=s.index(end,head)
s=s[:head]+'''        // Personal Tomas always shows this profile's records only. The caregiver
        // role never merges another person's pending or confirmed medication
        // into this patient's history. Each profile keeps its original storage.
        if(getSharedPreferences("saudepratica_caregiver_v1",MODE_PRIVATE)
                .getString("caregiver_id",null)==profileId){
            body.addView(label("Cada familiar tem as suas TOMAS no próprio perfil. " +
                "Na escolha de perfil vês os contadores individuais de tomas e agenda.",
                12f,color=muted))
        }
'''+s[tail:]
write(p,read(p),s)

p='MainActivity.kt'
s=read(p)
old='''        val lateTomas=runCatching {
            val caregiver=getSharedPreferences("saudepratica_caregiver_v1",MODE_PRIVATE)
                .getString("caregiver_id",null)==activeProfileId
            (if(caregiver)profiles.all() else profiles.all().filter{it.id==activeProfileId})
                .sumOf{PersonalHealthStore(this,it.id).overdueIntakes().size}
        }.getOrDefault(0)'''
s=once(s,old,'''        val lateTomas=runCatching {
            PersonalHealthStore(this,activeProfileId).overdueIntakes().size
        }.getOrDefault(0)''','dashboard Tomas badge patient only')
# Insert independent patient badges inside the chooser, without including other
# profiles' records in the selected patient's medication screen.
old='''            row.addView(words,LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f))
            row.addView(TextView(this).apply{'''
new='''            val doseCount=runCatching{
                PersonalHealthStore(this,profile.id).overdueIntakes().size
            }.getOrDefault(0)
            val agendaCount=runCatching{
                DataRepository(this,profile.id).loadAppointments()
                    .count{!it.done && upcomingAppointmentTime(it)!=null}
            }.getOrDefault(0)
            words.addView(TextView(this).apply{
                text="💊 $doseCount por confirmar  ·  📅 $agendaCount próximos"
                textSize=12f
                setTextColor(if(doseCount>0) Color.rgb(230,148,82) else muted)
                setPadding(0,dp(7),0,0)
                maxLines=2
            })
            row.addView(words,LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f))
            row.addView(TextView(this).apply{'''
s=once(s,old,new,'per-patient chooser indicators')
old='            card.addView(row)\n            card.setOnClickListener{activateProfile(profile)}'
new='            card.addView(row)\n            val ownerOfAlarms=com.mediagenda.app.notifications.DeviceAlarmRouting\n                .explicit(this)==profile.id\n            val deviceButton=secondaryButton(if(ownerOfAlarms)\n                "📱 Alarmes deste telemóvel ✓" else "📱 Associar alarmes a este telemóvel"){\n                if(!ownerOfAlarms)MaterialAlertDialogBuilder(this)\n                    .setTitle("A quem pertence este telemóvel?")\n                    .setMessage("Só os alarmes de medicação deste perfil devem " +\n                        "tocar em ecrã inteiro neste telemóvel. Os restantes " +\n                        "familiares mantêm as suas tomas e agendas no respetivo perfil.")\n                    .setPositiveButton("Associar"){_,_->\n                        com.mediagenda.app.notifications.DeviceAlarmRouting\n                            .assign(this,profile.id)\n                        reschedule()\n                        showProfileSelection()\n                    }\n                    .setNegativeButton("Cancelar",null).show()\n            }\n            card.addView(deviceButton)\n            card.setOnClickListener{activateProfile(profile)}'
s=once(s,old,new,'explicit patient-to-device assignment in chooser')
# Make user-requested no-package state explicit and easy to select.
old='''        val photoModes=listOf("Foto da embalagem (se disponível)" to "photo",
            "Medicamento sem caixa" to "unboxed",
            "Embalagem sem fotografia" to "missing")'''
new='''        val photoModes=listOf("Foto da embalagem (se disponível)" to "photo",
            "SEM CAIXA · Só lamelas / blisters" to "unboxed",
            "Sem fotografia da caixa" to "missing")'''
s=once(s,old,new,'clear blister-only label')
old='''        lateinit var photoModeButton: MaterialButton
        photoModeButton=secondaryButton'''
new='''        lateinit var photoModeButton: MaterialButton
        lateinit var noBoxCheck: android.widget.CheckBox
        photoModeButton=secondaryButton'''
s=once(s,old,new,'blister checkbox variable')
old='''                    photoModeButton.text="Imagem: "+photoModes[which].first
                    dialog.dismiss()'''
new='''                    photoModeButton.text="Imagem: "+photoModes[which].first
                    noBoxCheck.isChecked=chosenPhotoMode=="unboxed"
                    dialog.dismiss()'''
s=once(s,old,new,'keep no-box mode synchronized with image choice')
old='''        box.addView(photoModeButton)
        if(existing==null)box.addView(noteBox("Bula do medicamento",'''
new='''        box.addView(photoModeButton)
        noBoxCheck=android.widget.CheckBox(this).apply{
            text="💊 NÃO TEM CAIXA · Só lamelas / blisters"
            textSize=15f
            isChecked=chosenPhotoMode=="unboxed"
            setOnCheckedChangeListener{_,checked->
                if(checked)chosenPhotoMode="unboxed"
                else if(chosenPhotoMode=="unboxed")chosenPhotoMode="photo"
                photoModeButton.text="Imagem: "+
                    photoModes.first{it.second==chosenPhotoMode}.first
            }
        }
        box.addView(noBoxCheck)
        if(existing==null)box.addView(noteBox("Bula do medicamento",'''
s=once(s,old,new,'visible blister option')
write(p,read(p),s)

print('Source patch v122 completed without modifying any patient files.')
