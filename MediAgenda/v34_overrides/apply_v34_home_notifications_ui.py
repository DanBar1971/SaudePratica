from pathlib import Path

main=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app/MainActivity.kt")
s=main.read_text(encoding="utf-8")
def change(old,new,description):
    global s
    if old not in s:raise RuntimeError("v1.9.15: missing "+description)
    s=s.replace(old,new,1)

start=s.index('''        val now=LocalDateTime.now()''', s.index("    private fun showHome()"))
end=s.index('''        val options = listOf(''',start)
s=s[:start]+'''        // Preserve the original compact status row beneath the personal
        // greeting. No bulky duplicate medication or agenda cards here.
        val totalMed=repo.loadMedications().size
        val outstanding=repo.loadAppointments().count{!it.done}
        box.addView(TextView(this).apply {
            text="$totalMed medicamento(s)  ·  $outstanding marcação(ões) por concluir"
            textSize=13f
            setTextColor(muted)
            setPadding(dp(4),dp(6),0,dp(15))
        })

'''+s[end:]

start=s.index('''        box.addView(infoCard("🔔", "Testar notificação"''')
end=s.index('''        box.addView(infoCard("⇩", "Importar JSON"''',start)
s=s[:start]+'''        box.addView(infoCard("🔔", "Notificações",
            "Testar avisos de agendamentos e alarmes de medicação") {
            showNotificationsMenu()
        })
'''+s[end:]

before="    private fun showDataTools() {"
assert before in s
helper='''    private fun showNotificationsMenu(){
        content.removeAllViews()
        screenHeader("🔔","Notificações","Testes e permissões por tipo de aviso")
        val scroll=ScrollView(this).apply{overScrollMode=View.OVER_SCROLL_NEVER}
        val box=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
        box.addView(noteBox("Avisos separados",
            "A agenda usa um som suave; a medicação usa um alarme forte. "+
            "Estes dois testes enviam apenas um aviso e não registam tomas."))
        box.addView(secondaryButton("📅 Testar notificação de agendamento"){
            testHealthNotification("appointment")
        })
        box.addView(noteBox("Agendamento",
            "Aviso da agenda, com som normal e vibração breve. "+
            "As marcações são lembradas às 18:00 do dia anterior."))
        box.addView(secondaryButton("💊 Testar alarme de medicação"){
            testHealthNotification("medication")
        })
        box.addView(noteBox("Medicação",
            "Alarme forte, separado das notificações da agenda. "+
            "O botão «Tomei» aparece apenas nos avisos reais de um medicamento."))
        box.addView(secondaryButton("⚙ Definições de notificações do Android"){
            startActivity(Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).apply{
                putExtra(Settings.EXTRA_APP_PACKAGE,packageName)
            })
        })
        box.addView(TextView(this).apply{
            text="O volume, os sons e os avisos no ecrã bloqueado podem ser alterados "+
                "nas definições de notificações do Android."
            textSize=12f
            setTextColor(muted)
            setPadding(dp(10),dp(18),dp(10),dp(24))
        })
        scroll.addView(box)
        content.addView(scroll,LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,0,1f))
        renderBottomNav(4)
    }

    private fun testHealthNotification(kind:String){
        if(Build.VERSION.SDK_INT>=33 &&
            ContextCompat.checkSelfPermission(this,Manifest.permission.POST_NOTIFICATIONS)
                !=PackageManager.PERMISSION_GRANTED){
            requestNotificationPermission()
            Toast.makeText(this,
                "Autoriza as notificações e volta a tocar no teste.",Toast.LENGTH_LONG).show()
            return
        }
        val med=kind=="medication"
        NotificationReceiver().onReceive(this,
            Intent(this,NotificationReceiver::class.java).apply{
                putExtra("profile_id",activeProfileId)
                putExtra("reminder_kind",kind)
                putExtra("title",if(med)"💊 Teste do alarme de medicação"
                    else "📅 Teste do aviso de agendamento")
                putExtra("body",if(med)
                    "Este é um alarme de teste: não foi registada nenhuma toma."
                    else "Este é um aviso de teste, com som mais discreto.")
                putExtra("notification_id",if(med)991501 else 991502)
            })
        Toast.makeText(this,"Teste enviado.",Toast.LENGTH_SHORT).show()
        if(med && Build.VERSION.SDK_INT>=Build.VERSION_CODES.S &&
            !getSystemService(AlarmManager::class.java).canScheduleExactAlarms()){
            requestExactAlarmAccess()
        }
    }

'''
s=s.replace(before,helper+before,1)
main.write_text(s,encoding="utf-8")
print("Home compact greeting restored; Mais -> Notificações has separate appointment/medication tests.")
