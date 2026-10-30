package com.mediagenda.app

import android.app.Activity
import android.content.Intent
import android.content.res.ColorStateList
import android.graphics.BitmapFactory
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.net.Uri
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.CheckBox
import android.widget.EditText
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.FileProvider
import androidx.core.widget.doAfterTextChanged
import com.google.android.material.button.MaterialButton
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import com.mediagenda.app.data.ProfileMediaStore
import com.mediagenda.app.data.ProfileStore
import com.mediagenda.app.i18n.AppLanguage
import com.mediagenda.app.notifications.DeviceAlarmRouting
import com.mediagenda.app.ocr.CitizenCardOcrParser
import com.mediagenda.app.ocr.ProfileCitizenCardOcr
import java.io.File

/** Guided 4-step profile creation. Nothing is persisted before the final confirmation. */
class ProfileWizardActivity:AppCompatActivity(){
    companion object { const val RESULT_PROFILE_ID="created_profile_id" }
    private val teal=Color.rgb(8,171,158)
    private val bg=Color.rgb(5,28,37)
    private var step=0
    private var name=""
    private var fullName=""
    private var birth=""
    private var nif=""
    private var sns=""
    private var ccNumber=""
    private var phone=""
    private var email=""
    private var owner=false
    private var caregiver=false
    private var saveCcPhotos=false
    private var currentPhotoKind="avatar"
    private var cameraFile:File?=null
    private val tempFiles=mutableMapOf<String,File>()
    private val ocrText=mutableMapOf<String,String>()
    private lateinit var body:LinearLayout
    private lateinit var progress:TextView
    private lateinit var next:MaterialButton
    private lateinit var previous:MaterialButton

    private val picker=registerForActivityResult(ActivityResultContracts.GetContent()){uri->
        if(uri!=null)copyPhotoToPrivateDraft(uri,currentPhotoKind)
    }
    private val camera=registerForActivityResult(ActivityResultContracts.TakePicture()){ok->
        val file=cameraFile;cameraFile=null
        if(ok && (file?.length() ?: 0L)>100L){
            file?.let{processCapturedPhoto(it,currentPhotoKind)}
        }else{file?.delete();toast("Não foi possível obter a fotografia.")}
    }

    override fun onCreate(state:Bundle?){
        super.onCreate(state)
        if(state!=null){
            step=state.getInt("wizard_step",0).coerceIn(0,3)
            name=state.getString("wizard_name","")
            fullName=state.getString("wizard_full_name","")
            birth=state.getString("wizard_birth","")
            nif=state.getString("wizard_nif","")
            sns=state.getString("wizard_sns","")
            ccNumber=state.getString("wizard_cc","")
            phone=state.getString("wizard_phone","")
            email=state.getString("wizard_email","")
            owner=state.getBoolean("wizard_owner")
            caregiver=state.getBoolean("wizard_caregiver")
            saveCcPhotos=state.getBoolean("wizard_save_cc")
            currentPhotoKind=state.getString("wizard_current_photo","avatar")
            state.getStringArrayList("wizard_photo_paths")?.forEach { value->
                val key=value.substringBefore(':');val path=value.substringAfter(':')
                val file=File(path);if(key in listOf("avatar","cc_front","cc_back") &&
                    file.isFile && file.canonicalPath.startsWith(File(cacheDir,"profile_wizard").canonicalPath))
                    tempFiles[key]=file
            }
            cameraFile=state.getString("wizard_camera_path")?.let{File(it)}
        }
        val root=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL;setPadding(dp(18),dp(26),dp(18),dp(12));setBackgroundColor(bg)
        }
        val top=TextView(this).apply{
            text="SaúdePrática · Novo perfil";textSize=23f
            setTextColor(Color.WHITE);setTypeface(typeface,Typeface.BOLD)
            setPadding(0,dp(5),0,dp(10))
        }
        root.addView(top)
        progress=TextView(this).apply{textSize=13f;setTextColor(Color.rgb(113,227,206))}
        root.addView(progress)
        val scroll=ScrollView(this).apply{isFillViewport=true;isVerticalScrollBarEnabled=true}
        body=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL;setPadding(0,dp(16),0,dp(12))}
        scroll.addView(body)
        root.addView(scroll,LinearLayout.LayoutParams(-1,0,1f))
        val bottom=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL;gravity=Gravity.CENTER_VERTICAL}
        previous=button("‹ Anterior"){if(step>0){step--;render()}else finish()}
        next=button("Seguinte ›"){advance()}
        bottom.addView(previous,LinearLayout.LayoutParams(0,dp(58),1f).apply{marginEnd=dp(6)})
        bottom.addView(next,LinearLayout.LayoutParams(0,dp(58),1f).apply{marginStart=dp(6)})
        root.addView(bottom)
        setContentView(root)
        render()
    }
    override fun onSaveInstanceState(state:Bundle){
        state.putInt("wizard_step",step)
        state.putString("wizard_name",name);state.putString("wizard_full_name",fullName)
        state.putString("wizard_birth",birth);state.putString("wizard_nif",nif)
        state.putString("wizard_sns",sns);state.putString("wizard_cc",ccNumber)
        state.putString("wizard_phone",phone);state.putString("wizard_email",email)
        state.putBoolean("wizard_owner",owner);state.putBoolean("wizard_caregiver",caregiver)
        state.putBoolean("wizard_save_cc",saveCcPhotos);state.putString("wizard_current_photo",currentPhotoKind)
        state.putStringArrayList("wizard_photo_paths",ArrayList(tempFiles.map{"${it.key}:${it.value.absolutePath}"}))
        state.putString("wizard_camera_path",cameraFile?.absolutePath)
        super.onSaveInstanceState(state)
    }
    private fun dp(x:Int)=(x*resources.displayMetrics.density+.5f).toInt()
    private fun tr(pt:String,en:String,fr:String,de:String,es:String):String=when(AppLanguage.code(this)){
        "en"->en;"fr"->fr;"de"->de;"es"->es;else->pt
    }
    private fun toast(s:String)=Toast.makeText(this,s,Toast.LENGTH_LONG).show()
    private fun label(text:String,size:Float=15f,weight:Boolean=false):TextView=TextView(this).apply{
        this.text=text;textSize=size;setTextColor(Color.WHITE)
        if(weight)setTypeface(typeface,Typeface.BOLD)
        setPadding(0,dp(9),0,dp(8))
    }
    private fun button(title:String,clicked:()->Unit)=MaterialButton(this).apply{
        text=title;isAllCaps=false;textSize=14f;minHeight=dp(52)
        backgroundTintList=ColorStateList.valueOf(Color.rgb(9,112,105))
        setTextColor(Color.WHITE);cornerRadius=dp(15)
        setOnClickListener{clicked()}
    }
    private fun field(title:String,value:String,changed:(String)->Unit):EditText{
        body.addView(label(title,13f,true))
        return EditText(this).apply{
            setText(value);textSize=16f;setTextColor(Color.WHITE)
            setHintTextColor(Color.LTGRAY)
            backgroundTintList=ColorStateList.valueOf(teal)
            minHeight=dp(50);setSingleLine(true)
            doAfterTextChanged{changed(it?.toString().orEmpty())}
            body.addView(this)
        }
    }
    private fun hint(text:String){body.addView(label(text,13f).apply{setTextColor(Color.rgb(170,201,211))})}
    private fun check(title:String,selected:Boolean,clicked:(Boolean)->Unit){
        body.addView(CheckBox(this).apply{
            text=title;isChecked=selected;textSize=15f
            setTextColor(Color.WHITE);buttonTintList=ColorStateList.valueOf(teal)
            setPadding(dp(4),dp(11),dp(3),dp(11));minHeight=dp(52)
            setOnCheckedChangeListener{_,yes->clicked(yes)}
        })
    }
    private fun photo(kind:String){
        val file=tempFiles[kind]
        val size=if(kind=="avatar")144 else 84
        val pic=ImageView(this).apply{
            scaleType=ImageView.ScaleType.CENTER_CROP
            contentDescription=if(kind=="avatar")"Fotografia do perfil" else "Fotografia do Cartão de Cidadão"
            background=GradientDrawable().apply{setColor(Color.rgb(20,68,75));cornerRadius=dp(18).toFloat()}
            clipToOutline=true
            if(file?.isFile==true)setImageBitmap(BitmapFactory.decodeFile(file.absolutePath))
            else setImageResource(if(kind=="avatar")R.drawable.saude_icon else android.R.drawable.ic_menu_camera)
            setOnClickListener{choosePhoto(kind)}
        }
        body.addView(pic,LinearLayout.LayoutParams(dp(size),dp(size)).apply{
            gravity=Gravity.CENTER_HORIZONTAL;bottomMargin=dp(12)
        })
        body.addView(button(if(kind=="avatar")"📷 Tirar / escolher fotografia de perfil"
            else if(kind=="cc_front")"📷 Fotografia da frente do CC"
            else "📷 Fotografia do verso do CC"){choosePhoto(kind)})
    }
    private fun choosePhoto(kind:String){
        currentPhotoKind=kind
        MaterialAlertDialogBuilder(this)
            .setTitle("Adicionar fotografia")
            .setItems(arrayOf("Fotografar com a câmara","Escolher do telemóvel")){_,which->
                if(which==0){
                    try{
                        val dir=File(cacheDir,"profile_wizard").apply{mkdirs()}
                        cameraFile=File.createTempFile("wizard_", ".jpg",dir)
                        camera.launch(FileProvider.getUriForFile(this,"$packageName.documents",cameraFile!!))
                    }catch(e:Exception){toast("Câmara indisponível: "+e.message)}
                }else picker.launch("image/*")
            }.setNegativeButton("Cancelar",null).show()
    }
    private fun processCapturedPhoto(file:File,kind:String){
        val former=tempFiles.put(kind,file)
        if(former!=file)former?.delete()
        if(kind.startsWith("cc_"))scanCC(kind,file)
        render()
    }
    private fun copyPhotoToPrivateDraft(uri:Uri,kind:String){
        try{
            val file=File.createTempFile("wizard_", ".jpg",File(cacheDir,"profile_wizard").apply{mkdirs()})
            contentResolver.openInputStream(uri)?.use{input->file.outputStream().use{output->input.copyTo(output)}}
                ?:error("Não foi possível abrir a imagem")
            require(file.length() in 100..(12L*1024*1024)){"Fotografia inválida ou demasiado grande"}
            processCapturedPhoto(file,kind)
        }catch(e:Exception){toast(e.message?:"Erro ao guardar imagem")}
    }
    private fun scanCC(kind:String,file:File){
        val recognizer=TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)
        runCatching{InputImage.fromFilePath(this,Uri.fromFile(file))}
            .onFailure{toast("Fotografia inválida");recognizer.close()}
            .onSuccess{image->
                recognizer.process(image).addOnSuccessListener{result->
                    ocrText[kind]=result.text
                    val proposed=ProfileCitizenCardOcr.propose(
                        ocrText["cc_front"].orEmpty(),ocrText["cc_back"].orEmpty())
                        .filter {it.key in setOf("full_name","birth_date","nif","sns_number","cc_number")}
                    if(proposed.isEmpty()){
                        toast("OCR sem dados fiáveis. Podes preencher manualmente.")
                    }else{
                        val keep=BooleanArray(proposed.size){true}
                        MaterialAlertDialogBuilder(this).setTitle("Confirmar dados lidos do CC")
                            .setMultiChoiceItems(proposed.map{"${it.label}: ${it.value}"}.toTypedArray(),
                                keep){_,i,checked->keep[i]=checked}
                            .setPositiveButton("Aplicar escolhas"){_,_->
                                proposed.forEachIndexed{i,p->if(keep[i])when(p.key){
                                    "full_name"->fullName=p.value
                                    "birth_date"->birth=p.value
                                    "nif"->nif=p.value
                                    "sns_number"->sns=p.value
                                    "cc_number"->ccNumber=p.value
                                }}
                                render()
                            }.setNegativeButton("Não usar",null).show()
                    }
                }.addOnFailureListener{toast("Não foi possível ler o CC")}
                    .addOnCompleteListener{recognizer.close()}
            }
    }
    private fun render(){
        body.removeAllViews()
        progress.text="● ${step+1}/4   "+listOf("Identificação","Cartão de Cidadão","Perfis e funções","Confirmar e guardar")[step]
        previous.text=if(step==0)"Cancelar" else "‹ Anterior"
        next.text=if(step==3)"✓ Criar perfil" else "Seguinte ›"
        when(step){
            0->{
                body.addView(label("Quem vai utilizar este perfil?",22f,true))
                hint("Indica o nome e escolhe uma fotografia. Podes alterá-los mais tarde.")
                field("Nome do perfil *",name){name=it}
                photo("avatar")
            }
            1->{
                body.addView(label("Identificação (opcional)",22f,true))
                hint("Podes preencher à mão ou fotografar o Cartão de Cidadão. " +
                    "O OCR propõe valores; só guardamos os dados que confirmares.")
                field("Nome completo",fullName){fullName=it}
                field("Data nascimento (DD/MM/AAAA)",birth){birth=it}
                field("NIF",nif){nif=it}
                field("Número de utente SNS",sns){sns=it}
                field("Número do CC",ccNumber){ccNumber=it}
                photo("cc_front");photo("cc_back")
                check("Guardar as fotografias do CC neste perfil?",saveCcPhotos){saveCcPhotos=it}
                hint("Se não escolheres guardar, as fotografias temporárias serão eliminadas. " +
                    "O CC contém dados sensíveis; protege o telemóvel com PIN.")
            }
            2->{
                body.addView(label("Quem utiliza este telemóvel?",22f,true))
                hint("Podes marcar as duas opções. Cada telemóvel só deve ter um perfil " +
                    "associado a alarmes fortes de medicação.")
                check("📱 Este perfil é do utilizador deste telemóvel",owner){owner=it}
                check("🤲 Este perfil é um cuidador familiar",caregiver){caregiver=it}
                hint("O cuidador pode consultar as tomas dos familiares disponíveis neste telemóvel.")
            }
            3->{
                body.addView(label("Últimos detalhes",22f,true))
                hint("Os contactos são opcionais. Confirma os dados antes de criar o perfil.")
                field("Telemóvel / telefone",phone){phone=it}
                field("Email",email){email=it}
                body.addView(label("Resumo",18f,true))
                hint("Perfil: "+name.ifBlank{"Sem nome"}+"\n"+
                    "Cartão de Cidadão: "+(if(ccNumber.isNotBlank())"Dados inseridos" else "Opcional"))
                hint("Fotografia: "+(if(tempFiles["avatar"]!=null)"Sim" else "Ainda não")+
                    " · CC: "+(if(saveCcPhotos)"Guardar fotos" else "Não guardar fotos"))
                hint("Deste telemóvel: "+(if(owner)"Sim" else "Não"))
                hint("Cuidador: "+(if(caregiver)"Sim" else "Não"))
            }
        }
    }
    private fun advance(){
        if(step==0){
            if(name.isBlank()){toast("Introduz o nome do perfil.");return}
            if(ProfileStore(this).all().any{it.name.equals(name.trim(),true)}){
                toast("Já existe um perfil com este nome.");return
            }
        }
        if(step==1){
            if(nif.isNotBlank()&&!CitizenCardOcrParser.validNif(nif.filter(Char::isDigit))){
                toast("Confirma o NIF; os 9 dígitos não são válidos.");return
            }
            if(sns.isNotBlank() && sns.filter(Char::isDigit).length!=9){
                toast("O número de utente SNS deve ter 9 dígitos.");return
            }
        }
        if(step<3){step++;render()}else finishWizard()
    }
    private fun finishWizard(){
        try{
            val created=ProfileStore(this).create(name)
            val edit=getSharedPreferences(ProfileStore(this).preferencesFor(created.id),MODE_PRIVATE).edit()
                .putString("full_name",fullName.trim())
                .putString("birth_date",birth.trim())
                .putString("nif",nif.filter(Char::isDigit))
                .putString("sns_number",sns.filter(Char::isDigit))
                .putString("cc_number",ccNumber.trim())
                .putString("phone",phone.trim())
                .putString("email",email.trim())
            if(!edit.commit())error("Não foi possível guardar os dados pessoais")
            if(owner)DeviceAlarmRouting.assign(this,created.id)
            if(caregiver)getSharedPreferences("saudepratica_caregiver_v1",MODE_PRIVATE)
                .edit().putString("caregiver_id",created.id).commit()
            val store=ProfileMediaStore(this,created.id)
            val errors=mutableListOf<String>()
            for((key,file) in tempFiles){
                if(key=="avatar" || (saveCcPhotos && key in setOf("cc_front","cc_back")))
                    runCatching{store.save(key,Uri.fromFile(file))}.onFailure{errors+=key}
            }
            tempFiles.values.forEach{it.delete()};tempFiles.clear()
            if(errors.isNotEmpty())toast("Perfil criado, mas não foi possível guardar algumas fotos.")
            setResult(Activity.RESULT_OK,Intent().putExtra(RESULT_PROFILE_ID,created.id))
            finish()
        }catch(e:Exception){toast("Não foi possível criar o perfil: "+(e.message?:"Erro"))}
    }
    override fun onDestroy(){
        if(isFinishing && !isChangingConfigurations){
            tempFiles.values.forEach{it.delete()};tempFiles.clear()
            cameraFile?.delete()
        }
        super.onDestroy()
    }
}
