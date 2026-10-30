from pathlib import Path

root = Path("build-src/MediAgenda_Android_v1")
base = root/"app/src/main/java/com/mediagenda/app"

def patch(path,old,new,label):
    s=path.read_text(encoding="utf-8")
    if s.count(old)!=1:
        raise RuntimeError("v1.9.31: "+label+" expected 1 anchor, found "+str(s.count(old)))
    path.write_text(s.replace(old,new,1),encoding="utf-8")

store=base/"data/PersonalHealthStore.kt"
patch(store,
    '    private val allowed = setOf("symptoms", "measurements", "vaccines", "intakes")',
    '''    private val allowed = setOf("symptoms", "measurements", "vaccines",
        "intakes", "pending_intakes")
    companion object { private val intakeLock=Any() }''',
    "pending category")
patch(store,
    '''    /** A confirmation is a log entry, never an instruction to take a dose. */
    fun confirmIntake(medicationId: String, name: String): PersonalHealthRecord {
        require(medicationId.isNotBlank()) { "Medicamento inválido." }
        return add("intakes", name, mapOf("medication_id" to medicationId))
    }
''',
    '''    /** Called only after an actual scheduled medication notification is displayed.
     * It records an unconfirmed dose, NOT that the patient took the medication.
     * Rescheduling/rebroadcast of the same dose never creates duplicates.
     */
    fun noteReminder(medicationId:String,name:String,scheduledAt:Long) {
        if(medicationId.isBlank()||name.isBlank()||scheduledAt<=0L)return
        synchronized(intakeLock){
            val key=scheduledAt.toString()
            if(list("pending_intakes").any{
                    it.fields["medication_id"]==medicationId &&
                    it.fields["scheduled_at"]==key
                } || list("intakes").any{
                    it.fields["medication_id"]==medicationId &&
                    it.fields["scheduled_at"]==key
                })return
            add("pending_intakes",name,mapOf(
                "medication_id" to medicationId,
                "scheduled_at" to key,
                "source" to "medication_notification"),scheduledAt)
        }
    }

    /** Explicit action only: confirmation on a notification or inside Tomas.
     * Check for a prior confirmation before writing to prevent double counting.
     */
    fun confirmScheduledIntake(medicationId:String,name:String,
                               scheduledAt:Long):PersonalHealthRecord {
        require(medicationId.isNotBlank() && scheduledAt>0L)
        return synchronized(intakeLock){
            val key=scheduledAt.toString()
            val previous=list("intakes").firstOrNull{
                it.fields["medication_id"]==medicationId &&
                it.fields["scheduled_at"]==key
            }
            val confirmed=previous?:add("intakes",name,
                mapOf("medication_id" to medicationId,
                      "scheduled_at" to key,
                      "source" to "manual_confirmation"))
            list("pending_intakes").filter{
                it.fields["medication_id"]==medicationId &&
                it.fields["scheduled_at"]==key
            }.forEach{ remove(it) }
            confirmed
        }
    }

    /** The main medication-list Tomei button should clear today's unconfirmed
     * scheduled dose, if present, rather than produce two entries.
     */
    fun confirmIntake(medicationId: String, name: String): PersonalHealthRecord {
        require(medicationId.isNotBlank()) { "Medicamento inválido." }
        val now=System.currentTimeMillis()
        val today=java.time.Instant.ofEpochMilli(now)
            .atZone(java.time.ZoneId.systemDefault()).toLocalDate()
        val due=list("pending_intakes").firstOrNull{
            it.fields["medication_id"]==medicationId &&
            it.timestamp<=now+300000L &&
            java.time.Instant.ofEpochMilli(it.timestamp)
                .atZone(java.time.ZoneId.systemDefault()).toLocalDate()==today
        }
        return if(due!=null)confirmScheduledIntake(medicationId,name,due.timestamp)
            else synchronized(intakeLock){
                add("intakes",name,mapOf("medication_id" to medicationId))
            }
    }
''', "pending and confirmed dose storage")

receiver=base/"notifications/NotificationReceiver.kt"
patch(receiver,
    'import com.mediagenda.app.data.MedicationPhotoLoader',
    'import com.mediagenda.app.data.MedicationPhotoLoader\nimport com.mediagenda.app.data.PersonalHealthStore',
    "notification store import")
patch(receiver,
    '''            manager.notify(id, builder.build())
        } finally {''',
    '''            manager.notify(id, builder.build())
            // Persist the occurrence only when a real scheduled medicine alert
            // was actually dispatched. A test reminder never creates a dose.
            if(!medicationId.isNullOrBlank() && scheduledAt>0L &&
                ProfileStore(context).all().any{it.id==profileId}){
                runCatching{
                    val med=DataRepository(context,profileId).loadMedications()
                        .firstOrNull{it.id==medicationId}
                    if(med!=null)PersonalHealthStore(context,profileId)
                        .noteReminder(med.id,med.medication.ifBlank{"Medicação"},scheduledAt)
                }.onFailure{
                    android.util.Log.e("SaudePratica","Failed to save pending dose",it)
                }
            }
        } finally {''',
    "record unconfirmed after real notification")

intake=base/"notifications/IntakeActionReceiver.kt"
patch(intake,
    '''        val already=store.list("intakes").any{
            it.fields["medication_id"]==medId &&
            it.fields["scheduled_at"]==scheduledAt.toString()
        }
        if(!already){
            try {
                store.add("intakes",med.medication.ifBlank{"Medicação"},
                    mapOf("medication_id" to medId,
                        "scheduled_at" to scheduledAt.toString(),
                        "source" to "notification"))
            }catch(_:Exception){
                // Never claim that the dose was logged after a write error.
                return
            }
        }
''',
    '''        try {
            store.confirmScheduledIntake(medId,med.medication.ifBlank{"Medicação"},
                scheduledAt)
        }catch(e:Exception){
            android.util.Log.e("SaudePratica","Could not confirm dose",e)
            return
        }
''',
    "notification marks dose confirmed")

records=base/"HealthRecordsActivity.kt"
patch(records,
    '''        if(category=="emergency"){showEmergency();return}
        val head=LinearLayout(this).apply{''',
    '''        if(category=="emergency"){showEmergency();return}
        if(category=="intakes"){showIntakeHistory();return}
        val head=LinearLayout(this).apply{''',
    "separate intake history view")
patch(records,
    '''    private fun actions(item:PersonalHealthRecord){''',
    '''    private fun showIntakeHistory(){
        val confirmed=runCatching{store.list("intakes")}.getOrElse{
            alert("Erro ao ler tomas confirmadas: "+it.message);emptyList()
        }
        val checked=confirmed.mapNotNull{
            val id=it.fields["medication_id"].orEmpty()
            val date=it.fields["scheduled_at"].orEmpty()
            if(id.isNotBlank() && date.isNotBlank())id+"|"+date else null
        }.toSet()
        val pending=runCatching{store.list("pending_intakes")}.getOrElse{
            alert("Erro ao ler tomas pendentes: "+it.message);emptyList()
        }.filter{
            (it.fields["medication_id"].orEmpty()+"|"+
                it.fields["scheduled_at"].orEmpty()) !in checked
        }
        val format=SimpleDateFormat("dd/MM/yyyy · HH:mm",Locale("pt","PT"))
        body.addView(label("⏳ Tomas por confirmar",19f,true).apply{
            setPadding(dp(4),dp(18),0,dp(8))
        })
        body.addView(label(pending.size.toString()+" toma(s) pendente(s)",13f,
            color=muted).apply{setPadding(dp(4),0,0,dp(12))})
        if(pending.isEmpty()){
            body.addView(label("Não existem tomas pendentes.",13f,
                color=muted).apply{setPadding(dp(8),dp(6),0,dp(18))})
        }
        pending.forEach{item->
            val shell=card()
            val column=LinearLayout(this).apply{
                orientation=LinearLayout.VERTICAL
                setPadding(dp(15),dp(14),dp(15),dp(14))
            }
            column.addView(label(item.title,16f,true))
            val whenDue=item.fields["scheduled_at"]?.toLongOrNull()?:item.timestamp
            column.addView(label("Aviso: "+format.format(Date(whenDue)),12f,
                color=muted))
            column.addView(label("Aguardando confirmação da toma",12f,
                color=muted).apply{setPadding(0,dp(5),0,dp(8))})
            column.addView(button("✓ TOMEI — confirmar agora"){
                MaterialAlertDialogBuilder(this)
                    .setTitle("Confirmar toma")
                    .setMessage("Confirmas que tomaste "+item.title+"? "+
                        "A hora da confirmação será guardada agora.")
                    .setPositiveButton("Sim, tomei"){_,_->
                        val medId=item.fields["medication_id"].orEmpty()
                        runCatching{
                            store.confirmScheduledIntake(medId,item.title,whenDue)
                        }.onSuccess{refresh()}
                         .onFailure{alert(it.message?:"Não foi possível confirmar a toma.")}
                    }.setNegativeButton("Cancelar",null).show()
            })
            shell.addView(column)
            addCard(shell)
        }
        body.addView(label("✅ Tomas confirmadas",19f,true).apply{
            setPadding(dp(4),dp(18),0,dp(8))
        })
        body.addView(label(confirmed.size.toString()+" toma(s) confirmada(s)",
            13f,color=muted).apply{setPadding(dp(4),0,0,dp(12))})
        if(confirmed.isEmpty()){
            body.addView(label("Nenhuma toma confirmada.",13f,color=muted)
                .apply{setPadding(dp(8),dp(6),0,dp(15))})
        }
        confirmed.forEach{item->
            val shell=card()
            val row=LinearLayout(this).apply{
                orientation=LinearLayout.HORIZONTAL
                gravity=Gravity.CENTER_VERTICAL
                setPadding(dp(15),dp(14),dp(13),dp(14))
            }
            val col=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
            col.addView(label(item.title,16f,true))
            col.addView(label("Confirmada: "+format.format(Date(item.timestamp)),
                12f,color=muted))
            val scheduled=item.fields["scheduled_at"]?.toLongOrNull()
            if(scheduled!=null)col.addView(label(
                "Aviso: "+format.format(Date(scheduled)),12f,color=muted))
            row.addView(col,LinearLayout.LayoutParams(
                0,ViewGroup.LayoutParams.WRAP_CONTENT,1f))
            row.addView(label("›",28f,color=teal))
            shell.addView(row)
            shell.setOnClickListener{actions(item)}
            addCard(shell)
        }
        body.addView(label("Os avisos ficam por confirmar até registares "+
            "manualmente que tomaste. Uma notificação não comprova uma toma.",
            12f,color=muted).apply{
                setPadding(dp(8),dp(18),dp(8),dp(25))
            })
    }
    override fun onResume(){
        super.onResume()
        if(::body.isInitialized)refresh()
    }
    private fun actions(item:PersonalHealthRecord){''',
    "pending and confirmed grouped history")
patch(records,
    '''            else->Triple("✅","Tomas confirmadas","Histórico de medicação tomada")''',
    '''            else->Triple("💊","Tomas","Por confirmar e confirmadas")''',
    "history title")

main=base/"MainActivity.kt"
patch(main,
    '''DashboardModule("✅", "Tomas", "Histórico confirmado") { healthRecords("intakes") }''',
    '''DashboardModule("✅", "Tomas", "Pendentes e confirmadas") { healthRecords("intakes") }''',
    "Tomas menu label")

gradle=root/"app/build.gradle.kts"
patch(gradle,"versionCode = 40","versionCode = 41","versionCode")
patch(gradle,'versionName = "1.9.30"','versionName = "1.9.31"',"versionName")
print("v1.9.31: every real medication alert logs a pending dose; TOMEI confirms once, grouped in the Tomas module.")
