from pathlib import Path

file=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app/WorkMedicineActivity.kt")
s=file.read_text(encoding="utf-8")
old='''            box.addView(button("📋 Abrir ficha / editar dados"){editor(record)})
            val specialty=specialtyFilter ?: identifySpecialty(record)'''
new='''            box.addView(button("📋 Abrir ficha / editar dados"){editor(record)})
            box.addView(button("🗂 Classificar exame"){
                classifySpecialty(record)
            })
            val specialty=specialtyFilter ?: identifySpecialty(record)'''
assert s.count(old)==1
s=s.replace(old,new,1)

anchor='''    private fun editSpecialty(record:WorkDocument,type:String){'''
assert s.count(anchor)==1
newMethod='''    private fun classifySpecialty(record:WorkDocument){
        val choices=arrayOf("❤️ ECG / Eletrocardiograma",
            "👂 Audiometria / Audiograma",
            "👁 Avaliação Visual",
            "📂 Outro exame / documento")
        MaterialAlertDialogBuilder(this)
            .setTitle("Classificar exame")
            .setMessage("O documento original não será alterado. "+
                "Escolhe o tipo depois de verificar o conteúdo.")
            .setItems(choices){_,chosen->
                val examType=when(chosen){
                    0->"Eletrocardiograma"
                    1->"Audiometria"
                    2->"Avaliação Visual"
                    else->"Exame complementar / documento"
                }
                val updated=record.copy(
                    examType=examType,
                    aptitude=if(chosen<3)"Não aplicável" else record.aptitude
                )
                runCatching{store.update(updated)}
                    .onSuccess{
                        redraw()
                        Toast.makeText(this,"Exame classificado.",
                            Toast.LENGTH_SHORT).show()
                    }.onFailure{
                        message(it.message?:"Não foi possível classificar.")
                    }
            }.setNegativeButton("Cancelar",null).show()
    }

'''
s=s.replace(anchor,newMethod+anchor,1)
file.write_text(s,encoding="utf-8")

main=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app/MainActivity.kt")
s=main.read_text(encoding="utf-8")
old='''DashboardModule("🏥", "Medicina do Trabalho", "Aptidão, exames e histórico MCG")'''
new='''DashboardModule("🏥", "Saúde Ocupacional", "Medicina do Trabalho e exames")'''
assert s.count(old)==1
main.write_text(s.replace(old,new,1),encoding="utf-8")
print("MCG documents can be classified by user as ECG/audiometry/visual after ZIP import; home label Saúde Ocupacional.")
