from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"

for source,destination in (
    ("DocumentOrientationActivity.kt",base/"DocumentOrientationActivity.kt"),
    ("DocumentOrientationStore.kt",base/"data/DocumentOrientationStore.kt"),
):
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(Path("MediAgenda/v43_overrides",source)
        .read_text(encoding="utf-8"),encoding="utf-8")

def patch(file,old,new,label):
    s=file.read_text(encoding="utf-8")
    if s.count(old)!=1:
        raise RuntimeError("v1.9.24: missing/ambiguous "+label+": "+str(s.count(old)))
    file.write_text(s.replace(old,new,1),encoding="utf-8")

manifest=root/"app/src/main/AndroidManifest.xml"
patch(manifest,
    '''        <activity android:name=".ProfileMediaActivity" android:exported="false" />''',
    '''        <activity android:name=".ProfileMediaActivity" android:exported="false" />
        <activity android:name=".DocumentOrientationActivity" android:exported="false" />''',
    "orientation editor registration")

# CC scans and avatar: corrected JPEG bytes are used automatically by existing OCR.
p=base/"ProfileMediaActivity.kt"
patch(p,'''import android.content.pm.PackageManager''',
      '''import android.content.pm.PackageManager
import android.content.Intent''',"profile Intent")
patch(p,
    '''    private val picker=registerForActivityResult(ActivityResultContracts.GetContent()){uri->''',
    '''    private var lastOrientationKind="cc_front"
    private val orientationEditor=registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ){result->
        if(result.resultCode==RESULT_OK){
            draw()
            if(lastOrientationKind=="cc_front"||lastOrientationKind=="cc_back"){
                MaterialAlertDialogBuilder(this)
                    .setTitle("Ler CC após corrigir orientação?")
                    .setMessage("O OCR vai utilizar a imagem agora orientada.")
                    .setPositiveButton("Ler com OCR"){_,_->
                        scanSavedCitizenCard(lastOrientationKind)
                    }.setNegativeButton("Agora não",null).show()
            }
        }
    }
    private val picker=registerForActivityResult(ActivityResultContracts.GetContent()){uri->''',
    "profile orientation launcher")
patch(p,
    '''            if(photo!=null && (key=="cc_front" || key=="cc_back")) {''',
    '''            if(photo!=null){
                column.addView(outline("↶ ↷ Rodar / corrigir orientação"){
                    editOrientation(key)
                })
            }
            if(photo!=null && (key=="cc_front" || key=="cc_back")) {''',
    "profile orientation button")
patch(p,
    '''        body.addView(label(
            "As fotografias ficam na área privada deste utilizador. "+''',
    '''        body.addView(label(
            "As fotografias ficam na área privada deste utilizador. "+''',
    "footer patch anchor")
patch(p,
    '''            "Estas fotografias não são incluídas no backup JSON da aplicação.",''',
    '''            "Estas fotografias entram no backup familiar ZIP completo, "+
            "mas não no backup JSON antigo.",''',"backup clarification")
patch(p,
    '''    private fun chooseImage(kind:String){''',
    '''    private fun editOrientation(kind:String){
        lastOrientationKind=kind
        val request=Intent(this,DocumentOrientationActivity::class.java)
            .putExtra(DocumentOrientationActivity.PROFILE,profileId)
            .putExtra(DocumentOrientationActivity.GROUP,"identity")
            .putExtra(DocumentOrientationActivity.FILENAME,kind+".jpg")
            .putExtra(DocumentOrientationActivity.TITLE,
                if(kind=="cc_front")"CC — Frente"
                else if(kind=="cc_back")"CC — Verso"
                else "Fotografia do perfil")
        orientationEditor.launch(request)
    }
    private fun chooseImage(kind:String){''',"profile orientation launch method")
patch(p,
    '''                    .setPositiveButton("Ler e rever") { _,_ -> scanSavedCitizenCard(target) }
                    .setNegativeButton("Agora não",null).show()''',
    '''                    .setPositiveButton("Corrigir orientação"){_,_->
                        editOrientation(target)
                    }
                    .setNeutralButton("Ler já com OCR"){_,_->
                        scanSavedCitizenCard(target)
                    }
                    .setNegativeButton("Agora não",null).show()''',
    "offer orientation before CC OCR")

# General PDF and image document library.
p=base/"DocumentsActivity.kt"
patch(p,
    '''    private val picker = registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->''',
    '''    private val orientationEditor=registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ){result->if(result.resultCode==RESULT_OK)refresh()}
    private val picker = registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->''',
    "documents activity orientation launcher")
patch(p,
    '''    private fun actionsFor(doc: HealthDocument) {''',
    '''    private fun editOrientation(doc:HealthDocument){
        orientationEditor.launch(Intent(this,DocumentOrientationActivity::class.java)
            .putExtra(DocumentOrientationActivity.PROFILE,profile.id)
            .putExtra(DocumentOrientationActivity.GROUP,"documents")
            .putExtra(DocumentOrientationActivity.FILENAME,doc.fileName)
            .putExtra(DocumentOrientationActivity.TITLE,doc.name))
    }
    private fun actionsFor(doc: HealthDocument) {''',
    "documents orientation launch")
patch(p,
    '''            .setItems(arrayOf("👁 Abrir", "📤 Partilhar / guardar cópia", "✎ Mudar nome", "🗑 Apagar"))''',
    '''            .setItems(arrayOf("👁 Abrir original", "↶ ↷ Rodar / ver orientado",
                "📤 Partilhar / guardar cópia", "✎ Mudar nome", "🗑 Apagar"))''',
    "documents options")
patch(p,
    '''                    1 -> {
                        try {
                            startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).apply {''',
    '''                    1 -> editOrientation(doc)
                    2 -> {
                        try {
                            startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).apply {''',
    "documents actions share shift")
patch(p,
    '''                    2 -> renameDocument(doc)
                    else -> MaterialAlertDialogBuilder''',
    '''                    3 -> renameDocument(doc)
                    else -> MaterialAlertDialogBuilder''',
    "documents actions rename shift")
p=base/"data/HealthDocumentStore.kt"
patch(p,
    '''        file(document).delete()
    }

    private fun file''',
    '''        val original=file(document)
        original.delete()
        File(original.parentFile,original.name+".rotation.json").delete()
    }

    private fun file''',
    "clean document orientation metadata when removed")

# Laboratory reports.
p=base/"ClinicalLabsActivity.kt"
patch(p,
    '''    private lateinit var profileName:String''',
    '''    private lateinit var profileName:String
    private lateinit var activeProfileId:String''',
    "labs selected profile")
patch(p,
    '''        profileName=profile.name
        store=ClinicalLabStore''',
    '''        profileName=profile.name
        activeProfileId=profile.id
        store=ClinicalLabStore''',
    "labs active profile assignment")
patch(p,
    '''            box.addView(button("📄 Abrir documento original"){openOriginal(report)})''',
    '''            box.addView(button("📄 Abrir documento original"){openOriginal(report)})
            box.addView(button("↶ ↷ Corrigir orientação / ver PDF"){
                startActivity(Intent(this,DocumentOrientationActivity::class.java)
                    .putExtra(DocumentOrientationActivity.PROFILE,activeProfileId)
                    .putExtra(DocumentOrientationActivity.GROUP,"labs")
                    .putExtra(DocumentOrientationActivity.FILENAME,report.fileName)
                    .putExtra(DocumentOrientationActivity.TITLE,report.title))
            })''',
    "labs orientation button")
p=base/"labs/ClinicalLabStore.kt"
patch(p,
    '''        File(root,a.fileName).takeIf{it.canonicalFile.parentFile==root.canonicalFile}
            ?.delete()
    }''',
    '''        File(root,a.fileName).takeIf{it.canonicalFile.parentFile==root.canonicalFile}
            ?.let{file->
                file.delete()
                File(root,a.fileName+".rotation.json").delete()
            }
    }''',"labs orientation metadata cleanup")

# Occupational reports: PDF OCR uses saved per-page orientation.
p=base/"WorkMedicineActivity.kt"
patch(p,
    '''import com.mediagenda.app.data.ProfileStore''',
    '''import com.mediagenda.app.data.ProfileStore
import com.mediagenda.app.data.DocumentOrientationStore''',
    "work orientation import")
patch(p,
    '''                box.addView(button("📄 Ver PDF ou imagem original"){openDocument(record)})''',
    '''                box.addView(button("📄 Ver PDF ou imagem original"){openDocument(record)})
                box.addView(button("↶ ↷ Rodar documento / páginas PDF"){
                    openOrientation(record)
                })''',
    "work orientation option")
patch(p,
    '''    private fun openDocument(item:WorkDocument){''',
    '''    private fun openOrientation(item:WorkDocument){
        startActivity(Intent(this,DocumentOrientationActivity::class.java)
            .putExtra(DocumentOrientationActivity.PROFILE,patientId)
            .putExtra(DocumentOrientationActivity.GROUP,"workplace")
            .putExtra(DocumentOrientationActivity.FILENAME,item.filename)
            .putExtra(DocumentOrientationActivity.TITLE,item.name))
    }
    private fun openDocument(item:WorkDocument){''',
    "work orientation launch method")
patch(p,
    '''                        read(index+1,InputImage.fromBitmap(bitmap,0)){
                            bitmap.recycle();next(index+1)
                        }''',
    '''                        val stored=File(filesDir,
                            "saudepratica_workplace/"+patientId+"/"+doc.filename)
                        val oriented=DocumentOrientationStore.forOcr(bitmap,stored,index)
                        read(index+1,InputImage.fromBitmap(oriented,0)){
                            if(oriented!==bitmap)oriented.recycle()
                            bitmap.recycle();next(index+1)
                        }''',
    "work PDF OCR applies page rotation metadata")
# The scanned report variable in this method is named doc, verify from actual file.
# Health expenses: receipts, prescriptions and PDFs share the same editor.
p=base/"HealthExpensesActivity.kt"
patch(p,
    '''    private lateinit var profileName:String''',
    '''    private lateinit var profileName:String
    private lateinit var activeProfileId:String''',
    "expenses profile id")
patch(p,
    '''        profileName=person.name
        vault=HealthExpensesStore''',
    '''        profileName=person.name
        activeProfileId=person.id
        vault=HealthExpensesStore''',
    "expenses profile assignment")
patch(p,
    '''        val actions=arrayOf("👁 Abrir documento","🗑 Eliminar anexo")''',
    '''        val actions=arrayOf("👁 Abrir original",
            "↶ ↷ Corrigir orientação / ver páginas","🗑 Eliminar anexo")''',
    "expenses attachment actions")
patch(p,
    '''                }else{
                    MaterialAlertDialogBuilder(this)
                        .setTitle("Eliminar este anexo?")''',
    '''                }else if(index==1){
                    startActivity(Intent(this,DocumentOrientationActivity::class.java)
                        .putExtra(DocumentOrientationActivity.PROFILE,activeProfileId)
                        .putExtra(DocumentOrientationActivity.GROUP,"expenses")
                        .putExtra(DocumentOrientationActivity.FILENAME,a.name)
                        .putExtra(DocumentOrientationActivity.TITLE,a.title))
                }else{
                    MaterialAlertDialogBuilder(this)
                        .setTitle("Eliminar este anexo?")''',
    "expenses rotate attachment action")

gradle=root/"app/build.gradle.kts"
s=gradle.read_text(encoding="utf-8")
assert 'applicationId = "com.mediagenda.app.stable"' in s
assert 'versionCode = 33' in s and 'versionName = "1.9.23"' in s
gradle.write_text(s.replace('versionCode = 33','versionCode = 34',1)
                  .replace('versionName = "1.9.23"','versionName = "1.9.24"',1),
                  encoding="utf-8")
print("v1.9.24: image rotation and per-page PDF orientation in identity, documents, labs, work and expenses; CC and occupational OCR reuse corrections.")
