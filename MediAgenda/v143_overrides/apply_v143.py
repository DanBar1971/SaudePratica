#!/usr/bin/env python3
"""SaúdePrática v1.9.123: complete clinical ZIP and portable Windows backup."""
from pathlib import Path
from shutil import copyfile
app=Path("build-src/MediAgenda_Android_v1/app")
src=app/"src/main/java/com/mediagenda/app"
over=Path("MediAgenda/v143_overrides")
copyfile(over/"FamilyBackupStore.kt",src/"data/FamilyBackupStore.kt")
copyfile(over/"PortableWindowsBackup.kt",src/"data/PortableWindowsBackup.kt")
main=src/"MainActivity.kt"
s=main.read_text(encoding="utf-8")
def change(before,after,label):
    global s
    n=s.count(before)
    if n!=1:raise AssertionError(f"{label}: expected 1 anchor, got {n}")
    s=s.replace(before,after,1)

change("import com.mediagenda.app.data.FamilyBackupStore",
"""import com.mediagenda.app.data.FamilyBackupStore
import com.mediagenda.app.data.PortableWindowsBackup""","import")

change("    private val familyExport = registerForActivityResult(",
'''    private var windowsExportPassword:CharArray?=null
    private val windowsBackupExport=registerForActivityResult(
        ActivityResultContracts.CreateDocument("application/octet-stream")
    ){uri->
        val secret=windowsExportPassword
        windowsExportPassword=null
        if(uri!=null && secret!=null)exportWindowsBackup(uri,secret)
        else secret?.fill(0.toChar())
    }
    private val windowsBackupImport=registerForActivityResult(
        ActivityResultContracts.OpenDocument()
    ){uri->if(uri!=null)openWindowsBackup(uri)}

    private fun passwordInput(hint:String)=android.widget.EditText(this).apply{
        this.hint=hint
        inputType=android.text.InputType.TYPE_CLASS_TEXT or
            android.text.InputType.TYPE_TEXT_VARIATION_PASSWORD
    }
    private fun chooseWindowsExport(){
        val form=android.widget.LinearLayout(this).apply{
            orientation=android.widget.LinearLayout.VERTICAL
            setPadding(32,12,32,0)
        }
        val pass=passwordInput("Palavra-passe (mínimo 10 caracteres)")
        val confirm=passwordInput("Repetir palavra-passe")
        form.addView(pass);form.addView(confirm)
        val dialog=MaterialAlertDialogBuilder(this)
            .setTitle("Exportar backup para Windows")
            .setMessage("Cria um .spbackup encriptado com todos os perfis, "+
                "dados e ZIP Android original. Compatível com Windows 0.6.5 "+
                "para restauro/recuperação. Não é sincronização automática.")
            .setView(form).setNegativeButton("Cancelar",null)
            .setPositiveButton("Escolher destino",null).create()
        dialog.setOnShowListener{
            dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE)
                .setOnClickListener{
                    val pwd=pass.text.toString().toCharArray()
                    val check=confirm.text.toString().toCharArray()
                    if(pwd.size<10||!pwd.contentEquals(check)){
                        pwd.fill(0.toChar());check.fill(0.toChar())
                        confirm.error="Usa duas palavras-passe iguais com 10 ou mais caracteres."
                        return@setOnClickListener
                    }
                    check.fill(0.toChar())
                    windowsExportPassword?.fill(0.toChar())
                    windowsExportPassword=pwd
                    dialog.dismiss()
                    windowsBackupExport.launch("SaudePratica-familia-Windows.spbackup")
                }
        }
        dialog.show()
    }
    private fun exportWindowsBackup(uri:Uri,pwd:CharArray){
        val busy=MaterialAlertDialogBuilder(this)
            .setTitle("A preparar backup encriptado")
            .setMessage("A copiar documentos, perfis e registos…")
            .setCancelable(false).show()
        Thread{
            val result=runCatching{PortableWindowsBackup(this).export(uri,pwd)}
            runOnUiThread{
                if(!isFinishing)busy.dismiss()
                result.onSuccess{count->
                    MaterialAlertDialogBuilder(this)
                        .setTitle("Backup encriptado criado")
                        .setMessage("Incluídos "+count+" perfis e o ZIP Android original. "+
                            "Pode ser guardado/restaurado na SaúdePrática Windows. "+
                            "Isto não transfere automaticamente edições Windows "+
                            "de volta para Android.")
                        .setPositiveButton("OK",null).show()
                }.onFailure{showError("Falha ao exportar: "+it.message)}
            }
        }.start()
    }
    private fun openWindowsBackup(uri:Uri){
        val pass=passwordInput("Palavra-passe do .spbackup")
        val dialog=MaterialAlertDialogBuilder(this)
            .setTitle("Inspecionar backup Windows")
            .setMessage("Esta opção verifica o ficheiro e só permite recuperar "+
                "um ZIP Android ORIGINAL guardado no Windows. As edições feitas "+
                "no Windows não são sincronizadas por esta função.")
            .setView(pass).setNegativeButton("Cancelar",null)
            .setPositiveButton("Verificar",null).create()
        dialog.setOnShowListener{
            dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE)
                .setOnClickListener{
                    val pwd=pass.text.toString().toCharArray()
                    if(pwd.size<10){
                        pwd.fill(0.toChar());pass.error="Mínimo 10 caracteres"
                        return@setOnClickListener
                    }
                    dialog.dismiss()
                    inspectWindowsBackup(uri,pwd)
                }
        }
        dialog.show()
    }
    private fun inspectWindowsBackup(uri:Uri,pwd:CharArray){
        val busy=MaterialAlertDialogBuilder(this)
            .setTitle("A verificar backup Windows")
            .setMessage("A validar palavra-passe, assinatura AES-GCM e hashes…")
            .setCancelable(false).show()
        Thread{
            val checked=runCatching{PortableWindowsBackup(this).inspect(uri,pwd)}
            runOnUiThread{
                if(!isFinishing)busy.dismiss()
                checked.onSuccess{preview->
                    val choices=preview.originals.mapIndexed{index,item->
                        "Cópia "+(index+1)+" · "+(item.size/1048576)+" MB"
                    }.toTypedArray()
                    MaterialAlertDialogBuilder(this)
                        .setTitle("Recuperar ZIP Android original")
                        .setMessage("ATENÇÃO: vais substituir TODOS os perfis e "+
                            "dados deste telemóvel por uma cópia Android antiga. "+
                            "As alterações feitas no Windows NÃO serão aplicadas. "+
                            "Faz primeiro um backup deste telemóvel.")
                        .setItems(choices){_,index->
                            confirmRestoreWindowsOriginal(preview,index)
                        }
                        .setNegativeButton("Cancelar"){_,_->preview.discard()}
                        .setOnCancelListener{preview.discard()}.show()
                }.onFailure{showError("Backup Windows inválido: "+it.message)}
            }
        }.start()
    }
    private fun confirmRestoreWindowsOriginal(
        preview:PortableWindowsBackup.Preview,index:Int
    ){
        MaterialAlertDialogBuilder(this)
            .setTitle("Confirmar substituição de todos os dados")
            .setMessage("Recuperar o ZIP ORIGINAL Android? Os dados atuais "+
                "serão substituídos. Não são importadas as alterações editadas "+
                "no Windows. Confirmas que tens um backup atualizado?")
            .setNegativeButton("Cancelar"){_,_->preview.discard()}
            .setPositiveButton("Substituir os dados"){_,_->
                val busy=MaterialAlertDialogBuilder(this)
                    .setTitle("A recuperar dados Android")
                    .setMessage("A validar e restaurar o ZIP original…")
                    .setCancelable(false).show()
                Thread{
                    val outcome=runCatching{
                        try{PortableWindowsBackup(this).restoreOriginal(preview,index)}
                        finally{preview.discard()}
                    }
                    runOnUiThread{
                        if(!isFinishing)busy.dismiss()
                        outcome.onSuccess{
                            runCatching{NotificationScheduler(this).scheduleAllProfiles()}
                            MaterialAlertDialogBuilder(this)
                                .setTitle("Backup original recuperado")
                                .setMessage("Restaurados "+it.profiles+
                                    " perfis do backup Android original. "+
                                    "A aplicação vai reiniciar.")
                                .setCancelable(false)
                                .setPositiveButton("Continuar"){_,_->
                                    startActivity(Intent(this,SplashActivity::class.java)
                                        .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or
                                            Intent.FLAG_ACTIVITY_CLEAR_TASK))
                                    finish()
                                }.show()
                        }.onFailure{showError("Falha de restauro: "+it.message)}
                    }
                }.start()
            }.show()
    }

    private val familyExport = registerForActivityResult(''',"portable backup UI")

change('        box.addView(infoCard("⇩", "Importar JSON",',
'''        box.addView(infoCard("🔐", "Exportar backup para Windows",
            "Criar .spbackup encriptado para transferir perfis e documentos") {
            chooseWindowsExport()
        })
        box.addView(infoCard("🖥", "Inspecionar backup Windows",
            "Recuperar apenas o ZIP Android original do .spbackup") {
            windowsBackupImport.launch(arrayOf("application/octet-stream","*/*"))
        })
        box.addView(infoCard("⇩", "Importar JSON",''',"options")

main.write_text(s,encoding="utf-8")
gradle=app/"build.gradle.kts"
g=gradle.read_text(encoding="utf-8")
assert g.count("versionCode = 132")==1
assert g.count('versionName = "1.9.122"')==1
g=g.replace("versionCode = 132","versionCode = 133",1)
g=g.replace('versionName = "1.9.122"','versionName = "1.9.123"',1)
gradle.write_text(g,encoding="utf-8")
print("Android 1.9.123: complete family ZIP + portable Windows .spbackup.")
