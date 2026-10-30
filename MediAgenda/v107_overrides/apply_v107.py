"""SaudePratica v1.9.88: bound device patient, family notifications,
group pending review, remove medicine alarm and isolated alarm lockscreen task.

Safety: no automatic clinical profile merge, deletion or reclassification of
intakes; every group member remains individually unconfirmed until confirmed.
This patch follows v106 and fails closed if any required source anchor moved.
"""
from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
source=Path("MediAgenda/v107_overrides")

def change(rel,old,new,label):
    f=base/rel
    s=f.read_text(encoding="utf-8")
    found=s.count(old)
    if found!=1:
        raise RuntimeError(f"v107 {label}: expected one anchor, found {found}")
    f.write_text(s.replace(old,new,1),encoding="utf-8")

(base/"notifications/DeviceAlarmRouting.kt").write_text(
    (source/"DeviceAlarmRouting.kt").read_text(encoding="utf-8"),
    encoding="utf-8")

# A caregiver can switch active profiles to inspect family records without
# changing which patient owns this device and its intrusive alarms.
change("notifications/NotificationReceiver.kt",
'''                val selected=context.getSharedPreferences(
                    "saudepratica_intake_badge_v1",Context.MODE_PRIVATE)
                    .getString("current_profile",null)
                if(!selected.isNullOrBlank() && selected!=profileId){''',
'''                val configured=DataRepository(context,profileId)
                    .loadMedications().firstOrNull{it.id==medicationId}
                // A previously scheduled PendingIntent must not ring after
                // the user removes all medication alarm times.
                if(configured==null || (configured.reminderTime.isBlank() &&
                    configured.time.isBlank() && configured.doseTimes.isBlank()))
                    return
                if(!DeviceAlarmRouting.isLocalPatient(context,profileId)){''',
"route by device patient + no-alarm guard")

change("notifications/NotificationReceiver.kt",
'''                    }.onFailure{android.util.Log.w("SaudePraticaAlarm",
                        "Could not note other profile dose",it)}
                    return
                }
                val manager=context.getSystemService(NotificationManager::class.java)''',
'''                    }.onFailure{android.util.Log.w("SaudePraticaAlarm",
                        "Could not note other profile dose",it)}
                    // Caregiver: normal notification, NEVER start full-screen
                    // medication service for a different patient.
                    runCatching{
                        val med=DataRepository(context,profileId)
                            .loadMedications().firstOrNull{it.id==medicationId}
                        val patient=ProfileStore(context).all()
                            .firstOrNull{it.id==profileId}?.name
                            .orEmpty().ifBlank{"Familiar"}
                        val mgr=context.getSystemService(NotificationManager::class.java)
                        val channel="saudepratica_caregiver_notice_v1"
                        mgr.createNotificationChannel(android.app.NotificationChannel(
                            channel,"Avisos de medicação dos familiares",
                            NotificationManager.IMPORTANCE_DEFAULT).apply{
                            enableVibration(false)
                            setSound(null,null)
                        })
                        val view=Intent(context,
                            com.mediagenda.app.HealthRecordsActivity::class.java).apply{
                            putExtra(com.mediagenda.app.HealthRecordsActivity.EXTRA_PROFILE_ID,profileId)
                            putExtra(com.mediagenda.app.HealthRecordsActivity.EXTRA_CATEGORY,"intakes")
                            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                        }
                        val request=("family|"+profileId+"|"+medicationId+"|"+scheduledDoseAt)
                            .hashCode()
                        val pi=PendingIntent.getActivity(context,request,view,
                            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
                        mgr.notify(request,androidx.core.app.NotificationCompat.Builder(
                            context,channel)
                            .setSmallIcon(android.R.drawable.ic_dialog_info)
                            .setContentTitle("💊 "+patient+" · hora da medicação")
                            .setContentText(med?.medication.orEmpty()+" · "+
                                med?.dose.orEmpty().ifBlank{"Ver medicação"})
                            .setContentIntent(pi).setAutoCancel(true)
                            .setPriority(androidx.core.app.NotificationCompat.PRIORITY_DEFAULT)
                            .build())
                    }.onFailure{android.util.Log.e("SaudePraticaAlarm",
                        "Could not show caregiver notification",it)}
                    return
                }
                val manager=context.getSystemService(NotificationManager::class.java)''',
"caregiver normal notification")

change("notifications/MedicationAlarmService.kt",
'''        val selected=getSharedPreferences("saudepratica_intake_badge_v1",MODE_PRIVATE)
            .getString("current_profile",null)
        if(!demo && !selected.isNullOrBlank() && selected!=profileId){''',
'''        if(!demo && !DeviceAlarmRouting.isLocalPatient(this,profileId)){''',
"prevent strong alarms from profiles not belonging to this device")

# The group has individual pending records even if the patient immediately
# presses TOMEI. Nothing in the group is silently confirmed.
change("notifications/MedicationAlarmService.kt",
'''            }else MedicationAlarmService.stop(this,intent.getIntExtra("notification_id",0))
            startActivity(Intent(this,com.mediagenda.app.HealthRecordsActivity::class.java).apply{''',
'''            }else {
                MedicationAlarmGroup.pending(this,profile,
                    intent.getLongExtra("scheduled_at",0L),groupIds)
                MedicationAlarmService.stop(this,intent.getIntExtra("notification_id",0))
            }
            startActivity(Intent(this,com.mediagenda.app.HealthRecordsActivity::class.java).apply{''',
"create individual group pending entries on TOMEI")

# Device/patient affinity checkbox in the existing profile editor.
change("MainActivity.kt",
'''        }
        val prefs = getSharedPreferences(profiles.preferencesFor(activeProfileId), MODE_PRIVATE)''',
'''        }
        val devicePatientCheck=android.widget.CheckBox(this).apply{
            text="📱 Este perfil pertence a este telemóvel"
            textSize=15f
            isChecked=com.mediagenda.app.notifications.DeviceAlarmRouting
                .assigned(this@MainActivity)==activeProfileId
            setPadding(dp(5),dp(8),dp(5),dp(8))
        }
        val prefs = getSharedPreferences(profiles.preferencesFor(activeProfileId), MODE_PRIVATE)''',
"device patient selector")

change("MainActivity.kt",
'''        box.addView(caregiverCheck)
        box.addView(noteBox("Identificação e dados pessoais",''',
'''        box.addView(caregiverCheck)
        box.addView(noteBox("📱 Perfil associado a este telemóvel",
            "Só este perfil tem alarmes fortes. Os outros perfis geram "+
            "notificações discretas de medicação e agenda. "+
            "Podes continuar a consultar os quatro perfis."))
        box.addView(devicePatientCheck)
        box.addView(noteBox("Identificação e dados pessoais",''',
"device binding visible on patient card")

change("MainActivity.kt",
'''            else if(wasCaregiver)
                caregiverPrefs.edit().remove("caregiver_id").apply()
            profileDraft = null''',
'''            else if(wasCaregiver)
                caregiverPrefs.edit().remove("caregiver_id").apply()
            if(devicePatientCheck.isChecked)
                com.mediagenda.app.notifications.DeviceAlarmRouting
                    .assign(this,activeProfileId)
            else com.mediagenda.app.notifications.DeviceAlarmRouting
                .clearIfAssigned(this,activeProfileId)
            profileDraft = null''',
"persist device patient by stable profile id")

# Explicit "no alarm" choice. Keep the prescription and intake history.
change("MainActivity.kt",
'''        box.addView(reminder.container);box.addView(doseTimes.container)
        box.addView(medicationNotes.container)''',
'''        box.addView(reminder.container);box.addView(doseTimes.container)
        val disableMedicationAlarm=android.widget.CheckBox(this).apply{
            text="🔕 Sem alarme · retirar horários deste medicamento"
            textSize=15f
            isChecked=m.reminderTime.isBlank() && m.time.isBlank() &&
                m.doseTimes.isBlank()
            setOnCheckedChangeListener{_,checked->
                if(checked){
                    reminder.edit.setText("")
                    doseTimes.edit.setText("")
                }
            }
        }
        box.addView(disableMedicationAlarm)
        box.addView(medicationNotes.container)''',
"no alarm option on medication editor")

change("MainActivity.kt",
'''                m.notes=medicationNotes.edit.text.toString().trim()''',
'''                m.notes=medicationNotes.edit.text.toString().trim()
                if(disableMedicationAlarm.isChecked){
                    m.reminderTime=""
                    m.time=""
                    m.doseTimes=""
                }''',
"clear stored times if alarm disabled")

# Suppress only identical caregiver display cards from imported shadow profiles
# when the genuine local patient with the same name and same dose exists.
# Do NOT delete, merge or modify any underlying clinical records or profile IDs.
change("HealthRecordsActivity.kt",
'''            val familyOverdue=otherProfiles.flatMap{person->
                runCatching{PersonalHealthStore(this,person.id).overdueIntakes()
                    .map{person to it}}.getOrDefault(emptyList())
            }.sortedBy{it.second.fields["scheduled_at"]?.toLongOrNull()?:it.second.timestamp}''',
'''            val rawFamilyOverdue=otherProfiles.flatMap{person->
                runCatching{PersonalHealthStore(this,person.id).overdueIntakes()
                    .map{person to it}}.getOrDefault(emptyList())
            }.sortedBy{it.second.fields["scheduled_at"]?.toLongOrNull()?:it.second.timestamp}
            val canonical=rawFamilyOverdue.filter{
                !it.first.name.contains(" (recebido de ")
            }.map{(person,item)->
                person.name.trim().lowercase()+"|"+item.title.trim().lowercase()+
                    "|"+(item.fields["scheduled_at"]?.toLongOrNull()?:item.timestamp)
            }.toSet()
            val familyOverdue=rawFamilyOverdue.filter{(person,item)->
                val fromSync=person.name.contains(" (recebido de ")
                val key=person.name.substringBefore(" (recebido de ")
                    .trim().lowercase()+"|"+item.title.trim().lowercase()+
                    "|"+(item.fields["scheduled_at"]?.toLongOrNull()?:item.timestamp)
                !fromSync || key !in canonical
            }
            if(rawFamilyOverdue.size>familyOverdue.size)
                body.addView(label("ℹ️ "+
                    (rawFamilyOverdue.size-familyOverdue.size)+
                    " aviso(s) repetido(s) de perfis recebidos por sincronização "+
                    "foram ocultados nesta lista. Os registos originais continuam "+
                    "guardados até associares os perfis com segurança.",12f,color=muted))''',
"hide only exact repeated synced cards, preserve all data")

# Ensure alarm UI launches as an independent lockscreen task, never behind
# MainActivity's application PIN/login task.
manifest=root/"app/src/main/AndroidManifest.xml"
s=manifest.read_text(encoding="utf-8")
old='''            android:launchMode="singleTop" />'''
assert s.count('android:name=".notifications.MedicationAlarmActivity"')==1
section=s[s.index('android:name=".notifications.MedicationAlarmActivity"'):]
assert section.split("/>",1)[0].count(old.strip().replace(" />",""))==1, "alarm manifest launchMode changed"
section=section.replace(old,
'''            android:launchMode="singleTop"
            android:taskAffinity="com.mediagenda.app.medalarm" />''',1)
manifest.write_text(s[:s.index('android:name=".notifications.MedicationAlarmActivity"')]+section,encoding="utf-8")

gradle=root/"app/build.gradle.kts"
s=gradle.read_text(encoding="utf-8")
assert s.count("versionCode = 97")==1 and s.count('versionName = "1.9.87"')==1
gradle.write_text(s.replace("versionCode = 97","versionCode = 98",1)
    .replace('versionName = "1.9.87"','versionName = "1.9.88"',1),
    encoding="utf-8")

print("v1.9.88: device alarm profile + family notifications + group review + no alarm option")
