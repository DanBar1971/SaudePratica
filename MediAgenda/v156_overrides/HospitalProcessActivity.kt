package com.mediagenda.app

import android.content.Intent
import android.content.res.ColorStateList
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.graphics.drawable.LayerDrawable
import android.graphics.drawable.ColorDrawable
import android.net.Uri
import android.os.Bundle
import android.text.InputType
import android.util.AtomicFile
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.ArrayAdapter
import android.widget.EditText
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.Spinner
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.button.MaterialButton
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import org.json.JSONArray
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.io.File
import java.io.FileOutputStream
import java.math.BigDecimal
import java.security.MessageDigest
import java.util.Locale

/**
 * Offline, user-entered hospital process dossier. No IPO/SNS server connection.
 * Stored beneath saudepratica_workplace/<profileId>/ so the existing family
 * backup and Nearby profile export can carry JSON and the optional image.
 * NEVER ship real patient details or a staff contact list in the APK.
 */
class HospitalProcessActivity : AppCompatActivity() {
    companion object {
        const val EXTRA_PROFILE_ID = "profile_id"
        const val EXTRA_HOSPITAL = "hospital_unit"
        const val EXTRA_PROCESS = "hospital_process"
    }
    private val teal = Color.rgb(7, 172, 163)
    private val surface = Color.rgb(25, 42, 56)
    private val muted = Color.rgb(184, 201, 209)
    private lateinit var profileId:String
    private lateinit var hospital:String
    private lateinit var process:String
    private lateinit var key:String
    private lateinit var folder:File
    private lateinit var body:LinearLayout
    private var database=JSONObject()

    private val pickIdentity=registerForActivityResult(
        ActivityResultContracts.GetContent()) { uri ->
        if(uri!=null) saveIdentityPhoto(uri)
    }
    private val pickTeam=registerForActivityResult(
        ActivityResultContracts.GetContent()) { uri ->
        if(uri!=null) importTeamFile(uri)
    }

    override fun onCreate(savedInstanceState:Bundle?) {
        super.onCreate(savedInstanceState)
        profileId=intent.getStringExtra(EXTRA_PROFILE_ID).orEmpty()
        hospital=intent.getStringExtra(EXTRA_HOSPITAL).orEmpty().trim()
        process=intent.getStringExtra(EXTRA_PROCESS).orEmpty().trim()
        if(!Regex("[A-Za-z0-9_-]{1,100}").matches(profileId)
            || process.isBlank() || process.length>120 || hospital.length>180){
            finish()
            return
        }
        val existingProfile=com.mediagenda.app.data.ProfileStore(this)
            .all().any{it.id==profileId}
        if(!existingProfile){finish();return}
        key=MessageDigest.getInstance("SHA-256").digest(
            (hospital.trim().lowercase(Locale.ROOT)+"|"+
                process.trim().lowercase(Locale.ROOT)).toByteArray(Charsets.UTF_8))
            .joinToString(""){ "%02x".format(it) }
        folder=File(filesDir,"saudepratica_workplace/"+profileId)
        folder.mkdirs()
        val file=File(folder,"hospital_processes.json")
        database=runCatching{
            if(file.exists()) JSONObject(file.readText(Charsets.UTF_8)) else JSONObject()
        }.getOrElse{
            Toast.makeText(this,"Não foi possível ler o arquivo clínico. Nenhum dado foi apagado.",
                Toast.LENGTH_LONG).show()
            finish();return
        }
        redraw()
    }

    private fun processData():JSONObject {
        val all=database.optJSONObject("processes")?:JSONObject().also{
            database.put("processes",it)
        }
        return all.optJSONObject(key)?:JSONObject().apply {
            put("unit",hospital);put("number",process)
            put("team",JSONArray());put("charges",JSONArray())
            put("transports",JSONArray())
            all.put(key,this)
        }
    }
    private fun save():Boolean {
        val target=File(folder,"hospital_processes.json")
        val atomic=AtomicFile(target)
        var out:java.io.FileOutputStream?=null
        return try {
            database.put("version",1)
            out=atomic.startWrite()
            out.write(database.toString().toByteArray(Charsets.UTF_8))
            atomic.finishWrite(out)
            true
        }catch(e:Exception){
            if(out!=null)atomic.failWrite(out)
            Toast.makeText(this,"Não foi possível guardar: "+(e.message?:"erro"),
                Toast.LENGTH_LONG).show()
            false
        }
    }
    private fun list(name:String):JSONArray{
        val p=processData()
        return p.optJSONArray(name)?:JSONArray().also{p.put(name,it)}
    }
    private fun dp(value:Int)=(value*resources.displayMetrics.density).toInt()
    private fun text(value:String,size:Float=15f, bold:Boolean=false):TextView =
        TextView(this).apply {
            text=value; textSize=size;setTextColor(if(bold)Color.WHITE else muted)
            if(bold)setTypeface(typeface,android.graphics.Typeface.BOLD)
            setPadding(dp(2),dp(6),dp(2),dp(8))
        }
    private fun button(label:String,action:()->Unit)=MaterialButton(this).apply{
        text=label;isAllCaps=false;textSize=14f;cornerRadius=dp(18)
        setTextColor(Color.WHITE)
        backgroundTintList=ColorStateList.valueOf(Color.rgb(4,105,111))
        minHeight=dp(48)
        setOnClickListener{action()}
    }
    private fun panel(title:String,description:String?=null):LinearLayout{
        val wrapper=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(18),dp(15),dp(18),dp(15))
            background=GradientDrawable().apply{
                setColor(surface);cornerRadius=dp(22).toFloat()
                setStroke(dp(1),Color.rgb(64,90,106))
            }
        }
        wrapper.addView(text(title,20f,true))
        if(description!=null) wrapper.addView(text(description,13f))
        body.addView(wrapper,LinearLayout.LayoutParams(-1,-2).apply{
            bottomMargin=dp(13)
        })
        return wrapper
    }
    private fun row(vararg actions:Pair<String,()->Unit>):LinearLayout=
        LinearLayout(this).apply{
            orientation=LinearLayout.HORIZONTAL
            actions.forEach{(title,callback)->
                addView(button(title,callback),
                    LinearLayout.LayoutParams(0,-2,1f).apply{
                        marginEnd=dp(3)
                    })
            }
        }
    private fun field(hint:String,value:String="",numeric:Boolean=false)=
        EditText(this).apply{
            this.hint=hint;setText(value)
            setSingleLine(true);textSize=16f
            setTextColor(Color.WHITE);setHintTextColor(muted)
            if(numeric)inputType=InputType.TYPE_CLASS_NUMBER or
                InputType.TYPE_NUMBER_FLAG_DECIMAL
            setPadding(dp(10),dp(11),dp(10),dp(11))
        }
    private fun form(vararg fields:View)=LinearLayout(this).apply{
        orientation=LinearLayout.VERTICAL
        setPadding(dp(15),dp(8),dp(15),dp(6))
        fields.forEach{addView(it)}
    }
    private fun choice(values:List<String>,current:String)=Spinner(this).apply{
        adapter=ArrayAdapter(this@HospitalProcessActivity,
            android.R.layout.simple_spinner_dropdown_item,values)
        val idx=values.indexOf(current)
        setSelection(idx.coerceAtLeast(0))
    }
    private fun removeRecord(section:String,index:Int) {
        MaterialAlertDialogBuilder(this)
            .setTitle("Eliminar este registo?")
            .setMessage("Só este elemento do processo será eliminado.")
            .setNegativeButton("Cancelar",null)
            .setPositiveButton("Eliminar"){_,_->
                val items=list(section)
                if(index in 0 until items.length()){
                    items.remove(index)
                    if(save())redraw()
                }
            }.show()
    }
    private fun redraw(){
        val darkBackdrop=androidx.core.content.ContextCompat.getDrawable(
            this,R.drawable.saude_background)?.mutate()
        val wallpaper=if(darkBackdrop!=null)LayerDrawable(arrayOf(
            darkBackdrop,ColorDrawable(Color.argb(190,1,13,25))))
            else ColorDrawable(Color.rgb(5,24,35))
        val scroll=ScrollView(this).apply{
            isFillViewport=true
            background=wallpaper
        }
        body=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(17),dp(27),dp(17),dp(30))
        }
        scroll.addView(body)
        setContentView(scroll)
        body.addView(text("SaúdePrática",15f,true))
        body.addView(text("🏥 Processo hospitalar",25f,true))
        body.addView(text(hospital.ifBlank{"Unidade não indicada"}+" · "+process,16f))
        body.addView(button("‹ Voltar à Situação Clínica"){finish()})
        showTeam()
        showCharges()
        showIdentity()
        showTransport()
        body.addView(text(
            "Registos privados introduzidos manualmente. A SaúdePrática não consulta"+
                " nem submete informações na aplicação IPO Lisboa ou nos sistemas do SNS.",12f))
    }

    private fun showTeam(){
        val team=list("team")
        val card=panel("👩‍⚕️ A minha equipa","Profissionais e contactos associados apenas a esta unidade e processo.")
        if(team.length()==0)card.addView(text("Ainda não existem contactos."))
        for(i in 0 until team.length()){
            val item=team.optJSONObject(i)?:continue
            card.addView(text(item.optString("name")+
                " · "+item.optString("specialty"),16f,true))
            val email=item.optString("email")
            val phone=item.optString("phone")
            if(email.isNotBlank())card.addView(button("✉ "+email){
                runCatching{startActivity(Intent(Intent.ACTION_SENDTO,
                    Uri.parse("mailto:"+Uri.encode(email))))}
            })
            if(phone.isNotBlank())card.addView(button("☎ "+phone){
                runCatching{startActivity(Intent(Intent.ACTION_DIAL,
                    Uri.parse("tel:"+Uri.encode(phone))))}
            })
            val note=item.optString("notes")
            if(note.isNotBlank())card.addView(text(note,13f))
            card.addView(row("Editar" to {editTeam(i)}, "Eliminar" to {removeRecord("team",i)}))
        }
        card.addView(button("＋ Adicionar profissional"){editTeam(null)})
        card.addView(button("📂 Importar contactos de ficheiro JSON"){pickTeam.launch("*/*")})
    }
    private fun editTeam(index:Int?){
        val current=index?.let{list("team").optJSONObject(it)}?:JSONObject()
        val name=field("Nome do profissional",current.optString("name"))
        val specialty=field("Especialidade ou serviço",current.optString("specialty"))
        val email=field("Email (opcional)",current.optString("email"))
        val phone=field("Telefone (opcional)",current.optString("phone"))
        val notes=field("Notas (opcional)",current.optString("notes"))
        MaterialAlertDialogBuilder(this)
            .setTitle(if(index==null)"Novo contacto" else "Editar contacto")
            .setView(form(name,specialty,email,phone,notes))
            .setNegativeButton("Cancelar",null)
            .setPositiveButton("Guardar"){_,_->
                val entered=name.text.toString().trim()
                if(entered.isBlank()){
                    Toast.makeText(this,"Indica um nome.",Toast.LENGTH_SHORT).show()
                }else{
                    val item=JSONObject().put("name",entered.take(140))
                        .put("specialty",specialty.text.toString().trim().take(120))
                        .put("email",email.text.toString().trim().take(180))
                        .put("phone",phone.text.toString().trim().take(40))
                        .put("notes",notes.text.toString().trim().take(400))
                    val arr=list("team")
                    if(index==null)arr.put(item)else arr.put(index,item)
                    if(save())redraw()
                }
            }.show()
    }
    private fun importTeamFile(uri:Uri){
        try {
            val contents=contentResolver.openInputStream(uri)?.use{input->
                val bytes=ByteArrayOutputStream()
                val buffer=ByteArray(8192)
                var total=0
                while(true){
                    val n=input.read(buffer)
                    if(n<0)break
                    total+=n;require(total<=1024*1024){"O ficheiro é demasiado grande."}
                    bytes.write(buffer,0,n)
                }
                bytes.toString("UTF-8")
            }?:error("Não foi possível ler o ficheiro.")
            val source=JSONObject(contents)
            val contacts=source.optJSONArray("team")?:error("Falta a lista team.")
            require(contacts.length()<=250){"Demasiados contactos no ficheiro."}
            val arr=list("team")
            var added=0
            for(i in 0 until contacts.length()){
                val entry=contacts.optJSONObject(i)?:continue
                val name=entry.optString("name").trim().take(140)
                if(name.isBlank())continue
                val specialty=entry.optString("specialty").trim().take(120)
                val exists=(0 until arr.length()).any{j->
                    arr.optJSONObject(j)?.let{
                        it.optString("name").equals(name,true) &&
                            it.optString("specialty").equals(specialty,true)
                    }==true
                }
                if(exists)continue
                arr.put(JSONObject().put("name",name).put("specialty",specialty)
                    .put("email",entry.optString("email").take(180))
                    .put("phone",entry.optString("phone").take(40))
                    .put("notes",entry.optString("notes").take(400)))
                added++
            }
            if(save()){
                redraw()
                Toast.makeText(this,"Contactos adicionados: "+added,Toast.LENGTH_LONG).show()
            }
        }catch(e:Exception){
            Toast.makeText(this,"Importação recusada: "+e.message,Toast.LENGTH_LONG).show()
        }
    }

    private fun euro(cents:Int)=String.format(Locale("pt","PT"),"%.2f €",cents/100.0)
    private fun showCharges(){
        val charges=list("charges")
        val card=panel("💶 Taxas moderadoras","Consultas, exames e análises. Valores e pagamentos registados manualmente.")
        var outstanding=0
        for(category in listOf("Consultas","Exames","Análises")){
            var total=0
            var pending=0
            for(i in 0 until charges.length()){
                val entry=charges.optJSONObject(i)?:continue
                if(entry.optString("category")!=category)continue
                val cents=entry.optInt("cents")
                if(entry.optString("status")=="Por pagar")pending+=cents
                if(entry.optString("status")!="Anulado")total+=cents
            }
            outstanding+=pending
            card.addView(text(category+" · "+euro(total)+" · em dívida "+euro(pending),14f,true))
            for(i in 0 until charges.length()){
                val item=charges.optJSONObject(i)?:continue
                if(item.optString("category")!=category)continue
                card.addView(text(item.optString("date")+" · "+euro(item.optInt("cents"))+
                    " · "+item.optString("status")+" · "+item.optString("notes"),13f))
                card.addView(row("Editar" to {editCharge(i)},
                    "Eliminar" to {removeRecord("charges",i)}))
            }
        }
        card.addView(text("Total por pagar (registo manual): "+euro(outstanding),16f,true))
        card.addView(button("＋ Registar taxa / pagamento"){editCharge(null)})
    }
    private fun editCharge(index:Int?){
        val current=index?.let{list("charges").optJSONObject(it)}?:JSONObject()
        val categoryOptions=listOf("Consultas","Exames","Análises")
        val statusOptions=listOf("Por pagar","Pago","Isento","Anulado")
        val category=choice(categoryOptions,current.optString("category"))
        val amount=field("Valor em euros",if(index==null)"" else
            String.format(Locale.ROOT,"%.2f",current.optInt("cents")/100.0),true)
        val status=choice(statusOptions,current.optString("status"))
        val date=field("Data (AAAA-MM-DD, opcional)",current.optString("date"))
        val notes=field("Descrição / notas",current.optString("notes"))
        MaterialAlertDialogBuilder(this)
            .setTitle(if(index==null)"Registar taxa" else "Editar taxa")
            .setView(form(category,amount,status,date,notes))
            .setNegativeButton("Cancelar",null)
            .setPositiveButton("Guardar"){_,_->
                val euros=amount.text.toString().trim().replace(',','.')
                val cents=runCatching{BigDecimal(euros).movePointRight(2).intValueExact()}
                    .getOrNull()
                if(cents==null||cents<0||cents>100000000){
                    Toast.makeText(this,"Indica um valor válido.",Toast.LENGTH_LONG).show()
                }else{
                    val item=JSONObject().put("category",category.selectedItem.toString())
                        .put("cents",cents).put("status",status.selectedItem.toString())
                        .put("date",date.text.toString().trim().take(25))
                        .put("notes",notes.text.toString().trim().take(300))
                    val arr=list("charges")
                    if(index==null)arr.put(item)else arr.put(index,item)
                    if(save())redraw()
                }
            }.show()
    }

    private fun showIdentity(){
        val card=panel("🪪 Identificação do processo",
            "Guarda uma imagem privada do cartão/código do hospital, sem ligação à app de origem.")
        val filename=processData().optString("identity_image")
        val file=if(filename.isNotBlank() && Regex("process_[0-9a-f]{20}[.]jpg")
                .matches(filename))File(folder,filename) else null
        if(file?.isFile==true){
            val bounds=BitmapFactory.Options().apply{inJustDecodeBounds=true}
            BitmapFactory.decodeFile(file.path,bounds)
            val sample=BitmapFactory.Options().apply{
                inSampleSize=calculateSample(bounds.outWidth,bounds.outHeight,1000)
            }
            val image=runCatching{BitmapFactory.decodeFile(file.path,sample)}.getOrNull()
            if(image!=null){
                card.addView(ImageView(this).apply{
                    setImageBitmap(image)
                    adjustViewBounds=true
                    scaleType=ImageView.ScaleType.FIT_CENTER
                },LinearLayout.LayoutParams(-1,dp(280)))
            }
            card.addView(button("Eliminar imagem"){
                MaterialAlertDialogBuilder(this)
                    .setTitle("Eliminar imagem deste processo?")
                    .setNegativeButton("Cancelar",null)
                    .setPositiveButton("Eliminar"){_,_->
                        processData().remove("identity_image")
                        if(save()){file.delete();redraw()}
                    }.show()
            })
        }else card.addView(text("Sem imagem de identificação associada."))
        card.addView(button("📷 Escolher imagem do telemóvel"){
            pickIdentity.launch("image/*")
        })
    }
    private fun calculateSample(w:Int,h:Int,max:Int):Int{
        var sample=1
        while(w/sample>max*2 || h/sample>max*2)sample*=2
        return sample
    }
    private fun saveIdentityPhoto(uri:Uri){
        try{
            val source=File.createTempFile("identity_",".tmp",cacheDir)
            try{
                var total=0L
                contentResolver.openInputStream(uri)?.use{input->
                    FileOutputStream(source).use{output->
                        val buf=ByteArray(32768)
                        while(true){
                            val n=input.read(buf)
                            if(n<0)break
                            total+=n
                            require(total<=12L*1024*1024){"A imagem não pode exceder 12 MB."}
                            output.write(buf,0,n)
                        }
                    }
                }?:error("Não foi possível abrir a imagem.")
                val bounds=BitmapFactory.Options().apply{inJustDecodeBounds=true}
                BitmapFactory.decodeFile(source.path,bounds)
                require(bounds.outWidth in 1..16000 && bounds.outHeight in 1..16000){
                    "Formato de imagem inválido."
                }
                val options=BitmapFactory.Options().apply{
                    inSampleSize=calculateSample(bounds.outWidth,bounds.outHeight,1600)
                }
                val bitmap=BitmapFactory.decodeFile(source.path,options)
                    ?:error("Não foi possível ler a imagem.")
                val target=File(folder,"process_"+key.take(20)+".jpg")
                val temporary=File(folder,target.name+".tmp")
                try {
                    FileOutputStream(temporary).use{stream->
                        require(bitmap.compress(Bitmap.CompressFormat.JPEG,85,stream)){
                            "Não foi possível guardar a fotografia."
                        }
                    }
                    require(temporary.renameTo(target)){"Falha ao guardar a imagem."}
                }finally{temporary.delete();bitmap.recycle()}
                processData().put("identity_image",target.name)
                if(save())redraw()
            }finally{source.delete()}
        }catch(e:Exception){
            Toast.makeText(this,"Imagem não guardada: "+e.message,
                Toast.LENGTH_LONG).show()
        }
    }

    private fun showTransport(){
        val transports=list("transports")
        val card=panel("🚕 Declarações de transporte",
            "Acompanhar pedidos e declarações. Os estados são manuais; não é enviado nenhum pedido ao hospital.")
        if(transports.length()==0)card.addView(text("Sem pedidos ou declarações registados."))
        for(i in 0 until transports.length()){
            val item=transports.optJSONObject(i)?:continue
            card.addView(text(item.optString("description")+" · "+
                item.optString("status"),15f,true))
            card.addView(text("Data: "+item.optString("date")+
                " · Referência: "+item.optString("reference")+
                "\n"+item.optString("notes"),13f))
            card.addView(row("Editar" to {editTransport(i)},
                "Eliminar" to {removeRecord("transports",i)}))
        }
        card.addView(button("＋ Registar pedido / declaração"){editTransport(null)})
    }
    private fun editTransport(index:Int?){
        val item=index?.let{list("transports").optJSONObject(it)}?:JSONObject()
        val title=field("Motivo / tipo de transporte",item.optString("description"))
        val statuses=listOf("Por pedir","Pedido enviado","A aguardar",
            "Declaração emitida","Concluído","Cancelado")
        val status=choice(statuses,item.optString("status"))
        val date=field("Data (AAAA-MM-DD)",item.optString("date"))
        val ref=field("N.º referência (opcional)",item.optString("reference"))
        val notes=field("Notas",item.optString("notes"))
        MaterialAlertDialogBuilder(this)
            .setTitle(if(index==null)"Novo transporte" else "Editar transporte")
            .setView(form(title,status,date,ref,notes))
            .setNegativeButton("Cancelar",null)
            .setPositiveButton("Guardar"){_,_->
                val value=title.text.toString().trim()
                if(value.isBlank()){
                    Toast.makeText(this,"Indica o tipo de pedido.",Toast.LENGTH_SHORT).show()
                }else{
                    val result=JSONObject().put("description",value.take(160))
                        .put("status",status.selectedItem.toString())
                        .put("date",date.text.toString().trim().take(25))
                        .put("reference",ref.text.toString().trim().take(80))
                        .put("notes",notes.text.toString().trim().take(300))
                    val arr=list("transports")
                    if(index==null)arr.put(result)else arr.put(index,result)
                    if(save())redraw()
                }
            }.show()
    }
}
