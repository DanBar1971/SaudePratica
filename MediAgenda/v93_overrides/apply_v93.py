"""SaúdePrática v1.9.75: simplified clinical document import and classification."""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
def change(path,old,new,label):
    s=path.read_text(encoding="utf-8")
    if s.count(old)!=1:
        raise RuntimeError(f"v93 {label}: expected 1 match, got {s.count(old)}")
    path.write_text(s.replace(old,new,1),encoding="utf-8")

p=base/"WorkMedicineActivity.kt"
change(p,'''        val actions=card("Adicionar documentos",
            "PDFs, fotografias ou exportação ZIP da plataforma MCG.")
        actions.addView(button("📦 Importar ZIP MCG"){
            if(!working)zipPicker.launch(arrayOf("application/zip",
                "application/x-zip-compressed","application/octet-stream"))
        })
        actions.addView(button("📄 Anexar PDF ou imagem"){
            if(!working)chooseCategory {
                documentPicker.launch(arrayOf("application/pdf","image/*"))
            }
        })
        actions.addView(button("📷 Digitalizar com a câmara"){
            if(!working)chooseCategory {
                if(ContextCompat.checkSelfPermission(this,Manifest.permission.CAMERA)
                    ==PackageManager.PERMISSION_GRANTED)takePhoto()
                else permission.launch(Manifest.permission.CAMERA)
            }
        })''','''        val actions=card("Adicionar documentos",
            "Anexa um PDF ou imagem, ou fotografa um documento. "+
            "Depois indica o nome, a secção e o tipo de exame ou análise.")
        actions.addView(button("📄 Anexar PDF ou imagem"){
            if(!working){
                chosenCategory=null
                documentPicker.launch(arrayOf("application/pdf","image/*"))
            }
        })
        actions.addView(button("📷 Digitalizar com a câmara"){
            if(!working){
                chosenCategory=null
                if(ContextCompat.checkSelfPermission(this,Manifest.permission.CAMERA)
                    ==PackageManager.PERMISSION_GRANTED)takePhoto()
                else permission.launch(Manifest.permission.CAMERA)
            }
        })''',"remove MCG button and defer classification")

change(p,'''val filter=card("Consultar documentos","Seleciona uma secção, como no menu MCG.")''',
'''val filter=card("Consultar documentos","Seleciona uma secção dos documentos arquivados.")''',"remove old portal copy")
change(p,'''                "Importa o ZIP MCG, anexa um documento ou adiciona um registo.")''',
'''                "Anexa um PDF, fotografa um documento ou cria um registo.")''',"empty state")
change(p,'''        final.addView(text("Documentos privados por utilizador, guardados "+
            "neste telemóvel. A importação ZIP ignora ficheiros repetidos. "+''',
'''        final.addView(text("Documentos privados por utilizador, guardados "+
            "neste telemóvel. PDFs e fotografias são classificados no momento de anexar. "+''',"privacy copy")
change(p,'''    private fun promptImport(uri:Uri,temp:File?){
        val name=field("Nome do documento","Medicina do Trabalho")
        val box=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(18),dp(10),dp(18),dp(8))
            addView(text("Os ficheiros ficam privados no perfil de "+
                patientName+". Podes corrigir a classificação após importar.",
                13f,false,muted))
            addView(name)
        }
        val dialog=MaterialAlertDialogBuilder(this)
            .setTitle("Adicionar documento")
            .setView(box)
            .setNegativeButton("Cancelar"){_,_->temp?.delete()}
            .setOnCancelListener{temp?.delete()}
            .setPositiveButton("Guardar",null).show()''',
'''    private fun promptImport(uri:Uri,temp:File?){
        val name=field("Nome do documento","")
        val groups=WorkplaceClassifier.types
        val groupLabels=groups.map(::caption)
        val groupSpinner=Spinner(this).apply{
            adapter=ArrayAdapter(this@WorkMedicineActivity,
                android.R.layout.simple_spinner_dropdown_item,groupLabels)
            val defaultGroup=when {
                specialtyFilter!=null->WorkplaceClassifier.COMPLETED
                chosenCategory in groups->chosenCategory!!
                else->WorkplaceClassifier.OTHER
            }
            setSelection(groups.indexOf(defaultGroup).coerceAtLeast(0))
            contentDescription="Secção para arquivar o documento"
        }
        val kinds=listOf(
            "Outro documento","Análises clínicas","Análises ao sangue",
            "Análises à urina","Hemograma","Bioquímica",
            "Eletrocardiograma","Audiometria","Avaliação Visual",
            "Ecografia","Radiografia","TAC / Tomografia",
            "Ressonância magnética","Endoscopia","Espirometria",
            "Ficha de aptidão","Relatório clínico","Receita médica",
            "Credencial / convocatória","Outro exame"
        )
        val kindSpinner=Spinner(this).apply{
            adapter=ArrayAdapter(this@WorkMedicineActivity,
                android.R.layout.simple_spinner_dropdown_item,kinds)
            val selected=when(specialtyFilter){
                "ecg"->"Eletrocardiograma"
                "audio"->"Audiometria"
                "vision"->"Avaliação Visual"
                else->"Outro documento"
            }
            setSelection(kinds.indexOf(selected).coerceAtLeast(0))
            contentDescription="Tipo de exame, análise ou documento"
        }
        val box=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(18),dp(8),dp(18),dp(8))
            addView(text("O ficheiro será guardado apenas no perfil de "+
                patientName+". Escolhe a classificação antes de guardar.",
                13f,false,muted))
            addView(text("Nome do documento",14f,true,ink))
            addView(name)
            addView(text("Secção",14f,true,ink))
            addView(groupSpinner,LinearLayout.LayoutParams(-1,dp(50)))
            addView(text("Tipo de exame, análise ou documento",14f,true,ink))
            addView(kindSpinner,LinearLayout.LayoutParams(-1,dp(50)))
        }
        val dialog=MaterialAlertDialogBuilder(this)
            .setTitle("Classificar e guardar documento")
            .setView(ScrollView(this).apply{addView(box)})
            .setNegativeButton("Cancelar"){_,_->temp?.delete()}
            .setOnCancelListener{temp?.delete()}
            .setPositiveButton("Guardar",null).show()''',"classify in import dialog")
change(p,'''                    val item=store.add(uri,title,chosenCategory?:WorkplaceClassifier.OTHER)
                    val examName=when(specialtyFilter){
                        "ecg"->"Eletrocardiograma"
                        "audio"->"Audiometria"
                        "vision"->"Avaliação Visual"
                        else->null
                    }
                    if(examName!=null)store.update(
                        item.copy(examType=examName,aptitude="Não aplicável")
                    )''',
'''                    val group=groups[groupSpinner.selectedItemPosition]
                    val kind=kinds[kindSpinner.selectedItemPosition]
                    val item=store.add(uri,title,group)
                    store.update(item.copy(examType=kind,
                        aptitude=if(kind=="Ficha de aptidão")
                            "Por confirmar" else "Não aplicável"))''',"persist category and subtype")

help=base/"SupportHelpActivity.kt"
change(help,'''                arrayOf("Guarda documentos e exames no perfil certo. Podes fotografar ou escolher ficheiros já existentes.",
                    "Save documents and tests to the correct profile. Take a photo or choose an existing file.",
                    "Enregistrez les documents dans le bon profil. Prenez une photo ou choisissez un fichier.",
                    "Speichern Sie Dokumente im richtigen Profil. Fotografieren oder vorhandene Datei auswählen.",
                    "Guarda documentos en el perfil adecuado. Haz una foto o selecciona un archivo.")),''',
'''                arrayOf("Em Situação Clínica, anexa um PDF ou imagem ou digitaliza com a câmara. No mesmo formulário escolhe o nome, a secção e o tipo de exame, análise ou documento. O ZIP MCG deixou de estar disponível neste módulo. Os PDFs também são arquivados em Documentos Digitais, no perfil certo.",
                    "In Clinical History, attach a PDF or image or take a photo. Enter its name, archive section and exam/lab-test/document type together. MCG ZIP import is no longer shown here. PDFs also appear in Digital Documents for the same profile.",
                    "Dans Situation clinique, ajoutez un PDF ou une photo. Saisissez le nom, la section et le type d'examen, d'analyse ou de document dans le même formulaire. L'import ZIP MCG n'est plus disponible ici. Les PDF sont également archivés dans Documents numériques du même profil.",
                    "Unter Klinische Akte ein PDF oder Foto hinzufügen und Name, Bereich sowie Untersuchungs- oder Dokumenttyp auswählen. MCG-ZIP-Import wird hier nicht mehr angezeigt. PDF-Dateien erscheinen auch in Digitale Dokumente des gleichen Profils.",
                    "En Situación clínica, adjunta un PDF o imagen o haz una foto. Selecciona nombre, sección y tipo de examen, análisis o documento en el mismo formulario. La importación ZIP MCG ya no aparece aquí. Los PDF también se guardan en Documentos digitales del mismo perfil.")),''',"update illustrated guide languages")

gradle=root/"app/build.gradle.kts"
change(gradle,"versionCode = 84","versionCode = 85","version code")
change(gradle,'versionName = "1.9.74"','versionName = "1.9.75"',"version name")
print("SaúdePrática 1.9.75: clinical attachments name, section and type together")
