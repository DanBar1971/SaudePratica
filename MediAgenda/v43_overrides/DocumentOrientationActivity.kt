package com.mediagenda.app

import android.content.Intent
import android.content.res.ColorStateList
import android.content.res.Configuration
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Color
import android.graphics.Matrix
import android.graphics.pdf.PdfRenderer
import android.net.Uri
import android.os.Bundle
import android.os.ParcelFileDescriptor
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import com.google.android.material.button.MaterialButton
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import com.mediagenda.app.data.DocumentOrientationStore
import java.io.File
import java.util.Locale

/** Local image/PDF orientation editor; never modifies the original PDF. */
class DocumentOrientationActivity:AppCompatActivity(){
    companion object{
        const val PROFILE="profile_id"
        const val GROUP="document_group"
        const val FILENAME="document_filename"
        const val TITLE="document_title"
    }
    private lateinit var source:File
    private lateinit var display:ImageView
    private lateinit var status:TextView
    private lateinit var pending:MutableMap<Int,Int>
    private var pdf=false
    private var pageCount=1
    private var pageIndex=0
    private var exifRotation=0
    private var busy=false
    private var preview:Bitmap?=null
    private val teal=Color.rgb(8,168,156)
    private val dark get()=when(getSharedPreferences("mediagenda_ui",MODE_PRIVATE)
        .getString("theme_mode","system")){
        "dark"->true;"light"->false
        else->(resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK)==
            Configuration.UI_MODE_NIGHT_YES
    }
    private val fg get()=if(dark)Color.WHITE else Color.rgb(19,36,51)
    private fun dp(v:Int)=(v*resources.displayMetrics.density+.5f).toInt()
    private val exportPage=registerForActivityResult(
        ActivityResultContracts.CreateDocument("image/png")
    ){uri->
        if(uri!=null)runCatching{
            val bitmap=loadSource(1900)
            val finalImage=rotate(bitmap,currentAngle())
            try{
                contentResolver.openOutputStream(uri,"w")?.use{
                    check(finalImage.compress(Bitmap.CompressFormat.PNG,100,it))
                }?:error("Não foi possível criar a imagem.")
                toast("Página exportada com a orientação corrigida.")
            }finally{
                if(finalImage!==bitmap)finalImage.recycle()
                bitmap.recycle()
            }
        }.onFailure{alert(it.message?:"Não foi possível exportar a página.")}
    }
    override fun onCreate(state:Bundle?){
        super.onCreate(state)
        val profile=intent.getStringExtra(PROFILE).orEmpty()
        val group=intent.getStringExtra(GROUP).orEmpty()
        val filename=intent.getStringExtra(FILENAME).orEmpty()
        val groups=mapOf(
            "identity" to "saudepratica_identity",
            "documents" to "saudepratica_documents",
            "workplace" to "saudepratica_workplace",
            "labs" to "saudepratica_labs",
            "expenses" to "saudepratica_expenses"
        )
        if((profile!="legacy"&&!profile.matches(Regex("""[0-9a-fA-F-]{36}""")))||
            group !in groups.keys||
            !filename.matches(Regex("""[a-zA-Z0-9_-]{1,90}\.(jpg|jpeg|png|webp|heic|heif|pdf)"""))){
            finish();return
        }
        val folder=File(filesDir,"${groups.getValue(group)}/$profile")
        val target=File(folder,filename)
        if(target.canonicalFile.parentFile!=folder.canonicalFile ||
            !target.isFile || target.length()>90L*1024*1024){
            finish();return
        }
        source=target
        pdf=filename.endsWith(".pdf")
        pending=DocumentOrientationStore.readAll(source).toMutableMap()
        exifRotation=if(pdf)0 else DocumentOrientationStore.exifRotation(source)
        try{
            if(pdf){
                val descriptor=ParcelFileDescriptor.open(source,ParcelFileDescriptor.MODE_READ_ONLY)
                PdfRenderer(descriptor).use{renderer->pageCount=renderer.pageCount}
                check(pageCount in 1..250){"PDF com um número de páginas não suportado."}
            }
        }catch(e:Exception){alert(e.message?:"Não foi possível abrir o PDF.");return}
        val root=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(14),dp(10),dp(14),dp(12))
            setBackgroundColor(if(dark)Color.rgb(5,23,33)else Color.rgb(245,249,250))
        }
        root.addView(TextView(this).apply{
            text="‹  SaúdePrática  /  Corrigir orientação"
            textSize=19f;setTextColor(teal)
            setPadding(dp(4),dp(6),dp(2),dp(16))
            setOnClickListener{finish()}
        })
        root.addView(TextView(this).apply{
            text=intent.getStringExtra(TITLE).orEmpty().ifBlank{"Documento"}
            setTextColor(fg);textSize=20f
            setPadding(dp(5),0,dp(5),dp(10))
        })
        status=TextView(this).apply{
            setTextColor(if(dark)Color.rgb(188,213,222)else Color.rgb(68,91,107))
            textSize=13f;gravity=Gravity.CENTER
            setPadding(0,dp(4),0,dp(10))
        }
        root.addView(status)
        display=ImageView(this).apply{
            scaleType=ImageView.ScaleType.FIT_CENTER
            setBackgroundColor(if(dark)Color.rgb(20,36,45)else Color.rgb(229,238,241))
            contentDescription="Pré-visualização da orientação do documento"
        }
        root.addView(display,LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,0,1f))
        fun row(vararg entries:Pair<String,()->Unit>){
            val bar=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL}
            entries.forEach{(caption,click)->
                bar.addView(button(caption,click),LinearLayout.LayoutParams(
                    0,ViewGroup.LayoutParams.WRAP_CONTENT,1f))
            }
            root.addView(bar)
        }
        row("↶ 90º" to {change(-90)}, "↷ 90º" to {change(90)},
            "⤾ 180º" to {change(180)})
        row("↺ Repor" to {pending[pageIndex]=0;redraw()},
            "✨ Auto OCR" to {detectOrientation()})
        if(pdf){
            row("‹ Página" to {if(pageIndex>0){pageIndex--;redraw()}},
                "Página ›" to {if(pageIndex<pageCount-1){pageIndex++;redraw()}},
                "Exportar PNG" to {
                    exportPage.launch("SaudePratica-pagina-${pageIndex+1}.png")
                })
        }
        row("Cancelar" to {finish()}, "Guardar orientação" to {saveOrientation()})
        if(pdf)root.addView(TextView(this).apply{
            text="O PDF original não é alterado. A orientação de cada página "+
                "fica guardada na SaúdePrática; podes exportar a página rodada em PNG."
            textSize=12f;setTextColor(fg)
            setPadding(dp(6),dp(4),dp(6),0)
        })
        WindowCompat.setDecorFitsSystemWindows(window,false)
        window.statusBarColor=Color.TRANSPARENT
        window.navigationBarColor=Color.TRANSPARENT
        WindowInsetsControllerCompat(window,window.decorView).apply{
            isAppearanceLightStatusBars=!dark
            isAppearanceLightNavigationBars=!dark
        }
        ViewCompat.setOnApplyWindowInsetsListener(root){view,insets->
            val safe=insets.getInsets(WindowInsetsCompat.Type.statusBars() or
                WindowInsetsCompat.Type.navigationBars() or
                WindowInsetsCompat.Type.displayCutout())
            view.setPadding(dp(14)+safe.left,dp(10)+safe.top,
                dp(14)+safe.right,dp(12)+safe.bottom)
            insets
        }
        setContentView(root)
        ViewCompat.requestApplyInsets(root)
        redraw()
    }
    private fun button(label:String,action:()->Unit)=MaterialButton(this).apply{
        text=label;isAllCaps=false;textSize=12f
        setTextColor(if(dark)Color.rgb(152,239,229)else Color.rgb(0,104,102))
        backgroundTintList=ColorStateList.valueOf(
            if(dark)Color.rgb(29,48,57)else Color.rgb(226,240,238))
        cornerRadius=dp(11)
        setOnClickListener{if(!busy)action()}
    }
    private fun currentAngle()=((pending[pageIndex]?:0)%360+360)%360
    private fun change(deg:Int){
        pending[pageIndex]=((currentAngle()+deg)%360+360)%360
        redraw()
    }
    private fun loadSource(maxSide:Int):Bitmap{
        if(pdf){
            ParcelFileDescriptor.open(source,ParcelFileDescriptor.MODE_READ_ONLY).use{descriptor->
                PdfRenderer(descriptor).use{renderer->
                    val page=renderer.openPage(pageIndex)
                    try{
                        val ratio=minOf(maxSide.toFloat()/page.width,
                            maxSide.toFloat()/page.height,2.5f)
                        val width=(page.width*ratio).toInt().coerceAtLeast(1)
                        val height=(page.height*ratio).toInt().coerceAtLeast(1)
                        val bitmap=Bitmap.createBitmap(width,height,Bitmap.Config.ARGB_8888)
                        bitmap.eraseColor(Color.WHITE)
                        page.render(bitmap,null,Matrix().apply{postScale(ratio,ratio)},
                            PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
                        return bitmap
                    }finally{page.close()}
                }
            }
        }
        val bounds=BitmapFactory.Options().apply{inJustDecodeBounds=true}
        BitmapFactory.decodeFile(source.absolutePath,bounds)
        check(bounds.outWidth in 1..15000&&bounds.outHeight in 1..15000){
            "Dimensões inválidas."
        }
        var sample=1
        while(bounds.outWidth/sample>maxSide*2||
            bounds.outHeight/sample>maxSide*2)sample*=2
        return BitmapFactory.decodeFile(source.absolutePath,BitmapFactory.Options().apply{
            inSampleSize=sample
            inPreferredConfig=Bitmap.Config.ARGB_8888
        })?:error("Não foi possível ler a fotografia.")
    }
    private fun rotate(bitmap:Bitmap,degrees:Int):Bitmap{
        val angle=(degrees+if(pdf)0 else exifRotation)%360
        if(angle==0)return bitmap
        return Bitmap.createBitmap(bitmap,0,0,bitmap.width,bitmap.height,
            Matrix().apply{postRotate(angle.toFloat())},true)
    }
    private fun redraw(){
        if(busy)return
        try{
            val bitmap=loadSource(1400)
            val corrected=rotate(bitmap,currentAngle())
            if(corrected!==bitmap)bitmap.recycle()
            display.setImageBitmap(corrected)
            preview?.recycle()
            preview=corrected
            status.text=(if(pdf)"Página ${pageIndex+1} de $pageCount · " else "")+
                "Orientação: ${(currentAngle()+exifRotation)%360}º"
        }catch(e:Exception){alert(e.message?:"Falha na pré-visualização.")}
    }
    private fun detectOrientation(){
        if(busy)return
        busy=true
        val input=runCatching{loadSource(1200)}.getOrElse{
            busy=false;alert("Falha a abrir imagem: "+it.message);return
        }
        val detector=TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)
        var index=0
        val scores=mutableListOf<Pair<Int,Int>>()
        val original=currentAngle()
        val turns=intArrayOf(0,90,180,270)
        val progress=MaterialAlertDialogBuilder(this)
            .setTitle("Detetar orientação")
            .setMessage("A analisar localmente quatro orientações. "+
                "Confirma a sugestão antes de guardar.")
            .setView(ProgressBar(this).apply{setPadding(dp(24),dp(10),dp(24),dp(16))})
            .setCancelable(false).show()
        fun finish(){
            detector.close();input.recycle()
            busy=false;progress.dismiss()
            val winner=scores.maxByOrNull{it.second}
            if(winner==null||winner.second<=1){
                alert("Não foi possível determinar a orientação. "+
                    "Utiliza os botões de 90º e confirma visualmente.")
                return
            }
            pending[pageIndex]=(original+winner.first)%360
            redraw()
            toast("Orientação sugerida: ${currentAngle()}º. Confirma e guarda.")
        }
        fun next(){
            if(index>=turns.size){finish();return}
            val turn=turns[index++]
            val angle=(original+turn+exifRotation)%360
            detector.process(InputImage.fromBitmap(input,angle))
                .addOnSuccessListener{result->
                    val normalized=result.text.uppercase(Locale.ROOT)
                        .replace("Ã","A").replace("Õ","O").replace("Ç","C")
                    val clues=listOf("PORTUGAL","CARTAO","CITIZEN",
                        "NOME","NASCIMENTO","APELIDO","FILIACAO",
                        "DATA","EXAME","RESULTADO","RELATORIO",
                        "VISAO","AUDIO","FARMACIA","NIF","SNS")
                    val score=(normalized.count{it.isLetter()}/22)+
                        clues.count{normalized.contains(it)}*18+
                        result.textBlocks.map{block->
                            block.lines.count{it.text.length>=4}
                        }.sum()
                    scores.add(turn to score);next()
                }.addOnFailureListener{scores.add(turn to 0);next()}
        }
        next()
    }
    private fun saveOrientation(){
        if(busy)return
        busy=true
        try{
            if(pdf || source.extension.lowercase() in listOf("heic","heif")){
                DocumentOrientationStore.writeAll(source,pending)
                toast("Orientação guardada sem alterar o documento original.")
            }else{
                DocumentOrientationStore.rewriteImage(source,currentAngle())
                DocumentOrientationStore.writeAll(source,emptyMap())
                toast("Imagem rodada e guardada para o OCR.")
            }
            setResult(RESULT_OK,Intent())
            finish()
        }catch(e:Exception){
            busy=false
            alert("Não foi possível guardar a rotação: "+e.message)
        }
    }
    private fun alert(message:String){
        MaterialAlertDialogBuilder(this).setTitle("SaúdePrática")
            .setMessage(message).setPositiveButton("OK",null).show()
    }
    private fun toast(value:String)=android.widget.Toast.makeText(
        this,value,android.widget.Toast.LENGTH_LONG).show()
    override fun onDestroy(){
        if(::display.isInitialized)display.setImageDrawable(null)
        preview?.recycle()
        super.onDestroy()
    }
}
