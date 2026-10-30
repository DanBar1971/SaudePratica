from pathlib import Path

main=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app/MainActivity.kt")
s=main.read_text(encoding="utf-8")
def sub(old,new,label):
    global s
    if old not in s:raise RuntimeError("SaúdePrática home greeting missing "+label)
    s=s.replace(old,new,1)

sub('''        screenHeader("⌂", "Início", "A sua saúde, tudo num só lugar")''',
'''        screenHeader("⌂", "Início", "")''',"remove home slogan")

start=s.index('''        val who = profileName().ifBlank { "Utilizador" }''',s.index("    private fun showHome()"))
end=s.index('''        val options = listOf(''',start)
s=s[:start]+'''        val now=LocalDateTime.now()
        val nextMed=repo.loadMedications().mapNotNull { med ->
            nextMedicationTime(med)?.let { med to it }
        }.minByOrNull { it.second }
        val nextAp=repo.loadAppointments().filter{!it.done}.mapNotNull { appointment ->
            upcomingAppointmentTime(appointment,now)?.let { appointment to it }
        }.minByOrNull { it.second }
        fun whenText(value:LocalDateTime):String {
            val day=when(value.toLocalDate()){
                now.toLocalDate()->"Hoje"
                now.toLocalDate().plusDays(1)->"Amanhã"
                else->value.format(DateTimeFormatter.ofPattern("dd MMM",Locale("pt","PT")))
            }
            return "$day às ${value.format(DateTimeFormatter.ofPattern("HH:mm"))}"
        }
        val nextMedText=nextMed?.let{(med,date)->
            whenText(date)+" · "+med.medication.ifBlank{"Medicação programada"}
        } ?: "Sem tomas programadas."
        val nextApText=nextAp?.let{(appointment,date)->
            whenText(date)+" · "+appointment.activity.ifBlank{
                appointment.department.ifBlank{"Marcação"}
            }
        } ?: "Sem consultas ou exames futuros registados."
        // Quick personalised preview, not a second copy of the module menu.
        box.addView(infoCard("💊","Próxima medicação",nextMedText){showMedication()})
        box.addView(infoCard("📅","Próxima marcação",nextApText){showAgenda()})

''' +s[end:]

anchor='''    private fun showHome() {'''
helper='''    private fun upcomingAppointmentTime(ap:Appointment,
        now:LocalDateTime=LocalDateTime.now()):LocalDateTime? {
        val start=runCatching{LocalDate.parse(ap.date)}.getOrNull()?:return null
        val time=runCatching{LocalTime.parse(ap.time)}.getOrNull()?:return null
        val recur=ap.recurrence
        val until=runCatching{LocalDate.parse(recur.until)}.getOrNull()
        return (0..366).asSequence()
            .map{now.toLocalDate().plusDays(it.toLong())}
            .filter{!it.isBefore(start)}
            .filter{until==null||!it.isAfter(until)}
            .filter{day->
                when(recur.mode){
                    "weekdays"->day.dayOfWeek.value in 1..5
                    "weekly"->if(recur.weekdays.isEmpty())
                        day.dayOfWeek==start.dayOfWeek
                        else (day.dayOfWeek.value-1) in recur.weekdays
                    else->day==start
                }
            }.map{LocalDateTime.of(it,time)}
            .firstOrNull{it.isAfter(now)}
    }

'''
sub(anchor,helper+anchor,"appointment summary helper")
sub('''            text = "$icon  $title"
            textSize = 27f''',
'''            text = if(title=="Início")
                "Olá, ${profileName().ifBlank{"bem-vindo"}}!"
                else "$icon  $title"
            textSize = 27f''',"hello in main title")
sub('''        brand.addView(TextView(this).apply {
            text = subtitle
            textSize = 13f
            setTextColor(muted)
            setPadding(0, dp(3), 0, 0)
        })''',
'''        if(title!="Início")brand.addView(TextView(this).apply {
            text = subtitle
            textSize = 13f
            setTextColor(muted)
            setPadding(0, dp(3), 0, 0)
        })''',"hide home tagline")
sub('''                text=profile.take(12)
                textSize=12f''',
'''                text=if(title=="Início")"⌄" else profile.take(12)
                textSize=12f''',"avoid repeated name in badge")
main.write_text(s,encoding="utf-8")
print("Home now says Olá + active profile and previews the next med and appointment; Início heading and old generic tagline removed.")
