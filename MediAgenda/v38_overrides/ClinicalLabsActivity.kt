package com.mediagenda.app

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.content.res.ColorStateList
import android.content.res.Configuration
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Color
import android.graphics.Matrix
import android.graphics.Typeface
import android.graphics.drawable.BitmapDrawable
import android.graphics.drawable.ColorDrawable
import android.graphics.drawable.LayerDrawable
import android.graphics.pdf.PdfRenderer
import android.net.Uri
import android.os.Bundle
import android.os.ParcelFileDescriptor
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import com.google.android.material.button.MaterialButton
import com.google.android.material.card.MaterialCardView
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import com.google.mlkit.vision.text.Text
import com.mediagenda.app.data.ProfileStore
import com.mediagenda.app.labs.ClinicalLabParser
import com.mediagenda.app.labs.ClinicalLabStore
import com.mediagenda.app.labs.LabValue
import com.mediagenda.app.labs.LabWord
import com.mediagenda.app.labs.LabReport
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class ClinicalLabsActivity:AppCompatActivity(){
    companion object { const val EXTRA_PROFILE_ID="profile_id" }
    private lateinit var store:ClinicalLabStore
    private lateinit var profileName:String
    private lateinit var body:LinearLayout
    private var cameraFile:File?=null
    private var busy=false
    private val teal=Color.rgb(7,163,157)
    private val dark get()=when(getSharedPreferences("mediagenda_ui",MODE_PRIVATE)
        .getString("theme_mode","system")){
        "dark"->true;"light"->false
        else->(resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK)==
            Configuration.UI_MODE_NIGHT_YES
    }
    private val ink get()=if(dark)Color.rgb(241,248,250)else Color.rgb(19,34,56)
    private val muted get()=if(dark)Color.rgb(190,210,220)else Color.rgb(89,105,122)
    private val surface get()=if(dark)Color.rgb(28,41,53)else Color.WHITE
    private val border get()=if(dark)Color.rgb(61,83,97)else Color.rgb(226,234,241)
    private fun dp(v:Int)=(v*resources.displayMetrics.density+.5f).toInt()

    private val picker=registerForActivityResult(ActivityResultContracts.OpenDocument()){uri->
        if(uri!=null)startScan(uri,null)
    }
    private val camera=registerForActivityResult(ActivityResultContracts.TakePicture()){taken->
        val file=cameraFile
        cameraFile=null
        if(taken&&file!=null)startScan(
            FileProvider.getUriForFile(this,packageName+".documents",file),file
        )else file?.delete()
    }
    private val permission=registerForActivityResult(ActivityResultContracts.RequestPermission()){
        if(it)capture()else notify("Câmara não autorizada.")
    }

    override fun onCreate(savedInstanceState:Bundle?){
        super.onCreate(savedInstanceState)
        val all=ProfileStore(this).all()
        val profile=all.firstOrNull{it.id==intent.getStringExtra(EXTRA_PROFILE_ID)}
            ?:all.singleOrNull()?:run{finish();return}
        profileName=profile.name
        store=ClinicalLabStore(this,profile.id)
        val wallpaper=ContextCompat.getDrawable(this,R.drawable.saude_background)
        if(wallpaper is BitmapDrawable)wallpaper.gravity=Gravity.FILL
        val root=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            background=if(dark&&wallpaper!=null)LayerDrawable(arrayOf(
                wallpaper,ColorDrawable(Color.argb(120,2,14,24))))
                else ColorDrawable(if(dark)Color.rgb(4,21,31)else Color.rgb(246,249,251))
        }
        val header=LinearLayout(this).apply{
            orientation=LinearLayout.HORIZONTAL;gravity=Gravity.CENTER_VERTICAL
            setPadding(dp(16),dp(10),dp(16),dp(12))
        }
        header.addView(label("‹",36f,false,teal).apply{
            gravity=Gravity.CENTER
            contentDescription="Voltar ao Início"
            setOnClickListener{finish()}
        },LinearLayout.LayoutParams(dp(36),dp(68)))
        val headings=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
        headings.addView(label("SaúdePrática",13f,true,teal))
        headings.addView(label("🧪 Análises Clínicas",25f,true))
        headings.addView(label(profileName+" · relatórios e resultados",13f,false,muted))
        header.addView(headings,LinearLayout.LayoutParams(0,
            ViewGroup.LayoutParams.WRAP_CONTENT,1f))
        root.addView(header)
        val scroller=ScrollView(this).apply{overScrollMode=View.OVER_SCROLL_NEVER}
        body=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL
            setPadding(dp(16),dp(3),dp(16),dp(24))}
        scroller.addView(body)
        root.addView(scroller,LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,0,1f))
        WindowCompat.setDecorFitsSystemWindows(window,false)
        window.statusBarColor=Color.TRANSPARENT
        window.navigationBarColor=Color.TRANSPARENT
        val controls=WindowInsetsControllerCompat(window,window.decorView)
        controls.isAppearanceLightStatusBars=!dark
        controls.isAppearanceLightNavigationBars=!dark
        ViewCompat.setOnApplyWindowInsetsListener(root){view,insets->
            val safe=insets.getInsets(WindowInsetsCompat.Type.statusBars() or
                WindowInsetsCompat.Type.navigationBars() or
                WindowInsetsCompat.Type.displayCutout())
            view.setPadding(safe.left, safe.top,safe.right,safe.bottom)
            insets
        }
        setContentView(root)
        ViewCompat.requestApplyInsets(root)
        refresh()
    }
    private fun label(text:String,size:Float=14f,strong:Boolean=false,
        color:Int=ink)=TextView(this).apply{
            this.text=text;textSize=size;setTextColor(color)
            if(strong)setTypeface(null,Typeface.BOLD)
        }
    private fun button(text:String,onClick:()->Unit)=MaterialButton(this).apply{
        this.text=text;isAllCaps=false;textSize=13f
        setTextColor(if(dark)Color.rgb(151,244,227)else Color.rgb(5,112,107))
        backgroundTintList=ColorStateList.valueOf(Color.TRANSPARENT)
        strokeColor=ColorStateList.valueOf(teal);strokeWidth=dp(1)
        cornerRadius=dp(16);setOnClickListener{onClick()}
    }
    private fun card(title:String,description:String=""):LinearLayout{
        val shell=MaterialCardView(this).apply{
            radius=dp(19).toFloat();strokeWidth=dp(1);strokeColor=border
            setCardBackgroundColor(surface)
        }
        val box=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(17),dp(15),dp(17),dp(17))
        }
        box.addView(label(title,18f,true))
        if(description.isNotBlank())box.addView(label(description,13f,false,muted)
            .apply{setPadding(0,dp(7),0,dp(8))})
        shell.addView(box)
        body.addView(shell,LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT)
            .apply{bottomMargin=dp(14)})
        return box
    }
    private fun edit(hint:String,value:String="")=EditText(this).apply{
        this.hint=hint
        setText(value)
        setSingleLine(true)
        textSize=15f
        setTextColor(ink);setHintTextColor(muted)
        backgroundTintList=ColorStateList.valueOf(teal)
        setPadding(dp(2),dp(6),dp(2),dp(7))
    }
    private fun notify(message:String)=MaterialAlertDialogBuilder(this)
        .setTitle("SaúdePrática").setMessage(message)
        .setPositiveButton("OK",null).show()

    private fun refresh(){
        body.removeAllViews()
        val actions=card("Adicionar relatório",
            "PDF com várias páginas, imagem recebida ou fotografia das análises.")
        actions.addView(button("📎 Importar PDF / imagem"){
            if(!busy)picker.launch(arrayOf("application/pdf","image/*"))
        })
        actions.addView(button("📷 Fotografar relatório"){
            if(busy)return@button
            if(ContextCompat.checkSelfPermission(this,Manifest.permission.CAMERA)
                ==PackageManager.PERMISSION_GRANTED)capture()
            else permission.launch(Manifest.permission.CAMERA)
        })
        val reports=runCatching{store.list()}.getOrElse{
            notify("Não foi possível ler os relatórios guardados: "+it.message)
            emptyList()
        }
        card("Relatórios guardados",""+reports.size+" documento(s) neste perfil.")
        reports.forEach{report->
            val box=card(report.title,report.date.ifBlank{"Data da análise não indicada"}+
                "  ·  "+report.values.size+" resultado(s) revistos")
            box.addView(button("👁 Ver resultados"){viewReport(report)})
            box.addView(button("📄 Abrir documento original"){openOriginal(report)})
            box.addView(button("🗑 Apagar relatório"){
                MaterialAlertDialogBuilder(this).setTitle("Eliminar relatório?")
                    .setMessage("Apagar este relatório e a sua cópia do documento?")
                    .setPositiveButton("Eliminar"){_,_->
                        runCatching{store.delete(report)}.onSuccess{refresh()}
                            .onFailure{notify(it.message?:"Erro a apagar.")}
                    }.setNegativeButton("Cancelar",null).show()
            })
        }
        card("Sobre estes resultados",
            "A SaúdePrática guarda o relatório original e os dados que confirmares. "+
            "O OCR pode falhar em nomes, unidades, vírgulas ou intervalos de referência. "+
            "Confirma com o documento e com um profissional de saúde. "+
            "A aplicação não faz diagnósticos.")
    }

    private fun capture(){
        try{
            val path=File(cacheDir,"clinical_lab_camera").apply{mkdirs()}
            val photo=File.createTempFile("analise_",".jpg",path)
            cameraFile=photo
            camera.launch(FileProvider.getUriForFile(this,
                packageName+".documents",photo))
        }catch(e:Exception){
            cameraFile?.delete()
            cameraFile=null
            notify("Não foi possível iniciar a câmara: "+e.message)
        }
    }

    private fun startScan(uri:Uri,temp:File?){
        if(busy)return
        val mime=contentResolver.getType(uri)?:if(uri.toString().endsWith(".pdf"))
            "application/pdf" else "image/jpeg"
        busy=true
        val info=label("A reconhecer o relatório…",15f,false,ink)
        val container=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(18),dp(12),dp(18),dp(12))
            addView(ProgressBar(this@ClinicalLabsActivity))
            addView(info)
        }
        val wait=MaterialAlertDialogBuilder(this)
            .setTitle("OCR das análises clínicas")
            .setView(container).setCancelable(false).show()
        val recognizer=TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)
        val results=mutableListOf<LabValue>()
        val raw=StringBuilder()
        var lastSection=""
        fun finish(error:String?=null){
            busy=false
            recognizer.close()
            if(!isFinishing)wait.dismiss()
            if(error!=null){
                temp?.delete()
                notify(error)
            }else{
                review(uri,mime,temp,results,raw.toString())
            }
        }
        fun record(page:Int,image:InputImage,continueScan:()->Unit){
            recognizer.process(image)
                .addOnSuccessListener{response->
                    raw.append("\n--- PÁGINA ").append(page).append(" ---\n")
                        .append(response.text).append("\n")
                    val words=response.textBlocks.flatMap{block->
                        block.lines.flatMap{line->line.elements}
                    }.mapNotNull{part->
                        part.boundingBox?.let{r->
                            LabWord(part.text,r.left.toFloat()/
                                image.width.coerceAtLeast(1),
                                r.exactCenterY(),r.height().toFloat())
                        }
                    }
                    val parsed=ClinicalLabParser.extract(words,page,lastSection)
                    results.addAll(parsed.first)
                    lastSection=parsed.second
                    continueScan()
                }.addOnFailureListener{error->
                    raw.append("\nPágina ").append(page)
                        .append(": OCR falhou — ").append(error.message)
                    continueScan()
                }
        }
        if(mime=="application/pdf"){
            try{
                val descriptor=contentResolver.openFileDescriptor(uri,"r")
                    ?:error("Não foi possível abrir o PDF.")
                val renderer=PdfRenderer(descriptor)
                val count=renderer.pageCount
                if(count<=0||count>40){
                    renderer.close()
                    error("Este PDF tem "+count+" páginas (máximo 40 por relatório).")
                }
                fun next(index:Int){
                    if(index>=count){
                        renderer.close();finish();return
                    }
                    info.text="A reconhecer página "+(index+1)+" de "+count+"…"
                    try{
                        val page=renderer.openPage(index)
                        val factor=minOf(2.4f,1700f/page.width.toFloat())
                        val w=(page.width*factor).toInt().coerceAtLeast(1)
                        val h=(page.height*factor).toInt().coerceAtLeast(1)
                        val bitmap=Bitmap.createBitmap(w,h,Bitmap.Config.ARGB_8888)
                        bitmap.eraseColor(Color.WHITE)
                        page.render(bitmap,null,Matrix().apply{postScale(factor,factor)},
                            PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
                        page.close()
                        record(index+1,InputImage.fromBitmap(bitmap,0)){
                            bitmap.recycle()
                            next(index+1)
                        }
                    }catch(e:Exception){
                        renderer.close()
                        finish("Erro na página "+(index+1)+": "+e.message)
                    }
                }
                next(0)
            }catch(e:Exception){finish("Não foi possível ler o PDF: "+e.message)}
        }else if(mime.startsWith("image/")){
            try{
                val image=InputImage.fromFilePath(this,uri)
                record(1,image){finish()}
            }catch(e:Exception){finish("Não foi possível abrir a imagem: "+e.message)}
        }else finish("Escolhe um PDF ou uma imagem.")
    }

    private fun review(uri:Uri,mime:String,temp:File?,
        detected:List<LabValue>,rawText:String){
        val form=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL
            setPadding(dp(16),dp(6),dp(16),dp(16))}
        fun line(v:View){form.addView(v,LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT)
            .apply{bottomMargin=dp(8)})}
        line(label("Corrige valores, unidades e referências antes de guardar.",
            13f,false,muted))
        val title=edit("Nome do relatório","Análises Clínicas")
        val date=edit("Data da análise (DD/MM/AAAA)","")
        line(title);line(date)
        val entries=mutableListOf<List<EditText>>()
        fun addEntry(v:LabValue){
            line(label("Página "+v.page+" · "+v.section.ifBlank{"Resultados"},13f,false,teal))
            val a=edit("Parâmetro",v.parameter)
            val b=edit("Resultado",v.result)
            val c=edit("Unidade",v.unit)
            val d=edit("Valores de referência",v.reference)
            val e=edit("Resultado anterior (se existir)",v.previous)
            listOf(a,b,c,d,e).forEach(::line)
            entries.add(listOf(a,b,c,d,e))
        }
        detected.forEach(::addEntry)
        if(detected.isEmpty())line(label("Não consegui separar resultados automaticamente. "+
            "Podes adicioná-los manualmente ou consultar o texto lido.",13f,false,muted))
        line(button("＋ Adicionar parâmetro"){
            addEntry(LabValue("","", "", "", "", "",1))
        })
        line(button("🔎 Ver texto integral do OCR"){
            val t=TextView(this).apply{
                text=rawText.ifBlank{"Não foi encontrado texto legível."}
                setTextIsSelectable(true);setTextColor(ink)
                setPadding(dp(14),dp(12),dp(14),dp(12))
            }
            MaterialAlertDialogBuilder(this).setTitle("Texto extraído")
                .setView(ScrollView(this).apply{addView(t)})
                .setPositiveButton("Fechar",null).show()
        })
        line(label("O ficheiro original será guardado neste perfil. "+
            "Os valores de referência são os do laboratório, não recomendações da aplicação.",
            12f,false,muted))
        val scroll=ScrollView(this).apply{addView(form)}
        val dialog=MaterialAlertDialogBuilder(this)
            .setTitle("Rever análise clínica")
            .setView(scroll).setPositiveButton("Guardar",null)
            .setNegativeButton("Cancelar"){_,_->temp?.delete()}
            .setOnCancelListener{temp?.delete()}
            .show()
        dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE)
            .setOnClickListener{
                val name=title.text.toString().trim()
                if(name.isBlank()){title.error="Indica o nome.";return@setOnClickListener}
                val dateRaw=date.text.toString().trim()
                if(dateRaw.isNotBlank()){
                    val valid=runCatching{
                        java.time.LocalDate.parse(dateRaw,
                            java.time.format.DateTimeFormatter.ofPattern("dd/MM/uuuu")
                                .withResolverStyle(java.time.format.ResolverStyle.STRICT))
                    }.isSuccess
                    if(!valid){date.error="Data inválida.";return@setOnClickListener}
                }
                val values=entries.mapNotNull { group->
                    val parts=group.map{it.text.toString().trim()}
                    if(parts[0].isBlank()||parts[1].isBlank())null else
                        LabValue("",parts[0],parts[1],parts[2],parts[3],parts[4],1)
                }
                if(values.isEmpty() && rawText.isBlank()){
                    notify("Não existem dados reconhecidos. Corrige ou adiciona um parâmetro.")
                    return@setOnClickListener
                }
                runCatching{store.add(uri,name,dateRaw,mime,rawText,values)}
                    .onSuccess{
                        dialog.dismiss()
                        temp?.delete()
                        refresh()
                        Toast.makeText(this,"Relatório guardado neste perfil.",
                            Toast.LENGTH_LONG).show()
                    }.onFailure{notify(it.message?:"Não foi possível guardar o relatório.")}
            }
    }
    private fun viewReport(report:LabReport){
        val lines=buildString{
            append(report.title)
            if(report.date.isNotBlank())append("\nData: ").append(report.date)
            report.values.forEach{v->
                append("\n\n").append(v.parameter).append(": ").append(v.result)
                if(v.unit.isNotBlank())append(" ").append(v.unit)
                if(v.reference.isNotBlank())append("\nReferência: ").append(v.reference)
                if(v.previous.isNotBlank())append("\nAnterior: ").append(v.previous)
            }
            append("\n\n--- TEXTO ORIGINAL DO OCR ---\n")
            append(report.rawText)
        }
        val text=TextView(this).apply{
            this.text=lines
            setTextColor(ink);textSize=14f;setTextIsSelectable(true)
            setPadding(dp(16),dp(12),dp(16),dp(12))
        }
        MaterialAlertDialogBuilder(this)
            .setTitle("Resultados guardados")
            .setView(ScrollView(this).apply{addView(text)})
            .setPositiveButton("Fechar",null).show()
    }
    private fun openOriginal(report:LabReport){
        runCatching{
            startActivity(Intent.createChooser(Intent(Intent.ACTION_VIEW).apply{
                setDataAndType(store.contentUri(report),report.mime)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            },"Abrir análises"))
        }.onFailure{notify("Não foi possível abrir o documento original: "+it.message)}
    }
}
