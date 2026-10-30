from pathlib import Path

base=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app")
pin=base/"SaudePraticaApplication.kt"
s=pin.read_text(encoding="utf-8")
old='''    override fun onActivityStopped(activity:Activity) {
        started=(started-1).coerceAtLeast(0)
        if(started==0){
            AppPinSession.unlocked=false
            AppPinSession.gateRequested=false
        }
    }'''
new='''    override fun onActivityStopped(activity:Activity) {
        // Opening Android's contact picker, file manager, WhatsApp or simply
        // switching apps must not revoke an already verified PIN session.
        // The session is process-local: it naturally expires when Android
        // terminates the app's process or after a device restart.
        started=(started-1).coerceAtLeast(0)
    }'''
assert s.count(old)==1
pin.write_text(s.replace(old,new,1),encoding="utf-8")

splash=base/"SplashActivity.kt"
s=splash.read_text(encoding="utf-8")
old='''            val destination=if(pinEnabled)AppPinActivity::class.java else MainActivity::class.java'''
new='''            val destination=if(pinEnabled && !AppPinSession.unlocked)
                AppPinActivity::class.java else MainActivity::class.java'''
assert s.count(old)==1
s=s.replace(old,new,1)
s=s.replace('''                if(pinEnabled)putExtra(AppPinActivity.FROM_SPLASH,true)''',
'''                if(destination==AppPinActivity::class.java)
                    putExtra(AppPinActivity.FROM_SPLASH,true)''',1)
splash.write_text(s,encoding="utf-8")

main=base/"MainActivity.kt"
s=main.read_text(encoding="utf-8")
def change(old,new,label):
    global s
    if s.count(old)!=1:
        raise RuntimeError("SaúdePrática 1.9.21: missing "+label+": "+str(s.count(old)))
    s=s.replace(old,new,1)

change('''import com.mediagenda.app.data.AppPinStore''',
'''import com.mediagenda.app.data.AppPinStore
import com.mediagenda.app.data.FamilyBackupStore''',"backup import")

# Register ActivityResultContracts launchers along with the existing launchers,
# never register them dynamically after the Activity has started.
change('''    private val phoneContactPicker = registerForActivityResult(''',
'''    private val familyExport = registerForActivityResult(
        ActivityResultContracts.CreateDocument("application/zip")
    ) { uri -> uri?.let { exportFamilyZip(it) } }
    private val familyImport = registerForActivityResult(
        ActivityResultContracts.OpenDocument()
    ) { uri -> uri?.let { askRestoreFamilyZip(it) } }

    private val phoneContactPicker = registerForActivityResult(''',
"backup activity result launchers")

change('''    private data class DashboardModule(
        val icon: String, val title: String, val subtitle: String, val action: () -> Unit
    )''',
'''    private data class DashboardModule(
        val icon: String, val title: String, val subtitle: String, val action: () -> Unit
    )

    // Settings are per-user and do not erase any hidden module's data.
    private val dashboardLabels=listOf(
        "Medicação","Tomas","Agenda","Calendário","Documentos",
        "Análises Clínicas","Saúde Ocupacional","Beber água",
        "Ciclo Menstrual","Nutrição","Saúde Visual","Sintomas",
        "Medições","Vacinas","Emergência","Farmácias","SNS 24",
        "Despesas de Saúde"
    )
    private fun dashboardPrefs()=getSharedPreferences(
        "saudepratica_modules_"+activeProfileId,MODE_PRIVATE)

    private fun showDashboardChecklist(){
        val hidden=dashboardPrefs().getStringSet("hidden",emptySet())
            .orEmpty().toMutableSet()
        val options=dashboardLabels.toTypedArray()
        val checked=BooleanArray(options.size){options[it] !in hidden}
        MaterialAlertDialogBuilder(this)
            .setTitle("Módulos do ecrã principal")
            .setMessage("Seleciona os módulos que queres ver no Início. "+
                "Os dados dos módulos ocultos não são apagados. "+
                "O módulo Mais fica sempre disponível.")
            .setMultiChoiceItems(options,checked){_,index,value->
                checked[index]=value
            }
            .setPositiveButton("Guardar"){_,_->
                val invisible=options.filterIndexed{index,_->!checked[index]}.toSet()
                dashboardPrefs().edit().putStringSet("hidden",invisible).apply()
                showDataTools()
            }
            .setNeutralButton("Mostrar todos"){_,_->
                dashboardPrefs().edit().remove("hidden").apply()
                showDataTools()
            }.setNegativeButton("Cancelar",null).show()
    }

    private fun exportFamilyZip(uri:Uri){
        val pending=MaterialAlertDialogBuilder(this)
            .setTitle("A criar backup completo")
            .setMessage("A guardar os perfis, fotografias, documentos e dados…")
            .setCancelable(false).show()
        Thread{
            val outcome=runCatching{FamilyBackupStore(this).export(uri)}
            runOnUiThread{
                if(!isFinishing)pending.dismiss()
                outcome.onSuccess{summary->
                    MaterialAlertDialogBuilder(this)
                        .setTitle("Backup completo criado")
                        .setMessage("Utilizadores: "+summary.profiles+
                            "\\nFicheiros: "+summary.files+
                            "\\n\\nEste ZIP contém dados clínicos e documentos "+
                            "privados. Guarda-o num local protegido. "+
                            "O ficheiro não está encriptado e não inclui o PIN.")
                        .setPositiveButton("OK",null).show()
                }.onFailure{
                    showError("Não foi possível exportar o backup: "+it.message)
                }
            }
        }.start()
    }
    private fun askRestoreFamilyZip(uri:Uri){
        MaterialAlertDialogBuilder(this)
            .setTitle("Importar backup completo")
            .setMessage("ATENÇÃO: esta opção substitui TODOS os perfis "+
                "e respetivos dados neste telemóvel pelos do ficheiro ZIP. "+
                "Não mistura os dois conjuntos de utilizadores.\\n\\n"+
                "Cria primeiro um backup deste telemóvel, se já tiver dados. "+
                "O PIN atual deste dispositivo será mantido.")
            .setNegativeButton("Cancelar",null)
            .setPositiveButton("Substituir os dados"){_,_->restoreFamilyZip(uri)}
            .show()
    }
    private fun restoreFamilyZip(uri:Uri){
        val waiting=MaterialAlertDialogBuilder(this)
            .setTitle("A restaurar backup")
            .setMessage("A verificar o ZIP e a restaurar os ficheiros…")
            .setCancelable(false).show()
        Thread {
            val outcome=runCatching{FamilyBackupStore(this).restore(uri)}
            runOnUiThread{
                if(!isFinishing)waiting.dismiss()
                outcome.onSuccess{
                    runCatching{NotificationScheduler(this).scheduleAllProfiles()}
                    MaterialAlertDialogBuilder(this)
                        .setTitle("Restauro concluído")
                        .setMessage("Foram restaurados "+it.profiles+
                            " utilizadores e "+it.files+" ficheiros. "+
                            "A SaúdePrática vai reiniciar para mostrar os "+
                            "dados restaurados. O PIN deste telefone mantém-se.")
                        .setCancelable(false)
                        .setPositiveButton("Continuar"){_,_->
                            startActivity(Intent(this,SplashActivity::class.java)
                                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or
                                    Intent.FLAG_ACTIVITY_CLEAR_TASK))
                            finish()
                        }.show()
                }.onFailure{
                    showError("O restauro não foi concluído: "+it.message)
                }
            }
        }.start()
    }''',
"checklist and full backup methods")

change('''        options.chunked(2).forEach { pair ->''',
'''        val hiddenModules=dashboardPrefs().getStringSet("hidden",emptySet())
            .orEmpty()
        val visibleModules=options.filter {
            it.title=="Mais" || it.title !in hiddenModules
        }
        visibleModules.chunked(2).forEach { pair ->''',
"dashboard visibility filters")

change('''        box.addView(infoCard("◐", "Aspeto da aplicação", "Escolha entre automático, claro e escuro.") {''',
'''        box.addView(infoCard("☑", "Escolher módulos do Início",
            "Selecionar com checklist o que aparece no menu principal") {
            showDashboardChecklist()
        })
        box.addView(infoCard("◐", "Aspeto da aplicação", "Escolha entre automático, claro e escuro.") {''',
"show modules setting")

change('''        box.addView(infoCard("⇩", "Importar JSON",''',
'''        box.addView(infoCard("📦", "Backup completo da família",
            "Exportar ZIP com utilizadores, dados, fotos, PDFs e exames") {
            MaterialAlertDialogBuilder(this).setTitle("Backup completo")
                .setMessage("Copia os dados de TODOS os utilizadores, "+
                    "incluindo ficheiros e documentos. O ZIP NÃO está "+
                    "encriptado: partilha-o apenas por meios seguros. "+
                    "O PIN deste dispositivo não é exportado.")
                .setPositiveButton("Criar ZIP"){_,_->
                    familyExport.launch("SaudePratica-backup-familia.zip")
                }.setNegativeButton("Cancelar",null).show()
        })
        box.addView(infoCard("📥", "Restaurar backup completo",
            "Importar ZIP num novo telemóvel; substitui os dados atuais") {
            familyImport.launch(arrayOf("application/zip",
                "application/x-zip-compressed","application/octet-stream"))
        })
        box.addView(infoCard("⇩", "Importar JSON",''',
"backup options before legacy JSON")
main.write_text(s,encoding="utf-8")

java=Path("MediAgenda/v40_overrides/FamilyBackupStore.kt")
dest=base/"data/FamilyBackupStore.kt"
dest.write_text(java.read_text(encoding="utf-8"),encoding="utf-8")

gradle=Path("build-src/MediAgenda_Android_v1/app/build.gradle.kts")
g=gradle.read_text(encoding="utf-8")
assert 'applicationId = "com.mediagenda.app.stable"' in g
assert 'versionCode = 30' in g and 'versionName = "1.9.20"' in g
gradle.write_text(g.replace('versionCode = 30','versionCode = 31',1)
                  .replace('versionName = "1.9.20"','versionName = "1.9.21"',1),
                  encoding="utf-8")
print("PIN kept unlocked until process is killed; family backup ZIP export/restore and per-profile module checklist installed.")
