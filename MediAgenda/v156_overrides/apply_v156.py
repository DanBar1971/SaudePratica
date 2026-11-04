#!/usr/bin/env python3
"""SaúdePrática 1.9.136: optional offline hospital dossier and calendar handoff.

Runs after 1.9.135 reconstruction. No personal patient/staff data goes into git.
Never alters alarm services, medical records, the package ID, or Android signing.
"""
from pathlib import Path
from shutil import copyfile
from hashlib import sha256

app=Path("build-src/MediAgenda_Android_v1/app")
src=app/"src/main/java/com/mediagenda/app"
patch=Path("MediAgenda/v156_overrides")

protected=[
    "notifications/MedicationAlarmService.kt",
    "notifications/NotificationScheduler.kt",
    "notifications/NotificationReceiver.kt",
    "notifications/MedicationAlarmCoordinator.kt",
    "notifications/MedicationAlarmPreferences.kt",
    "notifications/IntakeActionReceiver.kt",
    "notifications/DeviceAlarmRouting.kt",
]
baseline={p:sha256((src/p).read_bytes()).hexdigest()
          for p in protected if (src/p).exists()}
assert len(baseline)>=5,"Missing protected alarm modules"

copyfile(patch/"HospitalProcessActivity.kt",src/"HospitalProcessActivity.kt")

clinical=src/"WorkMedicineActivity.kt"
s=clinical.read_text(encoding="utf-8")
old="""            clinicalCard.addView(controls)
        }
        clinicalCard.addView(button("＋ Adicionar número de observação / processo"){"""
new="""            clinicalCard.addView(controls)
            clinicalCard.addView(button("🏥 A minha equipa · Taxas · Identificação · Transporte"){
                val unit=if(record.contains("|"))record.substringBefore("|").trim() else ""
                val number=if(record.contains("|"))record.substringAfter("|").trim() else record
                startActivity(android.content.Intent(this,HospitalProcessActivity::class.java)
                    .putExtra(HospitalProcessActivity.EXTRA_PROFILE_ID,patientId)
                    .putExtra(HospitalProcessActivity.EXTRA_HOSPITAL,unit)
                    .putExtra(HospitalProcessActivity.EXTRA_PROCESS,number))
            })
        }
        clinicalCard.addView(button("＋ Adicionar número de observação / processo"){"""
assert s.count(old)==1,("hospital process clinical anchor",s.count(old))
clinical.write_text(s.replace(old,new,1),encoding="utf-8")

main=src/"MainActivity.kt"
s=main.read_text(encoding="utf-8")
anchor="""content.addView(quickActions,LinearLayout.LayoutParams(-1,-2).apply{bottomMargin=dp(6)})
        val allAppointments=repo.loadAppointments().sortedWith("""
replace="""content.addView(quickActions,LinearLayout.LayoutParams(-1,-2).apply{bottomMargin=dp(6)})
        content.addView(secondaryButton("📅 Adicionar consulta ao calendário do telemóvel"){
            chooseAppointmentForSystemCalendar()
        })
        val allAppointments=repo.loadAppointments().sortedWith("""
assert s.count(anchor)==1,("calendar agenda button anchor",s.count(anchor))
s=s.replace(anchor,replace,1)
helper=r'''
    /**
     * Explicit user-controlled handoff to the Android calendar editor.
     * No READ/WRITE_CALENDAR permission, no silent event creation, and no
     * invented time when an appointment contains only a date.
     */
    private fun chooseAppointmentForSystemCalendar(){
        val upcoming=repo.loadAppointments().filter{appointment->
            !appointment.cancelled &&
            runCatching{java.time.LocalDate.parse(appointment.date)}
                .getOrNull()?.let{!it.isBefore(java.time.LocalDate.now())}==true
        }.sortedWith(compareBy<com.mediagenda.app.model.Appointment>{it.date}
            .thenBy{it.time})
        if(upcoming.isEmpty()){
            showError("Este perfil não tem marcações futuras para colocar no calendário.")
            return
        }
        val labels=upcoming.map{
            it.date+" · "+it.time.ifBlank{"hora por indicar"}+" · "+
                it.activity.take(85)
        }.toTypedArray()
        com.google.android.material.dialog.MaterialAlertDialogBuilder(this)
            .setTitle("Escolher marcação · Calendário")
            .setMessage("O calendário do telemóvel abre para rever e guardar. Não há sincronização automática com o hospital.")
            .setItems(labels){_,selected->
                val a=upcoming[selected]
                val date=runCatching{java.time.LocalDate.parse(a.date)}
                    .getOrNull()?:return@setItems
                val parsed=runCatching{java.time.LocalTime.parse(a.time)}
                    .getOrNull()
                val allDay=parsed==null
                val begin=if(allDay)
                    date.atStartOfDay(java.time.ZoneOffset.UTC)
                        .toInstant().toEpochMilli()
                    else date.atTime(parsed).atZone(java.time.ZoneId.systemDefault())
                        .toInstant().toEpochMilli()
                val end=begin+if(allDay)24L*60*60*1000 else 60L*60*1000
                val eventIntent=android.content.Intent(
                    android.content.Intent.ACTION_INSERT).apply{
                    data=android.provider.CalendarContract.Events.CONTENT_URI
                    putExtra(android.provider.CalendarContract.Events.TITLE,
                        a.activity.ifBlank{"Marcação de saúde"})
                    putExtra(android.provider.CalendarContract.Events.DESCRIPTION,
                        "Criado a partir da SaúdePrática. Confirma os dados antes de guardar.")
                    putExtra(android.provider.CalendarContract.EXTRA_EVENT_BEGIN_TIME,begin)
                    putExtra(android.provider.CalendarContract.EXTRA_EVENT_END_TIME,end)
                    putExtra(android.provider.CalendarContract.Events.ALL_DAY,allDay)
                }
                try{
                    startActivity(eventIntent)
                }catch(_:android.content.ActivityNotFoundException){
                    showError("Não está instalada nenhuma aplicação de calendário compatível.")
                }
            }.setNegativeButton("Cancelar",null).show()
    }

'''
anchor2="    private fun showProfileSelection() {"
assert s.count(anchor2)==1,("calendar method insertion point",s.count(anchor2))
s=s.replace(anchor2,helper+anchor2,1)
main.write_text(s,encoding="utf-8")

manifest=app/"src/main/AndroidManifest.xml"
m=manifest.read_text(encoding="utf-8")
assert m.count("</application>")==1
m=m.replace("</application>",'''        <activity android:name=".HospitalProcessActivity"
            android:exported="false" />
    </application>''',1)
manifest.write_text(m,encoding="utf-8")

gradle=app/"build.gradle.kts"
g=gradle.read_text(encoding="utf-8")
assert g.count("versionCode = 145")==1,"Wrong Android versionCode for 1.9.135"
assert g.count('versionName = "1.9.135"')==1,"Wrong Android versionName"
g=g.replace("versionCode = 145","versionCode = 146",1)
g=g.replace('versionName = "1.9.135"','versionName = "1.9.136"',1)
gradle.write_text(g,encoding="utf-8")

for name,digest in baseline.items():
    assert sha256((src/name).read_bytes()).hexdigest()==digest,(
        "Forbidden alarm modification: "+name)
print("v1.9.136: hospital dossier + explicit calendar handoff; alarms unchanged")
