package com.mediagenda.app.data

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.media.ExifInterface
import android.net.Uri
import java.io.File

/**
 * Copies selected photographs into private app storage for the selected profile.
 * Re-encodes to JPEG, strips source metadata and never exposes identity photos
 * through a FileProvider or to another application.
 */
class ProfileMediaStore(private val context:Context, profileId:String) {
    private val id=profileId.also {
        require(it=="legacy"||it.matches(Regex("[0-9a-fA-F-]{36}"))){
            "Perfil inválido."
        }
    }
    private val folder=File(context.filesDir,"saudepratica_identity/$id").apply {
        if(!exists()&&!mkdirs())error("Não foi possível criar a pasta privada.")
    }
    private fun file(kind:String):File {
        require(kind in setOf("avatar","cc_front","cc_back")){"Tipo de fotografia inválido."}
        return File(folder,"$kind.jpg")
    }
    fun exists(kind:String)=file(kind).isFile()
    fun remove(kind:String):Boolean = !file(kind).exists()||file(kind).delete()

    fun photo(kind:String,maximum:Int=600):Bitmap? {
        val source=file(kind)
        if(!source.isFile())return null
        return runCatching {
            val options=BitmapFactory.Options().apply{inJustDecodeBounds=true}
            BitmapFactory.decodeFile(source.absolutePath,options)
            require(options.outWidth>0&&options.outHeight>0)
            var sample=1
            while(options.outWidth/sample>maximum*2||options.outHeight/sample>maximum*2)sample*=2
            BitmapFactory.decodeFile(source.absolutePath,BitmapFactory.Options().apply {
                inSampleSize=sample
                inPreferredConfig=Bitmap.Config.RGB_565
            })
        }.getOrNull()
    }

    fun save(kind:String,uri:Uri) {
        val target=file(kind)
        val resolver=context.contentResolver
        val bounds=BitmapFactory.Options().apply{inJustDecodeBounds=true}
        resolver.openInputStream(uri)?.use{BitmapFactory.decodeStream(it,null,bounds)}
            ?:error("Não foi possível ler a imagem.")
        require(bounds.outWidth in 1..15000&&bounds.outHeight in 1..15000){
            "Dimensões da fotografia inválidas."
        }
        val scale=if(kind=="avatar")900 else 2000
        var sample=1
        while(bounds.outWidth/sample>scale*2||bounds.outHeight/sample>scale*2)sample*=2
        var bitmap=resolver.openInputStream(uri)?.use {
            BitmapFactory.decodeStream(it,null,BitmapFactory.Options().apply{
                inSampleSize=sample
                inPreferredConfig=Bitmap.Config.ARGB_8888
            })
        }?:error("O ficheiro não contém uma fotografia válida.")
        try{
            val rotation=runCatching {
                resolver.openInputStream(uri)?.use{
                    when(ExifInterface(it).getAttributeInt(ExifInterface.TAG_ORIENTATION,
                        ExifInterface.ORIENTATION_NORMAL)){
                        ExifInterface.ORIENTATION_ROTATE_90->90f
                        ExifInterface.ORIENTATION_ROTATE_180->180f
                        ExifInterface.ORIENTATION_ROTATE_270->270f
                        else->0f
                    }
                }?:0f
            }.getOrDefault(0f)
            if(rotation!=0f){
                val corrected=Bitmap.createBitmap(bitmap,0,0,bitmap.width,bitmap.height,
                    Matrix().apply{postRotate(rotation)},true)
                if(corrected!==bitmap){bitmap.recycle();bitmap=corrected}
            }
            val max=Math.max(bitmap.width,bitmap.height)
            if(max>scale){
                val factor=scale.toFloat()/max
                val reduced=Bitmap.createScaledBitmap(bitmap,
                    (bitmap.width*factor).toInt().coerceAtLeast(1),
                    (bitmap.height*factor).toInt().coerceAtLeast(1),true)
                if(reduced!==bitmap){bitmap.recycle();bitmap=reduced}
            }
            val temp=File.createTempFile("profile_",".tmp",folder)
            try{
                temp.outputStream().use {
                    require(bitmap.compress(Bitmap.CompressFormat.JPEG,88,it)){
                        "Não foi possível codificar a fotografia."
                    }
                }
                require(temp.length() in 1..8_000_000L){"Fotografia demasiado grande."}
                if(!temp.renameTo(target)){
                    temp.copyTo(target,overwrite=true)
                    temp.delete()
                }
            }finally{temp.delete()}
        }finally{bitmap.recycle()}
    }
}
