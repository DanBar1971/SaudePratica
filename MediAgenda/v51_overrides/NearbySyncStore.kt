package com.mediagenda.app.sync

import android.content.Context
import android.net.Uri
import android.util.AtomicFile
import com.mediagenda.app.data.ProfileStore
import com.mediagenda.app.notifications.NotificationScheduler
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.security.MessageDigest
import java.util.UUID
import java.util.zip.ZipEntry
import java.util.zip.ZipInputStream
import java.util.zip.ZipOutputStream

data class SyncReport(val added:Int,val files:Int,val conflicts:Int,val profiles:Int)

/** Incremental, additive family sync. It is NOT a backup restore.
 * Deletes and conflicting edits are never propagated automatically.
 * Call only following two-sided Nearby authentication and opt-in.
 */
class NearbySyncStore(private val context:Context) {
    private val root=context.filesDir
    private val profileIds=Regex("(?:legacy|[a-fA-F0-9-]{36})")
    private val names=Regex("[A-Za-z0-9_.-]{1,140}")
    private val maxTotal=240L*1024*1024
    private val maxSingle=65L*1024*1024
    private val maxFiles=2500
    private var added=0
    private var copied=0
    private var conflicts=0
    private val prefs=context.getSharedPreferences("saudepratica_nearby_sync_v1",Context.MODE_PRIVATE)

    fun deviceId():String=synchronized(NearbySyncStore::class.java){
        val id=prefs.getString("device_id","").orEmpty()
        if(id.matches(Regex("[a-fA-F0-9-]{36}")))id
        else UUID.randomUUID().toString().also{check(prefs.edit().putString("device_id",it).commit())}
    }
    private fun digest(f:File):String{
        val md=MessageDigest.getInstance("SHA-256")
        f.inputStream().use{input->
            val buffer=ByteArray(32768)
            while(true){val n=input.read(buffer);if(n<0)break;md.update(buffer,0,n)}
        }
        return md.digest().joinToString(""){"%02x".format(it)}
    }
    private fun validPath(path:String):Boolean{
        if(path.length>235||path.startsWith("/")||path.contains('\\')||path.contains(':'))return false
        val p=path.split('/')
        if(p.any{it.isEmpty()||it==".."||it=="."})return false
        if(p.size==1)return p[0]=="medicacao.json"||p[0]=="agenda.json"
        if(p.size==2 && p[0]=="medication_photos")return names.matches(p[1]) &&
            p[1].lowercase().endsWith(".jpg")
        if(p.size!=3||!profileIds.matches(p[1])||!names.matches(p[2]))return false
        return when(p[0]){
            "saudepratica_profiles"->p[2]=="medicacao.json"||p[2]=="agenda.json"
            "saudepratica_health"->p[2]=="records.json"
            "saudepratica_identity"->p[2] in setOf("avatar.jpg","cc_front.jpg","cc_back.jpg")
            "saudepratica_documents","saudepratica_labs","saudepratica_workplace" ->
                listOf(".json",".pdf",".jpg",".jpeg",".png",".webp",".heic",".heif")
                    .any{p[2].lowercase().endsWith(it)}
            else->false
        }
    }
    private fun allowedPrefs(id:String):JSONObject{
        val source=context.getSharedPreferences(ProfileStore(context).preferencesFor(id),Context.MODE_PRIVATE)
        val obj=JSONObject()
        for((k,v) in source.all){
            if(k.length>120||Regex("pin|pass|token|secret|auth|session",RegexOption.IGNORE_CASE)
                    .containsMatchIn(k))continue
            val value=when(v){
                is String->JSONObject().put("t","s").put("v",v)
                is Boolean->JSONObject().put("t","b").put("v",v)
                is Int->JSONObject().put("t","i").put("v",v)
                is Long->JSONObject().put("t","l").put("v",v)
                is Float->JSONObject().put("t","f").put("v",v.toDouble())
                else->null
            }
            if(value!=null)obj.put(k,value)
        }
        return obj
    }
    private fun files():List<Pair<String,File>>{
        val found=linkedMapOf<String,File>()
        fun include(rel:String){
            if(!validPath(rel))return
            val f=File(root,rel)
            if(f.isFile && f.canonicalFile.parentFile==f.parentFile.canonicalFile)found[rel]=f
        }
        include("medicacao.json");include("agenda.json")
        for(p in ProfileStore(context).all()){
            val id=p.id
            if(id!="legacy"){
                include("saudepratica_profiles/$id/medicacao.json")
                include("saudepratica_profiles/$id/agenda.json")
            }
            listOf("saudepratica_health","saudepratica_identity","saudepratica_documents",
                "saudepratica_labs","saudepratica_workplace").forEach{folder->
                File(root,"$folder/$id").listFiles()?.forEach { include("$folder/$id/${it.name}") }
            }
        }
        File(root,"medication_photos").listFiles()?.forEach{include("medication_photos/${it.name}")}
        return found.toList().sortedBy{it.first}
    }
    fun export():File{
        val files=files()
        require(files.size<=maxFiles && files.sumOf{it.second.length()}<=maxTotal){
            "Os documentos excedem o limite desta sincronização (240 MB)."
        }
        val people=JSONArray()
        ProfileStore(context).all().forEach{p->
            people.put(JSONObject().put("id",p.id).put("name",p.name)
                .put("prefs",allowedPrefs(p.id)))
        }
        require(people.length()>0){"Cria um perfil antes de sincronizar."}
        val manifest=JSONObject().put("kind","saudepratica-nearby-v1")
            .put("device_id",deviceId()).put("profiles",people).put("files",JSONArray())
        val folder=File(context.cacheDir,"saudepratica_sync").apply{mkdirs()}
        val outgoing=File(folder,"send_${UUID.randomUUID()}.zip")
        try{
            ZipOutputStream(outgoing.outputStream().buffered()).use{zip->
                for((rel,file) in files){
                    zip.putNextEntry(ZipEntry("data/$rel"))
                    file.inputStream().use{it.copyTo(zip,32768)}
                    zip.closeEntry()
                    manifest.getJSONArray("files").put(JSONObject().put("path",rel)
                        .put("size",file.length()).put("sha256",digest(file)))
                }
                zip.putNextEntry(ZipEntry("manifest.json"))
                zip.write(manifest.toString().toByteArray(Charsets.UTF_8))
                zip.closeEntry()
            }
            return outgoing
        }catch(t:Throwable){outgoing.delete();throw t}
    }
    private fun mergePreferences(id:String,json:JSONObject){
        val prefs=context.getSharedPreferences(ProfileStore(context).preferencesFor(id),Context.MODE_PRIVATE)
        val edit=prefs.edit()
        for(k in json.keys()){
            if(k.length>120||Regex("pin|pass|token|secret|auth|session",RegexOption.IGNORE_CASE)
                    .containsMatchIn(k))continue
            val v=json.optJSONObject(k)?:continue
            if(prefs.contains(k)){
                if(prefs.all[k]?.toString()!=v.opt("v")?.toString())conflicts++
                continue
            }
            when(v.optString("t")){
                "s"->edit.putString(k,v.optString("v").take(4000))
                "b"->edit.putBoolean(k,v.optBoolean("v"))
                "i"->edit.putInt(k,v.optInt("v"))
                "l"->edit.putLong(k,v.optLong("v"))
                "f"->edit.putFloat(k,v.optDouble("v").toFloat())
            }
        }
        check(edit.commit())
    }
    private fun target(path:String,ids:Map<String,String>):File{
        if(path=="medicacao.json"||path=="agenda.json"){
            val id=ids["legacy"]?:error("Perfil legacy em falta.")
            return if(id=="legacy")File(root,path)else File(root,"saudepratica_profiles/$id/$path")
        }
        val parts=path.split('/')
        if(parts[0]=="medication_photos")return File(root,path)
        val id=ids[parts[1]]?:error("O ficheiro não pertence aos perfis enviados.")
        return if(parts[0]=="saudepratica_profiles"&&id=="legacy") File(root,parts[2])
            else File(root,"${parts[0]}/$id/${parts[2]}")
    }
    private fun meta(path:String)=path.substringAfterLast('/') in
        setOf("medicacao.json","agenda.json","records.json","index.json","lab_reports.json")
    private fun atomic(dest:File,content:String){
        require(dest.parentFile!!.isDirectory||dest.parentFile!!.mkdirs())
        val file=AtomicFile(dest)
        val out=file.startWrite()
        try{out.write(content.toByteArray(Charsets.UTF_8));file.finishWrite(out)}
        catch(t:Throwable){file.failWrite(out);throw t}
    }
    private fun conflict(path:String,source:File,remoteId:String){
        conflicts++
        val folder=File(root,"saudepratica_sync_conflicts").apply{mkdirs()}
        val digest=MessageDigest.getInstance("SHA-256")
            .digest("$remoteId|$path".toByteArray()).take(8)
            .joinToString(""){"%02x".format(it)}
        val output=File(folder,"${digest}_${UUID.randomUUID()}.conflict")
        source.copyTo(output)
    }
    private fun binary(target:File,source:File,path:String,device:String){
        if(target.isFile){
            if(target.length()!=source.length()||digest(target)!=digest(source))conflict(path,source,device)
            return
        }
        check(target.parentFile!!.isDirectory||target.parentFile!!.mkdirs())
        val tmp=File(target.parentFile,target.name+".sync_tmp")
        try{
            source.copyTo(tmp,true)
            check(tmp.renameTo(target))
            copied++
        }finally{tmp.delete()}
    }
    private fun relinkPhotos(item:JSONObject){
        val photos=item.optJSONArray("images")?:return
        val cleaned=JSONArray()
        for(i in 0 until photos.length()){
            val src=Uri.parse(photos.optString(i)).lastPathSegment.orEmpty()
            val filename=src.substringAfterLast('/')
            val f=File(root,"medication_photos/$filename")
            if(names.matches(filename)&&f.isFile && (0 until cleaned.length()).none{
                    cleaned.optString(it)==f.absolutePath})cleaned.put(f.absolutePath)
        }
        item.put("images",cleaned)
    }
    private fun mergeMetadata(dest:File,source:File,path:String,device:String){
        val name=path.substringAfterLast('/')
        val key=when(name){"medicacao.json"->"medications";"agenda.json"->"appointments";else->null}
        val incomingObject=if(key!=null)JSONObject(source.readText())else null
        val incoming=if(key!=null)incomingObject!!.optJSONArray(key)?:JSONArray() else JSONArray(source.readText())
        val rootObject=if(key!=null){
            if(dest.isFile)JSONObject(dest.readText())else JSONObject().put(key,JSONArray())
        }else null
        val current=if(key!=null)rootObject!!.optJSONArray(key)?:JSONArray()
            else if(dest.isFile)JSONArray(dest.readText())else JSONArray()
        val present=mutableMapOf<String,JSONObject>()
        for(i in 0 until current.length()){
            val item=current.optJSONObject(i)?:continue
            present[item.optString("id")]=item
        }
        var changed=false
        for(i in 0 until incoming.length()){
            val item=incoming.optJSONObject(i)?:continue
            val id=item.optString("id")
            require(id.length in 1..120){"Registo com ID inválido."}
            if(name=="medicacao.json")relinkPhotos(item)
            val existing=present[id]
            if(existing==null){
                current.put(item);present[id]=item;added++;changed=true
            }else if(name=="medicacao.json"){
                val a=existing.optJSONArray("images")?:JSONArray()
                val b=item.optJSONArray("images")?:JSONArray()
                for(j in 0 until b.length()){
                    val photo=b.optString(j)
                    if((0 until a.length()).none{a.optString(it)==photo}){a.put(photo);changed=true}
                }
                existing.put("images",a)
                val l=JSONObject(existing.toString()).apply{remove("images")}
                val r=JSONObject(item.toString()).apply{remove("images")}
                if(l.toString()!=r.toString())conflict(path,source,device)
            }else if(existing.toString()!=item.toString())conflict(path,source,device)
        }
        if(name=="records.json"){
            val taken=mutableSetOf<String>()
            for(i in 0 until current.length()){
                val item=current.optJSONObject(i)?:continue
                if(item.optString("kind")=="intakes"){
                    val f=item.optJSONObject("fields")?:continue
                    if(f.optString("scheduled_at").isNotBlank())taken.add(
                        f.optString("medication_id")+"|"+f.optString("scheduled_at"))
                }
            }
            val filtered=JSONArray()
            for(i in 0 until current.length()){
                val item=current.optJSONObject(i)?:continue
                val f=item.optJSONObject("fields")
                if(item.optString("kind")=="pending_intakes"&&f!=null&&
                    (f.optString("medication_id")+"|"+f.optString("scheduled_at")) in taken){
                    changed=true;continue
                }
                filtered.put(item)
            }
            if(changed)atomic(dest,filtered.toString())
        }else if(changed){
            if(key!=null){rootObject!!.put(key,current);atomic(dest,rootObject.toString())}
            else atomic(dest,current.toString())
        }
    }
    fun receive(bundle:File):SyncReport {
        require(bundle.isFile&&bundle.length()<=maxTotal+80L*1024*1024){
            "Transferência demasiado grande."}
        added=0;copied=0;conflicts=0
        val stage=File(context.cacheDir,"saude_sync_in_${UUID.randomUUID()}")
        check(stage.mkdirs())
        try{
            val files=linkedMapOf<String,File>()
            var manifestFile:File?=null
            var total=0L
            ZipInputStream(bundle.inputStream().buffered()).use{zip->
                while(true){
                    val entry=zip.nextEntry?:break
                    require(!entry.isDirectory && files.size<maxFiles)
                    val name=entry.name
                    val target=if(name=="manifest.json"){
                        require(manifestFile==null)
                        File(stage,"manifest.json").also{manifestFile=it}
                    }else{
                        require(name.startsWith("data/"))
                        val rel=name.removePrefix("data/")
                        require(validPath(rel)&&!files.containsKey(rel))
                        File(stage,rel).also{
                            require(it.canonicalPath.startsWith(stage.canonicalPath+"/"))
                            check(it.parentFile!!.isDirectory||it.parentFile!!.mkdirs())
                            files[rel]=it
                        }
                    }
                    var bytes=0L
                    target.outputStream().use{output->
                        val buffer=ByteArray(32768)
                        while(true){
                            val n=zip.read(buffer);if(n<0)break
                            bytes+=n;total+=n
                            require(bytes<=maxSingle&&total<=maxTotal){"Dados recebidos excedem o limite."}
                            output.write(buffer,0,n)
                        }
                    }
                    zip.closeEntry()
                }
            }
            val mf=manifestFile?:error("Manifesto em falta.")
            require(mf.length() in 1..2_000_000L)
            val manifest=JSONObject(mf.readText())
            require(manifest.optString("kind")=="saudepratica-nearby-v1")
            val device=manifest.getString("device_id")
            require(device.matches(Regex("[a-fA-F0-9-]{36}"))&&device!=deviceId())
            val expected=manifest.getJSONArray("files")
            require(expected.length()==files.size)
            val seen=mutableSetOf<String>()
            for(i in 0 until expected.length()){
                val record=expected.getJSONObject(i)
                val path=record.getString("path")
                require(seen.add(path))
                val file=files[path]?:error("Ficheiro em falta: $path")
                require(file.length()==record.getLong("size")&&digest(file)==record.getString("sha256")){
                    "Transferência falhou a validação de integridade."
                }
            }
            val profiles=manifest.getJSONArray("profiles")
            require(profiles.length() in 1..30)
            val ids=mutableMapOf<String,String>()
            val store=ProfileStore(context)
            // Do not interpret remote 'legacy' as the same person locally.
            for(i in 0 until profiles.length()){
                val person=profiles.getJSONObject(i)
                val remote=person.getString("id")
                val name=person.getString("name").trim()
                require(profileIds.matches(remote)&&name.length in 1..120&&!ids.containsKey(remote))
                val existing=store.all().firstOrNull{it.name.equals(name,ignoreCase=true)}
                val localId=(existing?:store.create(name)).id
                ids[remote]=localId
                mergePreferences(localId,person.optJSONObject("prefs")?:JSONObject())
            }
            // Attachments are in place before metadata is made visible.
            files.filterNot{meta(it.key)}.forEach{(path,file)->
                binary(target(path,ids),file,path,device)
            }
            files.filter{meta(it.key)}.forEach{(path,file)->
                mergeMetadata(target(path,ids),file,path,device)
            }
            runCatching{NotificationScheduler(context).scheduleAllProfiles()}
            return SyncReport(added,copied,conflicts,ids.size)
        }finally{stage.deleteRecursively()}
    }
}