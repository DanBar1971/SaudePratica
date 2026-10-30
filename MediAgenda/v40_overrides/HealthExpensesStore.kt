package com.mediagenda.app.expenses

import android.content.Context
import android.net.Uri
import android.util.AtomicFile
import androidx.core.content.FileProvider
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.math.BigDecimal
import java.math.RoundingMode
import java.security.MessageDigest
import java.util.UUID

data class HealthExpenseAttachment(
    val id:String,val title:String,val name:String,val mime:String
)
data class HealthExpense(
    val id:String,val date:String,val category:String,val merchant:String,
    val description:String,val receiptNumber:String,val supplierNif:String,
    val amountCents:Long,val reimbursedCents:Long,val taxStatus:String,
    val notes:String,val attachments:List<HealthExpenseAttachment>,
    val createdAt:Long
)

/** Local private register of receipts, prescriptions, insurance or ADSE
 * reimbursements. This app NEVER determines tax eligibility automatically.
 */
class HealthExpensesStore(private val context:Context,private val profileId:String){
    init{
        require(profileId=="legacy"||
            profileId.matches(Regex("""[a-fA-F0-9-]{36}"""))){"Perfil inválido."}
    }
    private val root=File(context.filesDir,"saudepratica_expenses/"+profileId)
        .apply{if(!exists()&&!mkdirs())error("Erro a criar arquivo privado.")}
    private val index=File(root,"expenses.json")
    private val kinds=setOf("Farmácia","Consulta","Exame","Tratamento",
        "Óculos / Lentes","Dispositivo médico","Seguro / ADSE","Outros")
    private val statuses=setOf("Por verificar","Pendente no e-Fatura",
        "Confirmado no e-Fatura","Não aplicável")
    private fun encode(r:HealthExpense)=JSONObject()
        .put("id",r.id).put("date",r.date).put("category",r.category)
        .put("merchant",r.merchant).put("description",r.description)
        .put("receiptNumber",r.receiptNumber).put("supplierNif",r.supplierNif)
        .put("amountCents",r.amountCents).put("reimbursedCents",r.reimbursedCents)
        .put("taxStatus",r.taxStatus).put("notes",r.notes)
        .put("createdAt",r.createdAt)
        .put("attachments",JSONArray().apply{
            r.attachments.forEach{a->
                put(JSONObject().put("id",a.id).put("title",a.title)
                    .put("name",a.name).put("mime",a.mime))
            }
        })
    private fun decode(o:JSONObject):HealthExpense{
        val arr=o.optJSONArray("attachments")?:JSONArray()
        val files=(0 until arr.length()).mapNotNull{i->
            arr.optJSONObject(i)?.let{item->
                HealthExpenseAttachment(item.optString("id"),
                    item.optString("title"),item.optString("name"),
                    item.optString("mime"))
            }
        }
        return HealthExpense(o.optString("id"),o.optString("date"),
            o.optString("category"),o.optString("merchant"),
            o.optString("description"),o.optString("receiptNumber"),
            o.optString("supplierNif"),o.optLong("amountCents"),
            o.optLong("reimbursedCents"),o.optString("taxStatus","Por verificar"),
            o.optString("notes"),files,o.optLong("createdAt"))
    }
    fun list():List<HealthExpense>{
        if(!index.isFile)return emptyList()
        val json=JSONArray(index.readText(Charsets.UTF_8))
        return (0 until json.length()).mapNotNull{json.optJSONObject(it)?.let(::decode)}
            .sortedWith(compareByDescending<HealthExpense>{it.date}
                .thenByDescending{it.createdAt})
    }
    private fun write(values:List<HealthExpense>){
        val array=JSONArray().apply{values.forEach{put(encode(it))}}
        val atomic=AtomicFile(index)
        val out=atomic.startWrite()
        try{
            out.write(array.toString(1).toByteArray(Charsets.UTF_8))
            atomic.finishWrite(out)
        }catch(e:Exception){atomic.failWrite(out);throw e}
    }
    fun validate(v:HealthExpense){
        require(v.category in kinds){"Tipo de despesa inválido."}
        require(v.taxStatus in statuses){"Estado fiscal inválido."}
        require(v.merchant.length<=160 && v.description.length<=400 &&
            v.notes.length<=1500){"Texto demasiado longo."}
        require(v.amountCents in 0..100_000_000_00L &&
            v.reimbursedCents in 0..100_000_000_00L){"Valor inválido."}
        require(v.date.matches(Regex("""\d{4}-\d{2}-\d{2}"""))&&
            runCatching{java.time.LocalDate.parse(v.date)}.isSuccess){
            "Data inválida."
        }
    }
    fun save(record:HealthExpense){
        validate(record)
        val all=list()
        write(if(all.any{it.id==record.id})
            all.map{if(it.id==record.id)record else it}
            else all+record)
    }
    fun create(date:String,category:String,merchant:String,
        description:String,receiptNumber:String,supplierNif:String,
        amount:Long,reimbursed:Long,status:String,notes:String)=
        HealthExpense(UUID.randomUUID().toString(),date,category,merchant,
            description,receiptNumber,supplierNif,amount,reimbursed,status,
            notes,emptyList(),System.currentTimeMillis())
    private fun extension(mime:String):Pair<String,String> = when(mime){
        "application/pdf"->".pdf" to mime
        "image/jpeg","image/jpg"->".jpg" to "image/jpeg"
        "image/png"->".png" to mime
        "image/webp"->".webp" to mime
        "image/heic"->".heic" to mime
        "image/heif"->".heif" to mime
        else->error("Só é possível anexar PDF ou imagem.")
    }
    fun attach(expenseId:String,uri:Uri,title:String):HealthExpense{
        val all=list()
        val original=all.firstOrNull{it.id==expenseId}?:error("Despesa inexistente.")
        val mime=context.contentResolver.getType(uri)?:if(uri.toString().endsWith(".pdf"))
            "application/pdf" else "image/jpeg"
        val (ext,officialMime)=extension(mime.lowercase())
        val id=UUID.randomUUID().toString()
        val file=File(root,id+ext)
        try{
            val input=context.contentResolver.openInputStream(uri)
                ?:error("Não foi possível ler o anexo.")
            var amount=0L
            val hash=MessageDigest.getInstance("SHA-256")
            input.use{source->
                file.outputStream().use{output->
                    val buffer=ByteArray(16*1024)
                    while(true){
                        val count=source.read(buffer)
                        if(count<0)break
                        amount+=count
                        require(amount<=35L*1024*1024){"Anexo maior que 35 MB."}
                        hash.update(buffer,0,count)
                        output.write(buffer,0,count)
                    }
                }
            }
            require(amount>0){"Anexo vazio."}
            val sha=hash.digest()
            // No duplicate attachments on the same entry, even with a
            // different title or incoming filename.
            for(attachment in original.attachments){
                val existing=File(root,attachment.name)
                if(existing.isFile&&existing.length()==amount &&
                    MessageDigest.isEqual(MessageDigest.getInstance("SHA-256")
                        .digest(existing.readBytes()),sha)){
                    error("Este anexo já está guardado nesta despesa.")
                }
            }
            val entry=HealthExpenseAttachment(id,
                title.trim().ifBlank{"Documento"}.take(110),file.name,officialMime)
            val updated=original.copy(attachments=original.attachments+entry)
            save(updated)
            return updated
        }catch(e:Exception){file.delete();throw e}
    }
    fun removeAttachment(record:HealthExpense,attachmentId:String){
        val att=record.attachments.firstOrNull{it.id==attachmentId}?:return
        save(record.copy(attachments=record.attachments.filterNot{it.id==attachmentId}))
        File(root,att.name).takeIf{it.canonicalFile.parentFile==root.canonicalFile}?.delete()
    }
    fun remove(record:HealthExpense){
        write(list().filterNot{it.id==record.id})
        record.attachments.forEach{att->
            File(root,att.name).takeIf{it.canonicalFile.parentFile==root.canonicalFile}
                ?.delete()
        }
    }
    fun open(record:HealthExpense,attachment:HealthExpenseAttachment):Uri{
        require(attachment in record.attachments){"Anexo inválido."}
        require(Regex("""[a-fA-F0-9-]{36}\.(pdf|jpg|png|webp|heic|heif)""")
            .matches(attachment.name)){"Nome de ficheiro inválido."}
        return FileProvider.getUriForFile(context,context.packageName+".documents",
            File(root,attachment.name))
    }
    companion object{
        fun parseEuros(value:String):Long{
            val fixed=value.trim().replace("€","").replace(" ","")
                .replace(",",".")
            if(fixed.isEmpty())return 0
            val number=BigDecimal(fixed)
            require(number.signum()>=0&&number.scale()<=2 &&
                number<=BigDecimal("100000000.00")){"Valor inválido."}
            return number.multiply(BigDecimal("100"))
                .setScale(0,RoundingMode.UNNECESSARY).longValueExact()
        }
        fun euros(cents:Long)=String.format(java.util.Locale("pt","PT"),
            "%.2f €",cents/100.0)
    }
}
