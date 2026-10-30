from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app")
path=root/"ProfileMediaActivity.kt"
s=path.read_text(encoding="utf-8")
def change(old,new,label):
    global s
    if old not in s:
        raise RuntimeError("v1.9.10 profile OCR missing: "+label+" "+old[:100])
    s=s.replace(old,new,1)

change('''import android.widget.ImageView''',
'''import android.widget.ImageView
import android.widget.EditText
import android.widget.CheckBox
import android.widget.ProgressBar''',"form controls")

change('''import com.mediagenda.app.data.ProfileStore''',
'''import com.mediagenda.app.data.ProfileStore
import com.mediagenda.app.ocr.ProfileCitizenCardOcr
import com.mediagenda.app.ocr.CitizenCardOcrParser
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.time.format.ResolverStyle''',"text recognition imports")

change('''    private var target="avatar"
    private var pendingCamera:File?=null''',
'''    private var target="avatar"
    private var pendingCamera:File?=null
    private var ocrRunning=false''',"OCR state")

change('''        body.addView(label(
            "As fotografias ficam na área privada deste utilizador.''',
'''        if(media.exists("cc_front") || media.exists("cc_back")){
            body.addView(outline("🔎 Ler CC com OCR e preencher o perfil") {
                scanSavedCitizenCard()
            },LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT).apply{bottomMargin=dp(12)})
        }
        body.addView(label(
            "As fotografias ficam na área privada deste utilizador.''',"OCR button")

change('''            Toast.makeText(this,"Fotografia guardada.",Toast.LENGTH_SHORT).show()
            draw()''',
'''            Toast.makeText(this,"Fotografia guardada.",Toast.LENGTH_SHORT).show()
            draw()
            if(target=="cc_front" || target=="cc_back"){
                MaterialAlertDialogBuilder(this)
                    .setTitle("Ler Cartão de Cidadão?")
                    .setMessage("Queres reconhecer os dados da imagem e preencher a ficha? Poderás confirmar cada campo antes de guardar.")
                    .setPositiveButton("Ler e rever") { _,_ -> scanSavedCitizenCard() }
                    .setNegativeButton("Agora não",null).show()
            }''',"offer OCR after import")

anchor='''    private fun showImage(key:String,title:String){'''
methods='''    private fun scanSavedCitizenCard(){
        if(ocrRunning)return
        val front=media.photo("cc_front",2000)
        val back=media.photo("cc_back",2000)
        if(front==null&&back==null){
            showError("Guarda primeiro a fotografia da frente ou do verso do CC.")
            return
        }
        ocrRunning=true
        val wait=MaterialAlertDialogBuilder(this)
            .setTitle("A ler Cartão de Cidadão")
            .setMessage("O reconhecimento é efetuado no telemóvel. Os dados só serão guardados depois de confirmares.")
            .setView(ProgressBar(this).apply{
                isIndeterminate=true
                setPadding(dp(20),dp(12),dp(20),dp(12))
            }).setCancelable(false).show()
        val reader=TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)
        var finished=false
        fun end(frontText:String,backText:String,error:String?=null){
            if(finished)return
            finished=true
            ocrRunning=false
            reader.close()
            wait.dismiss()
            if(error!=null){
                showError(error)
                return
            }
            val proposals=ProfileCitizenCardOcr.propose(frontText,backText)
            if(proposals.isEmpty())
                showError("Não identifiquei dados legíveis. Fotografa o cartão inteiro, com boa luz e sem reflexos, ou preenche o perfil manualmente.")
            else showOcrReview(proposals)
        }
        fun processBack(frontText:String){
            if(back==null){end(frontText,"");return}
            reader.process(InputImage.fromBitmap(back,0))
                .addOnSuccessListener{end(frontText,it.text)}
                .addOnFailureListener{end(frontText,"","Não foi possível reconhecer o verso do CC.")}
        }
        if(front!=null){
            reader.process(InputImage.fromBitmap(front,0))
                .addOnSuccessListener{processBack(it.text)}
                .addOnFailureListener{
                    // Back may still contain useful NIF / SNS / NISS.
                    if(back!=null)processBack("")
                    else end("","","Não foi possível reconhecer a frente do CC.")
                }
        } else processBack("")
    }

    private fun showOcrReview(proposals:List<ProfileCitizenCardOcr.Proposed>){
        // Never overwrite previously entered personal data by default.
        val profilePrefs=ProfileStore(this).preferencesFor(profileId)
        val prefs=getSharedPreferences(profilePrefs,MODE_PRIVATE)
        val form=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(18),dp(8),dp(18),dp(14))
        }
        form.addView(label(
            "Confirma os valores e seleciona os campos que queres guardar. "+
            "Os campos já preenchidos não ficam selecionados automaticamente.",
            13f,false,if(dark)Color.rgb(228,240,242)else Color.rgb(50,74,84)))
        val controls=proposals.map { item ->
            val current=prefs.getString(item.key,"").orEmpty()
            val checked=CheckBox(this).apply {
                text=item.label
                textSize=15f
                setTextColor(if(dark)Color.rgb(248,249,250)else Color.rgb(22,42,54))
                isChecked=current.isBlank()
            }
            form.addView(checked)
            val input=EditText(this).apply {
                setText(item.value)
                textSize=15f
                setTextColor(if(dark)Color.rgb(244,249,251)else Color.rgb(20,37,51))
                backgroundTintList=ColorStateList.valueOf(primary)
                setSingleLine(true)
            }
            form.addView(input)
            if(current.isNotBlank()){
                form.addView(label("Já guardado: "+current,12f,false,
                    if(dark)Color.rgb(194,216,224)else Color.rgb(73,97,109)))
            }
            Triple(item,checked,input)
        }
        val scroller=ScrollView(this).apply{addView(form)}
        val dialog=MaterialAlertDialogBuilder(this)
            .setTitle("Confirmar dados do CC")
            .setView(scroller)
            .setPositiveButton("Guardar escolhidos",null)
            .setNegativeButton("Cancelar",null)
            .show()
        dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE).setOnClickListener{
            val selected=controls.filter { it.second.isChecked }
            if(selected.isEmpty()){
                Toast.makeText(this,"Seleciona pelo menos um campo.",Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            val editor=prefs.edit()
            for((field,_,input) in selected){
                val raw=input.text.toString().trim()
                if(raw.isBlank()){input.error="Campo vazio";return@setOnClickListener}
                val accepted=when(field.key){
                    "nif"->CitizenCardOcrParser.validNif(raw)
                    "sns_number"->raw.matches(Regex("""\d{9}"""))
                    "niss"->raw.matches(Regex("""\d{11}"""))
                    "birth_date","cc_valid_until"->runCatching {
                        LocalDate.parse(raw,DateTimeFormatter.ofPattern("dd/MM/uuuu")
                            .withResolverStyle(ResolverStyle.STRICT))
                    }.isSuccess
                    "gender"->raw in listOf("Feminino","Masculino","Outro")
                    "height_cm"->raw.replace(',','.').toDoubleOrNull()?.let {
                        it.isFinite() && it in 40.0..250.0
                    }==true
                    else->raw.length <= 200
                }
                if(!accepted){
                    input.error="Verifica este valor antes de guardar."
                    return@setOnClickListener
                }
                editor.putString(field.key,raw)
            }
            if(!editor.commit()){
                showError("Não foi possível guardar os dados do perfil.")
                return@setOnClickListener
            }
            setResult(RESULT_OK)
            dialog.dismiss()
            Toast.makeText(this,"Dados confirmados e guardados.",Toast.LENGTH_LONG).show()
            // The parent refreshes its profile form when this screen closes.
        }
    }

'''
change(anchor,methods+anchor,"OCR and manual review")

path.write_text(s,encoding="utf-8")
print("v1.9.10: OCR stored front/back CC, explicit editable per-field approval, no automatic overwrite.")
