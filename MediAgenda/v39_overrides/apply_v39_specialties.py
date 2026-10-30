from pathlib import Path
base=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app")

def replace(path,old,new,label):
    s=path.read_text(encoding="utf-8")
    if s.count(old)!=1:raise RuntimeError("Specialties missing anchor: "+label)
    path.write_text(s.replace(old,new,1),encoding="utf-8")

store=base/"work/WorkMedicineStore.kt"
replace(store,'''    val rawOcr:String,
    val createdAt:Long
)''','''    val rawOcr:String,
    val createdAt:Long,
    val examData:Map<String,String> = emptyMap()
)''',"model")
replace(store,'''.put("createdAt",a.createdAt)''','''.put("createdAt",a.createdAt)
        .put("examData",JSONObject().apply{
            a.examData.forEach{(key,value)->put(key,value)}
        })''',"encode")
replace(store,'''        o.optLong("createdAt")
    )''','''        o.optLong("createdAt"),
        o.optJSONObject("examData")?.let{values->
            buildMap<String,String>{
                val keys=values.keys()
                while(keys.hasNext()){
                    val key=keys.next()
                    if(key.length<=80)put(key,values.optString(key).take(1200))
                }
            }
        } ?: emptyMap()
    )''',"decode")

main=base/"WorkMedicineActivity.kt"
replace(main,'''    private var activeFilter="all"
    private var cameraTmp:File?=null''','''    private var activeFilter="all"
    private var specialtyFilter:String?=null
    private var cameraTmp:File?=null''',"state")
replace(main,'''head.addView(text("🏥 Medicina do Trabalho",23f,true))''',
'''head.addView(text("🏥 Saúde Ocupacional",23f,true))''',"heading")
replace(main,'''        val actions=card("Adicionar documentos",''',
'''        val exams=card("Exames complementares",
            "Cada especialidade tem histórico e campos próprios.")
        exams.addView(button("🧪 Análises Clínicas"){
            startActivity(Intent(this,ClinicalLabsActivity::class.java)
                .putExtra(ClinicalLabsActivity.EXTRA_PROFILE_ID,patientId))
        })
        exams.addView(button("❤️ ECG · Eletrocardiograma"){openSpecialty("ecg")})
        exams.addView(button("👂 Audiometria · Audiograma"){openSpecialty("audio")})
        exams.addView(button("👁 Avaliação Visual"){openSpecialty("vision")})

        val actions=card("Adicionar documentos",''',"menu")
replace(main,'''        val filter=card("Consultar documentos","Seleciona uma secção, como no menu MCG.")''',
'''        if(specialtyFilter!=null){
            val kind=specialtyFilter!!
            val title=when(kind){
                "ecg"->"❤️ ECG · Eletrocardiograma"
                "audio"->"👂 Audiometria"
                else->"👁 Avaliação Visual"
            }
            val specialized=card(title,
                "Resultados e relatórios originais por data.")
            specialized.addView(button("＋ Novo registo de exame"){
                val name=when(kind){
                    "ecg"->"ECG"
                    "audio"->"Audiometria"
                    else->"Avaliação Visual"
                }
                val record=store.createManual(name,WorkplaceClassifier.COMPLETED)
                val updated=record.copy(examType=when(kind){
                    "ecg"->"Eletrocardiograma"
                    "audio"->"Audiometria"
                    else->"Avaliação Visual"
                },aptitude="Não aplicável")
                store.update(updated)
                editSpecialty(updated,kind)
            })
            specialized.addView(button("📄 Anexar PDF / imagem do exame"){
                chosenCategory=WorkplaceClassifier.COMPLETED
                if(!working)documentPicker.launch(arrayOf("application/pdf","image/*"))
            })
            specialized.addView(button("‹ Todos os exames"){
                specialtyFilter=null
                activeFilter="all"
                redraw()
            })
        }
        val filter=card("Consultar documentos","Seleciona uma secção, como no menu MCG.")''',"specialized controls")
replace(main,'''                    activeFilter=key;redraw()''','''                    activeFilter=key;specialtyFilter=null;redraw()''',"filter reset")
replace(main,'''        val selected=items.filter{activeFilter=="all"||it.category==activeFilter}''',
'''        val selected=items.filter{
            if(specialtyFilter!=null)identifySpecialty(it)==specialtyFilter
            else activeFilter=="all"||it.category==activeFilter
        }''',"specialty filter")
replace(main,'''            box.addView(button("📋 Abrir ficha / editar dados"){editor(record)})''',
'''            box.addView(button("📋 Abrir ficha / editar dados"){editor(record)})
            val specialty=specialtyFilter ?: identifySpecialty(record)
            if(specialty!=null){
                val count=record.examData.count{it.value.isNotBlank()}
                box.addView(button("📈 Resultados por exame ($count campos)"){
                    editSpecialty(record,specialty)
                })
            }''',"results")
replace(main,'''        final.addView(button("🧪 Abrir Análises Clínicas"){
            startActivity(Intent(this,ClinicalLabsActivity::class.java)
                .putExtra(ClinicalLabsActivity.EXTRA_PROFILE_ID,patientId))
        })''',
'''        final.addView(text(
            "As análises clínicas continuam numa biblioteca única, "+
            "sem duplicar relatórios. ECG, audiometria e avaliação visual "+
            "têm registos próprios nesta área.",
            13f,false,muted))''',"footer")

specialty='''    private fun openSpecialty(type:String){
        specialtyFilter=type
        activeFilter="all"
        redraw()
    }
    private fun identifySpecialty(item:WorkDocument):String?{
        val n=(item.examType+" "+item.name+" "+item.originalName)
            .lowercase(Locale.ROOT)
        return when{
            n.contains("electrocardio")||n.contains("eletrocardio")||
                n.contains("ecg")->"ecg"
            n.contains("audiometr")||n.contains("audiogram")->"audio"
            listOf("visão","visao","visual","oftalmol","optometr")
                .any{n.contains(it)}->"vision"
            else->null
        }
    }
    private fun editSpecialty(record:WorkDocument,type:String){
        val parameters=when(type){
            "ecg"->listOf(
                "heart_rate" to "Frequência cardíaca (bpm)",
                "rhythm" to "Ritmo (conforme relatório)",
                "pr" to "Intervalo PR (ms)",
                "qrs" to "Duração QRS (ms)",
                "qt" to "Intervalo QT (ms)",
                "qtc" to "Intervalo QTc (ms)",
                "axis" to "Eixo cardíaco (conforme relatório)",
                "interpretation" to "Conclusão médica do ECG"
            )
            "audio"->buildList{
                add("method" to "Método de audiometria")
                for((side,title) in listOf("right" to "Direito","left" to "Esquerdo")){
                    for(hz in listOf(125,250,500,1000,2000,3000,4000,6000,8000)){
                        add((side+"_"+hz) to ("Ouvido "+title+" · "+hz+" Hz (dB HL)"))
                    }
                }
                add("interpretation" to "Conclusão do audiograma")
            }
            else->listOf(
                "od_without" to "Acuidade OD sem correção",
                "oe_without" to "Acuidade OE sem correção",
                "od_with" to "Acuidade OD com correção",
                "oe_with" to "Acuidade OE com correção",
                "both" to "Acuidade visual binocular",
                "color_method" to "Visão cromática · teste efetuado",
                "color_result" to "Visão cromática · resultado do relatório",
                "binocular" to "Visão binocular · estereopsia / alinhamento",
                "peripheral" to "Visão periférica · campo visual",
                "glasses" to "Óculos / lentes utilizados",
                "interpretation" to "Conclusão do exame visual"
            )
        }
        val dialogTitle=when(type){
            "ecg"->"ECG · Resultados"
            "audio"->"Audiometria · Resultados"
            else->"Avaliação Visual · Resultados"
        }
        val form=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(16),dp(8),dp(16),dp(12))
        }
        form.addView(text(
            "Regista apenas valores que constem do exame. "+
            "Não é um teste médico realizado pelo telemóvel nem calcula diagnósticos.",
            13f,false,muted))
        val date=field("Data do exame (DD/MM/AAAA)",
            record.date.takeIf{it.isNotBlank()}?.let(::showDate)?:"")
        val clinic=field("Clínica / unidade",record.clinic)
        form.addView(date);form.addView(clinic)
        val controls=linkedMapOf<String,EditText>()
        parameters.forEach{(key,label)->
            val input=field(label,record.examData[key].orEmpty())
            if(key=="interpretation"){
                input.isSingleLine=false;input.minLines=2;input.maxLines=5
            }
            controls[key]=input
            form.addView(input)
        }
        if(record.filename.isNotBlank()){
            form.addView(button("📄 Abrir exame original"){openDocument(record)})
            form.addView(button("🔎 OCR do documento"){scan(record)})
        }
        val dialog=MaterialAlertDialogBuilder(this).setTitle(dialogTitle)
            .setView(ScrollView(this).apply{addView(form)})
            .setPositiveButton("Guardar",null)
            .setNegativeButton("Cancelar",null).show()
        dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE)
            .setOnClickListener{
                val whenDate=validDate(date.text.toString())
                if(whenDate==null){
                    date.error="Data inválida"
                    return@setOnClickListener
                }
                val values=record.examData.toMutableMap()
                controls.forEach{(key,input)->
                    values[key]=input.text.toString().trim().take(1200)
                }
                val modified=record.copy(date=whenDate,
                    clinic=clinic.text.toString().trim(),examData=values)
                runCatching{store.update(modified)}
                    .onSuccess{
                        dialog.dismiss();redraw()
                        Toast.makeText(this,"Resultados guardados.",Toast.LENGTH_SHORT).show()
                    }.onFailure{message(it.message?:"Erro ao guardar.")}
            }
    }

'''
replace(main,'''    private fun showDate(d:String)=runCatching{''',specialty+'''    private fun showDate(d:String)=runCatching{''',"methods")
replace(main,'''                    store.add(uri,title,chosenCategory?:WorkplaceClassifier.OTHER)
                }.onSuccess{
                    dialog.dismiss();temp?.delete();redraw()''',
'''                    val item=store.add(uri,title,chosenCategory?:WorkplaceClassifier.OTHER)
                    val examName=when(specialtyFilter){
                        "ecg"->"Eletrocardiograma"
                        "audio"->"Audiometria"
                        "vision"->"Avaliação Visual"
                        else->null
                    }
                    if(examName!=null)store.update(
                        item.copy(examType=examName,aptitude="Não aplicável")
                    )
                }.onSuccess{
                    dialog.dismiss();temp?.delete();redraw()''',"import specialty")
print("Added nested specialist areas: shared labs, ECG, audiometry and vision, all with dated structured results and original documents.")
