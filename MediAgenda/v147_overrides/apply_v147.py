#!/usr/bin/env python3
"""Android v1.9.127: two privacy-safe .spbackup scopes and UI unification.
Runs after v146. Never alters alarms or imports another person's data.
"""
from pathlib import Path
app=Path("build-src/MediAgenda_Android_v1/app")
src=app/"src/main/java/com/mediagenda/app"

def patch(file,old,new,label):
    s=file.read_text(encoding="utf-8")
    n=s.count(old)
    if n!=1:raise AssertionError(f"{file.name} {label}: expected 1 got {n}")
    file.write_text(s.replace(old,new,1),encoding="utf-8")

family=src/"data/FamilyBackupStore.kt"
patch(family,"    private fun paths():List<Pair<String,File>>{",
      "    private fun paths(onlyProfile:String?=null):List<Pair<String,File>>{","scoped files")
patch(family,"        return result.sortedBy{it.first}",'''
        if(onlyProfile==null)return result.sortedBy{it.first}
        // A single-person file MUST NOT contain any other family member.
        val medicine=DataRepository(context,onlyProfile).medicationJson()
        val referenced=mutableSetOf<String>()
        val entries=JSONObject(medicine).optJSONArray("medications")?:JSONArray()
        for(i in 0 until entries.length()){
            val images=entries.optJSONObject(i)?.optJSONArray("images")?:continue
            for(j in 0 until images.length()){
                val name=images.optString(j).substringBefore('?').substringAfterLast('/')
                if(name.matches(Regex("[A-Za-z0-9_.-]{1,140}")))
                    referenced.add("medication_photos/"+name)
            }
        }
        val prefix="saudepratica_profiles/"+onlyProfile+"/"
        val glucoseKey=java.security.MessageDigest.getInstance("SHA-256")
            .digest(onlyProfile.toByteArray())
            .joinToString(""){"%02x".format(it)}
        return result.filter{(path,_)->
            path.startsWith(prefix) ||
            (onlyProfile=="legacy" &&
                path in setOf("medicacao.json","agenda.json")) ||
            path in referenced ||
            // Individual media/subfolders may be attached to this exact profile.
            path.startsWith("saudepratica_identity/"+onlyProfile+"/") ||
            path.startsWith("saudepratica_documents/"+onlyProfile+"/") ||
            path.startsWith("saudepratica_labs/"+onlyProfile+"/") ||
            path.startsWith("saudepratica_health/"+onlyProfile+"/") ||
            path.startsWith("saudepratica_workplace/"+onlyProfile+"/") ||
            path.startsWith("diabetes_v1/"+onlyProfile+"/") ||
            path=="diabetes_v1/"+glucoseKey+".json" ||
            path=="diabetes_v1/"+glucoseKey+".json.bak"
        }.sortedBy{it.first}''',"single person allowlist")
patch(family,"    private fun prefs():JSONObject{",
      "    private fun prefs(onlyProfile:String?=null):JSONObject{","scoped prefs")
patch(family,'''            if(!prefAllowed(name))return@forEach''','''            if(!prefAllowed(name))return@forEach
            if(onlyProfile!=null && name!="saudepratica_profiles_v1" &&
                name!=ProfileStore(context).preferencesFor(onlyProfile) &&
                !name.endsWith("_"+onlyProfile))
                return@forEach''',"prefs privacy")
patch(family,'''            out.put(name,values)''','''            if(name=="saudepratica_profiles_v1" && onlyProfile!=null){
                val source=values.optJSONObject("profiles")
                    ?:error("Lista de perfis em falta.")
                val full=JSONArray(source.getString("v"))
                val single=JSONArray()
                for(i in 0 until full.length()){
                    val record=full.getJSONObject(i)
                    if(record.optString("id")==onlyProfile)single.put(record)
                }
                require(single.length()==1){"Perfil selecionado não encontrado."}
                values.put("profiles",JSONObject().put("t","s")
                    .put("v",single.toString()))
            }
            out.put(name,values)''',"one profile registry")
patch(family,'''    fun export(destination:Uri):FamilyBackupSummary {
        val allProfiles=ProfileStore(context).all()
        require(allProfiles.isNotEmpty()){"Não existem perfis para guardar."}''','''    fun export(destination:Uri,onlyProfile:String?=null):FamilyBackupSummary {
        val allProfiles=ProfileStore(context).all()
            .filter{onlyProfile==null||it.id==onlyProfile}
        require(allProfiles.isNotEmpty()){"Perfil selecionado não encontrado."}''',"export profile arg")
patch(family,"        val files=paths()\n        for(person in allProfiles){",
      "        val files=paths(onlyProfile)\n        for(person in allProfiles){","use selected files")
patch(family,'''.put("profiles",ProfileStore(context).all().size)
            .put("prefs",prefs())''','''.put("profiles",allProfiles.size)
            .put("prefs",prefs(onlyProfile))''',"profile manifest")
portable=src/"data/PortableWindowsBackup.kt"
patch(portable,"    fun export(destination:Uri,password:CharArray):Int{",
      "    fun export(destination:Uri,password:CharArray,onlyProfile:String?=null):Int{",
      "portable scoped export")
patch(portable,"            FamilyBackupStore(context).export(Uri.fromFile(source))",
      "            FamilyBackupStore(context).export(Uri.fromFile(source),onlyProfile)",
      "scoped original ZIP")
patch(portable,'''            val profiles=ProfileStore(context).all()
            require(profiles.isNotEmpty()&&profiles.size<=80)''','''            val profiles=ProfileStore(context).all()
                .filter{onlyProfile==null||it.id==onlyProfile}
            require(profiles.isNotEmpty()&&profiles.size<=80)''',"scoped profile contents")
patch(portable,'''                parts+=Part(pre+"attachments.json",bytes("[]"))
                parts+=Part(pre+"android_archives.json",''',
      '''                parts+=Part(pre+"attachments.json",bytes("[]"))
                parts+=Part(pre+"backup_scope.json",bytes(JSONObject()
                    .put("format",2).put("profile_count",profiles.size)
                    .put("scope",if(onlyProfile==null)"family" else "profile")
                    .toString()))
                parts+=Part(pre+"android_archives.json",''',"scope marker")
# No Windows-only data is silently sent to other profiles in the original archive.
main=src/"MainActivity.kt"
patch(main,'''    private var windowsExportPassword:CharArray?=null''',
'''    private var windowsExportPassword:CharArray?=null
    private var windowsExportProfile:String?=null''',"profile choice state")
patch(main,'''        if(uri!=null && secret!=null)exportWindowsBackup(uri,secret)
        else secret?.fill(0.toChar())''',
'''        if(uri!=null && secret!=null)exportWindowsBackup(uri,secret,windowsExportProfile)
        else secret?.fill(0.toChar())
        windowsExportProfile=null''',"export callback")
patch(main,"    private fun chooseWindowsExport(){",
      "    private fun chooseWindowsExport(onlyProfile:String?=null){","UI scoped request")
patch(main,'''            .setTitle("Exportar backup para Windows")
            .setMessage("Cria um .spbackup encriptado com todos os perfis, "+
                "dados e ZIP Android original. Compatível com Windows 0.6.5 "+
                "para restauro/recuperação. Não é sincronização automática.")''',
'''            .setTitle(if(onlyProfile==null)"Backup Família · .spbackup"
                else "Backup Perfil · .spbackup")
            .setMessage(if(onlyProfile==null)
                "Copia os dados da família inteira, incluindo fotos e documentos. "+
                "O ficheiro é encriptado e compatível com Windows e futuro macOS."
                else "Copia APENAS os dados do perfil atual, incluindo fotografias "+
                "e documentos. Nenhum dado de outro perfil pode ser incluído.")''',"scope title")
patch(main,'''                    windowsExportPassword=pwd
                    dialog.dismiss()
                    windowsBackupExport.launch("SaudePratica-familia-Windows.spbackup")''',
'''                    windowsExportPassword=pwd
                    windowsExportProfile=onlyProfile
                    dialog.dismiss()
                    windowsBackupExport.launch(if(onlyProfile==null)
                        "SaudePratica-familia.spbackup" else
                        "SaudePratica-perfil.spbackup")''',"scope file")
patch(main,'''    private fun exportWindowsBackup(uri:Uri,pwd:CharArray){''',
      '''    private fun exportWindowsBackup(uri:Uri,pwd:CharArray,onlyProfile:String?){''',
      "scope worker")
patch(main,'''PortableWindowsBackup(this).export(uri,pwd)''',
      '''PortableWindowsBackup(this).export(uri,pwd,onlyProfile)''',
      "scope writer")
# Old ZIP, JSON and Excel options stay in code for import compatibility but are
# no longer reachable from normal Backup/Restauro menus.
s=main.read_text(encoding="utf-8")
start=s.index('        box.addView(infoCard("📦", "Backup completo da família",')
end=s.index('\n            }\n            "apoio" -> {',start)
before=s[start:end]
after='''        box.addView(infoCard("🔐", "Backup .spbackup · Família",
            "Todos os perfis, medicação, consultas, fotografias e documentos") {
            chooseWindowsExport(null)
        })
        box.addView(infoCard("👤", "Backup .spbackup · Perfil",
            "Guardar apenas o perfil atualmente selecionado") {
            chooseWindowsExport(activeProfileId)
        })
        box.addView(infoCard("📥", "Restaurar .spbackup · Família ou Perfil",
            "Verificar integridade, comparar perfis e confirmar alterações") {
            windowsBackupImport.launch(arrayOf("application/octet-stream","*/*"))
        })'''
assert "Backup completo da família" in before and "Exportar JSON" in before
s=s[:start]+after+s[end:]
# The public restore now reads the edited Windows data after authenticating
# the .spbackup; it never replaces the phone with an old unchanged ZIP.
from shutil import copyfile
copyfile(Path("MediAgenda/v147_overrides/PortableWindowsClinicalRestore.kt"),
         src/"data/PortableWindowsClinicalRestore.kt")
bridge=src/"data/PortableWindowsBackup.kt"
p=bridge.read_text(encoding="utf-8")
reject='''            require(found.isNotEmpty()){
                "O ficheiro Windows não contém um backup Android original. " +
                    "A sincronização de alterações Windows ainda exige validação de conflitos."
            }
'''
assert p.count(reject)==1,"portable original-only restriction changed"
p=p.replace(reject,"",1)
bridge.write_text(p,encoding="utf-8")
addimport="import com.mediagenda.app.data.PortableWindowsBackup"
assert s.count(addimport)==1
s=s.replace(addimport,addimport+"\nimport com.mediagenda.app.data.PortableWindowsClinicalRestore",1)
start=s.index("    private fun inspectWindowsBackup(uri:Uri,pwd:CharArray){")
end=s.index("    private val familyExport = registerForActivityResult(",start)
replacement='''    private fun inspectWindowsBackup(uri:Uri,pwd:CharArray){
        val busy=MaterialAlertDialogBuilder(this)
            .setTitle("A verificar backup encriptado")
            .setMessage("A autenticar palavra-passe e todos os ficheiros…")
            .setCancelable(false).show()
        Thread{
            val result=runCatching{
                val preview=PortableWindowsBackup(this).inspect(uri,pwd)
                try{
                    val plan=PortableWindowsClinicalRestore(this).inspect(preview)
                    preview to plan
                }catch(error:Exception){preview.discard();throw error}
            }
            runOnUiThread{
                if(!isFinishing)busy.dismiss()
                result.onSuccess{(preview,plan)->
                    MaterialAlertDialogBuilder(this)
                        .setTitle("Pré-visualizar restauro "+if(plan.scope=="family")
                            "da Família" else "do Perfil")
                        .setMessage(plan.description()+"\\\\n\\\\n"+
                            "Os dados de medicação, agenda e imagens correspondentes "+
                            "serão restaurados conforme editados no Windows. "+
                            "Perfis existentes serão SUBSTITUÍDOS, não duplicados. "+
                            "Os restantes dados do telemóvel ficam preservados. "+
                            "É criada uma cópia de segurança antes da alteração. "+
                            "Confirma que o destino de cada perfil está correto.")
                        .setNegativeButton("Cancelar"){_,_->preview.discard()}
                        .setPositiveButton("Confirmar restauro"){_,_->
                            restoreWindowsEdited(preview,plan)
                        }
                        .setOnCancelListener{preview.discard()}
                        .show()
                }.onFailure{showError("Backup inválido: "+it.message)}
            }
        }.start()
    }
    private fun restoreWindowsEdited(
        preview:PortableWindowsBackup.Preview,
        plan:PortableWindowsClinicalRestore.Plan
    ){
        val busy=MaterialAlertDialogBuilder(this)
            .setTitle("A restaurar dados confirmados")
            .setMessage("A criar cópia de segurança e a validar fotografias…")
            .setCancelable(false).show()
        Thread{
            val result=runCatching{
                try{PortableWindowsClinicalRestore(this).restore(preview,plan)}
                finally{preview.discard()}
            }
            runOnUiThread{
                if(!isFinishing)busy.dismiss()
                result.onSuccess{count->
                    runCatching{NotificationScheduler(this).scheduleAllProfiles()}
                    MaterialAlertDialogBuilder(this)
                        .setTitle("Restauro concluído")
                        .setMessage("Restaurados "+count+" perfis. "+
                            "A SaúdePrática será reiniciada para carregar "+
                            "os novos dados e atualizar os alarmes.")
                        .setCancelable(false)
                        .setPositiveButton("Continuar"){_,_->
                            startActivity(Intent(this,SplashActivity::class.java)
                                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or
                                    Intent.FLAG_ACTIVITY_CLEAR_TASK))
                            finish()
                        }.show()
                }.onFailure{showError("Restauro interrompido: "+it.message)}
            }
        }.start()
    }

'''
s=s[:start]+replacement+s[end:]
s=s.replace('''            .setTitle("Inspecionar backup Windows")
            .setMessage("Esta opção verifica o ficheiro e só permite recuperar "+
                "um ZIP Android ORIGINAL guardado no Windows. As edições feitas "+
                "no Windows não são sincronizadas por esta função.")''',
'''            .setTitle("Restaurar .spbackup · Família ou Perfil")
            .setMessage("Será verificada a palavra-passe e apresentada a lista "+
                "dos perfis, medicações, consultas e anexos. Podes confirmar "+
                "a substituição dos dados editados no Windows.")''')
# Before claiming export success: read the encrypted file back from Android
# SAF, authenticate AES-GCM, hash all entries and count clinical patients.
previous='''            val result=runCatching{PortableWindowsBackup(this).export(uri,pwd,onlyProfile)}'''
checked='''            val verificationPassword=pwd.copyOf()
            val result=runCatching{
                val exported=PortableWindowsBackup(this)
                    .export(uri,pwd,onlyProfile)
                val ready=PortableWindowsBackup(this)
                    .inspect(uri,verificationPassword)
                try{
                    val plan=PortableWindowsClinicalRestore(this).inspect(ready)
                    require(plan.people.size==exported){
                        "Backup não contém todos os perfis esperados."
                    }
                    require((onlyProfile==null && plan.scope=="family") ||
                            (onlyProfile!=null && plan.scope=="profile")){
                        "Tipo do backup incorreto."
                    }
                    exported
                }finally{ready.discard()}
            }
            verificationPassword.fill(0.toChar())'''
assert s.count(previous)==1,"Export worker source anchor not found"
s=s.replace(previous,checked,1)
# Visible, truthful count before export (without generating empty JSON).
notice='''        val dialog=MaterialAlertDialogBuilder(this)
            .setTitle(if(onlyProfile==null)"Backup Família · .spbackup"'''
assert s.count(notice)==1,"scope prompt not found"
s=s.replace(notice,'''        val chosen=ProfileStore(this).all()
            .filter{onlyProfile==null || it.id==onlyProfile}
        val clinical=runCatching{
            require(chosen.isNotEmpty()){"Perfil não selecionado."}
            val totals=chosen.fold(0 to 0){running,person->
                val folder=if(person.id=="legacy")"" else
                    "saudepratica_profiles/"+person.id+"/"
                val meds=File(filesDir,folder+"medicacao.json")
                val agenda=File(filesDir,folder+"agenda.json")
                require(meds.isFile && agenda.isFile){
                    "Ficheiros clínicos em falta para "+person.name
                }
                val n=org.json.JSONObject(meds.readText())
                    .getJSONArray("medications").length()
                val a=org.json.JSONObject(agenda.readText())
                    .getJSONArray("appointments").length()
                running.first+n to running.second+a
            }
            chosen.size.toString()+" perfis · "+totals.first+
                " medicações · "+totals.second+" agendamentos"
        }.getOrElse{
            showError("Não é seguro exportar: "+it.message)
            return
        }
        val dialog=MaterialAlertDialogBuilder(this)
            .setTitle(if(onlyProfile==null)"Backup Família · .spbackup"''',1)
const message='''            .setMessage(if(onlyProfile==null)
                "Copia os dados da família inteira, incluindo fotos e documentos. "+
                "O ficheiro é encriptado e compatível com Windows e futuro macOS."
                else "Copia APENAS os dados do perfil atual, incluindo fotografias "+
                "e documentos. Nenhum dado de outro perfil pode ser incluído.")'''
assert s.count(message)==1
s=s.replace(message,'''            .setMessage("Dados encontrados: "+clinical+".\\n\\n"+
                (if(onlyProfile==null)
                    "Ficheiro cifrado com a família inteira, fotografias e PDFs."
                else
                    "Ficheiro cifrado APENAS com os dados do perfil selecionado.")+
                "\\n\\nConfirma que estas quantidades estão corretas antes de exportar.")''',1)
main.write_text(s,encoding="utf-8")
gradle=app/"build.gradle.kts"
g=gradle.read_text(encoding="utf-8")
assert 'versionName = "1.9.126"' in g and "versionCode = 136" in g
g=g.replace('versionName = "1.9.126"','versionName = "1.9.127"',1)
g=g.replace("versionCode = 136","versionCode = 137",1)
gradle.write_text(g,encoding="utf-8")
print("Android 1.9.127: only two scope-safe .spbackup backup options.")
