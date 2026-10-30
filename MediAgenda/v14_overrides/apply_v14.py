from pathlib import Path

root = Path("build-src/MediAgenda_Android_v1")
p = root / "app/src/main/java/com/mediagenda/app/MainActivity.kt"
s = p.read_text(encoding="utf-8")

def replace(old, new, count=1):
    global s
    if old not in s:
        raise RuntimeError("v1.4 patch target missing: " + old[:100])
    s = s.replace(old, new, count)

replace("import com.mediagenda.app.ocr.MedicationBoxOcrParser\n",
        "import com.mediagenda.app.ocr.MedicationBoxOcrParser\nimport com.mediagenda.app.ocr.CitizenCardOcrParser\n")

replace("private enum class PhotoMode { AGENDA, PRESCRIPTION, MEDICATION_BOX }",
        "private enum class PhotoMode { AGENDA, PRESCRIPTION, MEDICATION_BOX, MEDICATION_ATTACH, ID_CARD_BACK }")

replace("    private var pendingPhotoUri: Uri? = null",
'''    private var pendingPhotoUri: Uri? = null
    private var pendingIdentityPhotoFile: File? = null
    private var pendingMedicationPhotoTargetId: String? = null
    private var profileDraft: Triple<String, String, String>? = null
    private var activeMedicationDialog: androidx.appcompat.app.AlertDialog? = null''')

replace('        if (!ok) return@registerForActivityResult',
'''        if (!ok) {
            if (pendingPhotoMode == PhotoMode.ID_CARD_BACK) {
                pendingIdentityPhotoFile?.delete()
                pendingIdentityPhotoFile = null
                showProfileDialog(false)
            }
            return@registerForActivityResult
        }''')

replace("            PhotoMode.MEDICATION_BOX -> recognizeMedicationBox(uri)",
'''            PhotoMode.MEDICATION_BOX -> recognizeMedicationBox(uri)
            PhotoMode.MEDICATION_ATTACH -> attachPhotoToExistingMedication(uri)
            PhotoMode.ID_CARD_BACK -> recognizeCitizenCard(uri)''')

replace('''    private fun captureMedicationBoxPhoto() {
        pendingPhotoMode = PhotoMode.MEDICATION_BOX
        capturePhotoWithPermission()
    }''',
'''    private fun captureMedicationBoxPhoto() {
        pendingPhotoMode = PhotoMode.MEDICATION_BOX
        capturePhotoWithPermission()
    }

    private fun captureMedicationPhotoFor(id: String) {
        pendingMedicationPhotoTargetId = id
        pendingPhotoMode = PhotoMode.MEDICATION_ATTACH
        activeMedicationDialog?.dismiss()
        activeMedicationDialog = null
        capturePhotoWithPermission()
    }

    private fun captureCitizenCardBack() {
        pendingPhotoMode = PhotoMode.ID_CARD_BACK
        capturePhotoWithPermission()
    }''')

replace("if (mode == PhotoMode.MEDICATION_BOX)",
        "if (mode == PhotoMode.MEDICATION_BOX || mode == PhotoMode.MEDICATION_ATTACH)")

replace('''            PhotoMode.MEDICATION_BOX -> "medicamento"
            PhotoMode.AGENDA -> "agenda"''',
'''            PhotoMode.MEDICATION_BOX -> "medicamento"
            PhotoMode.MEDICATION_ATTACH -> "caixa_anexada"
            PhotoMode.ID_CARD_BACK -> "cc_temporario"
            PhotoMode.AGENDA -> "agenda"''')

replace('        val uri = FileProvider.getUriForFile(this, "${BuildConfig.APPLICATION_ID}.fileprovider", file)',
'''        if (mode == PhotoMode.ID_CARD_BACK) pendingIdentityPhotoFile = file
        val uri = FileProvider.getUriForFile(this, "${BuildConfig.APPLICATION_ID}.fileprovider", file)''')

replace("    private fun recognizeMedicationBox(uri: Uri) {",
'''    private fun attachPhotoToExistingMedication(uri: Uri) {
        val target = pendingMedicationPhotoTargetId
        pendingMedicationPhotoTargetId = null
        val all = repo.loadMedications()
        val index = all.indexOfFirst { it.id == target }
        if (index < 0) {
            showError("O medicamento já não existe. A fotografia não foi associada.")
            return
        }
        val med = all[index]
        val photos = med.images.toMutableList()
        if (!photos.contains(uri.toString())) photos.add(uri.toString())
        all[index] = med.copy(images = photos)
        repo.saveMedications(all)
        Toast.makeText(this, "Foto da caixa associada a ${med.medication}", Toast.LENGTH_LONG).show()
        showMedication()
    }

    private fun recognizeCitizenCard(uri: Uri) {
        val input = try { InputImage.fromFilePath(this, uri) } catch (e: Exception) {
            pendingIdentityPhotoFile?.delete()
            pendingIdentityPhotoFile = null
            showError("Erro ao abrir fotografia do Cartão de Cidadão.")
            showProfileDialog(false)
            return
        }
        TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS).process(input)
            .addOnSuccessListener { result ->
                val found = CitizenCardOcrParser.parse(result.text)
                val draft = profileDraft
                profileDraft = Triple(draft?.first.orEmpty(),
                    found.nif.ifBlank { draft?.second.orEmpty() },
                    found.snsNumber.ifBlank { draft?.third.orEmpty() })
                if (found.nif.isBlank() && found.snsNumber.isBlank())
                    Toast.makeText(this, "Não encontrei números legíveis. Pode preencher manualmente.", Toast.LENGTH_LONG).show()
                showProfileDialog(false)
            }
            .addOnFailureListener {
                Toast.makeText(this, "OCR não conseguiu ler o cartão. Pode preencher manualmente.", Toast.LENGTH_LONG).show()
                showProfileDialog(false)
            }
            .addOnCompleteListener {
                // The Citizen Card photo is never kept in the app.
                pendingIdentityPhotoFile?.delete()
                pendingIdentityPhotoFile = null
            }
    }

    private fun recognizeMedicationBox(uri: Uri) {''')

replace('''        MaterialAlertDialogBuilder(this)
            .setTitle(if(fromScan) "Confirmar medicação"''',
'''        if (existing != null) {
            box.addView(secondaryButton("📷 Adicionar foto da caixa a esta ficha") {
                captureMedicationPhotoFor(existing.id)
            })
            if (existing.images.isNotEmpty()) {
                box.addView(noteBox("Fotografias guardadas", "${existing.images.size} fotografia(s) associadas a este medicamento."))
            }
        }
        activeMedicationDialog = MaterialAlertDialogBuilder(this)
            .setTitle(if(fromScan) "Confirmar medicação"''')

# Existing profile dialog is replaced with a richer editable profile + OCR.
start = s.index('    private fun showProfileDialog(firstRun: Boolean) {')
end = s.index('\n    private fun reschedule()', start)
s = s[:start] + '''    private fun showProfileDialog(firstRun: Boolean) {
        val prefs = getSharedPreferences("mediagenda_profile", MODE_PRIVATE)
        val draft = profileDraft
        val box = formBox()
        box.addView(noteBox("Dados do perfil", "O NIF e o número de utente são opcionais. O Cartão de Cidadão é lido localmente e a fotografia é eliminada após o OCR. Confirme os números antes de guardar."))

        val name = input("Nome do perfil", draft?.first ?: profileName())
        val nif = input("NIF (9 dígitos)", draft?.second ?: prefs.getString("nif", "").orEmpty())
        val sns = input("Número de utente SNS (9 dígitos)", draft?.third ?: prefs.getString("sns_number", "").orEmpty())
        listOf(name, nif, sns).forEach { box.addView(it.container) }

        var dialog: androidx.appcompat.app.AlertDialog? = null
        box.addView(secondaryButton("📷 Fotografar verso do Cartão de Cidadão") {
            profileDraft = Triple(name.edit.text.toString().trim(),
                nif.edit.text.toString().filter { it.isDigit() },
                sns.edit.text.toString().filter { it.isDigit() })
            dialog?.dismiss()
            captureCitizenCardBack()
        })

        dialog = MaterialAlertDialogBuilder(this)
            .setTitle(if (firstRun) "Bem-vindo à MediAgenda" else "Editar perfil")
            .setView(scroll(box))
            .setPositiveButton("Guardar", null)
            .apply { if (!firstRun) setNegativeButton("Cancelar", null) }
            .show()

        dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE).setOnClickListener {
            val n = name.edit.text.toString().trim()
            val fiscal = nif.edit.text.toString().filter { it.isDigit() }
            val health = sns.edit.text.toString().filter { it.isDigit() }
            if (fiscal.isNotBlank() && !CitizenCardOcrParser.validNif(fiscal)) {
                nif.edit.error = "NIF inválido. Confirme os 9 dígitos."
                return@setOnClickListener
            }
            if (health.isNotBlank() && (health.length != 9 || !health.all { it.isDigit() })) {
                sns.edit.error = "O número de utente deve ter 9 dígitos."
                return@setOnClickListener
            }
            prefs.edit()
                .putString("name", n)
                .putString("nif", fiscal)
                .putString("sns_number", health)
                .apply()
            profileDraft = null
            dialog.dismiss()
            showMedication()
        }
    }
''' + s[end:]

p.write_text(s, encoding="utf-8")

p = root / "app/build.gradle.kts"
s = p.read_text(encoding="utf-8")
if 'versionCode = 4' not in s: raise RuntimeError("Expected v1.3 version 4")
s = s.replace('versionCode = 4', 'versionCode = 5')
s = s.replace('versionName = "1.3.0"', 'versionName = "1.4.0"')
p.write_text(s, encoding="utf-8")

print("MediAgenda v1.4 patch applied")
