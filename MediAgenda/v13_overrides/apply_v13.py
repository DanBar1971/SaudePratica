from pathlib import Path

root = Path("build-src/MediAgenda_Android_v1")
p = root / "app/src/main/java/com/mediagenda/app/MainActivity.kt"
s = p.read_text(encoding="utf-8")

# Import parser.
s = s.replace(
    "import com.mediagenda.app.ocr.PrescriptionOcrParser\n",
    "import com.mediagenda.app.ocr.PrescriptionOcrParser\nimport com.mediagenda.app.ocr.MedicationBoxOcrParser\n"
)

# Add camera mode.
s = s.replace(
    "private enum class PhotoMode { AGENDA, PRESCRIPTION }",
    "private enum class PhotoMode { AGENDA, PRESCRIPTION, MEDICATION_BOX }"
)

# Route captured photo.
s = s.replace(
    "            PhotoMode.AGENDA -> recognizeAppointment(uri)\n            PhotoMode.PRESCRIPTION -> recognizePrescription(uri)",
    "            PhotoMode.AGENDA -> recognizeAppointment(uri)\n            PhotoMode.PRESCRIPTION -> recognizePrescription(uri)\n            PhotoMode.MEDICATION_BOX -> recognizeMedicationBox(uri)"
)

# Add a prominent box photo card before the prescription guide card.
needle = '''        val items = repo.loadMedications()
        content.addView(summaryCard(
            icon = "🔎",
'''
replacement = '''        val items = repo.loadMedications()

        content.addView(summaryCard(
            icon = "📦",
            title = "Fotografar caixa",
            body = "Fotografe a caixa do medicamento. A MediAgenda tenta ler o nome, dose e código de barras e preenche a ficha automaticamente.",
            action = "Fotografar"
        ) { captureMedicationBoxPhoto() })

        content.addView(summaryCard(
            icon = "🔎",
'''
if needle not in s:
    raise SystemExit("showMedication insertion point not found")
s = s.replace(needle, replacement, 1)

s = s.replace(
    'content.addView(emptyState("Ainda não há medicação", "Use “Ler guia” ou adicione manualmente."),',
    'content.addView(emptyState("Ainda não há medicação", "Fotografe uma caixa, leia uma guia ou adicione manualmente."),'
)

# Add capture function.
needle = '''    private fun capturePrescriptionPhoto() {
        pendingPhotoMode = PhotoMode.PRESCRIPTION
        capturePhotoWithPermission()
    }

    private fun captureAppointmentPhoto() {
'''
replacement = '''    private fun captureMedicationBoxPhoto() {
        pendingPhotoMode = PhotoMode.MEDICATION_BOX
        capturePhotoWithPermission()
    }

    private fun capturePrescriptionPhoto() {
        pendingPhotoMode = PhotoMode.PRESCRIPTION
        capturePhotoWithPermission()
    }

    private fun captureAppointmentPhoto() {
'''
if needle not in s:
    raise SystemExit("capture functions insertion point not found")
s = s.replace(needle, replacement, 1)

# Persist medicine-box photos; appointment/prescription photos can remain cache files.
old = '''    private fun launchCamera(mode: PhotoMode) {
        pendingPhotoMode = mode
        val dir = File(cacheDir, "camera").apply { mkdirs() }
        val prefix = if (mode == PhotoMode.PRESCRIPTION) "prescricao" else "agenda"
        val file = File(dir, "${prefix}_${System.currentTimeMillis()}.jpg")
        val uri = FileProvider.getUriForFile(this, "${BuildConfig.APPLICATION_ID}.fileprovider", file)
        pendingPhotoUri = uri
        takePhoto.launch(uri)
    }
'''
new = '''    private fun launchCamera(mode: PhotoMode) {
        pendingPhotoMode = mode
        val dir = if (mode == PhotoMode.MEDICATION_BOX)
            File(filesDir, "medication_photos").apply { mkdirs() }
        else
            File(cacheDir, "camera").apply { mkdirs() }

        val prefix = when (mode) {
            PhotoMode.PRESCRIPTION -> "prescricao"
            PhotoMode.MEDICATION_BOX -> "medicamento"
            PhotoMode.AGENDA -> "agenda"
        }
        val file = File(dir, "${prefix}_${System.currentTimeMillis()}.jpg")
        val uri = FileProvider.getUriForFile(this, "${BuildConfig.APPLICATION_ID}.fileprovider", file)
        pendingPhotoUri = uri
        takePhoto.launch(uri)
    }
'''
if old not in s:
    raise SystemExit("launchCamera block not found")
s = s.replace(old, new, 1)

# Add medication box OCR and duplicate handling immediately before prescription recognition.
needle = '''    private fun recognizePrescription(uri: Uri) {
'''
box_code = '''    private fun recognizeMedicationBox(uri: Uri) {
        val input = InputImage.fromFilePath(this, uri)
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
                showError("Não foi possível reconhecer a caixa. Tente novamente com a frente da caixa inteira, direita e com boa luz.")
            }
    }

    private fun handleMedicationBoxResult(text: String, codes: List<String>, uri: Uri) {
        val parsed = MedicationBoxOcrParser.parse(text, codes, uri.toString())
        if (parsed.medication.isBlank()) {
            MaterialAlertDialogBuilder(this)
                .setTitle("Não consegui identificar o medicamento")
                .setMessage("A fotografia foi guardada, mas o nome não ficou suficientemente legível. Tente fotografar a frente da caixa, com o nome e a dose visíveis.")
                .setPositiveButton("Tentar novamente") { _, _ -> captureMedicationBoxPhoto() }
                .setNegativeButton("Cancelar", null)
                .show()
            return
        }

        val all = repo.loadMedications()
        val parsedName = MedicationBoxOcrParser.normalizedMedicationName(parsed.medication)
        val parsedDose = MedicationBoxOcrParser.normalizedDose(parsed.dose)
        val parsedCodes = parsed.sourceBarcode.split("|").map { it.trim() }.filter { it.isNotBlank() }.toSet()

        val duplicate = all.firstOrNull { existing ->
            val existingName = MedicationBoxOcrParser.normalizedMedicationName(existing.medication)
            val existingDose = MedicationBoxOcrParser.normalizedDose(existing.dose)
            val existingCodes = existing.sourceBarcode.split("|").map { it.trim() }.filter { it.isNotBlank() }.toSet()

            val barcodeMatch = parsedCodes.isNotEmpty() && existingCodes.isNotEmpty() &&
                parsedCodes.any { it in existingCodes }

            val nameMatch = parsedName.isNotBlank() && parsedName == existingName
            val doseCompatible = parsedDose.isBlank() || existingDose.isBlank() || parsedDose == existingDose

            barcodeMatch || (nameMatch && doseCompatible)
        }

        if (duplicate != null) {
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
        }

        editMedication(null, parsed, true)
    }

    private fun recognizePrescription(uri: Uri) {
'''
if needle not in s:
    raise SystemExit("recognizePrescription insertion point not found")
s = s.replace(needle, box_code, 1)

p.write_text(s, encoding="utf-8")

# Version bump.
p = root / "app/build.gradle.kts"
s = p.read_text(encoding="utf-8")
s = s.replace('versionCode = 3', 'versionCode = 4')
s = s.replace('versionName = "1.2.0"', 'versionName = "1.3.0"')
# Stable package ID installs in parallel with earlier debug-signed builds.
# Keep it constant in future updates; the application namespace stays unchanged.
s = s.replace('applicationId = "com.mediagenda.app"', 'applicationId = "com.mediagenda.app.stable"')
p.write_text(s, encoding="utf-8")

print("MediAgenda v1.3 medication-box OCR patches applied")
