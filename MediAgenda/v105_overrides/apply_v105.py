"""v1.9.86 hotfix: status-bar insets and persisted snoozed pending intakes.

Snooze never means taken. It records one pending dose per actual medicine
and keeps justification separate from taken confirmations.
"""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
src=Path("MediAgenda/v105_overrides")
def edit(relative,old,new,label):
    file=base/relative
    data=file.read_text(encoding="utf-8")
    n=data.count(old)
    if n!=1:raise RuntimeError("v105 "+label+": anchor count "+str(n))
    file.write_text(data.replace(old,new,1),encoding="utf-8")

(base/"notifications/MedicationSnoozeState.kt").write_text(
    (src/"MedicationSnoozeState.kt").read_text(encoding="utf-8"),encoding="utf-8")

edit("notifications/MedicationAlarmService.kt",
'''        val root = ScrollView(this).apply { setBackgroundColor(Color.rgb(5, 24, 31)) }
        root.isFillViewport=true''',
'''        // HyperOS/Android edge-to-edge: preserve the status bar and display cutout.
        // Only affects the alarm Activity, not the app or notification appearance.
        androidx.core.view.WindowCompat.setDecorFitsSystemWindows(window,false)
        val root = ScrollView(this).apply { setBackgroundColor(Color.rgb(5, 24, 31)) }
        androidx.core.view.ViewCompat.setOnApplyWindowInsetsListener(root){view,insets->
            val top=insets.getInsets(
                androidx.core.view.WindowInsetsCompat.Type.statusBars() or
                androidx.core.view.WindowInsetsCompat.Type.displayCutout())
            val bottom=insets.getInsets(
                androidx.core.view.WindowInsetsCompat.Type.navigationBars())
            view.setPadding(top.left+dp(4),top.top+dp(20),
                top.right+dp(4),bottom.bottom+dp(12))
            insets
        }
        root.isFillViewport=true''',"alarm display below system status bar")
edit("notifications/MedicationAlarmService.kt",
'''        MedicationAlarmService.stop(context,intent.getIntExtra("notification_id",0))
        SnoozedMedicationNotice.show(context,profile,medId,whenOriginal,delay)''',
'''        // Record ALL outstanding doses immediately, not only the delayed
        // Android alarm. This makes them visible in Tomas during the 10 minutes.
        val ids=(intent.getStringArrayListExtra("group_med_ids").orEmpty()+
            MedicationAlarmGroup.members(context,profile,whenOriginal)+medId).distinct()
        val medications=DataRepository(context,profile).loadMedications().associateBy{it.id}
        val store=PersonalHealthStore(context,profile)
        ids.forEach{id->
            if(!MedicationAlarmCoordinator.wasHandled(context,profile,id,whenOriginal)){
                medications[id]?.let{m->
                    runCatching {
                        store.noteReminder(id,m.medication.ifBlank{"Medicação"},whenOriginal)
                        MedicationSnoozeState.save(context,profile,id,whenOriginal,delay)
                    }.onFailure{android.util.Log.e("SaudePraticaAlarm",
                        "Unable to save snoozed pending dose",it)}
                }
            }
        }
        IntakeBadgeManager.refresh(context,profile)
        MedicationAlarmService.stop(context,intent.getIntExtra("notification_id",0))
        SnoozedMedicationNotice.show(context,profile,medId,whenOriginal,delay)''',
"persist separate pending intakes on snooze")
edit("notifications/MedicationAlarmCoordinator.kt",
'''    fun resolve(c:Context,profile:String,medication:String,scheduledAt:Long) {
        if(profile.isBlank()||medication.isBlank()||scheduledAt<=0)return''',
'''    fun wasHandled(c:Context,profile:String,medication:String,scheduledAt:Long):Boolean{
        if(wasConfirmed(c,profile,medication,scheduledAt))return true
        if(profile.isBlank()||medication.isBlank()||scheduledAt<=0L)return false
        return runCatching{
            PersonalHealthStore(c,profile).list("ignored_intakes").any{
                it.fields["medication_id"]==medication &&
                it.fields["scheduled_at"]==scheduledAt.toString() &&
                it.fields["status"]=="justified_not_taken"
            }
        }.getOrDefault(false)
    }

    fun resolve(c:Context,profile:String,medication:String,scheduledAt:Long) {
        if(profile.isBlank()||medication.isBlank()||scheduledAt<=0)return
        MedicationSnoozeState.clear(c,profile,medication,scheduledAt)''',
"support justified-not-taken, clear saved snooze")
edit("notifications/MedicationAlarmCoordinator.kt",
'''        if(members.size>1 && members.any{!wasConfirmed(c,profile,it,scheduledAt)})
            return''',
'''        if(members.size>1 && members.any{!wasHandled(c,profile,it,scheduledAt)})
            return''',
"cancel group only if all members resolved")
edit("notifications/MedicationAlarmGroup.kt",
'''            if(!MedicationAlarmCoordinator.wasConfirmed(c,profile,id,at)){''',
'''            if(!MedicationAlarmCoordinator.wasHandled(c,profile,id,at)){''',
"no recreate justified pending dose")
edit("notifications/MedicationAlarmGroup.kt",
'''        ids.filter { !MedicationAlarmCoordinator.wasConfirmed(c,profile,it,at) }''',
'''        ids.filter { !MedicationAlarmCoordinator.wasHandled(c,profile,it,at) }''',
"ignore justified doses in group outstanding")
edit("notifications/NotificationReceiver.kt",
'''                }else if(MedicationAlarmCoordinator.wasConfirmed(context,profileId,
                    medicationId,scheduledDoseAt)){''',
'''                }else if(MedicationAlarmCoordinator.wasHandled(context,profileId,
                    medicationId,scheduledDoseAt)){''',
"do not alarm justified medicines")
edit("notifications/MedicationAlarmService.kt",
'''            else MedicationAlarmCoordinator.wasConfirmed(this,profileId,
                medicationId,scheduledAt))){''',
'''            else MedicationAlarmCoordinator.wasHandled(this,profileId,
                medicationId,scheduledAt))){''',
"service does not restart justified dose")
edit("notifications/MedicationAlarmService.kt",
'''MedicationAlarmCoordinator.wasConfirmed(this,profile,medId,''',
'''MedicationAlarmCoordinator.wasHandled(this,profile,medId,''',
"activity does not start justified dose")

edit("HealthRecordsActivity.kt",
'''            column.addView(label(if(item.id in overdue) "⚠️ Atrasada · por confirmar"''',
'''            val medId=item.fields["medication_id"].orEmpty()
            val postponedUntil=com.mediagenda.app.notifications.MedicationSnoozeState
                .until(this,profileId,medId,whenDue)
            if(postponedUntil>System.currentTimeMillis()){
                column.addView(label("⏰ Adiada até às "+
                    SimpleDateFormat("HH:mm",Locale("pt","PT"))
                        .format(Date(postponedUntil))+" · por confirmar",13f,
                    color=Color.rgb(255,190,112)))
            }
            column.addView(label(if(item.id in overdue) "⚠️ Atrasada · por confirmar"''',
"show snoozed pending status in Tomas")

edit("HealthRecordsActivity.kt",
'''            column.addView(button("✓ TOMEI — confirmar agora"){''',
'''            column.addView(button("Não tomei · justificar"){
                val reason=android.widget.EditText(this).apply{
                    hint="Motivo (por exemplo: esquecimento)"
                    inputType=android.text.InputType.TYPE_CLASS_TEXT or
                        android.text.InputType.TYPE_TEXT_FLAG_CAP_SENTENCES
                    setSingleLine(false)
                    setPadding(dp(14),dp(18),dp(14),dp(18))
                }
                MaterialAlertDialogBuilder(this)
                    .setTitle("Registar dose não tomada")
                    .setMessage("Medicamento: "+item.title+
                        "\\nEste registo NÃO confirma que a medicação foi tomada.")
                    .setView(reason)
                    .setNegativeButton("Cancelar",null)
                    .setPositiveButton("Guardar motivo"){_,_->
                        val note=reason.text.toString().trim()
                        if(note.isBlank()) {
                            alert("Indica o motivo, ou cancela sem alterar a toma.")
                        } else runCatching {
                            val id=item.fields["medication_id"].orEmpty()
                            check(id.isNotBlank() && whenDue>0L)
                            check(!com.mediagenda.app.notifications.MedicationAlarmCoordinator
                                .wasConfirmed(this,profileId,id,whenDue)){
                                "Esta toma já foi confirmada."
                            }
                            store.add("ignored_intakes",item.title,mapOf(
                                "medication_id" to id,
                                "scheduled_at" to whenDue.toString(),
                                "status" to "justified_not_taken",
                                "reason" to note.take(500),
                                "source" to "justificacao_manual"),System.currentTimeMillis())
                            store.remove(item)
                            com.mediagenda.app.notifications.MedicationAlarmCoordinator
                                .resolve(this,profileId,id,whenDue)
                            com.mediagenda.app.notifications.IntakeBadgeManager
                                .refresh(this,profileId)
                        }.onSuccess{refresh()}
                            .onFailure{alert(it.message?:"Não foi possível justificar.")}
                    }.show()
            })
            column.addView(button("✓ TOMEI — confirmar agora"){''',
"justify not taken without marking it taken")
edit("HealthRecordsActivity.kt",
'''        val ignoredKeys=store.ignoredAlarmKeys()''',
'''        val ignoredKeys=store.ignoredAlarmKeys()
        val justified=store.list("ignored_intakes").filter{
            it.fields["status"]=="justified_not_taken"
        }
        if(justified.isNotEmpty()){
            body.addView(label("📝 Tomas não realizadas · justificadas",17f,true))
            justified.sortedByDescending{it.timestamp}.take(20).forEach{item->
                body.addView(label(item.title+" · "+
                    item.fields["reason"].orEmpty(),12f,color=muted))
            }
        }''',
"show reason history distinctly from taken")
edit("notifications/MedicationAlarmService.kt",
'''        if(MedicationAlarmCoordinator.wasConfirmed(context,profile,medId,whenOriginal)){
            MedicationAlarmCoordinator.resolve(context,profile,medId,whenOriginal)
            return
        }''',
'''        val allMembers=(intent.getStringArrayListExtra("group_med_ids").orEmpty()+
            MedicationAlarmGroup.members(context,profile,whenOriginal)+medId).distinct()
        if(allMembers.all{
            MedicationAlarmCoordinator.wasHandled(context,profile,it,whenOriginal)
        }){
            MedicationAlarmCoordinator.resolve(context,profile,medId,whenOriginal)
            return
        }''',"group snooze checks all medicines, not just first")
build=root/"app/build.gradle.kts"
s=build.read_text(encoding="utf-8")
assert s.count("versionCode = 95")==1 and s.count('versionName = "1.9.85"')==1
build.write_text(s.replace("versionCode = 95","versionCode = 96",1)
    .replace('versionName = "1.9.85"','versionName = "1.9.86"',1),
    encoding="utf-8")
print("v1.9.86: alarm inset; persist snooze pending per profile/medicine; justify missing dose")
