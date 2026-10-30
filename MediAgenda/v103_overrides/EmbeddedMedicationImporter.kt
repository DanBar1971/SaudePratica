package com.mediagenda.app.data

import android.content.Context
import android.graphics.BitmapFactory
import android.util.Base64
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.security.MessageDigest
import java.util.UUID

/** Import medication photos embedded in a portable JSON file, locally per profile. */
internal object EmbeddedMedicationImporter {
    fun materialize(context:Context, profileId:String, root:JSONObject):Int {
        val payload=root.optJSONObject("embedded_medication_images") ?: return 0
        val meds=root.optJSONArray("medications") ?: error("Faltam medicamentos no ficheiro.")
        val dir=File(context.filesDir,"medication_photos").canonicalFile
        require(dir.isDirectory||dir.mkdirs()) {"Pasta privada de fotografias indisponível."}
        val paths=linkedMapOf<String,String>()
        val staged=mutableListOf<Pair<File,File>>()
        var size=0L
        try {
            val keys=payload.keys()
            while(keys.hasNext()){
                val name=keys.next()
                require(name.length in 5..120 && !name.contains("..") &&
                    name.matches(Regex("[A-Za-z0-9._ -]+[.](png|jpg|jpeg)",RegexOption.IGNORE_CASE))) {
                    "Nome de fotografia inválido: $name"
                }
                val asset=payload.optJSONObject(name) ?: error("Fotografia em falta: $name")
                val mime=asset.optString("mime_type")
                require(mime=="image/png"||mime=="image/jpeg") {"Tipo de imagem inválido."}
                val encoded=asset.optString("data_base64")
                require(encoded.length in 100..7_000_000) {"Fotografia $name demasiado grande."}
                val raw=try { Base64.decode(encoded,Base64.DEFAULT) }
                        catch(_:Exception){ error("Fotografia $name ilegível.") }
                size+=raw.size
                require(raw.size in 100..5_000_000 && size<=20_000_000){"Fotos demasiado grandes."}
                val png=raw.size>=8 && raw.copyOfRange(0,8).contentEquals(
                    byteArrayOf(137.toByte(),80,78,71,13,10,26,10))
                val jpeg=raw.size>=3 && raw[0]==0xff.toByte() &&
                    raw[1]==0xd8.toByte() && raw[2]==0xff.toByte()
                require((mime=="image/png" && png)||(mime=="image/jpeg" && jpeg)){
                    "Fotografia $name com formato incorreto."
                }
                val opts=BitmapFactory.Options().apply{inJustDecodeBounds=true}
                BitmapFactory.decodeByteArray(raw,0,raw.size,opts)
                require(opts.outWidth in 1..10000 && opts.outHeight in 1..10000){
                    "Dimensões de fotografia inválidas."
                }
                val digest=MessageDigest.getInstance("SHA-256").digest(raw)
                    .joinToString(""){ "%02x".format(it.toInt() and 0xff) }
                require(asset.optString("sha256").equals(digest,true)) {
                    "Fotografia $name incompleta ou alterada."
                }
                val id=profileId.replace(Regex("[^A-Za-z0-9_-]"),"_").take(50)
                val dest=File(dir,"medimport_${id}_${digest.take(32)}.${if(png)"png" else "jpg"}")
                if(!dest.isFile){
                    val temp=File(dir,".medimport_${UUID.randomUUID()}.tmp")
                    temp.writeBytes(raw)
                    staged.add(temp to dest)
                }
                paths[name]=dest.absolutePath
                require(paths.size<=40){"Demasiadas fotografias para importar."}
            }
            // Verify references from every medicine before publishing image files.
            for(i in 0 until meds.length()) {
                val med=meds.optJSONObject(i)?:error("Medicamento ilegível.")
                val refs=med.optJSONArray("embedded_image_names") ?: continue
                val images=med.optJSONArray("images")?:JSONArray()
                for(j in 0 until refs.length()){
                    val file=paths[refs.optString(j)]?:error("Fotografia associada em falta.")
                    if((0 until images.length()).none { images.optString(it)==file }) images.put(file)
                }
                med.put("images",images)
                med.remove("embedded_image_names")
            }
            for((tmp,out) in staged){
                if(!out.exists() && !tmp.renameTo(out))error("Não foi possível copiar imagens.")
                if(tmp.exists())tmp.delete()
            }
            root.remove("embedded_medication_images")
            root.remove("import_info")
            return paths.size
        } finally {
            staged.forEach{(tmp,_)->if(tmp.exists())tmp.delete()}
        }
    }
}
