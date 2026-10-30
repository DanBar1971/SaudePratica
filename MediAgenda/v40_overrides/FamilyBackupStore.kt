package com.mediagenda.app.data

import android.content.Context
import android.net.Uri
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.security.MessageDigest
import java.util.UUID
import java.util.zip.ZipInputStream
import java.util.zip.ZipOutputStream
import java.util.zip.ZipEntry

data class FamilyBackupSummary(val profiles:Int,val files:Int,val bytes:Long)

/** Complete, portable backup of SaúdePrática, excluding the device's PIN.
 * The ZIP contains private medical/identity data and IS NOT encrypted.
 */
class FamilyBackupStore(private val context:Context){
    private val root=context.filesDir
    private val tops=setOf("saudepratica_profiles","saudepratica_documents",
        "saudepratica_identity","saudepratica_health","saudepratica_labs",
        "saudepratica_workplace","saudepratica_cycle","medication_photos",
        "saudepratica_expenses","medicacao.json","agenda.json")
    private val maxTotal=850L*1024*1024
    private val maxEntry=120L*1024*1024
    private val maxFiles=3500
    private fun allowed(path:String):Boolean{
        if(path.isBlank()||path.startsWith("/")||path.contains('\\')||
           path.contains(':')||path.split('/').any{it=="."||it==".."||it.isEmpty()})
            return false
        val top=path.substringBefore('/')
        return top in tops && (top in setOf("agenda.json","medicacao.json") ||
            path.contains('/'))
    }
    private fun prefAllowed(name:String)=
        (name=="mediagenda_profile"||name=="mediagenda_ui"||
        name.startsWith("saudepratica_"))&&
        name!="saudepratica_app_pin_v1"&&
        !name.contains("token",true)&&!name.contains("secret",true)
    private fun digest()=MessageDigest.getInstance("SHA-256")
    private fun hex(a:ByteArray)=a.joinToString(""){"%02x".format(it)}
    private fun File.safe():Boolean=canonicalPath==absolutePath
    private fun paths():List<Pair<String,File>>{
        val result=mutableListOf<Pair<String,File>>()
        fun walk(file:File,path:String){
            if(!file.safe())return
            if(file.isDirectory){
                file.listFiles()?.forEach{walk(it,path+"/"+it.name)}
            }else if(file.isFile&&allowed(path))result.add(path to file)
        }
        for(name in tops){
            val f=File(root,name)
            if(f.exists())walk(f,name)
        }
        return result.sortedBy{it.first}
    }
    private fun prefs():JSONObject{
        val out=JSONObject()
        val dir=File(context.applicationInfo.dataDir,"shared_prefs")
        dir.listFiles()?.filter{it.name.endsWith(".xml")}?.forEach{file->
            val name=file.name.removeSuffix(".xml")
            if(!prefAllowed(name))return@forEach
            val values=JSONObject()
            context.getSharedPreferences(name,Context.MODE_PRIVATE).all.forEach{(key,v)->
                val item=when(v){
                    is String->JSONObject().put("t","s").put("v",v)
                    is Boolean->JSONObject().put("t","b").put("v",v)
                    is Int->JSONObject().put("t","i").put("v",v)
                    is Long->JSONObject().put("t","l").put("v",v)
                    is Float->JSONObject().put("t","f").put("v",v.toDouble())
                    is Set<*>->JSONObject().put("t","set")
                        .put("v",JSONArray(v.filterIsInstance<String>()))
                    else->null
                }
                if(item!=null&&key.length<240)values.put(key,item)
            }
            out.put(name,values)
        }
        return out
    }
    private fun setPrefs(o:JSONObject){
        val dir=File(context.applicationInfo.dataDir,"shared_prefs")
        dir.listFiles()?.filter{it.name.endsWith(".xml")}?.forEach{
            val name=it.name.removeSuffix(".xml")
            if(prefAllowed(name)){
                check(context.getSharedPreferences(name,Context.MODE_PRIVATE)
                    .edit().clear().commit()){"Erro ao limpar dados."}
            }
        }
        val names=o.keys()
        while(names.hasNext()){
            val name=names.next()
            require(prefAllowed(name)){"Definição não autorizada."}
            val editor=context.getSharedPreferences(name,Context.MODE_PRIVATE)
                .edit().clear()
            val entries=o.getJSONObject(name)
            val keys=entries.keys()
            while(keys.hasNext()){
                val key=keys.next()
                require(key.length<240){"Chave inválida."}
                val value=entries.getJSONObject(key)
                when(value.getString("t")){
                    "s"->editor.putString(key,value.getString("v"))
                    "b"->editor.putBoolean(key,value.getBoolean("v"))
                    "i"->editor.putInt(key,value.getInt("v"))
                    "l"->editor.putLong(key,value.getLong("v"))
                    "f"->editor.putFloat(key,value.getDouble("v").toFloat())
                    "set"->{
                        val values=value.getJSONArray("v")
                        editor.putStringSet(key,(0 until values.length())
                            .map{values.getString(it)}.toSet())
                    }
                    else->error("Tipo de preferência inválido.")
                }
            }
            check(editor.commit()){"Não foi possível restaurar dados."}
        }
    }
    private fun copyTree(from:File,to:File){
        if(from.isDirectory){
            check(to.isDirectory||to.mkdirs()){"Erro ao criar pasta."}
            from.listFiles()?.forEach{copyTree(it,File(to,it.name))}
        }else{
            check(to.parentFile!!.isDirectory||to.parentFile!!.mkdirs()){
                "Erro ao criar diretoria."
            }
            from.copyTo(to,true)
        }
    }
    private fun purge(){
        tops.forEach{
            val f=File(root,it)
            if(f.exists())check(f.deleteRecursively()){"Erro ao substituir ficheiros."}
        }
    }
    fun export(destination:Uri):FamilyBackupSummary {
        val files=paths()
        require(files.size<=maxFiles){"Demasiados ficheiros."}
        require(files.sumOf{it.second.length()}<=maxTotal){
            "O backup ultrapassa 850 MB."
        }
        val manifest=JSONObject()
            .put("kind","saudepratica-complete-backup")
            .put("format",1)
            .put("package",context.packageName)
            .put("profiles",ProfileStore(context).all().size)
            .put("prefs",prefs())
            .put("files",JSONArray())
        val stream=context.contentResolver.openOutputStream(destination,"w")
            ?:error("Não foi possível criar o ZIP.")
        var count=0L
        stream.use{output->
            ZipOutputStream(output.buffered()).use{zip->
                files.forEach{(path,file)->
                    val hash=digest()
                    var bytes=0L
                    zip.putNextEntry(ZipEntry("data/"+path))
                    file.inputStream().use{source->
                        val buffer=ByteArray(32768)
                        while(true){
                            val n=source.read(buffer)
                            if(n<0)break
                            bytes+=n;count+=n
                            require(bytes<=maxEntry && count<=maxTotal){
                                "Ficheiro demasiado grande."
                            }
                            hash.update(buffer,0,n);zip.write(buffer,0,n)
                        }
                    }
                    zip.closeEntry()
                    manifest.getJSONArray("files").put(JSONObject()
                        .put("path",path).put("size",bytes)
                        .put("sha256",hex(hash.digest())))
                }
                zip.putNextEntry(ZipEntry("backup.json"))
                zip.write(manifest.toString().toByteArray(Charsets.UTF_8))
                zip.closeEntry()
            }
        }
        return FamilyBackupSummary(manifest.getInt("profiles"),files.size,count)
    }
    fun restore(source:Uri):FamilyBackupSummary {
        val stage=File(context.cacheDir,"family_restore_"+UUID.randomUUID())
        val staging=File(stage,"incoming")
        check(staging.mkdirs()){"Erro a preparar restauro."}
        val old=File(stage,"original")
        var changed=false
        val oldPrefs=prefs()
        try{
            val hashes=mutableMapOf<String,Pair<Long,String>>()
            var manifestBytes:ByteArray?=null
            var count=0L
            val stream=context.contentResolver.openInputStream(source)
                ?:error("Não foi possível abrir o ZIP.")
            ZipInputStream(stream.buffered()).use{zip->
                var entries=0
                while(true){
                    val entry=zip.nextEntry?:break
                    if(entry.isDirectory){zip.closeEntry();continue}
                    entries++
                    require(entries<=maxFiles+1){"ZIP com demasiados ficheiros."}
                    val path=entry.name
                    val file=if(path=="backup.json")null else{
                        require(path.startsWith("data/")){"Conteúdo inválido."}
                        val name=path.removePrefix("data/")
                        require(allowed(name)){"Ficheiro não permitido."}
                        val dest=File(staging,name)
                        require(dest.canonicalPath.startsWith(staging.canonicalPath+"/")){
                            "Caminho inválido."
                        }
                        require(!dest.exists()){"Ficheiro duplicado."}
                        check(dest.parentFile!!.isDirectory||dest.parentFile!!.mkdirs()){
                            "Não foi possível criar pasta."
                        }
                        dest
                    }
                    if(file==null)require(manifestBytes==null){"Manifesto repetido."}
                    val memory=if(file==null)java.io.ByteArrayOutputStream() else null
                    val hash=digest()
                    var length=0L
                    (file?.outputStream()?:memory!!).use{output->
                        val buffer=ByteArray(32768)
                        while(true){
                            val n=zip.read(buffer)
                            if(n<0)break
                            count+=n;length+=n
                            require(count<=maxTotal&&length<=
                                (if(file==null)2_000_000L else maxEntry)){
                                "Backup demasiado grande."
                            }
                            hash.update(buffer,0,n);output.write(buffer,0,n)
                        }
                    }
                    if(file==null)manifestBytes=memory!!.toByteArray()
                    else hashes[path.removePrefix("data/")]=
                        length to hex(hash.digest())
                    zip.closeEntry()
                }
            }
            val manifest=JSONObject((manifestBytes?:
                error("Manifesto em falta.")).toString(Charsets.UTF_8))
            require(manifest.optString("kind")=="saudepratica-complete-backup"&&
                manifest.optInt("format")==1&&
                manifest.optString("package")==context.packageName){
                "Este ficheiro não é um backup compatível."
            }
            val items=manifest.getJSONArray("files")
            require(items.length()==hashes.size){"Ficheiros em falta."}
            for(i in 0 until items.length()){
                val item=items.getJSONObject(i)
                val found=hashes[item.getString("path")]
                    ?:error("O backup está incompleto.")
                require(found.first==item.getLong("size")&&
                    found.second.equals(item.getString("sha256"),true)){
                    "Um ficheiro do backup está danificado."
                }
            }
            val incoming=manifest.getJSONObject("prefs")
            val profilePrefs=incoming.optJSONObject("saudepratica_profiles_v1")
                ?:error("Falta a lista dos utilizadores.")
            val savedProfiles=profilePrefs.optJSONObject("profiles")
                ?:error("Perfis inválidos.")
            require(savedProfiles.optString("t")=="s"){"Perfis inválidos."}
            val people=JSONArray(savedProfiles.getString("v"))
            require(people.length() in 1..80){"Quantidade de utilizadores inválida."}
            val ids=mutableSetOf<String>()
            for(i in 0 until people.length()){
                val p=people.getJSONObject(i)
                val id=p.getString("id")
                require(id=="legacy"||id.matches(Regex("""[0-9a-fA-F-]{36}"""))){
                    "ID de perfil inválido."
                }
                require(ids.add(id)&&p.getString("name").isNotBlank()){
                    "Perfil inválido ou duplicado."
                }
            }
            check(old.mkdirs()){"Não foi possível preservar os dados atuais."}
            paths().forEach{(path,f)->copyTree(f,File(old,path))}
            changed=true
            purge()
            hashes.keys.forEach{path->
                copyTree(File(staging,path),File(root,path))
            }
            setPrefs(incoming)
            return FamilyBackupSummary(people.length(),hashes.size,count)
        }catch(error:Exception){
            if(changed){
                runCatching{
                    purge()
                    old.listFiles()?.forEach{copyTree(it,File(root,it.name))}
                    setPrefs(oldPrefs)
                }.onFailure{rollback->
                    throw IllegalStateException(
                        "Restauro incompleto e recuperação falhou. "+
                        "Não desinstales a aplicação.",rollback)
                }
            }
            throw error
        }finally{stage.deleteRecursively()}
    }
}
