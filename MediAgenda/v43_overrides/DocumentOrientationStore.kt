package com.mediagenda.app.data

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.media.ExifInterface
import android.util.AtomicFile
import org.json.JSONObject
import java.io.File

/**
 * Rotation preferences travel alongside private PDFs in the full ZIP backup.
 * Medical PDFs are never modified or re-encoded: signatures/text are preserved.
 */
object DocumentOrientationStore {
    private fun sidecar(file:File)=File(file.parentFile,file.name+".rotation.json")
    fun readAll(file:File):Map<Int,Int>{
        val path=sidecar(file)
        if(!path.isFile || path.length()>50000)return emptyMap()
        return runCatching{
            val obj=JSONObject(path.readText(Charsets.UTF_8))
            buildMap{
                val keys=obj.keys()
                while(keys.hasNext()){
                    val key=keys.next()
                    val page=key.toIntOrNull()?:continue
                    val angle=obj.optInt(key,0)
                    if(page in 0..249 && angle in listOf(0,90,180,270))
                        put(page,angle)
                }
            }
        }.getOrDefault(emptyMap())
    }
    fun angle(file:File,pageIndex:Int=0)=readAll(file)[pageIndex]?:0
    fun writeAll(file:File,values:Map<Int,Int>){
        require(values.keys.all{it in 0..249}&&
            values.values.all{it in listOf(0,90,180,270)}){
            "Orientação inválida."
        }
        val path=sidecar(file)
        val cleaned=values.filterValues{it!=0}
        if(cleaned.isEmpty()){
            if(path.exists())check(path.delete()){"Não foi possível repor a rotação."}
            return
        }
        val json=JSONObject()
        cleaned.toSortedMap().forEach{(key,value)->json.put(key.toString(),value)}
        val atomic=AtomicFile(path)
        val stream=atomic.startWrite()
        try{
            stream.write(json.toString().toByteArray(Charsets.UTF_8))
            atomic.finishWrite(stream)
        }catch(e:Exception){
            atomic.failWrite(stream)
            throw e
        }
    }
    fun exifRotation(file:File):Int=runCatching{
        when(ExifInterface(file.absolutePath).getAttributeInt(
            ExifInterface.TAG_ORIENTATION,ExifInterface.ORIENTATION_NORMAL)){
            ExifInterface.ORIENTATION_ROTATE_90->90
            ExifInterface.ORIENTATION_ROTATE_180->180
            ExifInterface.ORIENTATION_ROTATE_270->270
            else->0
        }
    }.getOrDefault(0)
    fun rotated(bitmap:Bitmap,angle:Int):Bitmap{
        if(angle%360==0)return bitmap
        require(angle%90==0){"Ângulo inválido."}
        return Bitmap.createBitmap(bitmap,0,0,bitmap.width,bitmap.height,
            Matrix().apply{postRotate(angle.toFloat())},true)
    }
    fun forOcr(bitmap:Bitmap,file:File,page:Int=0):Bitmap=
        rotated(bitmap,(angle(file,page)+if(file.extension.lowercase()=="pdf")0
            else exifRotation(file))%360)

    /**
     * Write full orientation into supported image bytes using Android's
     * AtomicFile backup mechanism. Prevent partial writes on interrupted saves.
     */
    fun rewriteImage(file:File,manualAngle:Int){
        require(file.isFile){"Imagem não encontrada."}
        val format=when(file.extension.lowercase()){
            "jpg","jpeg"->Bitmap.CompressFormat.JPEG
            "png"->Bitmap.CompressFormat.PNG
            "webp"->Bitmap.CompressFormat.WEBP
            else->error("Este formato guarda a orientação sem regravar os píxeis.")
        }
        val bounds=BitmapFactory.Options().apply{inJustDecodeBounds=true}
        BitmapFactory.decodeFile(file.absolutePath,bounds)
        require(bounds.outWidth in 1..15000&&bounds.outHeight in 1..15000){
            "Tamanho da imagem não suportado."
        }
        var sample=1
        val max=4500
        while(bounds.outWidth/sample>max||bounds.outHeight/sample>max)sample*=2
        val decoded=BitmapFactory.decodeFile(file.absolutePath,
            BitmapFactory.Options().apply{
                inSampleSize=sample
                inPreferredConfig=Bitmap.Config.ARGB_8888
            })?:error("Não foi possível abrir a fotografia.")
        val corrected=rotated(decoded,(manualAngle+exifRotation(file))%360)
        try{
            val atomic=AtomicFile(file)
            val stream=atomic.startWrite()
            try{
                check(corrected.compress(format,if(format==Bitmap.CompressFormat.PNG)
                    100 else 94,stream)){
                    "Não foi possível guardar os píxeis rodados."
                }
                atomic.finishWrite(stream)
            }catch(e:Exception){
                atomic.failWrite(stream)
                throw e
            }
        }finally{
            if(corrected!==decoded)corrected.recycle()
            decoded.recycle()
        }
    }
}
