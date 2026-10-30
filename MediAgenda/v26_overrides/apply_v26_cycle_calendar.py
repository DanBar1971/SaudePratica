from pathlib import Path
path=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app/MonthlyCalendarActivity.kt")
s=path.read_text(encoding="utf-8")
def edit(old,new,label):
 global s
 if old not in s:raise RuntimeError("v1.9.7 cycle calendar missing "+label)
 s=s.replace(old,new,1)
edit('''import java.time.LocalDate''','''import java.time.LocalTime
import java.time.LocalDate''',"time import")
edit('''import android.content.res.Configuration''','''import android.app.DatePickerDialog
import android.app.TimePickerDialog
import android.content.res.Configuration''',"picker imports")
edit('''import com.mediagenda.app.data.DataRepository''','''import com.mediagenda.app.data.DataRepository
import com.mediagenda.app.data.CycleStore
import com.mediagenda.app.notifications.NotificationScheduler
import com.google.android.material.dialog.MaterialAlertDialogBuilder''',"store imports")
edit('''    companion object{const val PROFILE="profile_id"}
    private var month=YearMonth.now()''','''    companion object{
        const val PROFILE="profile_id"
        const val MODE="mode"
    }
    private var periodMode=false
    private lateinit var cycle:CycleStore
    private var month=YearMonth.now()''',"mode")
edit('''        val root=LinearLayout(this).apply{''','''        periodMode=intent.getStringExtra(MODE)=="cycle"
        cycle=CycleStore(this,profileId)
        val root=LinearLayout(this).apply{''',"init")
edit('''        textHead.addView(label("📅 Calendário Mensal",23f,true))
        textHead.addView(label("Consultas e exames deste utilizador",12f,c=muted))''',
'''        textHead.addView(label(if(periodMode)"🌸 Ciclo Menstrual" else "📅 Calendário Mensal",23f,true))
        textHead.addView(label(if(periodMode)"Período e pílula deste utilizador" else "Consultas e exames deste utilizador",12f,c=muted))''',
"header")
edit('''                val count=onDate(date).size
                val cell=LinearLayout(this).apply{''',
'''                val count=onDate(date).size
                val period=periodMode && cycle.periods().any{date>=it.start&&date<=it.end}
                val predicted=periodMode && cycle.estimatedNext()==date
                val pill=periodMode && cycle.pillDay(date)
                val cell=LinearLayout(this).apply{''',"day state")
edit('''                    setBackgroundColor(if(selected==date)
                        if(dark)Color.rgb(11,87,85)else Color.rgb(220,248,243)
                        else Color.TRANSPARENT)''',
'''                    setBackgroundColor(when {
                        selected==date->if(dark)Color.rgb(11,87,85)else Color.rgb(220,248,243)
                        period->if(dark)Color.rgb(106,46,73)else Color.rgb(255,221,230)
                        else->Color.TRANSPARENT
                    })''',"day background")
edit('''                cell.addView(label(if(count>0)"●" else " ",13f,c=teal))''',
'''                val marker=buildString{
                    if(count>0)append("•")
                    if(period)append("♥")else if(predicted)append("◌")
                    if(pill)append(if(cycle.pillTaken(date))"✓" else "·")
                }
                cell.addView(label(marker.ifBlank{" "},12f,
                    c=if(period)Color.rgb(237,109,143)else teal))''',"cycle marks")
edit('''        body.addView(label("● Dias com agendamentos",12f,c=muted).apply{''',
'''        body.addView(label(if(periodMode)
            "♥ Período · ◌ Previsão · ✓ Pílula confirmada · • Agendamento"
            else "● Dias com agendamentos",12f,c=muted).apply{''',"legend")
edit('''        val titleDay=selected.format(DateTimeFormatter.ofPattern("EEEE, dd 'de' MMMM",pt))''',
'''        if(periodMode){cycleControls();return}
        val titleDay=selected.format(DateTimeFormatter.ofPattern("EEEE, dd 'de' MMMM",pt))''',"branch controls")
anchor='''    private fun onDate(date:LocalDate):List<Appointment> ='''
methods='''    private fun datePicker(default:LocalDate,chosen:(LocalDate)->Unit){
        DatePickerDialog(this,{_,year,month,day->
            chosen(LocalDate.of(year,month+1,day))
        },default.year,default.monthValue-1,default.dayOfMonth).show()
    }

    private fun cycleControls(){
        val dateText=selected.format(DateTimeFormatter.ofPattern("dd/MM/yyyy"))
        body.addView(label("Dia selecionado: "+dateText,17f,true).apply{
            setPadding(0,dp(15),0,dp(12))
        })
        val prev=cycle.periods().firstOrNull()
        body.addView(label(if(prev==null)"Ainda não há períodos registados."
            else "Último período: "+prev.start.toString()+" a "+prev.end.toString(),14f,c=muted))
        val estimate=cycle.estimatedNext()
        body.addView(label(if(estimate==null)"Registe o período para calcular uma estimativa."
            else "Próximo início estimado: "+estimate.format(DateTimeFormatter.ofPattern("dd/MM/yyyy")),
            13f,c=muted).apply{setPadding(0,dp(8),0,dp(12))})
        body.addView(outlined("+ Registar período"){datePicker(selected){start->
            datePicker(start){end->
                try{
                    cycle.addPeriod(start,end)
                    month=YearMonth.from(start);selected=start
                    display()
                }catch(e:Exception){showMessage(e.message?:"Datas inválidas.")}
            }
        }})
        val entry=cycle.periods().firstOrNull{selected>=it.start&&selected<=it.end}
        if(entry!=null)body.addView(outlined("Apagar período selecionado"){
            MaterialAlertDialogBuilder(this).setTitle("Apagar registo?")
                .setMessage("Eliminar o período iniciado em "+entry.start.toString()+"?")
                .setPositiveButton("Apagar"){_,_->cycle.removePeriod(entry.start);display()}
                .setNegativeButton("Cancelar",null).show()
        })
        val pattern=cycle.pillPattern
        val regimen=when(pattern){
            "daily"->"Todos os dias"
            "21_7"->"21 dias + 7 de pausa"
            "24_4"->"24 dias + 4 de pausa/placebo"
            else->"Não configurada"
        }
        body.addView(label("Pílula: "+regimen,16f,true).apply{
            setPadding(0,dp(16),0,dp(6))
        })
        if(pattern!="off"){
            body.addView(label("Hora: "+cycle.pillTime.toString()+
                " · Avisos: "+if(cycle.alerts)"ligados" else "desligados",13f,c=muted))
        }
        body.addView(outlined("⚙ Configurar pílula"){configurePill()})
        if(cycle.pillDay(selected) && selected<=LocalDate.now()){
            body.addView(outlined(
                if(cycle.pillTaken(selected))"✓ Toma confirmada (desfazer)"
                else "✓ Confirmar toma neste dia"){
                val already=cycle.pillTaken(selected)
                MaterialAlertDialogBuilder(this).setTitle("Registo da pílula")
                    .setMessage(if(already)"Retirar a confirmação deste dia?"
                        else "Confirmas que tomaste a pílula no dia "+dateText+"?")
                    .setPositiveButton(if(already)"Desfazer" else "Confirmar"){_,_->
                        cycle.setPillTaken(selected,!already);display()
                    }.setNegativeButton("Cancelar",null).show()
            })
        }
        body.addView(label(
            "As previsões são aproximadas e não identificam dias seguros para evitar gravidez. "+
            "O esquema da pílula e as pausas devem corresponder à indicação médica e à bula. "+
            "Em caso de esquecimento, segue essas instruções; esta aplicação não avalia proteção contracetiva.",
            12f,c=muted).apply{setPadding(dp(7),dp(18),dp(7),dp(22))})
    }

    private fun showMessage(message:String){
        MaterialAlertDialogBuilder(this).setTitle("SaúdePrática").setMessage(message)
            .setPositiveButton("OK",null).show()
    }

    private fun configurePill(){
        val patterns=arrayOf(
            "Sem pílula / desativar",
            "Todos os dias",
            "21 dias de toma e 7 de pausa",
            "24 dias de toma e 4 de pausa ou placebo"
        )
        MaterialAlertDialogBuilder(this).setTitle("Esquema da pílula")
            .setMessage("Escolhe apenas o esquema indicado pelo profissional de saúde. "+
                "Os lembretes são opcionais e desligados por defeito.")
            .setItems(patterns){_,which->
                if(which==0){
                    cycle.alerts=false
                    cycle.pillPattern="off"
                    NotificationScheduler(this).scheduleAllProfiles()
                    display()
                }else{
                    val pattern=when(which){1->"daily";2->"21_7";else->"24_4"}
                    datePicker(cycle.pillStart){start->
                        val t=cycle.pillTime
                        TimePickerDialog(this,{_,hour,minute->
                            MaterialAlertDialogBuilder(this)
                                .setTitle("Ativar lembretes?")
                                .setMessage("Queres receber um aviso à hora escolhida? "+
                                    "Os avisos devem ser configurados conforme a tua receita.")
                                .setPositiveButton("Sim, ativar"){_,_->
                                    savePill(pattern,start,LocalTime.of(hour,minute),true)
                                }
                                .setNegativeButton("Sem avisos"){_,_->
                                    savePill(pattern,start,LocalTime.of(hour,minute),false)
                                }.show()
                        },t.hour,t.minute,true).show()
                    }
                }
            }.setNegativeButton("Cancelar",null).show()
    }
    private fun savePill(pattern:String,start:LocalDate,time:LocalTime,alerts:Boolean){
        cycle.pillPattern=pattern;cycle.pillStart=start
        cycle.pillTime=time;cycle.alerts=alerts
        NotificationScheduler(this).scheduleAllProfiles()
        display()
    }

'''
edit(anchor,methods+anchor,"methods")
path.write_text(s,encoding="utf-8")
print("SaúdePrática v1.9.7 cycle controls, calendar markings, pill regimen and optional reminders.")
