from pathlib import Path

root=Path('build-src/MediAgenda_Android_v1')
base=root/'app/src/main/java/com/mediagenda/app'

def replace_once(path, old, new, label):
    txt=path.read_text(encoding='utf-8')
    count=txt.count(old)
    if count!=1:raise RuntimeError(f'{label}: expected exactly one anchor, found {count}')
    path.write_text(txt.replace(old,new,1),encoding='utf-8')

loader=base/'data/MedicationPhotoLoader.kt'
replace_once(loader,
'''        val file=when(uri.scheme){
            null -> File(value)
            "file"->File(uri.path?:return null)
            else->null
        }
''',
'''        val allowed=File(context.filesDir,"medication_photos").canonicalFile
        // Earlier versions saved an internal FileProvider URI rather than a
        // stable file path. Recover that same private JPEG directly by its
        // filename, even when ContentResolver cannot reopen the old URI.
        val internalContent=uri.scheme=="content" &&
            uri.authority==context.packageName+".fileprovider"
        val candidate=when(uri.scheme){
            null -> File(value)
            "file" -> File(uri.path?:return null)
            "content" -> if(internalContent)
                File(allowed,uri.lastPathSegment.orEmpty()) else null
            else -> null
        }
        val file=if(candidate!=null &&
            candidate.canonicalFile.parentFile==allowed &&
            candidate.isFile) candidate else if(uri.scheme=="content") null
            else return null
''', 'legacy content uri recovery')
replace_once(loader,
'''        if(file!=null){
            val allowed=File(context.filesDir,"medication_photos").canonicalFile
            if(file.canonicalFile.parentFile!=allowed)return null
        } else {
            // Do not load arbitrary websites or network URLs from saved JSON.
            if(uri.scheme!="content")return null
        }
''',
'''        // Never open files outside the app-private medication photo folder.
        if(file==null && uri.scheme!="content") return null
''', 'allow fallback to contentresolver')

# New photos are saved with a local path, not the transient FileProvider URI.
main=base/'MainActivity.kt'
replace_once(main,
'''                val local=FileProvider.getUriForFile(this,
                    BuildConfig.APPLICATION_ID+".fileprovider",file).toString()
                if(local !in stored[index].images)stored[index].images.add(local)
''',
'''                val local=file.absolutePath
                if(local !in stored[index].images)stored[index].images.add(local)
''', 'store stable private photo path')

replace_once(main,
'''        val photos = med.images.toMutableList()
        if (!photos.contains(uri.toString())) photos.add(uri.toString())
''',
'''        val photos = med.images.toMutableList()
        // Camera image was created inside the app's private folder; save its
        // file path so it remains readable by list, form and alarms.
        val source=uri.lastPathSegment.orEmpty()
        val stored=File(filesDir,"medication_photos/$source").canonicalFile
        val allowed=File(filesDir,"medication_photos").canonicalFile
        val saved=if(uri.authority==BuildConfig.APPLICATION_ID+".fileprovider" &&
            stored.parentFile==allowed && stored.isFile)
            stored.absolutePath else uri.toString()
        if (!photos.contains(saved)) photos.add(saved)
''', 'camera photo stable path')

# In-app record directly presents the packaging image, not just a "view" button.
replace_once(main,
'''            if (existing.images.isNotEmpty()) {
                box.addView(secondaryButton("👁 Ver imagem da embalagem"){
''',
'''            if (existing.images.isNotEmpty()) {
                val photos=repo.loadMedications().firstOrNull {
                    it.id==existing.id
                }?.images.orEmpty()
                val thumb=MedicationPhotoLoader.load(this,photos,750)
                if(thumb!=null){
                    box.addView(android.widget.TextView(this).apply {
                        text="Fotografia da embalagem"
                        textSize=16f
                        setTypeface(typeface,android.graphics.Typeface.BOLD)
                        setPadding(dp(4),dp(14),dp(4),dp(8))
                    })
                    box.addView(android.widget.ImageView(this).apply {
                        scaleType=android.widget.ImageView.ScaleType.FIT_CENTER
                        adjustViewBounds=true
                        setImageBitmap(thumb)
                        layoutParams=LinearLayout.LayoutParams(
                            ViewGroup.LayoutParams.MATCH_PARENT,dp(196))
                        contentDescription="Fotografia da embalagem do medicamento"
                    })
                } else {
                    box.addView(noteBox("Fotografia indisponível",
                        "A imagem está associada mas não pôde ser aberta. " +
                        "Podes anexar novamente a fotografia da embalagem."))
                }
                box.addView(secondaryButton("👁 Ver imagem da embalagem"){
''', 'medication form inline photo preview')

# Make packaging recognizable at a glance in medication list.
replace_once(main,
'''            layoutParams=LinearLayout.LayoutParams(dp(44),dp(44))
            visibility=View.GONE
''',
'''            layoutParams=LinearLayout.LayoutParams(dp(72),dp(72))
            background=GradientDrawable().apply {
                setColor(Color.parseColor("#E6F4F1"))
                cornerRadius=dp(12).toFloat()
            }
            clipToOutline=true
            contentDescription="Fotografia da embalagem"
            visibility=View.GONE
''', 'larger thumbnail in medication list')

gradle=root/'app/build.gradle.kts'
replace_once(gradle,'versionCode = 36','versionCode = 37','versionCode')
replace_once(gradle,'versionName = "1.9.26"','versionName = "1.9.27"','versionName')
print('v1.9.27: stable private packaging photo paths, legacy URI fallback, inline medication photo and 72dp medication list photo')
