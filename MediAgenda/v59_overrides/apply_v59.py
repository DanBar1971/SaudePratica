from pathlib import Path
root = Path('build-src/MediAgenda_Android_v1')
main = root/'app/src/main/java/com/mediagenda/app/MainActivity.kt'
gradle = root/'app/build.gradle.kts'

def patch(f, old, new, label):
    original=f.read_text(encoding='utf-8')
    n=original.count(old)
    if n!=1:raise RuntimeError(f'v1.9.40 {label}: expected exactly 1, got {n}')
    f.write_text(original.replace(old,new,1),encoding='utf-8')

patch(main,
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
        TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS).process(input)
            .addOnSuccessListener { vision ->
                BarcodeScanning.getClient().process(input)
                    .addOnSuccessListener { barcodes ->
                        val codes = barcodes.mapNotNull { it.rawValue }.filter { it.isNotBlank() }
                        handleMedicationBoxResult(vision.text, codes, uri)
                    }
                    .addOnFailureListener {
                        handleMedicationBoxResult(vision.text, emptyList(), uri)
                    }
            }
            .addOnFailureListener {
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
    }''',
'''    private fun recognizeMedicationBox(uri: Uri) {
        // Decode exactly like the preview. On some Android devices ML Kit's
        // InputImage.fromFilePath() cannot reopen an app-private FileProvider
        // URI, even while the app can open the corresponding private JPEG.
        // MedicationPhotoLoader handles that path, JPEG dimensions and EXIF.
        // FromBitmap bypasses the failing ContentResolver / FileProvider path.
        val reference=localMedicationBoxReference(uri)
        val bitmap=runCatching {
            MedicationPhotoLoader.load(this,listOf(reference),2000)
        }.onFailure {
            android.util.Log.e("SaudePraticaOCR","Box photo decode failed",it)
        }.getOrNull()
        if(bitmap==null){
            MaterialAlertDialogBuilder(this)
                .setTitle("Não foi possível abrir a fotografia")
                .setMessage("Não foi possível ler a imagem para reconhecimento. " +
                    "Podes associá-la manualmente, sem análise.")
                .setPositiveButton("Guardar fotografia sem IA"){_,_->
                    saveCapturedMedicationPhotoWithoutAi(uri)
                }
                .setNegativeButton("Fechar",null).show()
            return
        }
        val input=InputImage.fromBitmap(bitmap,0)
        // Keep the Bitmap alive until ML Kit has completed both operations.
        TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS).process(input)
            .addOnSuccessListener { vision ->
                BarcodeScanning.getClient().process(input)
                    .addOnCompleteListener { scanned ->
                        val codes=if(scanned.isSuccessful)
                            scanned.result.orEmpty().mapNotNull { it.rawValue }
                                .filter { it.isNotBlank() }
                            else emptyList()
                        bitmap.recycle()
                        handleMedicationBoxResult(vision.text,codes,uri)
                    }
            }
            .addOnFailureListener { error ->
                android.util.Log.e("SaudePraticaOCR","Box recognition failed",error)
                bitmap.recycle()
                MaterialAlertDialogBuilder(this)
                    .setTitle("Não consegui reconhecer esta caixa")
                    .setMessage("A fotografia foi guardada e podes usá-la sem " +
                        "reconhecimento ou tentar fotografar de novo. " +
                        "O nome e a dosagem devem estar legíveis.")
                    .setPositiveButton("Guardar fotografia sem IA"){_,_->
                        saveCapturedMedicationPhotoWithoutAi(uri)
                    }
                    .setNeutralButton("Tirar outra"){_,_->captureMedicationBoxPhoto()}
                    .setNegativeButton("Cancelar",null).show()
            }
    }''',
'replace failing FileProvider InputImage access with decoded bitmap used by preview')
patch(gradle,'versionCode = 49','versionCode = 50','version code')
patch(gradle,'versionName = "1.9.39"','versionName = "1.9.40"','version name')
print('v1.9.40: ML Kit consumes same successfully decoded camera photograph as preview, via InputImage.fromBitmap; non-destructive manual photo fallback.')