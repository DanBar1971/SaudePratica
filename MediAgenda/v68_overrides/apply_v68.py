from pathlib import Path
root = Path('build-src/MediAgenda_Android_v1')
base = root/'app/src/main/java/com/mediagenda/app'

def patch(file: Path, old: str, new: str, label: str):
    text = file.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'v1.9.50 {label}: expected one anchor, found {count}')
    file.write_text(text.replace(old,new,1),encoding='utf-8')

# All stored laboratory PDF/image reports are already in a profile-private
# folder supported by the internal PDF renderer/image decoder.
patch(base/'ClinicalLabsActivity.kt', '''    private fun openOriginal(report:LabReport){
        runCatching{
            startActivity(Intent.createChooser(Intent(Intent.ACTION_VIEW).apply{
                setDataAndType(store.contentUri(report),report.mime)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            },"Abrir análises"))
        }.onFailure{notify("Não foi possível abrir o documento original: "+it.message)}
    }''', '''    private fun openOriginal(report:LabReport){
        // Open the saved ORIGINAL internally; do not invoke Android's app picker.
        startActivity(Intent(this, DocumentOrientationActivity::class.java)
            .putExtra(DocumentOrientationActivity.PROFILE, activeProfileId)
            .putExtra(DocumentOrientationActivity.GROUP, "labs")
            .putExtra(DocumentOrientationActivity.FILENAME, report.fileName)
            .putExtra(DocumentOrientationActivity.TITLE, report.title)
            .putExtra(DocumentOrientationActivity.VIEW_ONLY, true))
    }''', 'laboratory-original')

patch(base/'WorkMedicineActivity.kt', '''    private fun openDocument(item:WorkDocument){
        runCatching{
            val uri=store.openUri(item)
            startActivity(Intent.createChooser(Intent(Intent.ACTION_VIEW).apply{
                setDataAndType(uri,item.mime)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            },"Abrir documento"))
        }.onFailure{message("Não foi possível abrir: "+it.message)}
    }''', '''    private fun openDocument(item:WorkDocument){
        // Both consultation documents and occupational examinations use
        // the internal viewer, retaining all pages of a PDF.
        startActivity(Intent(this, DocumentOrientationActivity::class.java)
            .putExtra(DocumentOrientationActivity.PROFILE, patientId)
            .putExtra(DocumentOrientationActivity.GROUP, "workplace")
            .putExtra(DocumentOrientationActivity.FILENAME, item.filename)
            .putExtra(DocumentOrientationActivity.TITLE, item.name)
            .putExtra(DocumentOrientationActivity.VIEW_ONLY, true))
    }''','workplace-original')

patch(base/'HealthExpensesActivity.kt', '''                if(index==0){
                    runCatching{
                        startActivity(Intent.createChooser(
                            Intent(Intent.ACTION_VIEW).apply{
                                setDataAndType(vault.open(e,a),a.mime)
                                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                            },"Abrir documento"))
                    }.onFailure{notice(it.message?:"Não foi possível abrir o documento.")}
                }else if(index==1){''', '''                if(index==0){
                    // Stored receipt, PDF, reimbursement or prescription:
                    // show internally instead of always asking which app.
                    startActivity(Intent(this, DocumentOrientationActivity::class.java)
                        .putExtra(DocumentOrientationActivity.PROFILE, activeProfileId)
                        .putExtra(DocumentOrientationActivity.GROUP, "expenses")
                        .putExtra(DocumentOrientationActivity.FILENAME, a.name)
                        .putExtra(DocumentOrientationActivity.TITLE, a.title)
                        .putExtra(DocumentOrientationActivity.VIEW_ONLY, true))
                }else if(index==1){''','expense-original')

# Read-only mode should not advertise editing or exporting a PDF page.
patch(base/'DocumentOrientationActivity.kt', '''        if(pdf){
            row("‹ Página" to {if(pageIndex>0){pageIndex--;redraw()}},
                "Página ›" to {if(pageIndex<pageCount-1){pageIndex++;redraw()}},
                "Exportar PNG" to {
                    exportPage.launch("SaudePratica-pagina-${pageIndex+1}.png")
                })
        }''', '''        if(pdf){
            if(readOnly){
                row("‹ Página anterior" to {if(pageIndex>0){pageIndex--;redraw()}},
                    "Próxima página ›" to {if(pageIndex<pageCount-1){pageIndex++;redraw()}})
            }else{
                row("‹ Página" to {if(pageIndex>0){pageIndex--;redraw()}},
                    "Página ›" to {if(pageIndex<pageCount-1){pageIndex++;redraw()}},
                    "Exportar PNG" to {
                        exportPage.launch("SaudePratica-pagina-${pageIndex+1}.png")
                    })
            }
        }''','viewer PDF-only navigation')

# Standard MIUI / Android 16 increased text spacing in short horizontal
# dialog footers, trimming Eliminar, Cancelar and Guardar. Compact them locally
# without changing the rest of the app's font sizes.
profile = base/'MainActivity.kt'
patch(profile, '''        fun footerParams()=LinearLayout.LayoutParams(0,dp(52),1f).apply {
            marginStart=dp(2);marginEnd=dp(2)
        }
        val deleteProfileButton=secondaryButton("Eliminar") {}.apply {''', '''        fun footerParams()=LinearLayout.LayoutParams(0,dp(52),1f).apply {
            marginStart=dp(1);marginEnd=dp(1)
        }
        fun compactProfileAction(button:MaterialButton):MaterialButton = button.apply {
            textSize=11f
            minWidth=0
            minimumWidth=0
            setPadding(dp(2),0,dp(2),0)
            setSingleLine(true)
        }
        val deleteProfileButton=compactProfileAction(secondaryButton("Eliminar") {}).apply {''','profile compact footer setup')
patch(profile, '''            textSize=13f
            visibility=if(firstRun)View.GONE else View.VISIBLE
        }
        val cancelProfileButton=secondaryButton("Cancelar") {}.apply {
            textSize=13f
            visibility=if(firstRun)View.GONE else View.VISIBLE
        }
        val saveProfileButton=primaryButton("Guardar") {}.apply {textSize=13f}''', '''            visibility=if(firstRun)View.GONE else View.VISIBLE
        }
        val cancelProfileButton=compactProfileAction(secondaryButton("Cancelar") {}).apply {
            visibility=if(firstRun)View.GONE else View.VISIBLE
        }
        val saveProfileButton=compactProfileAction(primaryButton("Guardar") {})''','profile action font size')

# A new version code is mandatory; v1.9.49 has already been installed.
gradle = root/'app/build.gradle.kts'
patch(gradle,'versionCode = 58','versionCode = 60','new version code')
patch(gradle,'versionName = "1.9.48"','versionName = "1.9.50"','new version name')

# Prevent regression: only documents' explicit share action may use a chooser.
for name in ('ClinicalLabsActivity.kt','WorkMedicineActivity.kt','HealthExpensesActivity.kt'):
    content=(base/name).read_text(encoding='utf-8')
    assert 'Intent.createChooser' not in content, name
print('v1.9.50: original files (laboratory/workplace/expenses/documents) always use internal viewer; profile footer buttons compact')