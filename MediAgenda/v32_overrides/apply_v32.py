from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1")
activity=root/"app/src/main/java/com/mediagenda/app/ProfileMediaActivity.kt"
s=activity.read_text(encoding="utf-8")
def replace(old,new,label):
    global s
    if old not in s:
        raise RuntimeError("v1.9.13: missing anchor: "+label)
    s=s.replace(old,new,1)

replace('''            column.addView(outline(if(photo==null)"📷 Adicionar fotografia"
                else "📷 Substituir fotografia"){chooseImage(key)})''',
'''            column.addView(outline(if(photo==null)"📷 Adicionar fotografia"
                else "📷 Substituir fotografia"){chooseImage(key)})
            if(photo!=null && (key=="cc_front" || key=="cc_back")) {
                column.addView(outline(
                    if(key=="cc_front")"🔎 OCR — Ler apenas a frente"
                    else "🔎 OCR — Ler apenas o verso"){
                    scanSavedCitizenCard(key)
                })
            }''',"per-card OCR buttons")

replace('''        if(media.exists("cc_front") || media.exists("cc_back")){
            body.addView(outline("🔎 Ler CC com OCR e preencher o perfil") {
                scanSavedCitizenCard()
            },LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT).apply{bottomMargin=dp(12)})
        }
''','',"remove ambiguous combined OCR")

replace('''                    .setPositiveButton("Ler e rever") { _,_ -> scanSavedCitizenCard() }''',
'''                    .setPositiveButton("Ler e rever") { _,_ -> scanSavedCitizenCard(target) }''',
"scan saved side after photo")

start=s.index("    private fun scanSavedCitizenCard(){")
end=s.index("    private fun showOcrReview(",start)
newFunc='''    private fun scanSavedCitizenCard(side:String){
        if(ocrRunning)return
        if(side!="cc_front" && side!="cc_back"){
            showError("Seleciona a frente ou o verso do Cartão de Cidadão.")
            return
        }
        val bitmap=media.photo(side,2400)
        if(bitmap==null){
            showError("Adiciona primeiro uma fotografia legível deste lado do CC.")
            return
        }
        ocrRunning=true
        val caption=if(side=="cc_front")"Frente do CC" else "Verso do CC"
        val wait=MaterialAlertDialogBuilder(this)
            .setTitle("A ler "+caption)
            .setMessage("O OCR é feito neste telemóvel. Nenhum campo será gravado sem confirmação.")
            .setView(ProgressBar(this).apply{
                isIndeterminate=true
                setPadding(dp(20),dp(12),dp(20),dp(12))
            }).setCancelable(false).show()
        val recognizer=TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)
        recognizer.process(InputImage.fromBitmap(bitmap,0))
            .addOnSuccessListener{response->
                ocrRunning=false
                recognizer.close()
                wait.dismiss()
                val front=if(side=="cc_front")response.text else ""
                val back=if(side=="cc_back")response.text else ""
                val proposed=ProfileCitizenCardOcr.propose(front,back)
                if(proposed.isNotEmpty())showOcrReview(proposed)
                else if(response.text.isNotBlank()) {
                    val dialog=TextView(this).apply{
                        text=response.text
                        setTextIsSelectable(true)
                        setTextColor(if(dark)Color.WHITE else Color.rgb(18,35,48))
                        setPadding(dp(18),dp(14),dp(18),dp(14))
                    }
                    MaterialAlertDialogBuilder(this)
                        .setTitle("Texto lido, sem dados identificados")
                        .setMessage("O OCR conseguiu ler texto, mas não reconheceu campos com segurança. Podes consultar o texto e preencher os campos manualmente.")
                        .setPositiveButton("Ver texto"){_,_->
                            MaterialAlertDialogBuilder(this)
                                .setTitle("Leitura OCR — "+caption)
                                .setView(ScrollView(this).apply{addView(dialog)})
                                .setPositiveButton("Fechar",null).show()
                        }.setNegativeButton("Fechar",null).show()
                }else showError("Não consegui reconhecer texto neste lado. Experimenta outra fotografia sem reflexos.")
            }
            .addOnFailureListener{
                ocrRunning=false
                recognizer.close()
                wait.dismiss()
                showError("Não foi possível ler "+caption+". Experimenta uma fotografia diferente.")
            }
    }

'''
s=s[:start]+newFunc+s[end:]
# Make success text explicit and keep existing values opt-in.
replace('''            Toast.makeText(this,"Dados confirmados e guardados.",Toast.LENGTH_LONG).show()
            // The parent refreshes its profile form when this screen closes.''',
'''            Toast.makeText(this,
                "Guardados "+selected.size+" campo(s) no perfil de "+profileName+".",
                Toast.LENGTH_LONG).show()
            // MainActivity must reload the persisted fields instead of applying
            // an old unsaved form draft over the newly scanned values.''',
"successful save feedback")

# When the OCR dialog closes, do not finish the image gallery; result is
# consumed by MainActivity as soon as the user goes back.
activity.write_text(s,encoding="utf-8")

main=root/"app/src/main/java/com/mediagenda/app/MainActivity.kt"
s=main.read_text(encoding="utf-8")
old='''        if (profiles.all().any { it.id == activeProfileId }) showProfileDialog(false)'''
new='''        if (profiles.all().any { it.id == activeProfileId }) {
            if (it.resultCode == RESULT_OK) {
                // Critical fix: the form that launched the photo screen still
                // held blank/old draft values. OCR had committed new data to
                // preferences, but the stale draft masked/overwrote them.
                profileDraft = null
                extendedProfileDraft = null
            }
            showProfileDialog(false)
        }'''
assert old in s, "Stale profile draft result callback not found"
main.write_text(s.replace(old,new,1),encoding="utf-8")

pin=root/"app/src/main/java/com/mediagenda/app/AppPinActivity.kt"
s=pin.read_text(encoding="utf-8")
old='''        isSingleLine=true;setTextColor(fg);setHintTextColor(secondary)
        backgroundTintList=ColorStateList.valueOf(teal)'''
new='''        isSingleLine=true;setTextColor(fg);setHintTextColor(secondary)
        // Unlike Android's standard password transformation, this always
        // shows **** and never exposes the last typed digit briefly.
        transformationMethod=object:android.text.method.ReplacementTransformationMethod(){
            override fun getOriginal():CharArray="0123456789".toCharArray()
            override fun getReplacement():CharArray="**********".toCharArray()
        }
        backgroundTintList=ColorStateList.valueOf(teal)'''
assert old in s, "PIN transformation anchor not found"
pin.write_text(s.replace(old,new,1),encoding="utf-8")

gradle=root/"app/build.gradle.kts"
s=gradle.read_text(encoding="utf-8")
assert 'applicationId = "com.mediagenda.app.stable"' in s
assert 'versionCode = 22' in s and 'versionName = "1.9.12"' in s
gradle.write_text(s.replace('versionCode = 22','versionCode = 23',1)
    .replace('versionName = "1.9.12"','versionName = "1.9.13"',1),encoding="utf-8")

print("v1.9.13: separate front/back CC OCR, fix stale profile draft hiding OCR saves, mask PIN digits as ****.")
