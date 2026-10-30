package com.mediagenda.app.labs

import android.content.Context
import android.net.Uri
import android.util.AtomicFile
import androidx.core.content.FileProvider
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.util.UUID

data class LabReport(
    val id:String,val title:String,val date:String,val created:Long,
    val mime:String,val fileName:String,val rawText:String,val values:List<LabValue>
)

class ClinicalLabStore(private val ctx:Context,private val profileId:String){
    init { require(profileId=="legacy" ||
        profileId.matches(Regex("""[0-9a-fA-F-]{36}"""))) }
    private val root=File(ctx.filesDir,"saudepratica_labs/"+profileId).apply{mkdirs()}
    private val index=File(root,"lab_reports.json")
    private fun encode(a:LabReport)=JSONObject()
        .put("id",a.id).put("title",a.title).put("date",a.date)
        .put("created",a.created).put("mime",a.mime).put("fileName",a.fileName)
        .put("rawText",a.rawText)
        .put("values",JSONArray().apply{
            a.values.forEach{v->put(JSONObject()
                .put("section",v.section).put("parameter",v.parameter)
                .put("result",v.result).put("unit",v.unit)
                .put("reference",v.reference).put("previous",v.previous)
                .put("page",v.page))}
        })
    private fun decode(o:JSONObject):LabReport{
        val values=o.optJSONArray("values")?:JSONArray()
        val items=(0 until values.length()).mapNotNull{i->
            values.optJSONObject(i)?.let{v->
                LabValue(v.optString("section"),v.optString("parameter"),
                    v.optString("result"),v.optString("unit"),
                    v.optString("reference"),v.optString("previous"),
                    v.optInt("page",1))
            }
        }
        return LabReport(o.optString("id"),o.optString("title"),o.optString("date"),
            o.optLong("created"),o.optString("mime"),o.optString("fileName"),
            o.optString("rawText"),items)
    }
    fun list():List<LabReport>{
        if(!index.exists())return emptyList()
        val array=JSONArray(index.readText(Charsets.UTF_8))
        return (0 until array.length()).mapNotNull{
            array.optJSONObject(it)?.let(::decode)
        }.sortedByDescending{it.created}
    }
    private fun persist(items:List<LabReport>){
        val array=JSONArray()
        items.forEach{array.put(encode(it))}
        val atomic=AtomicFile(index)
        val out=atomic.startWrite()
        try{
            out.write(array.toString(1).toByteArray(Charsets.UTF_8))
            atomic.finishWrite(out)
        }catch(e:Exception){atomic.failWrite(out);throw e}
    }
    fun add(source:Uri,title:String,date:String,mime:String,
            rawText:String,values:List<LabValue>):LabReport{
        require(title.trim().isNotEmpty()){"Indica um nome para as análises."}
        require(mime=="application/pdf"||mime.startsWith("image/")){"Formato inválido."}
        val id=UUID.randomUUID().toString()
        val suffix=if(mime=="application/pdf")".pdf" else ".jpg"
        val filename=id+suffix
        val file=File(root,filename)
        try{
            ctx.contentResolver.openInputStream(source)?.use{input->
                file.outputStream().use{out->
                    val buffer=ByteArray(16384)
                    var total=0L
                    while(true){
                        val count=input.read(buffer)
                        if(count<0)break
                        total+=count
                        require(total<=30L*1024*1024){
                            "Relatório demasiado grande (máximo 30 MB)."}
                        out.write(buffer,0,count)
                    }
                    require(total>0){"O ficheiro está vazio."}
                }
            }?:error("Não foi possível ler o documento.")
            val record=LabReport(id,title.trim().take(120),date.trim().take(30),
                System.currentTimeMillis(),mime,filename,rawText.take(150000),
                values.take(1000))
            persist(list()+record)
            return record
        }catch(e:Exception){file.delete();throw e}
    }
    fun delete(a:LabReport){
        persist(list().filterNot{it.id==a.id})
        File(root,a.fileName).takeIf{it.canonicalFile.parentFile==root.canonicalFile}
            ?.delete()
    }
    fun contentUri(a:LabReport):Uri{
        require(Regex("""[a-fA-F0-9-]{36}\.(pdf|jpg)""").matches(a.fileName))
        return FileProvider.getUriForFile(ctx,ctx.packageName+".documents",
            File(root,a.fileName))
    }
}
