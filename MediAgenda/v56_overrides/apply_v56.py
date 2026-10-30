from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1')
main=root/'app/src/main/java/com/mediagenda/app/MainActivity.kt'
gradle=root/'app/build.gradle.kts'
def patch(f,old,new,label):
    text=f.read_text(encoding='utf-8')
    n=text.count(old)
    if n!=1: raise RuntimeError('SaúdePrática v1.9.37 '+label+': expected one, found '+str(n))
    f.write_text(text.replace(old,new,1),encoding='utf-8')

patch(main,
    '            PhotoMode.MEDICATION_BOX -> recognizeMedicationBox(uri)',
    '            PhotoMode.MEDICATION_BOX -> askAboutCapturedMedicationPhoto(uri)',
    'camera callback')

patch(main,
    '''                "📦 Fotografar caixa de medicamento (ML Kit)",''',
    '''                "📷 Fotografar caixa (escolher análise depois)",''',
    'clear add choice')

patch(main,
    '''    private fun recognizeMedicationBox(uri: Uri) {''',
    '''    /** The photo is in the app's private medication_photos folder. The file
     * chooser therefore cannot display it: always offer the next action here.
     * The same capture is used for both recognition and normal attachment.
     */
    private fun localMedicationBoxReference(uri:Uri):String {
        val folder=File(filesDir,"medication_photos").canonicalFile
        val filename=uri.lastPathSegment.orEmpty().substringAfterLast('/')
        val candidate=File(folder,filename).canonicalFile
        return if(uri.authority==BuildConfig.APPLICATION_ID+".fileprovider" &&
            candidate.parentFile==folder && candidate.isFile)
            candidate.absolutePath else uri.toString()
    }

    private fun discardUnlinkedCameraPhoto(uri:Uri){
        if(uri.authority!=BuildConfig.APPLICATION_ID+".fileprovider")return
        val name=uri.lastPathSegment.orEmpty().substringAfterLast('/')
        if(!name.startsWith("medicamento_")||!name.endsWith(".jpg"))return
        val folder=File(filesDir,"medication_photos").canonicalFile
        val photo=File(folder,name).canonicalFile
        if(photo.parentFile==folder) photo.delete()
    }

    private fun askAboutCapturedMedicationPhoto(uri:Uri) {
        // Immediately after TakePicture, before any picker or OCR request.
        // Users can see what they photographed and choose one safe action.
        val box=LinearLayout(this).apply {
            orientation=LinearLayout.VERTICAL
            setPadding(dp(18),dp(8),dp(18),dp(10))
        }
        val preview=MedicationPhotoLoader.load(this,listOf(localMedicationBoxReference(uri)),900)
        if(preview!=null){
            box.addView(android.widget.ImageView(this).apply{
                setImageBitmap(preview)
                scaleType=android.widget.ImageView.ScaleType.FIT_CENTER
                adjustViewBounds=true
                layoutParams=LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,dp(175))
                contentDescription="Fotografia acabada de tirar à caixa"
            })
        }
        box.addView(noteBox("Fotografia captada",
            "Escolhe o que queres fazer com ESTA fotografia. " +
            "Não precisas de a procurar na galeria. " +
            "O reconhecimento funciona no telemóvel e os dados só " +
            "são guardados depois de confirmares."))
        lateinit var dialog:androidx.appcompat.app.AlertDialog
        box.addView(secondaryButton("✨ Analisar esta foto com ML Kit"){
            dialog.dismiss()
            recognizeMedicationBox(uri)
        })
        box.addView(secondaryButton("📷 Guardar fotografia sem analisar"){
            dialog.dismiss()
            saveCapturedMedicationPhotoWithoutAi(uri)
        })
        box.addView(secondaryButton("🔁 Tirar outra fotografia"){
            dialog.dismiss()
            discardUnlinkedCameraPhoto(uri)
            captureMedicationBoxPhoto()
        })
        dialog=MaterialAlertDialogBuilder(this)
            .setTitle("Caixa de medicamento")
            .setView(scroll(box))
            .setNegativeButton("Cancelar") { _,_->discardUnlinkedCameraPhoto(uri) }
            .create()
        dialog.show()
    }

    private fun saveCapturedMedicationPhotoWithoutAi(uri:Uri){
        val all=repo.loadMedications()
        val labels=listOf("➕ Criar nova ficha com esta fotografia")+
            all.map{it.medication.ifBlank{"Medicamento sem nome"}+
                (if(it.dose.isBlank())"" else " · "+it.dose)}
        MaterialAlertDialogBuilder(this)
            .setTitle("Associar a fotografia a que medicamento?")
            .setItems(labels.toTypedArray()){_,position->
                if(position==0){
                    editMedication(null,
                        Medication(images=mutableListOf(localMedicationBoxReference(uri))))
                }else{
                    val selected=all[position-1]
                    MaterialAlertDialogBuilder(this)
                        .setTitle("Confirmar fotografia")
                        .setMessage("Esta imagem corresponde à embalagem " +
                            "e à dosagem de ${selected.medication}"+
                            (if(selected.dose.isBlank())"" else " · ${selected.dose}")+"?")
                        .setPositiveButton("Sim, guardar"){_,_->
                            val latest=repo.loadMedications()
                            val idx=latest.indexOfFirst{it.id==selected.id}
                            if(idx>=0){
                                val path=localMedicationBoxReference(uri)
                                if(path !in latest[idx].images)latest[idx].images.add(path)
                                repo.saveMedications(latest)
                                showMedication()
                                Toast.makeText(this,"Foto associada à ficha.",
                                    Toast.LENGTH_LONG).show()
                            }else showError("O medicamento já não existe.")
                        }.setNegativeButton("Cancelar",null).show()
                }
            }.setNegativeButton("Cancelar",null).show()
    }

    private fun recognizeMedicationBox(uri: Uri) {''',
    'immediate preview and no gallery')

patch(main,
    '''            .addOnFailureListener {
                showError("Não foi possível reconhecer a caixa. Tente novamente com a frente da caixa inteira, direita e com boa luz.")
            }
    }

    private fun handleMedicationBoxResult''',
    '''            .addOnFailureListener {
                MaterialAlertDialogBuilder(this)
                    .setTitle("Não consegui ler esta fotografia")
                    .setMessage("A fotografia ainda está disponível. " +
                        "Podes guardá-la sem reconhecimento ou tirar outra. " +
                        "Para melhorar a leitura, fotografa a frente da caixa com boa luz.")
                    .setPositiveButton("Guardar sem IA"){_,_->
                        saveCapturedMedicationPhotoWithoutAi(uri)
                    }
                    .setNeutralButton("Tirar outra"){_,_->captureMedicationBoxPhoto()}
                    .setNegativeButton("Cancelar",null).show()
            }
    }

    private fun handleMedicationBoxResult''',
    'OCR recovery after failure')

patch(main,
    '''        val parsed = MedicationBoxOcrParser.parse(text, codes, uri.toString())''',
    '''        val parsed = MedicationBoxOcrParser.parse(text, codes,
            localMedicationBoxReference(uri))''',
    'always persist camera image')

patch(main,
    '''                .setPositiveButton("Tentar novamente") { _, _ -> captureMedicationBoxPhoto() }
                .setNegativeButton("Cancelar", null)''',
    '''                .setPositiveButton("Tentar novamente") { _, _ -> captureMedicationBoxPhoto() }
                .setNeutralButton("Guardar foto sem IA") { _, _ ->
                    saveCapturedMedicationPhotoWithoutAi(uri)
                }
                .setNegativeButton("Cancelar", null)''',
    'OCR empty name recovery')

patch(gradle,'versionCode = 46','versionCode = 47','version code')
patch(gradle,'versionName = "1.9.36"','versionName = "1.9.37"','version name')
print('SaúdePrática v1.9.37: camera photo preview with choice to analyze same photo, save without AI or retake.')