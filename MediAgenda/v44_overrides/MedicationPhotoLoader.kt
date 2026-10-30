package com.mediagenda.app.data

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.media.ExifInterface
import android.net.Uri
import java.io.File

/**
 * Loads the newest readable medication-box photo, not simply the first saved
 * URI. This is important for profiles migrated from an older installation
 * where camera content URIs may already be unavailable.
 *
 * Images stay on the device and are only decoded to bounded thumbnails.
 */
object MedicationPhotoLoader {
    fun load(context:Context,images:List<String>,maxSide:Int=480):Bitmap?{
        for(value in images.asReversed()){
            if(value.isBlank())continue
            try{
                val result=decode(context,value,maxSide)
                if(result!=null)return result
            }catch(_:Exception){
                // An older, missing or revoked URI must not conceal the next
                // good photograph of the medicine.
            }
        }
        return null
    }
    fun decode(context:Context,value:String,maxSide:Int=480):Bitmap?{
        require(maxSide in 64..2400)
        val uri=Uri.parse(value)
        val file=when(uri.scheme){
            null -> File(value)
            "file"->File(uri.path?:return null)
            else->null
        }
        if(file!=null){
            val allowed=File(context.filesDir,"medication_photos").canonicalFile
            if(file.canonicalFile.parentFile!=allowed)return null
        } else {
            // Do not load arbitrary websites or network URLs from saved JSON.
            if(uri.scheme!="content")return null
        }
        fun stream()=if(file!=null)file.inputStream()
            else context.contentResolver.openInputStream(uri)
        val bounds=BitmapFactory.Options().apply{inJustDecodeBounds=true}
        stream()?.use{BitmapFactory.decodeStream(it,null,bounds)}?:return null
        if(bounds.outWidth !in 1..16000 || bounds.outHeight !in 1..16000)
            return null
        var step=1
        // Power-of-two downsampling keeps card rendering cheap.
        while(bounds.outWidth/step>maxSide*2 ||
            bounds.outHeight/step>maxSide*2)step*=2
        val decoded=stream()?.use{
            BitmapFactory.decodeStream(it,null,BitmapFactory.Options().apply{
                inSampleSize=step
                inPreferredConfig=Bitmap.Config.ARGB_8888
            })
        }?:return null
        val orientation=runCatching{
            stream()?.use{
                ExifInterface(it).getAttributeInt(
                    ExifInterface.TAG_ORIENTATION,ExifInterface.ORIENTATION_NORMAL)
            }?:ExifInterface.ORIENTATION_NORMAL
        }.getOrDefault(ExifInterface.ORIENTATION_NORMAL)
        val transform=Matrix()
        when(orientation){
            ExifInterface.ORIENTATION_ROTATE_90->transform.postRotate(90f)
            ExifInterface.ORIENTATION_ROTATE_180->transform.postRotate(180f)
            ExifInterface.ORIENTATION_ROTATE_270->transform.postRotate(270f)
            ExifInterface.ORIENTATION_FLIP_HORIZONTAL->transform.postScale(-1f,1f)
            ExifInterface.ORIENTATION_FLIP_VERTICAL->transform.postScale(1f,-1f)
            ExifInterface.ORIENTATION_TRANSPOSE->{
                transform.postRotate(90f);transform.postScale(-1f,1f)
            }
            ExifInterface.ORIENTATION_TRANSVERSE->{
                transform.postRotate(270f);transform.postScale(-1f,1f)
            }
        }
        if(transform.isIdentity)return decoded
        return try{
            val rotated=Bitmap.createBitmap(decoded,0,0,decoded.width,
                decoded.height,transform,true)
            if(rotated!==decoded)decoded.recycle()
            rotated
        }catch(e:Exception){
            decoded.recycle()
            throw e
        }
    }
}
