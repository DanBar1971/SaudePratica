from pathlib import Path

root = Path("build-src/MediAgenda_Android_v1")
base = root / "app/src/main/java/com/mediagenda/app"

def replace_once(path, old, new, label):
    content = path.read_text(encoding="utf-8")
    count = content.count(old)
    if count != 1:
        raise RuntimeError(f"v1.9.47 {label}: expected one match, found {count}")
    path.write_text(content.replace(old, new, 1), encoding="utf-8")

docs = base / "DocumentsActivity.kt"
replace_once(docs, '''                    0 -> {
                        try {
                            startActivity(Intent.createChooser(Intent(Intent.ACTION_VIEW).apply {
                                setDataAndType(store.contentUri(doc), doc.mimeType)
                                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                            }, "Abrir documento"))
                        } catch (e: Exception) { message("Não foi possível abrir: " + e.message) }
                    }''',
'''                    0 -> {
                        // View PDFs and images directly in SaudePratica: do not
                        // force the Android application picker every time.
                        startActivity(Intent(this, DocumentOrientationActivity::class.java)
                            .putExtra(DocumentOrientationActivity.PROFILE, profile.id)
                            .putExtra(DocumentOrientationActivity.GROUP, "documents")
                            .putExtra(DocumentOrientationActivity.FILENAME, doc.fileName)
                            .putExtra(DocumentOrientationActivity.TITLE, doc.name)
                            .putExtra(DocumentOrientationActivity.VIEW_ONLY, true))
                    }''', "in-app open original")

viewer = base / "DocumentOrientationActivity.kt"
replace_once(viewer,
    '        const val TITLE="document_title"',
    '        const val TITLE="document_title"\n        const val VIEW_ONLY="view_only"',
    "viewer mode extra")
replace_once(viewer,
    '    private var pdf=false',
    '    private var readOnly=false\n    private var pdf=false',
    "viewer read-only flag")
replace_once(viewer,
    '        super.onCreate(state)\n        val profile=',
    '        super.onCreate(state)\n        readOnly=intent.getBooleanExtra(VIEW_ONLY,false)\n        val profile=',
    "viewer mode init")
replace_once(viewer,
    '            text="‹  SaúdePrática  /  Corrigir orientação"',
    '            text=if(readOnly) "‹  SaúdePrática  /  Visualizar documento" else\n                "‹  SaúdePrática  /  Corrigir orientação"',
    "viewer heading")
replace_once(viewer,
    '''        row("↶ 90º" to {change(-90)}, "↷ 90º" to {change(90)},
            "⤾ 180º" to {change(180)})
        row("↺ Repor" to {pending[pageIndex]=0;redraw()},
            "✨ Auto OCR" to {detectOrientation()})''',
    '''        if(!readOnly){
            row("↶ 90º" to {change(-90)}, "↷ 90º" to {change(90)},
                "⤾ 180º" to {change(180)})
            row("↺ Repor" to {pending[pageIndex]=0;redraw()},
                "✨ Auto OCR" to {detectOrientation()})
        }''',
    "viewer hides editing controls")
replace_once(viewer,
    '''        row("Cancelar" to {finish()}, "Guardar orientação" to {saveOrientation()})
        if(pdf)root.addView(TextView(this).apply{''',
    '''        if(readOnly)row("Fechar" to {finish()})
        else row("Cancelar" to {finish()}, "Guardar orientação" to {saveOrientation()})
        if(pdf && !readOnly)root.addView(TextView(this).apply{''',
    "viewer hides save controls")
replace_once(viewer,
    '            status.text=(if(pdf)',
    '''            status.text=if(readOnly){
                if(pdf) "Página "+(pageIndex+1)+" de "+pageCount else "Imagem original"
            }else (if(pdf)''',
    "viewer clean page counter")

gradle = root / "app/build.gradle.kts"
replace_once(gradle, 'versionCode = 56', 'versionCode = 57', "version code")
replace_once(gradle, 'versionName = "1.9.46"', 'versionName = "1.9.47"', "version name")
print("v1.9.47: PDFs and images open inside SaudePratica without the OS app chooser")
