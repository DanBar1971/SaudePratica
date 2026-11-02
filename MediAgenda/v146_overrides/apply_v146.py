#!/usr/bin/env python3
"""Android v1.9.126: reject metadata-only backups and preserve media.

Do not touch alarm source, schedule, medication model or PIN preferences.
Additional profile-scope restore requires clinical conflict checks before release.
"""
from pathlib import Path
from hashlib import sha256
app=Path("build-src/MediAgenda_Android_v1/app")
src=app/"src/main/java/com/mediagenda/app"
family=src/"data/FamilyBackupStore.kt"
portable=src/"data/PortableWindowsBackup.kt"
s=family.read_text(encoding="utf-8")
p=portable.read_text(encoding="utf-8")
def once(text,a,b,label):
    n=text.count(a)
    if n!=1:raise AssertionError((label,n))
    return text.replace(a,b,1)

s=once(s,"    fun export(destination:Uri):FamilyBackupSummary {\n        val files=paths()",
'''    fun export(destination:Uri):FamilyBackupSummary {
        val allProfiles=ProfileStore(context).all()
        require(allProfiles.isNotEmpty()){"Não existem perfis para guardar."}
        // Fail closed when original source files are missing. Never create empty replacements.
        for(person in allProfiles){
            val prefix=if(person.id=="legacy")"" else
                "saudepratica_profiles/"+person.id+"/"
            // NEVER call ensureFiles(): it would CREATE empty med/agenda
            // documents and camouflage missing patient records.
            require(File(root,prefix+"medicacao.json").isFile &&
                    File(root,prefix+"agenda.json").isFile){
                "Ficheiros clínicos em falta para "+person.name+
                ". Exportação cancelada para evitar um ZIP de 5 KB."
            }
        }
        val files=paths()
        for(person in allProfiles){
            val prefix=if(person.id=="legacy")"" else
                "saudepratica_profiles/"+person.id+"/"
            require(files.any{it.first==prefix+"medicacao.json"} &&
                    files.any{it.first==prefix+"agenda.json"}){
                "Falha no backup: medicação ou agenda de "+person.name+
                " não foi incluída. Nada foi anunciado como guardado."
            }
        }
        // If a medication references a local photo, the original must be
        // present; never claim a full backup without its photographs.
        val included=files.map{it.first}.toSet()
        for(person in allProfiles){
            val meds=org.json.JSONObject(
                DataRepository(context,person.id).medicationJson())
                .optJSONArray("medications")?:org.json.JSONArray()
            for(i in 0 until meds.length()){
                val photos=meds.optJSONObject(i)?.optJSONArray("images")?:continue
                for(j in 0 until photos.length()){
                    val reference=photos.optString(j)
                    val filename=reference.substringBefore('?').substringAfterLast('/')
                    if(filename.matches(Regex("[A-Za-z0-9_.-]{1,140}")) &&
                        reference.contains("medication_photos") &&
                        "medication_photos/"+filename !in included){
                        error("Fotografia do medicamento ausente do backup: "+
                            filename+". Exportação cancelada.")
                    }
                }
            }
        }''',"complete source data preflight")
family.write_text(s,encoding="utf-8")

p=once(p,"import android.util.Base64",
'''import android.util.Base64
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import java.io.ByteArrayOutputStream''',"safe thumbnail imports")
p=once(p,"    private data class Part(",
'''    private fun thumb(image:ByteArray):String{
        if(image.size !in 100..16_000_000)return ""
        return runCatching{
            val bounds=BitmapFactory.Options().apply{inJustDecodeBounds=true}
            BitmapFactory.decodeByteArray(image,0,image.size,bounds)
            require(bounds.outWidth in 1..10000 && bounds.outHeight in 1..10000)
            var sample=1
            while(bounds.outWidth/sample>1400 || bounds.outHeight/sample>1400)
                sample*=2
            val picture=BitmapFactory.decodeByteArray(image,0,image.size,
                BitmapFactory.Options().apply{inSampleSize=sample})
                ?:return@runCatching ""
            try{
                val output=ByteArrayOutputStream()
                for(quality in listOf(85,70,55,40)){
                    output.reset()
                    picture.compress(Bitmap.CompressFormat.JPEG,quality,output)
                    if(output.size()<=400_000)break
                }
                if(output.size()>400_000)"" else
                    Base64.encodeToString(output.toByteArray(),Base64.NO_WRAP)
            }finally{picture.recycle()}
        }.getOrDefault("")
    }
    private fun photo(file:File):String{
        if(!file.isFile || file.length() !in 100..16_000_000)return ""
        return thumb(file.readBytes())
    }
    private data class Part(''',"preview thumbnails")
p=once(p,'''                value.put("time",original.optString("reminder_time",
                    original.optString("time","")))''',
'''                value.put("time",original.optString("reminder_time",
                    original.optString("time","")))
                val refs=original.optJSONArray("images")
                if(refs!=null)for(j in 0 until refs.length()){
                    val filename=refs.optString(j).substringBefore('?')
                        .substringAfterLast('/')
                    if(!filename.matches(Regex("[A-Za-z0-9_.-]{1,140}")))continue
                    val preview=photo(File(context.filesDir,
                        "medication_photos/"+filename))
                    if(preview.isNotEmpty()){
                        value.put("photo_b64",preview)
                        break
                    }
                }''',"medication photo preview")
p=once(p,'''                val meta=JSONObject().put("id",winIds[i]).put("name",p.name)
                    .put("android_zip_source_id",p.id)
                    .put("android_zip_source_name",p.name)
                    .put("android_profile_original",JSONObject()
                        .put("id",p.id).put("name",p.name))''',
'''                val meta=JSONObject().put("id",winIds[i]).put("name",p.name)
                    .put("android_zip_source_id",p.id)
                    .put("android_zip_source_name",p.name)
                    .put("android_profile_original",JSONObject()
                        .put("id",p.id).put("name",p.name))
                val avatar=photo(File(context.filesDir,
                    "saudepratica_identity/"+p.id+"/avatar.jpg"))
                if(avatar.isNotEmpty())meta.put("photo_b64",avatar)''',"profile avatar")
p=once(p,'''            parts+=Part("attachments/"+digest.take(2)+"/"+digest+".bin",file=source)''',
'''            // Add actual images and digital documents as Windows-restorable
            // SHA-256 attachments, not empty attachments.json placeholders.
            val perPerson=profiles.associate{it.id to JSONArray()}.toMutableMap()
            val blobs=linkedMapOf<String,Part>()
            java.util.zip.ZipFile(source).use{archive->
                val entries=archive.entries()
                val photoRefs=profiles.associate{person->
                    val out=mutableSetOf<String>()
                    val meds=org.json.JSONObject(
                        DataRepository(context,person.id).medicationJson())
                        .optJSONArray("medications")?:JSONArray()
                    for(i in 0 until meds.length()){
                        val images=meds.optJSONObject(i)?.optJSONArray("images")?:continue
                        for(j in 0 until images.length()){
                            val filename=images.optString(j).substringBefore('?')
                                .substringAfterLast('/')
                            if(filename.matches(Regex("[A-Za-z0-9_.-]{1,140}")))
                                out.add("medication_photos/"+filename)
                        }
                    }
                    person.id to out
                }
                while(entries.hasMoreElements()){
                    val entry=entries.nextElement()
                    if(entry.isDirectory||!entry.name.startsWith("data/"))continue
                    if(entry.size !in 1..16_000_000)continue
                    val name=entry.name.removePrefix("data/")
                    if(!name.matches(Regex("[A-Za-z0-9_./-]{3,210}")))continue
                    val owner=profiles.firstOrNull{person->
                        name in (photoRefs[person.id]?:emptySet<String>()) ||
                        name.startsWith("saudepratica_identity/"+person.id+"/") ||
                        name.startsWith("saudepratica_documents/"+person.id+"/") ||
                        name.startsWith("saudepratica_labs/"+person.id+"/") ||
                        name.startsWith("saudepratica_workplace/"+person.id+"/")
                    }?:continue
                    if(name.endsWith(".json"))continue
                    val bytes=archive.getInputStream(entry).use{it.readBytes()}
                    require(bytes.size.toLong()==entry.size){"Anexo incompleto."}
                    val hash=sha(bytes)
                    val asset="attachments/"+hash.take(2)+"/"+hash+".bin"
                    blobs.putIfAbsent(asset,Part(asset,bytes))
                    perPerson[owner.id]!!.put(JSONObject()
                        .put("profile_id",winIds[profiles.indexOf(owner)])
                        .put("path",name)
                        .put("filename",name.substringAfterLast('/'))
                        .put("display_name",name.substringAfterLast('/'))
                        .put("category",if(name.startsWith("medication_photos/"))
                            "fotografia de medicamento" else "documento")
                        .put("sha256",hash).put("bytes",bytes.size))
                }
            }
            for(i in profiles.indices){
                val key="profiles/"+winIds[i]+"/attachments.json"
                val pos=parts.indexOfFirst{it.path==key}
                require(pos>=0){"Índice de fotografias em falta."}
                parts[pos]=Part(key,bytes(perPerson[profiles[i].id]!!.toString()))
            }
            parts.addAll(blobs.values)
            parts+=Part("attachments/"+digest.take(2)+"/"+digest+".bin",file=source)''',"actual media attachments")
portable.write_text(p,encoding="utf-8")

gradle=app/"build.gradle.kts"
g=gradle.read_text(encoding="utf-8")
assert g.count('versionName = "1.9.125"')==1
assert g.count("versionCode = 135")==1
g=g.replace('versionName = "1.9.125"','versionName = "1.9.126"',1)
g=g.replace("versionCode = 135","versionCode = 136",1)
gradle.write_text(g,encoding="utf-8")
print("Backup inspection: clinical files must exist; Windows portraits and medication photos included.")
