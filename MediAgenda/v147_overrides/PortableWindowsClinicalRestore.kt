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
        require(entry.size in 0L..16_000_000L){"Ficheiro demasiado grande."}
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
                require(record.size in 0L..16_000_000L){"Anexo demasiado grande."}
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
    /**
     * Recover untouched health modules of a NEW person from the nested Android
     * original. It is authenticated by the outer .spbackup and by each nested
     * original manifest entry. Existing people keep their local nonclinical data.
     *
     * Do not import device settings, alarm routes, PIN or other people's files.
     */
    private fun originalExtraFiles(
        outer:ZipFile,preview:PortableWindowsBackup.Preview,
        plan:Plan,pending:MutableMap<String,ByteArray>,
        profileSettings:MutableMap<String,JSONObject>
    ){
        if(preview.originals.isEmpty())return
        val newborn=plan.people.filter{it.create}
        if(newborn.isEmpty())return
        val sourceToDestination=mutableMapOf<String,String>()
        for(person in newborn){
            val metadata=JSONObject(String(bytes(outer,person.source,"profile.json")))
            val origin=metadata.optString("android_zip_source_id")
                .ifBlank{person.source}
            require(origin=="legacy"||
                origin.matches(Regex("[0-9a-fA-F-]{36}")))
            sourceToDestination[origin]=person.destination
        }
        for(original in preview.originals){
            val inner=outer.getEntry(original.name)?:error("Arquivo original em falta.")
            require(inner.size in 1L..220L*1024*1024)
            val temporary=File.createTempFile("sp_original_verified_",".zip",
                context.cacheDir)
            try{
                val hash=MessageDigest.getInstance("SHA-256")
                outer.getInputStream(inner).use{input->
                    temporary.outputStream().use{output->
                        val buffer=ByteArray(32768)
                        var count=0L
                        while(true){
                            val n=input.read(buffer);if(n<0)break
                            count+=n
                            require(count<=220L*1024*1024)
                            hash.update(buffer,0,n)
                            output.write(buffer,0,n)
                        }
                    }
                }
                require(hash.digest().joinToString(""){"%02x".format(it)}==
                    original.sha256){"Original Android corrompido."}
                ZipFile(temporary).use{zip->
                    val manifest=zip.getEntry("backup.json")
                        ?:error("Manifesto Android em falta.")
                    val header=JSONObject(zip.getInputStream(manifest)
                        .bufferedReader().use{it.readText()})
                    require(header.optString("kind")==
                        "saudepratica-complete-backup"&&
                        header.optInt("format")==1){
                        "Formato Android original inválido."
                    }
                    // Restore patient-specific health and identity fields,
                    // never device-wide PIN, notification, routing or theme.
                    val originalPrefs=header.optJSONObject("prefs")
                    if(originalPrefs!=null){
                        for((oldId,newId) in sourceToDestination){
                            val names= arrayOf(
                                if(oldId=="legacy")"mediagenda_profile"
                                    else "saudepratica_profile_"+oldId,
                                "saudepratica_body_"+oldId,
                                "saudepratica_cycle_"+oldId,
                                "saudepratica_emergency_"+oldId)
                            for(name in names){
                                val old=originalPrefs.optJSONObject(name)?:continue
                                val newName=when{
                                    name=="mediagenda_profile" ||
                                    name.startsWith("saudepratica_profile_")->
                                        if(newId=="legacy")"mediagenda_profile"
                                        else "saudepratica_profile_"+newId
                                    else->name.removeSuffix("_"+oldId)+"_"+newId
                                }
                                if(!profileSettings.containsKey(newName))
                                    profileSettings[newName]=JSONObject(old.toString())
                            }
                        }
                    }
                    val records=header.getJSONArray("files")
                    require(records.length()<=3500)
                    val processed=mutableSetOf<String>()
                    for(i in 0 until records.length()){
                        val record=records.getJSONObject(i)
                        val from=record.getString("path")
                        require(!from.startsWith("/") &&
                            !from.contains('\\') &&
                            from.split('/').none{it==".."||it=="."||it.isBlank()})
                        require(processed.add(from)){"Original com duplicados."}
                        var to:String?=null
                        for((source,dest) in sourceToDestination){
                            val owned= arrayOf("saudepratica_profiles/",
                                "saudepratica_identity/",
                                "saudepratica_documents/",
                                "saudepratica_labs/",
                                "saudepratica_workplace/",
                                "saudepratica_health/",
                                "saudepratica_cycle/",
                                "saudepratica_expenses/")
                            val prefix=owned.firstOrNull{
                                from.startsWith(it+source+"/")
                            }
                            if(prefix!=null){
                                to=prefix+dest+from.removePrefix(prefix+source)
                                break
                            }
                            val hashed=sha(source.toByteArray())
                            if(from=="diabetes_v1/"+hashed+".json" ||
                               from=="diabetes_v1/"+hashed+".json.bak"){
                                to="diabetes_v1/"+sha(dest.toByteArray())+
                                    from.removePrefix("diabetes_v1/"+hashed)
                                break
                            }
                        }
                        if(from.startsWith("medication_photos/") &&
                            sourceToDestination.isNotEmpty() &&
                            from.substringAfterLast('/').matches(
                                Regex("[a-zA-Z0-9_.-]{1,150}"))){
                            // A family/professional archive with multiple
                            // patients shares this directory. The original is
                            // already known by the selected backup scope.
                            if(plan.scope=="family" ||
                                sourceToDestination.size==1)to=from
                        }
                        if(to==null ||
                            to.endsWith("/medicacao.json") ||
                            to.endsWith("/agenda.json") ||
                            to=="medicacao.json"||to=="agenda.json")continue
                        if(pending.containsKey(to) || safePath(to).isFile)continue
                        val entry=zip.getEntry("data/"+from)
                            ?:error("Original contém ficheiros em falta.")
                        require(entry.size==record.getLong("size") &&
                            entry.size in 0L..16_000_000L){
                            "Anexo original excede os limites de recuperação."
                        }
                        val raw=zip.getInputStream(entry).use{it.readBytes()}
                        require(sha(raw).equals(record.getString("sha256"),true)){
                            "Original Android com hash incorreto."
                        }
                        pending[to]=raw
                    }
                }
            }finally{temporary.delete()}
        }
    }

    fun restore(preview:PortableWindowsBackup.Preview,expected:Plan,recoveryPassword:CharArray):Int {
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
        val profileSettings=linkedMapOf<String,JSONObject>()
        ZipFile(preview.decrypted).use{original->
            originalExtraFiles(original,preview,expected,pending,profileSettings)
            val allowed=arrayOf("name","nif","sns_number","full_name",
                "birth_date","gender","height_cm","adse","niss","address",
                "postal_code","health_unit","observation_number","phone","email",
                "nationality","birth_place")
            for(person in expected.people){
                val metadata=JSONObject(String(bytes(original,person.source,
                    "profile.json")))
                val name=if(person.destination=="legacy")"mediagenda_profile"
                    else "saudepratica_profile_"+person.destination
                val values=profileSettings.getOrPut(name){JSONObject()}
                for(key in allowed){
                    val value=if(key=="name")person.name
                        else metadata.optString(key)
                    if(value.isNotBlank()){
                        values.put(key,JSONObject().put("t","s")
                            .put("v",value.take(1000)))
                    }
                }
            }
        }
        require(pending.values.sumOf{it.size.toLong()}<=260L*1024*1024){
            "Demasiados dados para restaurar."
        }
        // Keep the recovery copy OUT of the exported patient's ZIP and cache.
        // This persistent, password-encrypted .spbackup survives a process crash.
        // The caller supplies the user's authenticated backup password again;
        // it is never written to disk and is zeroed on every exit path.
        val recoveryDir=File(context.filesDir,"sp_recovery_private")
        require(recoveryDir.isDirectory||recoveryDir.mkdirs()){
            "Não é possível preparar recuperação privada."
        }
        val safety=File.createTempFile("pre_restore_",".spbackup",recoveryDir)
        val rollbackPassword=recoveryPassword.copyOf()
        val prefs=context.getSharedPreferences("saudepratica_profiles_v1",
            Context.MODE_PRIVATE)
        try{
            if(before.isNotEmpty()){
                PortableWindowsBackup(context).export(Uri.fromFile(safety),
                    recoveryPassword)
                require(safety.length()>1000){
                    "Cópia de recuperação encriptada em falta."
                }
                // Verify the encrypted recovery copy, including all hashes,
                // before changing any live patient file.
                val checked=PortableWindowsBackup(context).inspect(
                    Uri.fromFile(safety),rollbackPassword.copyOf())
                try{
                    val snapshot=inspect(checked)
                    require(snapshot.people.size==before.size){
                        "A cópia de recuperação não inclui todos os perfis."
                    }
                }finally{checked.discard()}
            }
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
            // Typed profile preferences are imported for selected people
            // only. No alarm/PIN/login/device-routing shared preferences.
            for((name,values) in profileSettings){
                require(name=="mediagenda_profile" ||
                    name.matches(Regex("saudepratica_(profile|body|cycle|emergency)_[a-fA-F0-9-]{36}"))){
                    "Preferências fora do perfil."
                }
                val editor=context.getSharedPreferences(name,
                    Context.MODE_PRIVATE).edit()
                val keys=values.keys()
                while(keys.hasNext()){
                    val key=keys.next()
                    require(key.length in 1..120 &&
                        !key.contains("pin",true) &&
                        !key.contains("password",true) &&
                        !key.contains("token",true)){"Definição sensível."}
                    val item=values.getJSONObject(key)
                    when(item.getString("t")){
                        "s"->editor.putString(key,item.getString("v"))
                        "b"->editor.putBoolean(key,item.getBoolean("v"))
                        "i"->editor.putInt(key,item.getInt("v"))
                        "l"->editor.putLong(key,item.getLong("v"))
                        "f"->editor.putFloat(key,item.getDouble("v").toFloat())
                        "set"->{
                            val a=item.getJSONArray("v")
                            editor.putStringSet(key,(0 until a.length())
                                .map{a.getString(it)}.toSet())
                        }
                        else->error("Tipo de campo inválido no backup.")
                    }
                }
                check(editor.commit()){"Não foi possível guardar os dados do perfil."}
            }
            val registry=JSONArray()
            merged.forEach{registry.put(JSONObject().put("id",it.id)
                .put("name",it.name))}
            check(prefs.edit().putString("profiles",registry.toString()).commit()){
                "Falha ao gravar perfis."
            }
            return expected.people.size
        }catch(error:Exception){
            // If a clinical write failed, recover the authenticated Android
            // original from our encrypted .spbackup, not a plaintext ZIP.
            if(safety.length()>1000)try {
                val verified=PortableWindowsBackup(context).inspect(
                    Uri.fromFile(safety),rollbackPassword.copyOf())
                try{
                    require(verified.originals.isNotEmpty()){
                        "Backup de recuperação incompleto."
                    }
                    PortableWindowsBackup(context).restoreOriginal(verified,0)
                }finally{verified.discard()}
            }catch(e:Exception){error.addSuppressed(e)}
            throw error
        }finally{
            recoveryPassword.fill(0.toChar())
            rollbackPassword.fill(0.toChar())
            if(safety.length()==0L)safety.delete()
            // Valid encrypted recovery backups are intentionally retained.
        }
    }
}
