package com.mediagenda.app

import android.Manifest
import android.content.pm.PackageManager
import android.content.res.ColorStateList
import android.content.res.Configuration
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.BitmapDrawable
import android.graphics.drawable.ColorDrawable
import android.graphics.drawable.LayerDrawable
import android.net.Uri
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.LinearLayout
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
import com.mediagenda.app.data.ProfileMediaStore
import com.mediagenda.app.data.ProfileStore
import java.io.File

/** Personal photographs and identity documents stay inside this profile. */
class ProfileMediaActivity:AppCompatActivity(){
    companion object{const val PROFILE="profile_id"}
    private lateinit var profileId:String
    private lateinit var profileName:String
    private lateinit var media:ProfileMediaStore
    private lateinit var body:LinearLayout
    private var target="avatar"
    private var pendingCamera:File?=null
    private val primary=Color.rgb(7,166,156)
    private val dark:Boolean get()=when(
        getSharedPreferences("mediagenda_ui",MODE_PRIVATE).getString("theme_mode","system")){
        "dark"->true
        "light"->false
        else->(resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK)==
            Configuration.UI_MODE_NIGHT_YES
    }
    private val ink get()=if(dark)Color.rgb(242,248,251)else Color.rgb(19,34,56)
    private val muted get()=if(dark)Color.rgb(189,207,218)else Color.rgb(90,110,124)
    private fun dp(x:Int)=(x*resources.displayMetrics.density+.5f).toInt()
    private val picker=registerForActivityResult(ActivityResultContracts.GetContent()){uri->
        uri?.let{storeImage(it)}
    }
    private val camera=registerForActivityResult(ActivityResultContracts.TakePicture()){ok->
        val file=pendingCamera
        pendingCamera=null
        if(ok&&file!=null)storeImage(Uri.fromFile(file),file)else file?.delete()
    }
    private val cameraPermission=registerForActivityResult(ActivityResultContracts.RequestPermission()){ok->
        if(ok)startCamera()
        else Toast.makeText(this,"Câmara não autorizada.",Toast.LENGTH_SHORT).show()
    }
    override fun onCreate(savedInstanceState:Bundle?){
        super.onCreate(savedInstanceState)
        val people=ProfileStore(this).all()
        val p=people.firstOrNull{it.id==intent.getStringExtra(PROFILE)}
            ?:people.singleOrNull()?:run{finish();return}
        profileId=p.id
        profileName=p.name
        media=ProfileMediaStore(this,profileId)
        target=savedInstanceState?.getString("target")?:target
        pendingCamera=savedInstanceState?.getString("camera_path")?.let{File(it)}

        val backdrop=ContextCompat.getDrawable(this,R.drawable.saude_background)
        if(backdrop is BitmapDrawable)backdrop.gravity=Gravity.FILL
        val root=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            background=if(dark&&backdrop!=null)
                LayerDrawable(arrayOf(backdrop,ColorDrawable(Color.argb(112,3,14,23))))
                else ColorDrawable(if(dark)Color.rgb(5,22,31)else Color.rgb(246,249,251))
            setPadding(dp(16),dp(10),dp(16),dp(8))
        }
        val top=LinearLayout(this).apply{
            orientation=LinearLayout.HORIZONTAL;gravity=Gravity.CENTER_VERTICAL
        }
        top.addView(label("‹",33f,false,primary).apply{
            gravity=Gravity.CENTER
            contentDescription="Voltar ao perfil"
            setOnClickListener{finish()}
        },LinearLayout.LayoutParams(dp(38),dp(65)))
        val title=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
        title.addView(label("SaúdePrática",13f,true,primary))
        title.addView(label("👤 Fotografias do Perfil",22f,true))
        title.addView(label(profileName+" · guardadas neste telemóvel",12f,false,muted))
        top.addView(title,LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f))
        root.addView(top)
        val scroller=ScrollView(this).apply{overScrollMode=View.OVER_SCROLL_NEVER}
        body=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
        scroller.addView(body)
        root.addView(scroller,LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,0,1f))
        WindowCompat.setDecorFitsSystemWindows(window,false)
        window.statusBarColor=Color.TRANSPARENT
        window.navigationBarColor=Color.TRANSPARENT
        WindowInsetsControllerCompat(window,window.decorView).apply{
            isAppearanceLightStatusBars=!dark
            isAppearanceLightNavigationBars=!dark
            hide(WindowInsetsCompat.Type.navigationBars())
        }
        ViewCompat.setOnApplyWindowInsetsListener(root){v,insets->
            val safe=insets.getInsets(WindowInsetsCompat.Type.statusBars() or
                WindowInsetsCompat.Type.navigationBars() or WindowInsetsCompat.Type.displayCutout())
            v.setPadding(dp(16)+safe.left,dp(10)+safe.top,
                dp(16)+safe.right,dp(8)+safe.bottom)
            insets
        }
        setContentView(root)
        ViewCompat.requestApplyInsets(root)
        draw()
    }
    override fun onSaveInstanceState(out:Bundle){
        out.putString("target",target)
        out.putString("camera_path",pendingCamera?.absolutePath)
        super.onSaveInstanceState(out)
    }
    private fun label(t:String,size:Float=14f,bold:Boolean=false,color:Int=ink)=TextView(this).apply{
        text=t;textSize=size;setTextColor(color)
        if(bold)setTypeface(null,Typeface.BOLD)
    }
    private fun outline(value:String,click:()->Unit)=MaterialButton(this).apply{
        text=value;isAllCaps=false;textSize=12f
        setTextColor(if(dark)Color.rgb(140,238,226)else Color.rgb(5,110,103))
        backgroundTintList=ColorStateList.valueOf(Color.TRANSPARENT)
        strokeColor=ColorStateList.valueOf(primary)
        strokeWidth=dp(1);cornerRadius=dp(15)
        setOnClickListener{click()}
    }
    private fun card():MaterialCardView=MaterialCardView(this).apply{
        radius=dp(19).toFloat();strokeWidth=dp(1)
        strokeColor=if(dark)Color.rgb(73,98,111)else Color.rgb(214,226,235)
        setCardBackgroundColor(if(dark)Color.rgb(28,41,53)else Color.WHITE)
    }
    private fun draw(){
        body.removeAllViews()
        val entries=listOf(
            Triple("avatar","Fotografia de perfil","Aparece junto ao nome do utilizador"),
            Triple("cc_front","Cartão de Cidadão — Frente","Fotografia privada do documento"),
            Triple("cc_back","Cartão de Cidadão — Verso","Fotografia privada do documento")
        )
        entries.forEach{(key,title,info)->
            val shell=card()
            val column=LinearLayout(this).apply{
                orientation=LinearLayout.VERTICAL
                setPadding(dp(16),dp(14),dp(16),dp(15))
            }
            column.addView(label(title,18f,true))
            column.addView(label(info,12f,false,muted))
            val photo=media.photo(key,900)
            if(photo!=null){
                val image=ImageView(this).apply{
                    setImageBitmap(photo)
                    scaleType=ImageView.ScaleType.FIT_CENTER
                    contentDescription=title
                    setOnClickListener{showImage(key,title)}
                }
                column.addView(image,LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,dp(if(key=="avatar")150 else 190))
                    .apply{topMargin=dp(8)})
                column.addView(outline("👁 Ver em grande"){showImage(key,title)})
            }else column.addView(label("Ainda sem fotografia",13f,false,muted).apply{
                setPadding(0,dp(13),0,dp(12))
            })
            column.addView(outline(if(photo==null)"📷 Adicionar fotografia"
                else "📷 Substituir fotografia"){chooseImage(key)})
            if(photo!=null)column.addView(outline("Apagar fotografia"){
                MaterialAlertDialogBuilder(this)
                    .setTitle("Apagar fotografia?")
                    .setMessage("Eliminar esta imagem do perfil de $profileName?")
                    .setPositiveButton("Apagar"){_,_->
                        if(media.remove(key))draw()else showError("Não foi possível eliminar.")
                    }.setNegativeButton("Cancelar",null).show()
            })
            shell.addView(column)
            body.addView(shell,LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT)
                .apply{bottomMargin=dp(12)})
        }
        body.addView(label(
            "As fotografias ficam na área privada deste utilizador. "+
            "Para proteger documentos de identificação, usa o bloqueio de ecrã do telemóvel. "+
            "Estas fotografias não são incluídas no backup JSON da aplicação.",
            12f,false,muted).apply{setPadding(dp(8),dp(8),dp(8),dp(30))})
    }
    private fun chooseImage(kind:String){
        target=kind
        MaterialAlertDialogBuilder(this).setTitle("Adicionar fotografia")
            .setItems(arrayOf("📷 Fotografar","🖼️ Escolher imagem do telemóvel")){_,chosen->
                if(chosen==0){
                    if(ContextCompat.checkSelfPermission(this,Manifest.permission.CAMERA)
                        ==PackageManager.PERMISSION_GRANTED)startCamera()
                    else cameraPermission.launch(Manifest.permission.CAMERA)
                }else picker.launch("image/*")
            }.setNegativeButton("Cancelar",null).show()
    }
    private fun startCamera(){
        try{
            val folder=File(cacheDir,"saudepratica_document_scans").apply{mkdirs()}
            val tmp=File.createTempFile("profile_",".jpg",folder)
            pendingCamera=tmp
            val uri=FileProvider.getUriForFile(this,"$packageName.documents",tmp)
            camera.launch(uri)
        }catch(e:Exception){showError("Não foi possível abrir a câmara: "+e.message)}
    }
    private fun storeImage(uri:Uri,temporary:File?=null){
        try{
            media.save(target,uri)
            Toast.makeText(this,"Fotografia guardada.",Toast.LENGTH_SHORT).show()
            draw()
        }catch(e:Exception){showError(e.message?:"Não foi possível guardar a fotografia.")}
        finally{temporary?.delete()}
    }
    private fun showImage(key:String,title:String){
        val image=media.photo(key,1800)
        if(image==null){showError("Fotografia indisponível.");return}
        val view=ImageView(this).apply{
            setImageBitmap(image)
            scaleType=ImageView.ScaleType.FIT_CENTER
            adjustViewBounds=true
            setPadding(dp(12),dp(6),dp(12),dp(6))
        }
        val scroll=ScrollView(this)
        scroll.addView(view)
        MaterialAlertDialogBuilder(this).setTitle(title).setView(scroll)
            .setPositiveButton("Fechar",null).show()
    }
    private fun showError(value:String){
        MaterialAlertDialogBuilder(this).setTitle("SaúdePrática")
            .setMessage(value).setPositiveButton("OK",null).show()
    }
}
