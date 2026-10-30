from pathlib import Path

path=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app/ProfileMediaActivity.kt")
s=path.read_text(encoding="utf-8")
start=s.index("    private fun scanSavedCitizenCard(side:String){")
end=s.index("    private fun showOcrReview(",start)
replacement='''    private fun scanSavedCitizenCard(side:String){
        if(ocrRunning)return
        if(side!="cc_front"&&side!="cc_back")return
        val bitmap=media.photo(side,2400)?:run{
            showError("Adiciona primeiro a fotografia deste lado do CC.")
            return
        }
        ocrRunning=true
        val caption=if(side=="cc_front")"Frente do CC" else "Verso do CC"
        val progress=MaterialAlertDialogBuilder(this)
            .setTitle("OCR — "+caption)
            .setMessage("A reconhecer texto e ampliar a zona dos dados, sem enviar documentos para a Internet.")
            .setView(ProgressBar(this).apply{
                isIndeterminate=true
                setPadding(dp(18),dp(10),dp(18),dp(10))
            }).setCancelable(false).show()
        val reader=TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)
        fun complete(full:String,cropped:String){
            ocrRunning=false
            reader.close()
            if(!isFinishing)progress.dismiss()
            if(isFinishing)return
            val base=if(side=="cc_front")ProfileCitizenCardOcr.propose(full,"")
                else ProfileCitizenCardOcr.propose("",full)
            val secondary=if(side=="cc_front")ProfileCitizenCardOcr.propose(cropped,"")
                else ProfileCitizenCardOcr.propose("","FILIACAO\\n"+cropped+
                    "\\nIDENTIFICACAO FISCAL")
            val combined=linkedMapOf<String,ProfileCitizenCardOcr.Proposed>()
            base.forEach{combined[it.key]=it}
            secondary.forEach{field->
                val original=combined[field.key]
                if(original==null || (field.key in setOf("father_name","mother_name","cc_number") &&
                    field.value.length>original.value.length+3)){
                    combined[field.key]=field
                }
            }
            // Always offer the missing fields for explicit manual editing,
            // rather than silently skipping them or guessing their contents.
            if(side=="cc_back"){
                if(!combined.containsKey("father_name"))combined["father_name"]=
                    ProfileCitizenCardOcr.Proposed("father_name","Nome do pai","")
                if(!combined.containsKey("mother_name"))combined["mother_name"]=
                    ProfileCitizenCardOcr.Proposed("mother_name","Nome da mãe","")
            }else if(!combined.containsKey("cc_number")){
                combined["cc_number"]=ProfileCitizenCardOcr.Proposed(
                    "cc_number","Número do Cartão de Cidadão","")
            }
            val raw=buildString{
                append("LEITURA COMPLETA — ").append(caption)
                append("\\n").append(full)
                append("\\n\\nZONA AMPLIADA\\n").append(cropped)
            }
            showOcrReview(combined.values.toList(),raw)
        }
        reader.process(InputImage.fromBitmap(bitmap,0))
            .addOnSuccessListener{fullResult->
                val roi=runCatching {
                    val x=if(side=="cc_back")0.12f else 0.26f
                    val y=if(side=="cc_back")0.13f else 0.48f
                    val width=if(side=="cc_back")0.82f else 0.53f
                    val height=if(side=="cc_back")0.31f else 0.32f
                    val left=(bitmap.width*x).toInt()
                    val top=(bitmap.height*y).toInt()
                    val w=(bitmap.width*width).toInt().coerceAtMost(bitmap.width-left)
                    val h=(bitmap.height*height).toInt().coerceAtMost(bitmap.height-top)
                    val cropped=android.graphics.Bitmap.createBitmap(bitmap,left,top,w,h)
                    val newWidth=maxOf(cropped.width,1900)
                    if(newWidth==cropped.width)cropped else{
                        val result=android.graphics.Bitmap.createScaledBitmap(cropped,
                            newWidth,(cropped.height*newWidth.toFloat()/cropped.width)
                                .toInt().coerceAtLeast(1),true)
                        cropped.recycle()
                        result
                    }
                }.getOrNull()
                if(roi==null){
                    complete(fullResult.text,"")
                }else reader.process(InputImage.fromBitmap(roi,0))
                    .addOnSuccessListener{zoomed->
                        roi.recycle()
                        complete(fullResult.text,zoomed.text)
                    }
                    .addOnFailureListener{
                        roi.recycle()
                        complete(fullResult.text,"")
                    }
            }.addOnFailureListener{
                complete("","")
            }
    }

'''
s=s[:start]+replacement+s[end:]
s=s.replace('''    private fun showOcrReview(proposals:List<ProfileCitizenCardOcr.Proposed>){''',
'''    private fun showOcrReview(
        proposals:List<ProfileCitizenCardOcr.Proposed>,rawOcr:String
    ){''',1)
old='''        form.addView(label(
            "Confirma os valores e seleciona os campos que queres guardar. "+
            "Os campos já preenchidos não ficam selecionados automaticamente.",
            13f,false,if(dark)Color.rgb(228,240,242)else Color.rgb(50,74,84)))'''
new='''        form.addView(label(
            "Confirma os valores. Campos em branco podem ser preenchidos "+
            "manualmente. Os valores existentes não são substituídos sem seleção.",
            13f,false,if(dark)Color.rgb(228,240,242)else Color.rgb(50,74,84)))
        form.addView(outline("🔎 Ver texto completo reconhecido"){
            val display=TextView(this).apply{
                text=rawOcr
                setTextIsSelectable(true)
                setTextColor(if(dark)Color.WHITE else Color.rgb(18,35,48))
                setPadding(dp(18),dp(16),dp(18),dp(16))
            }
            MaterialAlertDialogBuilder(this)
                .setTitle("OCR local — texto reconhecido")
                .setView(ScrollView(this).apply{addView(display)})
                .setPositiveButton("Fechar",null).show()
        })'''
assert old in s
s=s.replace(old,new,1)
s=s.replace('''                isChecked=current.isBlank()''',
'''                isChecked=current.isBlank() && item.value.isNotBlank()''',1)
path.write_text(s,encoding="utf-8")
print("Per-side CC OCR now scans whole card plus enlarged field region; parent names and CC number can be reviewed and manually corrected.")
