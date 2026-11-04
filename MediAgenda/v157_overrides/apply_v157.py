#!/usr/bin/env python3
"""Android 1.9.137: compact team, per-process navigation, fixed calendar list."""
from pathlib import Path
from hashlib import sha256
src=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app")
gradle=src.parents[3]/"build.gradle.kts"
protected=["notifications/MedicationAlarmService.kt","notifications/NotificationScheduler.kt",
 "notifications/NotificationReceiver.kt","notifications/MedicationAlarmCoordinator.kt",
 "notifications/MedicationAlarmPreferences.kt","notifications/IntakeActionReceiver.kt",
 "notifications/DeviceAlarmRouting.kt"]
hashes={p:sha256((src/p).read_bytes()).hexdigest() for p in protected if (src/p).exists()}
assert len(hashes)>=5

def replace(text,old,new,tag):
    assert text.count(old)==1,(tag,text.count(old))
    return text.replace(old,new,1)

w=src/"WorkMedicineActivity.kt"
s=w.read_text()
start=s.index("        clinicalEntries.forEachIndexed{index,record->")
stop=s.index('        clinicalCard.addView(button("＋ Adicionar número de observação / processo"){',start)
s=s[:start]+'''        clinicalEntries.forEachIndexed{_,record->
            val unit=if(record.contains("|"))record.substringBefore("|").trim() else ""
            val number=if(record.contains("|"))record.substringAfter("|").trim() else record
            val display=if(unit.isBlank())number else unit+" · "+number
            clinicalCard.addView(button("🏥 "+display){
                startActivity(android.content.Intent(this,HospitalProcessActivity::class.java)
                    .putExtra(HospitalProcessActivity.EXTRA_PROFILE_ID,patientId)
                    .putExtra(HospitalProcessActivity.EXTRA_HOSPITAL,unit)
                    .putExtra(HospitalProcessActivity.EXTRA_PROCESS,number))
            })
        }
'''+s[stop:]
s=replace(s,"    private fun redraw(){",'''    override fun onResume(){
        super.onResume()
        if(::body.isInitialized)redraw()
    }

    private fun redraw(){''',"resume refresh")
w.write_text(s)

h=src/"HospitalProcessActivity.kt"
s=h.read_text()
s=replace(s,"import androidx.appcompat.app.AppCompatActivity",
'''import androidx.appcompat.app.AppCompatActivity
import androidx.core.widget.doAfterTextChanged
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat''',"imports")
s=replace(s,"        scroll.addView(body)\n        setContentView(scroll)",
'''        ViewCompat.setOnApplyWindowInsetsListener(scroll){view,insets->
            val safe=insets.getInsets(WindowInsetsCompat.Type.systemBars())
            view.setPadding(0,safe.top,0,safe.bottom)
            insets
        }
        scroll.addView(body)
        setContentView(scroll)''',"insets")
s=replace(s,'        body.addView(button("‹ Voltar à Situação Clínica"){finish()})',
'''        body.addView(button("‹ Voltar à Situação Clínica"){finish()})
        body.addView(row("✎ Editar processo" to {editProcess()},
            "× Eliminar processo" to {deleteProcess()}))''',"detail controls")
start=s.index("    private fun showTeam(){")
stop=s.index("    private fun editTeam(index:Int?){",start)
compact=r'''    private fun smallAction(label:String,description:String,callback:()->Unit)=
        MaterialButton(this).apply{
            text=label;contentDescription=description
            isAllCaps=false;textSize=17f;minWidth=dp(42);minHeight=dp(42)
            insetTop=0;insetBottom=0
            setPadding(0,0,0,0);cornerRadius=dp(10)
            backgroundTintList=ColorStateList.valueOf(Color.rgb(5,91,98))
            setTextColor(Color.WHITE)
            setOnClickListener{callback()}
        }

    private fun showTeam(){
        val entries=list("team")
        val card=panel("👩‍⚕️ A minha equipa",
            entries.length().toString()+" profissionais · só deste processo")
        val search=field("🔎 Procurar nome, especialidade ou email")
        card.addView(search)
        val rows=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
        card.addView(rows)
        fun populate(filter:String){
            rows.removeAllViews()
            var shown=0
            for(i in 0 until entries.length()){
                val p=entries.optJSONObject(i)?:continue
                val name=p.optString("name")
                val specialty=p.optString("specialty")
                val email=p.optString("email")
                val phone=p.optString("phone")
                if(filter.isNotBlank() &&
                    !(name+" "+specialty+" "+email+" "+phone)
                        .contains(filter,true))continue
                shown++
                val line=LinearLayout(this).apply{
                    orientation=LinearLayout.HORIZONTAL
                    gravity=Gravity.CENTER_VERTICAL
                    setPadding(0,dp(5),0,dp(5))
                }
                val details=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
                details.addView(text(name,15f,true).apply{setPadding(0,0,0,0)})
                if(specialty.isNotBlank())
                    details.addView(text(specialty,12f).apply{setPadding(0,0,0,0)})
                if(email.isNotBlank())details.addView(text("✉ "+email,12f).apply{
                    setTextColor(Color.rgb(110,232,220))
                    setPadding(0,dp(1),0,0)
                    setOnClickListener{runCatching{startActivity(Intent(
                        Intent.ACTION_SENDTO,Uri.parse("mailto:"+Uri.encode(email))))}}
                })
                if(phone.isNotBlank())details.addView(text("☎ "+phone,12f).apply{
                    setTextColor(Color.rgb(110,232,220))
                    setPadding(0,dp(1),0,0)
                    setOnClickListener{runCatching{startActivity(Intent(
                        Intent.ACTION_DIAL,Uri.parse("tel:"+Uri.encode(phone))))}}
                })
                line.addView(details,LinearLayout.LayoutParams(0,-2,1f))
                line.addView(smallAction("✎","Editar "+name){editTeam(i)},
                    LinearLayout.LayoutParams(dp(42),dp(42)).apply{marginStart=dp(4)})
                line.addView(smallAction("×","Eliminar "+name){
                    removeRecord("team",i)
                },LinearLayout.LayoutParams(dp(42),dp(42)).apply{marginStart=dp(4)})
                rows.addView(line)
                rows.addView(View(this).apply{
                    setBackgroundColor(Color.rgb(54,82,96))
                },LinearLayout.LayoutParams(-1,dp(1)))
            }
            if(shown==0)rows.addView(text(
                if(entries.length()==0)"Sem profissionais."
                else "Nenhum contacto encontrado.",13f))
        }
        search.doAfterTextChanged{populate(it?.toString().orEmpty().trim())}
        populate("")
        card.addView(button("＋ Adicionar profissional"){editTeam(null)})
        card.addView(button("📂 Importar contactos JSON"){pickTeam.launch("*/*")})
    }

    private fun processPreferences()=getSharedPreferences(
        com.mediagenda.app.data.ProfileStore(this).preferencesFor(profileId),MODE_PRIVATE)

    private fun savedRecord(unit:String,number:String)=
        if(unit.isBlank())number else unit+" | "+number

    private fun editProcess(){
        val unitField=field("Unidade hospitalar",hospital)
        val numberField=field("Número de processo",process)
        MaterialAlertDialogBuilder(this).setTitle("Editar processo hospitalar")
            .setView(form(unitField,numberField))
            .setNegativeButton("Cancelar",null)
            .setPositiveButton("Guardar"){_,_->
                val u=unitField.text.toString().trim().replace("|","/")
                    .replace("\n"," ").take(180)
                val n=numberField.text.toString().trim().replace("|","/")
                    .replace("\n"," ").take(120)
                if(n.isBlank()){
                    Toast.makeText(this,"Indica o número do processo.",
                        Toast.LENGTH_LONG).show()
                }else{
                    val prefs=processPreferences()
                    val old=prefs.getString("observations_by_unit","").orEmpty()
                    val all=old.lines().filter{it.isNotBlank()}.toMutableList()
                    val pos=all.indexOfFirst{it.equals(savedRecord(hospital,process),true)}
                    val target=savedRecord(u,n)
                    if(pos<0||all.withIndex().any{
                            it.index!=pos && it.value.equals(target,true)}){
                        Toast.makeText(this,"Processo não encontrado ou duplicado.",
                            Toast.LENGTH_LONG).show()
                    }else{
                        val newKey=MessageDigest.getInstance("SHA-256").digest(
                            (u.lowercase(Locale.ROOT)+"|"+
                                n.lowercase(Locale.ROOT)).toByteArray())
                            .joinToString(""){"%02x".format(it)}
                        val original=database.toString()
                        val entry=processData()
                        val group=database.getJSONObject("processes")
                        if(newKey!=key && group.has(newKey)){
                            Toast.makeText(this,"A ficha já existe.",Toast.LENGTH_LONG).show()
                        }else{
                            entry.put("unit",u).put("number",n)
                            group.put(newKey,entry)
                            if(newKey!=key)group.remove(key)
                            all[pos]=target
                            if(save() && prefs.edit().putString("observations_by_unit",
                                    all.joinToString("\n")).commit()){
                                hospital=u;process=n;key=newKey;redraw()
                            }else{
                                database=JSONObject(original);save()
                            }
                        }
                    }
                }
            }.show()
    }

    private fun deleteProcess(){
        MaterialAlertDialogBuilder(this).setTitle("Eliminar processo?")
            .setMessage("Eliminar só esta unidade/número e os respetivos contactos, taxas, imagem e transportes? Os outros processos permanecem.")
            .setNegativeButton("Cancelar",null)
            .setPositiveButton("Eliminar"){_,_->
                val prefs=processPreferences()
                val old=prefs.getString("observations_by_unit","").orEmpty()
                val all=old.lines().filter{it.isNotBlank()}
                val remaining=all.filterNot{
                    it.equals(savedRecord(hospital,process),true)}
                if(all.size==remaining.size){
                    Toast.makeText(this,"Processo não encontrado.",Toast.LENGTH_LONG).show()
                }else if(prefs.edit().putString("observations_by_unit",
                        remaining.joinToString("\n")).commit()){
                    val pic=processData().optString("identity_image")
                    database.optJSONObject("processes")?.remove(key)
                    if(save()){
                        if(pic.matches(Regex("process_[0-9a-f]{20}[.]jpg")))
                            File(folder,pic).delete()
                        finish()
                    }else prefs.edit().putString("observations_by_unit",old).commit()
                }
            }.show()
    }

'''
s=s[:start]+compact+s[stop:]
h.write_text(s)

# Fix calendar: setMessage + setItems hides items on some Android devices.
p=main.read_text()
start=p.index("    private fun chooseAppointmentForSystemCalendar(){")
stop=p.index("    private fun showProfileSelection() {",start)
chooser=r'''    private fun chooseAppointmentForSystemCalendar(){
        val entries=repo.loadAppointments().filter{
            !it.cancelled && runCatching{java.time.LocalDate.parse(it.date)}.isSuccess
        }.sortedWith(compareBy<com.mediagenda.app.model.Appointment>{it.date}
            .thenBy{it.time})
        if(entries.isEmpty()){
            showError("Não há marcações neste perfil para exportar.")
            return
        }
        val today=java.time.LocalDate.now()
        val future=entries.filter{!java.time.LocalDate.parse(it.date).isBefore(today)}
        val history=entries.filter{java.time.LocalDate.parse(it.date).isBefore(today)}
        val layout=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(12),dp(12),dp(12),dp(10))
        }
        val tip=android.widget.TextView(this).apply{
            text="Escolhe uma consulta e confirma no Google Calendário. Uma de cada vez; não é sincronização automática."
            textSize=14f;setPadding(dp(5),0,dp(5),dp(12))
            setTextColor(if(isDarkPalette)Color.WHITE else Color.rgb(24,45,60))
        }
        val actions=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL}
        val items=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
        val scroll=android.widget.ScrollView(this).apply{addView(items)}
        layout.addView(tip);layout.addView(actions)
        layout.addView(scroll,LinearLayout.LayoutParams(-1,dp(350)))
        val dialog=com.google.android.material.dialog.MaterialAlertDialogBuilder(this)
            .setTitle("Marcação → Google Calendário")
            .setView(layout).setNegativeButton("Cancelar",null).create()
        fun export(a:com.mediagenda.app.model.Appointment){
            val day=java.time.LocalDate.parse(a.date)
            val time=runCatching{java.time.LocalTime.parse(a.time)}.getOrNull()
            val allDay=time==null
            val startMillis=if(allDay)
                day.atStartOfDay(java.time.ZoneOffset.UTC).toInstant().toEpochMilli()
                else day.atTime(time!!).atZone(java.time.ZoneId.systemDefault())
                    .toInstant().toEpochMilli()
            val intent=android.content.Intent(Intent.ACTION_INSERT).apply{
                data=android.provider.CalendarContract.Events.CONTENT_URI
                putExtra(android.provider.CalendarContract.Events.TITLE,
                    a.activity.ifBlank{"Marcação SaúdePrática"})
                putExtra(android.provider.CalendarContract.Events.DESCRIPTION,
                    "Exportada manualmente da SaúdePrática. Confirmar antes de guardar.")
                putExtra(android.provider.CalendarContract.EXTRA_EVENT_BEGIN_TIME,startMillis)
                putExtra(android.provider.CalendarContract.EXTRA_EVENT_END_TIME,
                    startMillis+if(allDay)86400000L else 3600000L)
                putExtra(android.provider.CalendarContract.Events.ALL_DAY,allDay)
            }
            try{startActivity(intent);dialog.dismiss()}
            catch(_:android.content.ActivityNotFoundException){
                showError("Não está instalada uma app de calendário compatível.")
            }
        }
        fun render(rows:List<com.mediagenda.app.model.Appointment>){
            items.removeAllViews()
            if(rows.isEmpty())items.addView(android.widget.TextView(this).apply{
                text="Sem marcações nesta categoria."
                setTextColor(if(isDarkPalette)Color.WHITE else Color.DKGRAY)
                textSize=14f;setPadding(dp(7),dp(18),0,dp(18))
            })
            rows.forEach{a->
                items.addView(secondaryButton(
                    a.date+" · "+a.time.ifBlank{"Dia inteiro"}+"\n"+
                    a.activity.take(80)){
                    export(a)
                }.apply{
                    isAllCaps=false;textSize=14f;setTextColor(Color.WHITE)
                    backgroundTintList=android.content.res.ColorStateList.valueOf(
                        Color.rgb(4,100,105))
                })
            }
        }
        actions.addView(secondaryButton("Próximas ("+future.size+")"){
            render(future)
        },LinearLayout.LayoutParams(0,dp(45),1f))
        actions.addView(secondaryButton("Histórico ("+history.size+")"){
            render(history.reversed())
        },LinearLayout.LayoutParams(0,dp(45),1f))
        render(future)
        dialog.show()
    }

'''
p=p[:start]+chooser+p[stop:]
p=replace(p,'secondaryButton("📅 Adicionar consulta ao calendário do telemóvel")',
            'secondaryButton("📅 Enviar marcação ao Google Calendário")',
            "calendar label")
main.write_text(p)
g=gradle.read_text()
g=replace(g,"versionCode = 146","versionCode = 147","code")
g=replace(g,'versionName = "1.9.136"','versionName = "1.9.137"',"name")
gradle.write_text(g)
for file,digest in hashes.items():
    assert sha256((src/file).read_bytes()).hexdigest()==digest,file
print("Android 1.9.137 OK; protected alarms untouched")
