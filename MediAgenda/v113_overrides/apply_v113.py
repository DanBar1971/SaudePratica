"""SaúdePrática v1.9.94 Fase D — original PDF/image vault and clinic search.
Implemented directly in existing Kotlin, using Android SAF, PdfRenderer, ML Kit
and original HealthcareCatalog. Do not import unlicensed PDF Scanner code.
"""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"

def change(rel,old,new,label):
    file=base/rel
    source=file.read_text(encoding="utf-8")
    n=source.count(old)
    if n!=1:raise RuntimeError("Fase D "+label+" anchors "+str(n))
    file.write_text(source.replace(old,new,1),encoding="utf-8")

# 1: universally archive original PDF and image bytes and deduplicate via SHA256.
# File metadata is unchanged so old backups and internal PDF viewer still work.
change("data/HealthDocumentStore.kt",
'''    /** Archives an original PDF in the active user's Documents vault.
     * Re-importing identical PDF bytes does not create duplicate entries.
     * This is separate from OCR: the complete original PDF is kept.
     * Returns true only when a new document was added.
     */
    fun archivePdfIfMissing(uri: Uri, title: String = suggestedName(uri)): Boolean {
        if (mime(uri).first != "application/pdf") return false''',
'''    /** Store the EXACT original PDF or image before OCR transforms it.
     * SHA-256 deduplicates each format, never mixes family profiles.
     * On-screen rotations and OCR crops are never substituted for originals.
     */
    fun archiveIfMissing(uri: Uri, title: String = suggestedName(uri)): Boolean {
        val incomingMime=mime(uri).first''',"general original-document archive")

change("data/HealthDocumentStore.kt",
'''            if (document.mimeType != "application/pdf") continue''',
'''            if (document.mimeType != incomingMime) continue''',
"dedup matching media type")

change("data/HealthDocumentStore.kt",
'''        add(uri, title)
        return true
    }

    fun rename(document: HealthDocument, title: String) {''',
'''        add(uri, title)
        return true
    }

    /** Compatibility: previous callers expecting only PDF keep their contract. */
    fun archivePdfIfMissing(uri:Uri,title:String=suggestedName(uri)):Boolean =
        if(mime(uri).first=="application/pdf")archiveIfMissing(uri,title) else false

    fun rename(document: HealthDocument, title: String) {''',
"backward compatibility existing pdf imports")

# 2: archive both PDF and IMG at the common medication/appointment OCR
# entrypoint. PDF renderer uses the same original source, never stores a
# temporary rendered PNG as another document.
change("MainActivity.kt",
'''    private fun importHealthDocument(uri: Uri, purpose: String) {
        val mime = contentResolver.getType(uri).orEmpty()
        if (mime != "application/pdf" && !uri.toString().lowercase().endsWith(".pdf")) {
            processImportedHealthImage(uri, purpose)
            return
        }''',
'''    private fun importHealthDocument(uri: Uri, purpose: String) {
        try {
            val store=com.mediagenda.app.data.HealthDocumentStore(this,activeProfileId)
            val added=store.archiveIfMissing(uri,store.suggestedName(uri))
            if(added)Toast.makeText(this,
                "Original PDF/imagem guardado em Documentos Digitais.",
                Toast.LENGTH_LONG).show()
        }catch(problem:Exception){
            showError("A importação foi interrompida para não perder o original: "+
                problem.message)
            return
        }
        val mime = contentResolver.getType(uri).orEmpty()
        if (mime != "application/pdf" && !uri.toString().lowercase().endsWith(".pdf")) {
            processImportedHealthImage(uri, purpose)
            return
        }''',"archive each document before OCR")

change("MainActivity.kt",
'''                    val documentStore = com.mediagenda.app.data.HealthDocumentStore(
                        this, activeProfileId)
                    val added = documentStore.archivePdfIfMissing(
                        uri, documentStore.suggestedName(uri))
                    if (added) Toast.makeText(this,
                        "PDF original guardado em Documentos Digitais.",
                        Toast.LENGTH_LONG).show()''',
'''                    // Already archived at import entry before opening renderer.
                    // OCR must never store a rendered page as a second original.''',
"prevent repeated PDF scan")

# 3: occupational medical documents and lab reports also archive images.
change("WorkMedicineActivity.kt",
'''                            this, patientId).archivePdfIfMissing(uri,title)''',
'''                            this, patientId).archiveIfMissing(uri,title)''',
"occupational both pdf and images")

change("ClinicalLabsActivity.kt",
'''                        if (mime == "application/pdf") {
                            runCatching {
                                com.mediagenda.app.data.HealthDocumentStore(
                                    this,activeProfileId).archivePdfIfMissing(uri,name)
                            }.onFailure { problem ->
                                notify("Relatório guardado em Análises, mas não foi possível " +
                                    "arquivar o PDF em Documentos Digitais: " + problem.message)
                            }
                        }''',
'''                        runCatching {
                            com.mediagenda.app.data.HealthDocumentStore(
                                this,activeProfileId).archiveIfMissing(uri,name)
                        }.onFailure { problem ->
                            notify("Relatório guardado em Análises, mas não foi possível " +
                                "arquivar o original em Documentos Digitais: " +
                                problem.message)
                        }''',
"clinical lab pdf and image original")

# 4: sharing multiple PDFs or images from e-mail/files is importable.
# No third-party provider service or permission to list entire user storage.
change("DocumentsActivity.kt",
'''        val shared = sharedUri(intent)
        val requested = intent.getStringExtra(EXTRA_PROFILE_ID)''',
'''        val shared = sharedUri(intent)
        val multiple = sharedUris(intent)
        val requested = intent.getStringExtra(EXTRA_PROFILE_ID)
        if(multiple.size>1){
            if(users.size>1){
                MaterialAlertDialogBuilder(this).setTitle("Arquivar documentos para...")
                    .setItems(users.map{it.name}.toTypedArray()){_,index->
                        choose(users[index]);archiveSharedBatch(multiple)
                    }.setNegativeButton("Cancelar"){_,_->finish()}.show()
            }else{
                choose(users.first());archiveSharedBatch(multiple)
            }
            return
        }''',
"multi-file share flow")

change("DocumentsActivity.kt",
'''    private fun sharedUri(incoming: Intent?): Uri? {''',
'''    private fun sharedUris(incoming:Intent?):List<Uri>{
        if(incoming?.action!=Intent.ACTION_SEND_MULTIPLE)return emptyList()
        val kind=incoming.type.orEmpty().lowercase()
        if(kind!="application/pdf" && kind!="*/*" && !kind.startsWith("image/"))
            return emptyList()
        @Suppress("DEPRECATION")
        val supplied=incoming.getParcelableArrayListExtra<Uri>(Intent.EXTRA_STREAM)
            .orEmpty()
        val clips=incoming.clipData?.let{clip->
            (0 until clip.itemCount.coerceAtMost(20)).mapNotNull{clip.getItemAt(it).uri}
        }.orEmpty()
        return (supplied+clips).distinct().take(20)
    }

    private fun archiveSharedBatch(uris:List<Uri>){
        var added=0
        val errors=mutableListOf<String>()
        for(uri in uris){
            runCatching{
                if(store.archiveIfMissing(uri,store.suggestedName(uri)))added++
            }.onFailure{errors.add(it.message?:"Ficheiro inválido")}
        }
        refresh()
        MaterialAlertDialogBuilder(this).setTitle("Importação de documentos")
            .setMessage("$added original(is) guardado(s) para "+profile.name+
                if(errors.isNotEmpty())"\\nNão foi possível importar "+
                    errors.size+" ficheiro(s): "+errors.first() else "")
            .setPositiveButton("OK",null).show()
    }

    private fun sharedUri(incoming: Intent?): Uri? {''',
"batch sharing import")

manifest=root/"app/src/main/AndroidManifest.xml"
m=manifest.read_text(encoding="utf-8")
old='''                <action android:name="android.intent.action.SEND" />'''
assert m.count(old)==1
m=m.replace(old,old+'''
                <action android:name="android.intent.action.SEND_MULTIPLE" />''',1)
manifest.write_text(m,encoding="utf-8")

# 5: release version only. All existing activities/graphics stay unchanged.
gradle=root/"app/build.gradle.kts"
g=gradle.read_text(encoding="utf-8")
assert g.count("versionCode = 103")==1
assert g.count('versionName = "1.9.93"')==1
gradle.write_text(g.replace("versionCode = 103","versionCode = 104",1)
    .replace('versionName = "1.9.93"','versionName = "1.9.94"',1),
    encoding="utf-8")
print("Fase D v1.9.94: universal PDF/image archiving + batch share + clinical imports")
