package com.mediagenda.app.data

import android.content.Context
import android.net.Uri
import android.util.Base64
import org.json.JSONArray
import org.json.JSONObject
import java.io.*
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.security.MessageDigest
import java.security.SecureRandom
import java.util.UUID
import java.util.zip.ZipEntry
import java.util.zip.ZipFile
import java.util.zip.ZipOutputStream
import javax.crypto.Cipher
import javax.crypto.CipherOutputStream
import javax.crypto.SecretKeyFactory
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.PBEKeySpec
import javax.crypto.spec.SecretKeySpec

/** Portable v1 shared with Windows; exchange is manual, not live sync.
 * The original Android ZIP is preserved. Windows edits cannot be silently
 * replayed by restoring an original snapshot.
 */
class PortableWindowsBackup(private val context:Context) {
    private val magic="SAUDEPRATICA-BACKUP-V1\n".toByteArray(Charsets.UTF_8)
    private val maxZip=220L*1024*1024
    private val maxTotal=512L*1024*1024
    private val namePattern=Regex("^(profiles/[0-9a-fA-F-]{36}/[A-Za-z0-9_.-]+|attachments/[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+)$")
    private fun bytes(s:String)=s.toByteArray(Charsets.UTF_8)
    private fun sha(data:ByteArray)=MessageDigest.getInstance("SHA-256").digest(data)
        .joinToString(""){"%02x".format(it)}
    private fun fileHash(f:File):String {
        val h=MessageDigest.getInstance("SHA-256")
        f.inputStream().buffered().use{input->
            val buffer=ByteArray(32768)
            while(true){val n=input.read(buffer);if(n<0)break;h.update(buffer,0,n)}
        }
        return h.digest().joinToString(""){"%02x".format(it)}
    }
    private fun copy(input:InputStream,output:OutputStream,max:Long):Long{
        val buffer=ByteArray(32768);var count=0L
        while(true){val n=input.read(buffer);if(n<0)break
            count+=n;require(count<=max){"O ficheiro excede o limite de segurança."}
            output.write(buffer,0,n)
        }
        return count
    }
    private fun secret(password:CharArray,salt:ByteArray):SecretKeySpec{
        require(password.size>=10){"A palavra-passe precisa de 10 caracteres ou mais."}
        val spec=PBEKeySpec(password,salt,600_000,256)
        return try{SecretKeySpec(SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256")
            .generateSecret(spec).encoded,"AES")}
        finally{spec.clearPassword()}
    }
    private data class Part(val path:String,val data:ByteArray?=null,val file:File?=null){
        val size:Long get()=file?.length()?:data?.size?.toLong()?:0L
        fun open():InputStream=file?.inputStream()?:ByteArrayInputStream(data?:byteArrayOf())
    }
    private fun medOrAgenda(profile:String,kind:String):ByteArray{
        val file=if(profile=="legacy")File(context.filesDir,
            if(kind=="medications")"medicacao.json" else "agenda.json")
        else File(context.filesDir,"saudepratica_profiles/$profile/"+
            if(kind=="medications")"medicacao.json" else "agenda.json")
        if(!file.exists())return bytes(JSONObject().put(kind,JSONArray()).toString())
        val source=JSONObject(file.readText(Charsets.UTF_8))
        val entries=source.optJSONArray(kind)?:JSONArray()
        require(entries.length()<=2000){"Muitos registos para o formato Windows."}
        val dest=JSONArray()
        for(i in 0 until entries.length()){
            val original=entries.getJSONObject(i)
            val value=JSONObject(original.toString())
            val sourceId=original.optString("id")
            val identity=if(kind=="medications")"med:"+
                sourceId.ifBlank{sha(bytes(original.toString()))}
                else "apt:"+sha(bytes(original.toString()))
            value.put("android_original",original)
            value.put("android_source_id",sourceId)
            value.put("android_source_key",identity)
            value.put("android_source_hash",sha(bytes(original.toString())))
            value.put("android_origin","android-portable-v1")
            value.put("id",UUID.nameUUIDFromBytes(bytes(
                "saudepratica-portable:$profile:$kind:$identity")).toString())
            if(kind=="medications"){
                value.put("name",original.optString("medication",
                    original.optString("name","Medicamento")))
                value.put("dose",original.optString("dose",original.optString("dosage","")))
                value.put("time",original.optString("reminder_time",
                    original.optString("time","")))
            } else {
                value.put("title",original.optString("title",original.optString("activity",
                    original.optString("department","Marcação"))))
                value.put("date",original.optString("date",""))
                value.put("time",original.optString("time",""))
            }
            dest.put(value)
        }
        return bytes(JSONObject().put(kind,dest).toString())
    }
    /** Produces a Windows-restorable .spbackup with per-profile JSON and a
     * complete original Android ZIP for unimplemented modules and all assets.
     */
    fun export(destination:Uri,password:CharArray):Int{
        val source=File.createTempFile("family_portable_",".zip",context.cacheDir)
        try{
            FamilyBackupStore(context).export(Uri.fromFile(source))
            require(source.length()<=maxZip){
                "O ZIP excede o limite Windows de 220 MB. Usa o backup ZIP Android normal."
            }
            val profiles=ProfileStore(context).all()
            require(profiles.isNotEmpty()&&profiles.size<=80){"Lista de perfis inválida."}
            val winIds=profiles.map{p->if(p.id=="legacy")UUID.nameUUIDFromBytes(
                bytes("saudepratica-legacy:"+context.packageName)).toString()
                else UUID.fromString(p.id).toString()}
            val digest=fileHash(source)
            val descriptor=JSONObject().put("sha256",digest).put("bytes",source.length())
                .put("filename","SaudePratica-backup-Android-original.zip")
                .put("profile_ids",JSONArray(winIds))
                .put("source_ids",JSONArray(profiles.map{it.id}))
            val parts=mutableListOf<Part>()
            for(i in profiles.indices){
                val p=profiles[i];val pre="profiles/"+winIds[i]+"/"
                val meta=JSONObject().put("id",winIds[i]).put("name",p.name)
                    .put("android_zip_source_id",p.id)
                    .put("android_zip_source_name",p.name)
                    .put("android_profile_original",JSONObject()
                        .put("id",p.id).put("name",p.name))
                parts+=Part(pre+"profile.json",bytes(meta.toString()))
                parts+=Part(pre+"medicacao.json",medOrAgenda(p.id,"medications"))
                parts+=Part(pre+"agenda.json",medOrAgenda(p.id,"appointments"))
                parts+=Part(pre+"attachments.json",bytes("[]"))
                parts+=Part(pre+"android_archives.json",
                    bytes(JSONArray().put(descriptor).toString()))
            }
            parts+=Part("attachments/"+digest.take(2)+"/"+digest+".bin",file=source)
            require(parts.size<=2000&&parts.sumOf{it.size}<=maxTotal){
                "Limite do backup portátil ultrapassado."
            }
            val rows=JSONArray()
            for(part in parts.sortedBy{it.path}){
                require(namePattern.matches(part.path)&&part.path.length<=200)
                val h=if(part.file!=null)fileHash(part.file) else sha(part.data?:byteArrayOf())
                rows.put(JSONObject().put("path",part.path)
                    .put("size",part.size).put("sha256",h))
            }
            val manifest=JSONObject().put("kind","saudepratica-portable-v1")
                .put("created_at",java.time.Instant.now().toString())
                .put("file_count",parts.size).put("files",rows)
            val salt=ByteArray(16).also{SecureRandom().nextBytes(it)}
            val nonce=ByteArray(12).also{SecureRandom().nextBytes(it)}
            val header=JSONObject().put("kind","saudepratica-encrypted-v1")
                .put("kdf","PBKDF2-HMAC-SHA256").put("iterations",600000)
                .put("salt_b64",Base64.encodeToString(salt,Base64.NO_WRAP))
                .put("cipher","AES-256-GCM")
                .put("nonce_b64",Base64.encodeToString(nonce,Base64.NO_WRAP))
            val head=bytes(header.toString())
            val prefix=ByteArrayOutputStream().apply{
                write(magic)
                write(ByteBuffer.allocate(4).order(ByteOrder.BIG_ENDIAN)
                    .putInt(head.size).array())
                write(head)
            }.toByteArray()
            val cipher=Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(Cipher.ENCRYPT_MODE,secret(password,salt),GCMParameterSpec(128,nonce))
            cipher.updateAAD(prefix)
            val output=context.contentResolver.openOutputStream(destination,"w")
                ?:error("Não foi possível criar o backup no destino.")
            output.use{out->
                out.write(prefix)
                ZipOutputStream(CipherOutputStream(out,cipher)).use{zip->
                    zip.putNextEntry(ZipEntry("manifest.json"))
                    zip.write(bytes(manifest.toString()))
                    zip.closeEntry()
                    for(part in parts.sortedBy{it.path}){
                        zip.putNextEntry(ZipEntry("data/"+part.path))
                        part.open().use{copy(it,zip,240L*1024*1024)}
                        zip.closeEntry()
                    }
                }
            }
            return profiles.size
        }finally{source.delete();password.fill('\u0000')}
    }

    data class Original(val sha256:String,val name:String,val size:Long)
    data class Preview(val decrypted:File,val originals:List<Original>){
        fun discard(){decrypted.delete()}
    }
    /** Authenticates the AES-GCM tag *before* reading any ZIP entry. */
    fun inspect(source:Uri,password:CharArray):Preview{
        val verified=File.createTempFile("windows_portable_verified_",".zip",context.cacheDir)
        try{
            (context.contentResolver.openInputStream(source)
                ?:error("Ficheiro inacessível.")).use{input->
                val reader=DataInputStream(input)
                val start=ByteArray(magic.size)
                reader.readFully(start)
                require(start.contentEquals(magic)){"Não é um .spbackup válido."}
                val lengthRaw=ByteArray(4);reader.readFully(lengthRaw)
                val length=ByteBuffer.wrap(lengthRaw).order(ByteOrder.BIG_ENDIAN).int
                require(length in 30..4096){"Cabeçalho demasiado grande."}
                val raw=ByteArray(length);reader.readFully(raw)
                val header=JSONObject(String(raw,Charsets.UTF_8))
                require(header.optString("kind")=="saudepratica-encrypted-v1" &&
                    header.optString("kdf")=="PBKDF2-HMAC-SHA256" &&
                    header.optInt("iterations")==600000 &&
                    header.optString("cipher")=="AES-256-GCM"){
                    "Versão de backup Windows não suportada."
                }
                val salt=Base64.decode(header.getString("salt_b64"),Base64.DEFAULT)
                val nonce=Base64.decode(header.getString("nonce_b64"),Base64.DEFAULT)
                require(salt.size==16&&nonce.size==12){"Parâmetros inválidos."}
                val cipher=Cipher.getInstance("AES/GCM/NoPadding")
                cipher.init(Cipher.DECRYPT_MODE,secret(password,salt),GCMParameterSpec(128,nonce))
                cipher.updateAAD(start+lengthRaw+raw)
                verified.outputStream().buffered().use{out->
                    val buffer=ByteArray(32768);var total=0L
                    while(true){
                        val count=input.read(buffer);if(count<0)break
                        total+=count
                        require(total<=maxTotal+1024){"Backup encriptado demasiado grande."}
                        val plain=cipher.update(buffer,0,count)
                        if(plain!=null)out.write(plain)
                    }
                    out.write(cipher.doFinal()) // Fails on wrong password or corruption.
                }
            }
            return Preview(verified,verifyManifestAndFindOriginals(verified))
        }catch(e:Exception){verified.delete();throw e}
        finally{password.fill('\u0000')}
    }
    private fun verifyManifestAndFindOriginals(file:File):List<Original>{
        ZipFile(file).use{zip->
            val items=zip.entries().toList()
            require(items.size in 2..2001){"Ficheiros ZIP inválidos."}
            val names=items.map{it.name}
            require(names.size==names.toSet().size && "manifest.json" in names){
                "Manifesto em falta ou entradas duplicadas."
            }
            require(items.sumOf{it.size}<=maxTotal && items.all{!it.isDirectory&&it.size>=0}){
                "ZIP ultrapassa os limites de segurança."
            }
            val manifest=JSONObject(zip.getInputStream(zip.getEntry("manifest.json"))
                .bufferedReader(Charsets.UTF_8).use{it.readText()})
            require(manifest.optString("kind")=="saudepratica-portable-v1"){
                "Formato clínico não suportado."
            }
            val files=manifest.getJSONArray("files")
            require(manifest.optInt("file_count")==files.length)
            val namesDeclared=mutableSetOf("manifest.json")
            val originalKeys=mutableMapOf<String,Original>()
            val indexed=mutableListOf<JSONObject>()
            for(i in 0 until files.length()){
                val row=files.getJSONObject(i)
                val path=row.getString("path")
                require(namePattern.matches(path)&&path.length<=200){
                    "Caminho inseguro no backup."
                }
                val full="data/"+path
                require(namesDeclared.add(full)){"Entrada duplicada."}
                val entry=zip.getEntry(full)?:error("Ficheiro em falta.")
                require(entry.size==row.getLong("size")&&entry.size<=240L*1024*1024){
                    "Ficheiro interno demasiado grande."
                }
                val h=MessageDigest.getInstance("SHA-256")
                zip.getInputStream(entry).use{stream->
                    val b=ByteArray(32768)
                    while(true){val n=stream.read(b);if(n<0)break;h.update(b,0,n)}
                }
                val check=h.digest().joinToString(""){"%02x".format(it)}
                require(check==row.getString("sha256")){"Ficheiro danificado."}
                if(path.endsWith("/android_archives.json")){
                    val index=JSONArray(zip.getInputStream(entry)
                        .bufferedReader(Charsets.UTF_8).use{it.readText()})
                    for(j in 0 until index.length())indexed+=index.getJSONObject(j)
                }
                if(path.startsWith("attachments/")){
                    originalKeys[path]=Original(check,full,entry.size)
                }
            }
            require(namesDeclared==names.toSet()){"Existem ficheiros extra."}
            val found=mutableMapOf<String,Original>()
            for(row in indexed){
                val h=row.getString("sha256")
                require(h.matches(Regex("[a-f0-9]{64}"))){"Hash inválido."}
                val path="attachments/"+h.take(2)+"/"+h+".bin"
                val part=originalKeys[path]?:error("O ZIP Android original não existe.")
                require(part.sha256==h && part.size==row.getLong("bytes")){
                    "Backup Android incompleto."
                }
                found[h]=part
            }
            require(found.isNotEmpty()){
                "O ficheiro Windows não contém um backup Android original. " +
                    "A sincronização de alterações Windows ainda exige validação de conflitos."
            }
            return found.values.toList()
        }
    }
    /** Restores only unchanged original Android snapshot, never Windows edits.
     * Caller must show explicit REPLACE ALL confirmation and offer own backup.
     */
    fun restoreOriginal(preview:Preview,index:Int):FamilyBackupSummary{
        val part=preview.originals.getOrNull(index)?:error("Origem inválida.")
        val file=File.createTempFile("portable_original_",".zip",context.cacheDir)
        try {
            ZipFile(preview.decrypted).use{zip->
                val entry=zip.getEntry(part.name)?:error("ZIP original em falta.")
                file.outputStream().use{out->
                    zip.getInputStream(entry).use{copy(it,out,maxZip)}
                }
            }
            require(file.length()==part.size&&fileHash(file)==part.sha256){
                "ZIP original danificado."
            }
            return FamilyBackupStore(context).restore(Uri.fromFile(file))
        }finally{file.delete()}
    }
}
