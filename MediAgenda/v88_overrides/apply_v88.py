"""SaúdePrática 1.9.70: reliable full-screen alarm and caregiver deletion."""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
def change(p,old,new,label):
 s=p.read_text(encoding="utf-8")
 if s.count(old)!=1:raise RuntimeError(f"v88 {label}: anchor {s.count(old)}")
 p.write_text(s.replace(old,new,1),encoding="utf-8")
alarm=base/"notifications/MedicationAlarmService.kt"
change(alarm,'        val full = PendingIntent.getActivity(this, currentId, open,',
'''        val full = PendingIntent.getActivity(this, currentId, open,''',"full intent")
change(alarm,'''        val n = NotificationCompat.Builder(this, CHANNEL)''','''        // Android 14+ may block full-screen intents unless the user grants
        // Settings > Special app access > Full screen notifications.
        // A visible activity is also launched directly while the app is
        // already foregrounded, rather than relying on a heads-up banner.
        val n = NotificationCompat.Builder(this, CHANNEL)''',"explanation")
change(alarm,'''        startTimeout()
        if(MedicationAlarmPreferences.mode(this)!="tone")announce(drugName,doseText)''','''        startTimeout()
        if(MedicationAlarmPreferences.mode(this)!="tone")announce(drugName,doseText)
        // Android restricts background activity starts. Only launch directly
        // when the app has a visible window; otherwise use full-screen intent.
        val foreground=runCatching {
            val manager=getSystemService(ActivityManager::class.java)
            manager.appTasks.any{ task->
                task.taskInfo.isRunning && task.taskInfo.topActivity?.packageName==packageName
            }
        }.getOrDefault(false)
        if(foreground){
            runCatching{startActivity(open)}.onFailure{
                android.util.Log.w("SaudePraticaAlarm","Foreground screen",it)
            }
        }''',"foreground activity")
change(alarm,'''        layout.addView(label(medicine?.medication?:if(demo)"Medicamento de teste" else "Medicação",29f))''','''        layout.addView(label(medicine?.medication?:if(demo)"Medicamento de teste" else "Medicação",36f))''',"big title")
change(alarm,'''        layout.addView(label(medicine?.dose.orEmpty(), 23f))''','''        layout.addView(label(medicine?.dose.orEmpty(), 27f))''',"big dose")
change(alarm,'''                    layoutParams = LinearLayout.LayoutParams(-1, dp(300))''','''                    layoutParams = LinearLayout.LayoutParams(-1, dp(350))''',"large photo")
# A shortcut to system settings must be explicit because Android 14+ controls
# full-screen notification privileges per application.
main=base/"MainActivity.kt"
change(main,'''        box.addView(secondaryButton("⚙ Configurar alarmes: som, voz e idioma"){
            showMedicationAlarmSettings()
        })''','''        box.addView(secondaryButton("⚙ Configurar alarmes: som, voz e idioma"){
            showMedicationAlarmSettings()
        })
        if(Build.VERSION.SDK_INT>=34){
            val manager=getSystemService(android.app.NotificationManager::class.java)
            if(!manager.canUseFullScreenIntent()){
                box.addView(noteBox("Ecrã completo do alarme",
                    "O Android bloqueou o ecrã completo. Autoriza a SaúdePrática "+
                    "nas permissões especiais de alarmes em ecrã completo."))
                box.addView(secondaryButton("🔔 Autorizar alarmes em ecrã completo"){
                    startActivity(Intent(android.provider.Settings.ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT,
                        android.net.Uri.parse("package:"+packageName)))
                })
            }
        }''',"full screen settings")
health=base/"HealthRecordsActivity.kt"
change(health,'''                shell.addView(column);addCard(shell)
            }
        }
        val format=SimpleDateFormat("dd/MM/yyyy · HH:mm",Locale("pt","PT"))''','''                // Caregiver may remove an unconfirmed reminder, never confirm
                // medication on someone else's behalf.
                column.addView(button("🗑 Remover aviso deste perfil"){
                    MaterialAlertDialogBuilder(this)
                        .setTitle("Remover aviso de "+person.name+"?")
                        .setMessage("Medicamento: "+item.title+"\\nPrevista: "+whenText+
                            "\\nRemove apenas este aviso do histórico de tomas. "+
                            "Não confirma a medicação nem altera a prescrição.")
                        .setPositiveButton("Remover"){_,_->
                            runCatching{
                                PersonalHealthStore(this,person.id).remove(item)
                                com.mediagenda.app.notifications.IntakeBadgeManager.refresh(
                                    this,profileId)
                                refresh()
                            }.onFailure{alert(it.message?:"Não foi possível remover o aviso")}
                        }.setNegativeButton("Cancelar",null).show()
                })
                shell.addView(column);addCard(shell)
            }
        }
        val format=SimpleDateFormat("dd/MM/yyyy · HH:mm",Locale("pt","PT"))''',"caregiver remove overdue")
# A caregiver can also delete confirmed intakes of family profiles.
change(health,'''        val format=SimpleDateFormat("dd/MM/yyyy · HH:mm",Locale("pt","PT"))
        val overdue=store.overdueIntakes()''','''        if(caregiverId==profileId){
            val familyConfirmed=ProfileStore(this).all().filter{it.id!=profileId}
                .flatMap{person->runCatching{
                    PersonalHealthStore(this,person.id).list("intakes")
                        .map{person to it}
                }.getOrDefault(emptyList())}
                .sortedByDescending{it.second.timestamp}
            body.addView(label("✅ Tomas confirmadas da família · "+
                familyConfirmed.size,19f,true).apply{
                setPadding(dp(4),dp(18),0,dp(8))
            })
            familyConfirmed.forEach{(person,item)->
                val shell=card()
                val column=LinearLayout(this).apply{
                    orientation=LinearLayout.VERTICAL
                    setPadding(dp(15),dp(14),dp(15),dp(14))
                }
                val whenText=SimpleDateFormat("dd/MM/yyyy · HH:mm",
                    Locale("pt","PT")).format(Date(item.timestamp))
                column.addView(label(person.name+" · "+item.title,16f,true))
                column.addView(label("Confirmada: "+whenText,12f,color=muted))
                column.addView(button("🗑 Apagar registo de "+person.name){
                    MaterialAlertDialogBuilder(this)
                        .setTitle("Apagar toma confirmada?")
                        .setMessage("Perfil: "+person.name+"\\nMedicamento: "+
                            item.title+"\\nEste registo será removido do histórico. "+
                            "Não altera a prescrição.")
                        .setPositiveButton("Apagar"){_,_->
                            runCatching{
                                PersonalHealthStore(this,person.id).remove(item)
                                com.mediagenda.app.notifications.IntakeBadgeManager.refresh(
                                    this,profileId)
                                refresh()
                            }.onFailure{alert(it.message?:"Não foi possível apagar")}
                        }.setNegativeButton("Cancelar",null).show()
                })
                shell.addView(column);addCard(shell)
            }
        }
        val format=SimpleDateFormat("dd/MM/yyyy · HH:mm",Locale("pt","PT"))
        val overdue=store.overdueIntakes()''',"caregiver confirmed deletion")
# Tombstones for deleted pending intake reminders must synchronize like deleted
# confirmations; otherwise the reminder can return after family sync.
store=base/"data/PersonalHealthStore.kt"
change(store,'''            if(item.kind=="intakes" && previous.any{it.id==item.id}){''','''            if(item.kind in setOf("intakes","pending_intakes") &&
                previous.any{it.id==item.id}){''',"pending tombstone")
change(store,'''                val fields=mutableMapOf("deleted_intake_id" to item.id)''','''                val fields=mutableMapOf("deleted_intake_id" to item.id,
                    "deleted_kind" to item.kind)''',"kind tombstone")
# For synced pending deletion, existing dedupe already filters tombstones
# by record ID; preserving that ID prevents recreation from another phone.
gradle=root/"app/build.gradle.kts"
change(gradle,"versionCode = 79","versionCode = 80","version code")
change(gradle,'versionName = "1.9.69"','versionName = "1.9.70"',"version name")
print("SaúdePrática 1.9.70: full-screen alarm and caregiver reminder deletion")
