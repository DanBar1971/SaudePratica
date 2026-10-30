from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"

def patch(file,old,new,label):
    text=file.read_text(encoding="utf-8")
    if text.count(old)!=1:
        raise RuntimeError("v1.9.25: "+label+" anchor not found uniquely: "+str(text.count(old)))
    file.write_text(text.replace(old,new,1),encoding="utf-8")

(base/"data/MedicationPhotoLoader.kt").write_text(
    Path("MediAgenda/v44_overrides/MedicationPhotoLoader.kt")
    .read_text(encoding="utf-8"),encoding="utf-8")

main=base/"MainActivity.kt"
patch(main,
    'import com.mediagenda.app.data.ProfileMediaStore',
    'import com.mediagenda.app.data.ProfileMediaStore\nimport com.mediagenda.app.data.MedicationPhotoLoader',
    "loader import")

patch(main,
    'val address=input("Email do destinatário (opcional)","")',
    '''val registeredEmail=getSharedPreferences(
            profiles.preferencesFor(activeProfileId),MODE_PRIVATE)
            .getString("email","").orEmpty().trim()
        val recipient=registeredEmail.takeIf{
            it.isNotBlank() &&
            android.util.Patterns.EMAIL_ADDRESS.matcher(it).matches()
        }.orEmpty()
        val address=input("Email do destinatário (opcional)",recipient)''',
    "appointment recipient from current profile")

patch(main,
    '''                file.outputStream().use {
                    check(bitmap.compress(android.graphics.Bitmap.CompressFormat.JPEG,86,it))
                }
                if(bitmap!==original)bitmap.recycle()''',
    '''                file.outputStream().use {
                    check(bitmap.compress(android.graphics.Bitmap.CompressFormat.JPEG,86,it))
                }
                check(file.length()>128L &&
                    MedicationPhotoLoader.decode(this,file.absolutePath,320)!=null){
                    "A imagem escolhida não é legível. Seleciona outra."
                }
                if(bitmap!==original)bitmap.recycle()''',
    "validate medication gallery image")

old='''        h.pill.visibility=View.VISIBLE
        h.thumbnail.visibility=View.GONE
        h.thumbnail.setImageDrawable(null)
        m.images.firstOrNull()?.let { source ->
            try {
                val uri=Uri.parse(source)
                val options=android.graphics.BitmapFactory.Options().apply { inSampleSize=8 }
                val bmp=h.card.context.contentResolver.openInputStream(uri)?.use {
                    android.graphics.BitmapFactory.decodeStream(it,null,options)
                }
                if(bmp != null) {
                    h.thumbnail.setImageBitmap(bmp)
                    h.thumbnail.visibility=View.VISIBLE
                    h.pill.visibility=View.GONE
                }
            } catch (_:Exception) {}
        }'''
new='''        h.pill.visibility=View.VISIBLE
        h.thumbnail.visibility=View.GONE
        h.thumbnail.setImageDrawable(null)
        h.thumbnail.tag=m.id
        if(m.images.isNotEmpty()){
            val images=m.images.toList()
            val id=m.id
            val context=h.card.context.applicationContext
            imageWorkers.execute{
                val bitmap=MedicationPhotoLoader.load(context,images,320)
                imageUi.post{
                    if(h.thumbnail.tag==id){
                        if(bitmap!=null){
                            h.thumbnail.setImageBitmap(bitmap)
                            h.thumbnail.visibility=View.VISIBLE
                            h.pill.visibility=View.GONE
                        }
                    }else bitmap?.recycle()
                }
            }
        }'''
patch(main,old,new,"render newest readable image instead of emoji")

patch(main,
    '''):RecyclerView.Adapter<MedicationAdapter.H>() {
    class H(''',
    '''):RecyclerView.Adapter<MedicationAdapter.H>() {
    companion object {
        private val imageWorkers=java.util.concurrent.Executors.newFixedThreadPool(2)
        private val imageUi=android.os.Handler(android.os.Looper.getMainLooper())
    }
    class H(''',
    "thumbnail background executor")

# Add a preview in the medication record, so the user can confirm which photo
# was really saved, and diagnose a stale URI without touching prescription data.
patch(main,
    '''                box.addView(noteBox("Fotografias guardadas",''',
    '''                box.addView(secondaryButton("👁 Ver imagem da embalagem"){
                    val photos=repo.loadMedications().firstOrNull{
                        it.id==existing.id
                    }?.images.orEmpty()
                    val preview=MedicationPhotoLoader.load(this,photos,1200)
                    if(preview==null){
                        showError("Esta fotografia já não está acessível. "+
                            "Escolhe novamente a imagem da embalagem.")
                    }else{
                        val photo=android.widget.ImageView(this).apply{
                            scaleType=android.widget.ImageView.ScaleType.FIT_CENTER
                            adjustViewBounds=true
                            setImageBitmap(preview)
                        }
                        MaterialAlertDialogBuilder(this)
                            .setTitle("Imagem da embalagem")
                            .setView(photo)
                            .setPositiveButton("Fechar",null)
                            .setOnDismissListener{
                                photo.setImageDrawable(null)
                                preview.recycle()
                            }.show()
                    }
                })
                box.addView(noteBox("Fotografias guardadas",''',
    "show attached photo in medication form")

patch(main,
    '''            openUrl("https://www.infarmed.pt/web/infarmed/servicos-on-line")''',
    '''            openUrl("https://extranet.infarmed.pt/INFOMED-fo/")''',
    "open real Infomed")

patch(main,
    '''        box.addView(secondaryButton("📖 Procurar folheto · INFARMED"){
            openUrl("https://www.google.com/search?q="+Uri.encode(
                "site:infarmed.pt "+term+" folheto informativo RCM"))
        })''',
    '''        box.addView(secondaryButton("🔎 Pesquisar FI e ficha técnica · INFARMED"){
            // Search is prefilled with the medication's name and dose.
            // The result must be verified by brand, strength and packaging.
            openUrl("https://www.google.com/search?q="+Uri.encode(
                "site:infarmed.pt/documents/ "+term+
                " (folheto informativo OR resumo características medicamento)"))
        })
        box.addView(secondaryButton("🇪🇺 Pesquisar Agência Europeia (EMA)"){
            openUrl("https://www.google.com/search?q="+Uri.encode(
                "site:ema.europa.eu/pt/medicines "+term+
                " folheto informação medicamento"))
        })''',
    "search official medicine documentation in one click")

patch(main,
    '''        box.addView(noteBox("Fotografias da Internet",''',
    '''        box.addView(noteBox("Infomed e fichas técnicas",
            "O Infomed é a base oficial portuguesa para pesquisar "+
            "medicamentos, FI e RCM. A pesquisa FI/RCM já é feita "+
            "automaticamente por nome e dose nos documentos públicos. "+
            "A base Infomed abre diretamente no sítio oficial, pois "+
            "não existe uma API pública livre documentada para "+
            "consultar diretamente todas as fichas."))
        box.addView(noteBox("Fotografias da Internet",''',
    "avoid implying proprietary API access")

gradle=root/"app/build.gradle.kts"
text=gradle.read_text(encoding="utf-8")
assert 'applicationId = "com.mediagenda.app.stable"' in text
assert text.count('versionCode = 34')==1 and text.count('versionName = "1.9.24"')==1
gradle.write_text(text.replace('versionCode = 34','versionCode = 35',1)
    .replace('versionName = "1.9.24"','versionName = "1.9.25"',1),encoding="utf-8")
print("v1.9.25: appointment emails auto-fill from active profile; medication thumbnails use newest readable photo; real Infomed and prefilled official FI/RCM search.")
