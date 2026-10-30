package com.mediagenda.app.work

import android.content.Context
import android.net.Uri
import android.util.AtomicFile
import androidx.core.content.FileProvider
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.InputStream
import java.security.MessageDigest
import java.util.UUID
import java.util.zip.ZipInputStream

data class WorkDocument(
    val id:String,
    val name:String,
    val category:String,
    val examType:String,
    val date:String,
    val time:String,
    val employer:String,
    val clinic:String,
    val doctor:String,
    val aptitude:String,
    val restrictions:String,
    val notes:String,
    val nextReview:String,
    val originalName:String,
    val filename:String,
    val mime:String,
    val sha256:String,
    val rawOcr:String,
    val createdAt:Long
)

data class WorkZipResult(val added:Int,val duplicates:Int,val skipped:Int)

/** Records only this user's own archived occupational documents. */
class WorkMedicineStore(private val context:Context,private val profileId:String) {
    init{
        require(profileId=="legacy"||profileId.matches(Regex("""[a-fA-F0-9-]{36}"""))) {
            "Perfil inválido."
        }
    }
    private val folder=File(context.filesDir,"saudepratica_workplace/$profileId")
        .apply{if(!exists()&&!mkdirs())error("Não foi possível criar a pasta.")}
    private val index=File(folder,"index.json")
    private val maxFile=30L*1024*1024
    private val maxZip=160L*1024*1024
    private fun obj(a:WorkDocument)=JSONObject()
        .put("id",a.id).put("name",a.name).put("category",a.category)
        .put("examType",a.examType).put("date",a.date).put("time",a.time)
        .put("employer",a.employer).put("clinic",a.clinic)
        .put("doctor",a.doctor).put("aptitude",a.aptitude)
        .put("restrictions",a.restrictions).put("notes",a.notes)
        .put("nextReview",a.nextReview).put("originalName",a.originalName)
        .put("filename",a.filename).put("mime",a.mime)
        .put("sha256",a.sha256).put("rawOcr",a.rawOcr)
        .put("createdAt",a.createdAt)
    private fun decode(o:JSONObject)=WorkDocument(
        o.optString("id"),o.optString("name"),o.optString("category"),
        o.optString("examType"),o.optString("date"),o.optString("time"),
        o.optString("employer"),
        o.optString("clinic"),o.optString("doctor"),
        o.optString("aptitude"),o.optString("restrictions"),
        o.optString("notes"),o.optString("nextReview"),
        o.optString("originalName"),o.optString("filename"),
        o.optString("mime"),o.optString("sha256"),o.optString("rawOcr"),
        o.optLong("createdAt")
    )
    fun all():List<WorkDocument>{
        if(!index.exists())return emptyList()
        val a=JSONArray(index.readText(Charsets.UTF_8))
        return (0 until a.length()).mapNotNull { a.optJSONObject(it)?.let(::decode) }
            .sortedWith(compareByDescending<WorkDocument>{it.date}
                .thenByDescending{it.createdAt})
    }
    private fun persist(items:List<WorkDocument>){
        val json=JSONArray()
        items.forEach{json.put(obj(it))}
        val atomic=AtomicFile(index)
        val output=atomic.startWrite()
        try{
            output.write(json.toString(1).toByteArray(Charsets.UTF_8))
            atomic.finishWrite(output)
        }catch(e:Exception){atomic.failWrite(output);throw e}
    }
    private fun extension(path:String):Pair<String,String>? {
        val n=path.lowercase()
        return when {
            n.endsWith(".pdf")->".pdf" to "application/pdf"
            n.endsWith(".jpg")||n.endsWith(".jpeg")->".jpg" to "image/jpeg"
            n.endsWith(".png")->".png" to "image/png"
            n.endsWith(".webp")->".webp" to "image/webp"
            n.endsWith(".heic")->".heic" to "image/heic"
            n.endsWith(".heif")->".heif" to "image/heif"
            else->null
        }
    }
    private fun hash(bytes:ByteArray)=MessageDigest.getInstance("SHA-256")
        .digest(bytes).joinToString(""){"%02x".format(it)}
    private fun saveStream(input:InputStream,source:String,existing:MutableList<WorkDocument>,
                           byteLimit:Long=maxFile):Boolean{
        val format=extension(source)?:return false
        val path=source.replace('\\','/')
        val segments=path.split('/')
        require(!path.startsWith("/")&&!path.contains(":")&&
            segments.none{it==".."||it=="."}){"Ficheiro inválido no ZIP."}
        val id=UUID.randomUUID().toString()
        val dst=File(folder,id+format.first)
        val hash=MessageDigest.getInstance("SHA-256")
        try{
            var total=0L
            dst.outputStream().use{output->
                val buffer=ByteArray(16384)
                while(true){
                    val count=input.read(buffer)
                    if(count<0)break
                    total+=count
                    require(total<=byteLimit){"O ficheiro excede 30 MB."}
                    hash.update(buffer,0,count)
                    output.write(buffer,0,count)
                }
            }
            require(total>0){"Ficheiro vazio."}
            val sha=hash.digest().joinToString(""){"%02x".format(it)}
            if(existing.any{it.sha256==sha}){
                dst.delete()
                return false
            }
            val kind=WorkplaceClassifier.group(path)
            val type=WorkplaceClassifier.type(path)
            val item=WorkDocument(id,WorkplaceClassifier.title(path,type),kind,
                type,WorkplaceClassifier.date(path),"","","","",
                "Por confirmar","","","",path.take(220),
                dst.name,format.second,sha,"",System.currentTimeMillis())
            existing.add(item)
            try{persist(existing)}catch(e:Exception){
                existing.remove(item);throw e
            }
            return true
        }catch(e:Exception){dst.delete();throw e}
    }
    fun createManual(title:String,category:String):WorkDocument{
        require(category in WorkplaceClassifier.types){"Categoria inválida."}
        val clean=title.trim().take(105)
        require(clean.isNotBlank()){"Indica uma descrição."}
        val record=WorkDocument(
            UUID.randomUUID().toString(),clean,category,
            "Registo manual","","","","","","Por confirmar",
            "","","","","","","","",System.currentTimeMillis()
        )
        persist(all()+record)
        return record
    }
    fun add(uri:Uri,title:String,category:String):WorkDocument{
        require(category in WorkplaceClassifier.types){"Categoria inválida."}
        val type=context.contentResolver.getType(uri).orEmpty()
        val ext=when(type){
            "application/pdf"->".pdf"
            "image/jpeg"->".jpg"
            "image/png"->".png"
            "image/webp"->".webp"
            "image/heic"->".heic"
            "image/heif"->".heif"
            else-> when{
                uri.toString().endsWith(".pdf")->".pdf"
                else->error("Seleciona um PDF ou uma imagem.")
            }
        }
        val original=title.trim().ifBlank{"Documento de Medicina do Trabalho"}
        val existing=all().toMutableList()
        val input=context.contentResolver.openInputStream(uri)
            ?:error("Não foi possível abrir o documento.")
        input.use{
            val added=saveStream(it,original+ext,existing)
            require(added){"Este documento já está guardado neste perfil."}
        }
        val latest=existing.last()
        val updated=latest.copy(name=original.take(105),
            category=category,examType=WorkplaceClassifier.type(original),
            originalName=original.take(220))
        update(updated)
        return updated
    }
    fun importZip(uri:Uri):WorkZipResult{
        val existing=all().toMutableList()
        val preexisting=existing.map{it.sha256}.toHashSet()
        var added=0;var duplicates=0;var skipped=0;var allBytes=0L
        val input=context.contentResolver.openInputStream(uri)
            ?:error("Não foi possível abrir o ZIP.")
        ZipInputStream(input.buffered()).use{zip->
            var count=0
            while(true){
                val entry=zip.nextEntry?:break
                count++
                require(count<=250){"O ZIP ultrapassa 250 entradas."}
                if(entry.isDirectory){zip.closeEntry();continue}
                val path=entry.name.replace('\\','/')
                if(extension(path)==null){
                    skipped++
                    zip.closeEntry()
                    continue
                }
                if(path.startsWith("/")||path.split('/').any{it==".."||it=="."}){
                    skipped++;zip.closeEntry();continue
                }
                val filename=UUID.randomUUID().toString()+extension(path)!!.first
                val dst=File(folder,filename)
                val sha=MessageDigest.getInstance("SHA-256")
                try{
                    var fileBytes=0L
                    dst.outputStream().use{output->
                        val buffer=ByteArray(16384)
                        while(true){
                            val n=zip.read(buffer)
                            if(n<0)break
                            fileBytes+=n
                            allBytes+=n
                            require(fileBytes<=maxFile&&allBytes<=maxZip){
                                "ZIP excede o limite de segurança (30 MB por ficheiro, 160 MB no total)."
                            }
                            sha.update(buffer,0,n);output.write(buffer,0,n)
                        }
                    }
                    if(fileBytes==0L){dst.delete();skipped++;continue}
                    val digest=sha.digest().joinToString(""){"%02x".format(it)}
                    if(preexisting.contains(digest)||existing.any{it.sha256==digest}){
                        dst.delete();duplicates++
                        continue
                    }
                    val group=WorkplaceClassifier.group(path)
                    val examType=WorkplaceClassifier.type(path)
                    val record=WorkDocument(UUID.randomUUID().toString(),
                        WorkplaceClassifier.title(path,examType),group,examType,
                        WorkplaceClassifier.date(path),"","","","","Por confirmar",
                        "","","",path.take(220),filename,
                        extension(path)!!.second,digest,"",System.currentTimeMillis())
                    existing.add(record)
                    try{
                        persist(existing)
                        added++
                    }catch(e:Exception){
                        existing.remove(record);dst.delete();throw e
                    }
                }catch(e:Exception){dst.delete();throw e}
                finally {zip.closeEntry()}
            }
        }
        return WorkZipResult(added,duplicates,skipped)
    }
    fun update(value:WorkDocument){
        require(value.category in WorkplaceClassifier.types){"Categoria inválida."}
        require(value.aptitude in listOf("Por confirmar","Apto",
            "Apto condicionalmente","Inapto temporariamente",
            "Inapto definitivamente","Não aplicável")){"Aptidão inválida."}
        val old=all()
        require(old.any{it.id==value.id}){"Documento não encontrado."}
        persist(old.map{if(it.id==value.id)value else it})
    }
    fun remove(value:WorkDocument){
        persist(all().filterNot{it.id==value.id})
        val file=File(folder,value.filename)
        if(file.canonicalFile.parentFile==folder.canonicalFile)file.delete()
    }
    fun openUri(value:WorkDocument):Uri{
        require(Regex("""[a-zA-Z0-9-]+\.(pdf|jpg|png|webp|heic|heif)""")
            .matches(value.filename)){"Ficheiro inválido."}
        return FileProvider.getUriForFile(context,
            context.packageName+".documents",File(folder,value.filename))
    }
    fun canScan(value:WorkDocument)=value.mime=="application/pdf"||
        value.mime.startsWith("image/")
}
