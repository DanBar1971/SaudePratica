from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
main=root/"app/src/main/java/com/mediagenda/app/MainActivity.kt"
gradle=root/"app/build.gradle.kts"
s=main.read_text(encoding="utf-8")
def change(old,new):
 global s
 if old not in s: raise RuntimeError("SaudePratica v1.9 anchor missing: "+repr(old[:100]))
 s=s.replace(old,new,1)
change('putExtra("title", "🔔 MediAgenda — teste")','putExtra("title", "🔔 SaúdePrática — teste")')
change('private fun showMedicationAddOptions() {', '''private var documentPurpose = "medication"
    private val documentPicker = registerForActivityResult(
        androidx.activity.result.contract.ActivityResultContracts.OpenDocument()
    ) { uri ->
        if (uri != null) importHealthDocument(uri, documentPurpose)
    }

    private fun pickHealthDocument(purpose: String) {
        documentPurpose = purpose
        documentPicker.launch(arrayOf("application/pdf", "image/*"))
    }

    private fun importHealthDocument(uri: Uri, purpose: String) {
        val mime = contentResolver.getType(uri).orEmpty()
        if (mime != "application/pdf" && !uri.toString().lowercase().endsWith(".pdf")) {
            processImportedHealthImage(uri, purpose)
            return
        }
        try {
            val descriptor = contentResolver.openFileDescriptor(uri, "r")
                ?: throw IllegalStateException("Documento inacessível")
            descriptor.use { fd ->
                android.graphics.pdf.PdfRenderer(fd).use { renderer ->
                    if (renderer.pageCount == 0) throw IllegalStateException("PDF vazio")
                    val pages = (0 until renderer.pageCount).map { "Página ${it+1}" }.toTypedArray()
                    MaterialAlertDialogBuilder(this)
                        .setTitle("Escolher página do PDF")
                        .setItems(pages) { _, selected ->
                            try {
                                // Reopen the PDF: the selection dialog outlives this descriptor.
                                contentResolver.openFileDescriptor(uri, "r")!!.use { selectedFd ->
                                    android.graphics.pdf.PdfRenderer(selectedFd).use { selectedRenderer ->
                                        selectedRenderer.openPage(selected).use { page ->
                                            val scale = (2200f / maxOf(page.width, page.height)).coerceAtMost(3f)
                                            val bitmap = android.graphics.Bitmap.createBitmap(
                                                (page.width*scale).toInt().coerceAtLeast(1),
                                                (page.height*scale).toInt().coerceAtLeast(1),
                                                android.graphics.Bitmap.Config.ARGB_8888)
                                            bitmap.eraseColor(Color.WHITE)
                                            val matrix = android.graphics.Matrix().apply { setScale(scale, scale) }
                                            page.render(bitmap, null, matrix, android.graphics.pdf.PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
                                            val file = java.io.File(cacheDir, "saudepratica_ocr_page.png")
                                            java.io.FileOutputStream(file).use { out ->
                                                bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, out)
                                            }
                                            bitmap.recycle()
                                            processImportedHealthImage(Uri.fromFile(file), purpose)
                                        }
                                    }
                                }
                            } catch (error: Exception) {
                                showError("Não foi possível ler a página: ${error.message}")
                            }
                        }.setNegativeButton("Cancelar", null).show()
                }
            }
        } catch (error: Exception) {
            showError("Não foi possível abrir o PDF: ${error.message}")
        }
    }

    private fun processImportedHealthImage(uri: Uri, purpose: String) {
        when (purpose) {
            "agenda" -> recognizeAppointment(uri)
            "box" -> recognizeMedicationBox(uri)
            else -> recognizePrescription(uri)
        }
    }

    private fun showAboutSaudePratica() {
        val version = try {
            packageManager.getPackageInfo(packageName, 0).versionName ?: "1.9.0"
        } catch (_: Exception) { "1.9.0" }
        MaterialAlertDialogBuilder(this)
            .setTitle("Acerca da SaúdePrática")
            .setMessage("SaúdePrática\\nVersão: $version\\nAutor: Daniel Barradas\\nAndroid\\n\\nGestão pessoal de medicação, consultas e documentos.")
            .setPositiveButton("Fechar", null).show()
    }

    private fun showMedicationAddOptions() {''')
change('''"📦 Fotografar caixa de medicamento",
                "🔎 Ler guia de tratamento",''','''"📦 Fotografar caixa de medicamento",
                "🔎 Ler guia de tratamento",
                "📄 Importar PDF ou imagem",''')
change('''0 -> captureMedicationBoxPhoto()
                    1 -> startPrescriptionScan()
                    else -> editMedication(null)''','''0 -> captureMedicationBoxPhoto()
                    1 -> startPrescriptionScan()
                    2 -> pickHealthDocument("medication")
                    else -> editMedication(null)''')
change('''"📷 Fotografar folha de marcações",
                "✍️ Introduzir manualmente"''','''"📷 Fotografar folha de marcações",
                "📄 Importar PDF ou imagem",
                "✍️ Introduzir manualmente"''')
change('''0 -> captureAppointmentPhoto()
                    else -> editAppointment(null)''','''0 -> captureAppointmentPhoto()
                    1 -> pickHealthDocument("agenda")
                    else -> editAppointment(null)''')
anchor='''        box.addView(infoCard("👤", "Perfil", profileName().ifBlank { "Definir nome do perfil" }) { showProfileDialog(false) })'''
change(anchor,anchor+'''
        box.addView(infoCard("ℹ️", "Acerca", "SaúdePrática — versão e autor") {
            showAboutSaudePratica()
        })''')
s=s.replace("Aspeto da MediAgenda","Aspeto da SaúdePrática").replace("a partir da MediAgenda","a partir da SaúdePrática")
main.write_text(s,encoding="utf-8")
g=gradle.read_text(encoding="utf-8")
assert 'applicationId = "com.mediagenda.app.stable"' in g
assert 'versionCode = 9' in g and 'versionName = "1.8.0"' in g
g=g.replace('versionCode = 9','versionCode = 10',1).replace('versionName = "1.8.0"','versionName = "1.9.0"',1)
gradle.write_text(g,encoding="utf-8")
print("SaúdePrática 1.9 patch applied")
