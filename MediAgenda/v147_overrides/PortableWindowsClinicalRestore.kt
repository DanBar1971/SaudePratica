package com.mediagenda.app.data

import android.content.Context
import android.net.Uri
import android.util.Base64
import android.graphics.BitmapFactory
import org.json.JSONObject
import org.json.JSONArray
import java.io.File
import java.util.UUID
import java.security.MessageDigest
import java.util.zip.ZipFile

/** Manual, confirmed portable Windows -> Android clinical data restore.
 * No alarm scheduling or receiver changes. Requires previously authenticated
 * and SHA256 checked PortableWindowsBackup.Preview.
 */
class PortableWindowsClinicalRestore(private val context:Context) {
    data class Person(val source:String,val destination:String,val name:String,
        val create:Boolean,val medicationCount:Int,val appointmentCount:Int,
        val attachmentCount:Int)
    data class Plan(val scope:String,val people:List<Person>){
        fun description()=people.joinToString("\n"){
            (if(it.create)"CRIAR " else "SUBSTITUIR ")+it.name+" · "+
            it.medicationCount+" medicamentos, "+it.appointmentCount+
            " consultas, "+it.attachmentCount+" anexos"
        }
    }
    private val root=context.filesDir.canonicalFile
    private fun sha(bytes:ByteArray)=MessageDigest.getInstance("SHA-256")
        .digest(bytes).joinToString(""){"%02x".format(it)}
    private fun safePath(name:String):File {
        require(name.isNotBlank() && !name.startsWith("/") &&
            !name.contains('\\') && name.split('/').none{
                it==".."||it=="."||it.isEmpty()
            }){"Caminho inseguro."}
        val file=File(root,name).canonicalFile
        require(file.path.startsWith(root.path+File.separator)){
            "Caminho fora da SaúdePrática."
        }
        return file
    }
    private fun bytes(zip:ZipFile,id:String,name:String):ByteArray{
        val entry=zip.getEntry("data/profiles/"+id+"/"+name)
            ?:error("O perfil não inclui "+name)
        require(entry.size in 0..16_000_000){"Ficheiro demasiado grande."}
        return zip.getInputStream(entry).use{it.readBytes()}
    }
    private fun scan(zip:ZipFile):Plan {
        val ids=zip.entries().asSequence().map{it.name}
            .filter{it.matches(Regex("data/profiles/[0-9a-fA-F-]{36}/profile\\.json"))}
            .map{it.split('/')[2]}.toList()
        require(ids.size in 1..80 && ids.toSet().size==ids.size){
            "Perfis do backup inválidos."
        }
        val locals=ProfileStore(context).all()
        val chosen=mutableSetOf<String>()
        val scopes=mutableSetOf<String>()
        val persons=ids.map{id->
            val meta=JSONObject(String(bytes(zip,id,"profile.json")))
            require(meta.optString("id")==id){"Perfil sem identificador válido."}
            val name=meta.getString("name").trim()
            require(name.isNotEmpty()&&name.length<=120){"Nome inválido."}
            val original=meta.optString("android_zip_source_id")
                .takeIf{it=="legacy" || it.matches(Regex("[0-9a-fA-F-]{36}"))}
            val byId=locals.filter{it.id==original || it.id==id}
            val byName=locals.filter{it.name.equals(name,true)}
            require(byId.size<=1 && byName.size<=1){
                "Encontrados perfis duplicados com o mesmo nome ou ID."
            }
            val matched=byId.firstOrNull()?:byName.firstOrNull()
            if(matched!=null && byId.isNotEmpty() && byName.isNotEmpty())
                require(byId[0].id==byName[0].id){
                    "O nome e o ID pertencem a pessoas diferentes."
                }
            val dest=matched?.id ?: (original?:id)
            require(dest=="legacy" || dest.matches(Regex("[0-9a-fA-F-]{36}")))
            require(chosen.add(dest)){"Perfis com destino duplicado."}
            val meds=JSONObject(String(bytes(zip,id,"medicacao.json")))
                .getJSONArray("medications")
            val appointments=JSONObject(String(bytes(zip,id,"agenda.json")))
                .getJSONArray("appointments")
            val attachments=JSONArray(String(bytes(zip,id,"attachments.json")))
            require(meds.length()<=2000&&appointments.length()<=2000&&
                attachments.length()<=2000)
            for(i in 0 until attachments.length()){
                val entry=attachments.getJSONObject(i)
                require(entry.getString("profile_id")==id){"Anexo de outro perfil."}
                val hash=entry.getString("sha256")
                require(hash.matches(Regex("[a-f0-9]{64}"))){"Hash inválido."}
                val record=zip.getEntry("data/attachments/"+hash.take(2)+
                    "/"+hash+".bin")?:error("Anexo em falta.")
                require(record.size in 0..16_000_000){"Anexo demasiado grande."}
            }
            val entry=zip.getEntry("data/profiles/"+id+"/backup_scope.json")
            if(entry!=null){
                val scope=JSONObject(zip.getInputStream(entry).bufferedReader()
                    .use{it.readText()}).getString("scope")
                require(scope=="family"||scope=="profile")
                scopes.add(scope)
            }
            Person(id,dest,name,matched==null,meds.length(),
                appointments.length(),attachments.length())
        }
        require(scopes.size<=1){"Tipos de backup diferentes."}
        val scope=scopes.firstOrNull()?:"family"
        require(scope!="profile"||persons.size==1){
            "Backup de perfil inclui outros familiares."
        }
        return Plan(scope,persons)
    }
    fun inspect(preview:PortableWindowsBackup.Preview):Plan=
        ZipFile(preview.decrypted).use{scan(it)}

    private fun records(input:JSONArray,med:Boolean,media:MutableMap<String,ByteArray>):JSONArray{
        val ids=mutableSetOf<String>()
        val output=JSONArray()
        for(i in 0 until input.length()){
            val item=input.getJSONObject(i)
            val original=item.optJSONObject("android_original")
            val row=JSONObject(original?.toString() ?: item.toString())
            val id=item.optString("android_source_id")
                .ifBlank{original?.optString("id").orEmpty()}
                .ifBlank{item.optString("id")}
            require(id.isNotBlank()&&ids.add(id)){"Registos duplicados."}
            row.put("id",id)
            if(med){
                if(item.has("name"))row.put("medication",item.getString("name"))
                for(k in arrayOf("dose","time","reminder_time","notes",
                    "administration_route","indication","suspended_from",
                    "dose_pattern","dose_times","repeat_mode","repeat_start",
                    "repeat_until","repeat_weekdays","schedule")){
                    if(item.has(k))row.put(k,item.get(k))
                }
                if(item.has("photo_b64")){
                    val raw=Base64.decode(item.getString("photo_b64"),Base64.DEFAULT)
                    require(raw.size in 100..3_000_000){"Imagem excessiva."}
                    val bitmap=BitmapFactory.Options().apply{inJustDecodeBounds=true}
                    BitmapFactory.decodeByteArray(raw,0,raw.size,bitmap)
                    require(bitmap.outWidth in 1..10000 &&
                        bitmap.outHeight in 1..10000){"Foto inválida."}
                    val path="medication_photos/sp_"+sha(raw)+".jpg"
                    media[path]=raw
                    row.put("images",JSONArray().put(safePath(path).absolutePath))
                }
            }else{
                if(item.has("title"))row.put("activity",item.getString("title"))
                for(k in arrayOf("date","time","department","specialty",
                    "location","resource","type","done","cancelled",
                    "reminders_minutes","recurrence","photo_uri","ocr_text")){
                    if(item.has(k))row.put(k,item.get(k))
                }
            }
            output.put(row)
        }
        return output
    }
    fun restore(preview:PortableWindowsBackup.Preview,expected:Plan):Int {
        val pending=linkedMapOf<String,ByteArray>()
        val before=ProfileStore(context).all()
        ZipFile(preview.decrypted).use{zip->
            require(scan(zip)==expected){
                "Os perfis mudaram desde a pré-visualização."
            }
            for(person in expected.people){
                val med=JSONObject(String(bytes(zip,person.source,"medicacao.json")))
                val agenda=JSONObject(String(bytes(zip,person.source,"agenda.json")))
                val photos=linkedMapOf<String,ByteArray>()
                val medicine=records(med.getJSONArray("medications"),true,photos)
                val appointments=records(agenda.getJSONArray("appointments"),false,photos)
                val profileDir=if(person.destination=="legacy")"" else
                    "saudepratica_profiles/"+person.destination+"/"
                for((filename,key,rows) in arrayOf(
                    Triple("medicacao.json","medications",medicine),
                    Triple("agenda.json","appointments",appointments))){
                    val location=profileDir+filename
                    val current=safePath(location)
                    val target=if(current.isFile)JSONObject(current.readText())
                        else JSONObject()
                    target.put(key,rows).put("last_notified",JSONObject())
                    pending[location]=target.toString(2).toByteArray()
                }
                val attachments=JSONArray(String(bytes(zip,person.source,
                    "attachments.json")))
                for(i in 0 until attachments.length()){
                    val item=attachments.getJSONObject(i)
                    val path=item.getString("path")
                    val originalId=JSONObject(String(bytes(zip,person.source,
                        "profile.json"))).optString("android_zip_source_id")
                    val mapped=if(originalId.isNotBlank()&&originalId!=person.destination)
                        path.replace("/"+originalId+"/","/"+person.destination+"/")
                        else path
                    // Unknown and non-clinical paths are not overwritten.
                    if(!(mapped.startsWith("medication_photos/") ||
                         mapped.startsWith("saudepratica_documents/"+
                             person.destination+"/") ||
                         mapped.startsWith("saudepratica_identity/"+
                             person.destination+"/") ||
                         mapped.startsWith("saudepratica_labs/"+
                             person.destination+"/") ||
                         mapped.startsWith("saudepratica_workplace/"+
                             person.destination+"/")))continue
                    val hash=item.getString("sha256")
                    val entry=zip.getEntry("data/attachments/"+hash.take(2)+
                        "/"+hash+".bin")?:error("Anexo em falta.")
                    val raw=zip.getInputStream(entry).use{it.readBytes()}
                    require(sha(raw)==hash){"Anexo corrompido."}
                    pending[mapped]=raw
                }
                val meta=JSONObject(String(bytes(zip,person.source,"profile.json")))
                if(meta.optString("photo_b64").isNotBlank()){
                    val photo=Base64.decode(meta.getString("photo_b64"),Base64.DEFAULT)
                    val info=BitmapFactory.Options().apply{inJustDecodeBounds=true}
                    BitmapFactory.decodeByteArray(photo,0,photo.size,info)
                    require(photo.size<=3_000_000&&info.outWidth>0&&info.outHeight>0)
                    pending["saudepratica_identity/"+person.destination+
                        "/avatar.jpg"]=photo
                }
                pending.putAll(photos)
            }
        }
        require(pending.values.sumOf{it.size.toLong()}<=260L*1024*1024){
            "Demasiados dados para restaurar."
        }
        val safety=File.createTempFile("sp_pre_restauro_",".zip",context.cacheDir)
        val prefs=context.getSharedPreferences("saudepratica_profiles_v1",
            Context.MODE_PRIVATE)
        try{
            if(before.isNotEmpty())FamilyBackupStore(context)
                .export(Uri.fromFile(safety))
            val merged=before.toMutableList()
            for(person in expected.people){
                val index=merged.indexOfFirst{it.id==person.destination}
                val updated=HealthProfile(person.destination,person.name)
                if(index>=0)merged[index]=updated else merged.add(updated)
            }
            require(merged.map{it.id}.toSet().size==merged.size)
            for((name,content) in pending){
                val destination=safePath(name)
                require(destination.parentFile!!.isDirectory ||
                    destination.parentFile!!.mkdirs())
                val temporary=File.createTempFile("sp_restore_",".tmp",
                    destination.parentFile)
                try{
                    temporary.writeBytes(content)
                    require(sha(temporary.readBytes())==sha(content))
                    require(temporary.renameTo(destination)){
                        "Erro ao substituir dados."
                    }
                }finally{temporary.delete()}
            }
            val registry=JSONArray()
            merged.forEach{registry.put(JSONObject().put("id",it.id)
                .put("name",it.name))}
            check(prefs.edit().putString("profiles",registry.toString()).commit()){
                "Falha ao gravar perfis."
            }
            return expected.people.size
        }catch(error:Exception){
            if(safety.length()>0)try {
                FamilyBackupStore(context).restore(Uri.fromFile(safety))
            }catch(e:Exception){error.addSuppressed(e)}
            throw error
        }finally{safety.delete()}
    }
}
