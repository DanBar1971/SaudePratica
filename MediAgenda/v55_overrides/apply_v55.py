from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1')
base=root/'app/src/main/java/com/mediagenda/app'
source=Path('MediAgenda/v55_overrides')
(base/'SmartHelpActivity.kt').write_bytes((source/'SmartHelpActivity.kt').read_bytes())

def patch(file,old,new,label):
    s=file.read_text(encoding='utf-8')
    n=s.count(old)
    if n!=1:
        raise RuntimeError(f'v1.9.36 {label}: expected 1 match, found {n}')
    file.write_text(s.replace(old,new,1),encoding='utf-8')

main=base/'MainActivity.kt'
patch(main,
'''    private var pendingMedicineGalleryId:String?=null
    private val medicineGalleryPicker=registerForActivityResult(''',
'''    private var pendingMedicineGalleryId:String?=null
    // Gallery OCR is explicitly requested by the user, independent of the
    // existing "Anexar foto" flow that simply keeps a package photograph.
    private val smartBoxGalleryPicker=registerForActivityResult(
        ActivityResultContracts.OpenDocument()
    ){uri->
        if(uri!=null){
            runCatching {
                contentResolver.takePersistableUriPermission(uri,
                    Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            recognizeMedicationBox(uri)
        }
    }
    private val medicineGalleryPicker=registerForActivityResult(''',
    'separate OCR photo selector')

patch(main,
'''            .setItems(arrayOf(
                "📦 Fotografar caixa de medicamento",
                "🔎 Ler guia de tratamento",
                "📄 Importar PDF ou imagem",
                "✍️ Introduzir manualmente"
            )) { _, choice ->
                when (choice) {
                    0 -> captureMedicationBoxPhoto()
                    1 -> startPrescriptionScan()
                    2 -> pickHealthDocument("medication")
                    else -> editMedication(null)
                }
            }''',
'''            .setItems(arrayOf(
                "📦 Fotografar caixa de medicamento (ML Kit)",
                "✨ Reconhecer medicamento de fotografia existente (ML Kit)",
                "🔎 Ler guia de tratamento",
                "📄 Importar PDF ou imagem",
                "✍️ Introduzir manualmente"
            )) { _, choice ->
                when (choice) {
                    0 -> captureMedicationBoxPhoto()
                    1 -> smartBoxGalleryPicker.launch(arrayOf("image/*"))
                    2 -> startPrescriptionScan()
                    3 -> pickHealthDocument("medication")
                    else -> editMedication(null)
                }
            }''',
    'medicine scanner photo option')

patch(main,
'''    private fun recognizeMedicationBox(uri: Uri) {
        val input = InputImage.fromFilePath(this, uri)
        TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS).process(input)''',
'''    private fun recognizeMedicationBox(uri: Uri) {
        // ML Kit already ships with SaúdePrática. No image or OCR text is sent
        // to a cloud API. Recognition is optional and never changes the
        // "Anexar foto da embalagem" feature.
        val input = runCatching { InputImage.fromFilePath(this, uri) }
            .getOrElse {
                showError("Não foi possível abrir a fotografia escolhida. " +
                    "Experimenta escolher outra imagem ou fotografar a caixa.")
                return
            }
        TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS).process(input)''',
    'clear scanner file failure')

patch(main,
'''        if (duplicate != null) {
            val mergedImages = duplicate.images.toMutableList()
            parsed.images.forEach { if (!mergedImages.contains(it)) mergedImages.add(it) }

            val merged = duplicate.copy(
                medication = duplicate.medication.ifBlank { parsed.medication },
                dose = duplicate.dose.ifBlank { parsed.dose },
                sourceBarcode = duplicate.sourceBarcode.ifBlank { parsed.sourceBarcode },
                images = mergedImages
            )
            val updated = all.map { if (it.id == duplicate.id) merged else it }
            repo.saveMedications(updated)

            MaterialAlertDialogBuilder(this)
                .setTitle("Medicamento já registado")
                .setMessage("${merged.medication}${if (merged.dose.isBlank()) "" else " — ${merged.dose}"} já existe. Não criei uma ficha duplicada. A nova fotografia foi associada à ficha existente.")
                .setPositiveButton("Abrir ficha") { _, _ -> editMedication(merged) }
                .setNegativeButton("Fechar", null)
                .show()
            return
        }''',
'''        if (duplicate != null) {
            // Previous flow silently attached a photo to an existing dose.
            // Recognition may be mistaken: never modify clinical records
            // unless the user has explicitly accepted the detected match.
            MaterialAlertDialogBuilder(this)
                .setTitle("Possível medicamento já registado")
                .setMessage("A leitura sugere: ${parsed.medication} " +
                    "${parsed.dose}.\\n\\nJá existe: ${duplicate.medication} " +
                    "${duplicate.dose}.\\n\\nConfirma que é a MESMA " +
                    "embalagem e dosagem antes de associar a fotografia.")
                .setPositiveButton("Confirmar e associar fotografia") { _, _ ->
                    val current=repo.loadMedications()
                    val index=current.indexOfFirst { it.id==duplicate.id }
                    if(index>=0){
                        parsed.images.forEach { photo ->
                            if(photo !in current[index].images)
                                current[index].images.add(photo)
                        }
                        repo.saveMedications(current)
                        showMedication()
                    }
                }
                .setNeutralButton("Nova ficha") { _, _ -> editMedication(null,parsed,true) }
                .setNegativeButton("Cancelar",null)
                .show()
            return
        }''',
    'consent before attaching to existing medication')

patch(main,
'''        box.addView(infoCard("📖", "Ajuda", "Como usar a SaúdePrática, passo a passo") {''',
'''        box.addView(infoCard("✨", "Assistente de ajuda offline",
            "Faz perguntas sobre medicamentos, tomas, consultas e sincronização") {
            startActivity(Intent(this,SmartHelpActivity::class.java))
        })
        box.addView(infoCard("📖", "Ajuda", "Como usar a SaúdePrática, passo a passo") {''',
    'smart help menu')

manifest=root/'app/src/main/AndroidManifest.xml'
patch(manifest,
'''        <activity android:name=".SupportHelpActivity" android:exported="false" />''',
'''        <activity android:name=".SupportHelpActivity" android:exported="false" />
        <activity android:name=".SmartHelpActivity" android:exported="false" />''',
    'new help activity')

gradle=root/'app/build.gradle.kts'
patch(gradle,'versionCode = 45','versionCode = 46','bump version code')
patch(gradle,'versionName = "1.9.35"','versionName = "1.9.36"','bump version name')
print('v1.9.36: optional existing-gallery ML Kit box recognition and offline rule-based help assistant.')