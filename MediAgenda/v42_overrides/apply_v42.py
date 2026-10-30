from pathlib import Path

base=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app")
crop=base/"AvatarCropView.kt"
crop.write_text(Path("MediAgenda/v42_overrides/AvatarCropView.kt").read_text(encoding="utf-8"),
                encoding="utf-8")

store=base/"data/ProfileMediaStore.kt"
s=store.read_text(encoding="utf-8")
old='''    fun save(kind:String,uri:Uri) {'''
new='''    /**
     * Load a selected avatar without modifying the current saved photograph.
     * Decode at a safe preview size and apply camera EXIF orientation.
     */
    fun loadCropSource(uri:Uri):Bitmap {
        val resolver=context.contentResolver
        val bounds=BitmapFactory.Options().apply{inJustDecodeBounds=true}
        resolver.openInputStream(uri)?.use{input->
            BitmapFactory.decodeStream(input,null,bounds)
        }?:error("Não foi possível abrir a imagem.")
        require(bounds.outWidth in 1..15000 && bounds.outHeight in 1..15000){
            "Dimensões da fotografia inválidas."
        }
        val max=2200
        var sample=1
        while(bounds.outWidth/sample>max*2 || bounds.outHeight/sample>max*2){
            sample*=2
        }
        var bitmap=resolver.openInputStream(uri)?.use{input->
            BitmapFactory.decodeStream(input,null,
                BitmapFactory.Options().apply{
                    inSampleSize=sample
                    inPreferredConfig=Bitmap.Config.ARGB_8888
                })
        }?:error("Imagem inválida ou não suportada.")
        try{
            val orientation=resolver.openInputStream(uri)?.use{input->
                runCatching{
                    ExifInterface(input).getAttributeInt(
                        ExifInterface.TAG_ORIENTATION,
                        ExifInterface.ORIENTATION_NORMAL)
                }.getOrDefault(ExifInterface.ORIENTATION_NORMAL)
            }?:ExifInterface.ORIENTATION_NORMAL
            val matrix=Matrix()
            when(orientation){
                ExifInterface.ORIENTATION_ROTATE_90->matrix.postRotate(90f)
                ExifInterface.ORIENTATION_ROTATE_180->matrix.postRotate(180f)
                ExifInterface.ORIENTATION_ROTATE_270->matrix.postRotate(270f)
                ExifInterface.ORIENTATION_FLIP_HORIZONTAL->matrix.postScale(-1f,1f)
                ExifInterface.ORIENTATION_FLIP_VERTICAL->matrix.postScale(1f,-1f)
                ExifInterface.ORIENTATION_TRANSPOSE->{
                    matrix.postRotate(90f)
                    matrix.postScale(-1f,1f)
                }
                ExifInterface.ORIENTATION_TRANSVERSE->{
                    matrix.postRotate(270f)
                    matrix.postScale(-1f,1f)
                }
            }
            if(!matrix.isIdentity){
                val fixed=Bitmap.createBitmap(bitmap,0,0,
                    bitmap.width,bitmap.height,matrix,true)
                if(fixed!==bitmap){
                    bitmap.recycle()
                    bitmap=fixed
                }
            }
            val largest=maxOf(bitmap.width,bitmap.height)
            if(largest>max){
                val factor=max.toFloat()/largest
                val reduced=Bitmap.createScaledBitmap(bitmap,
                    (bitmap.width*factor).toInt().coerceAtLeast(1),
                    (bitmap.height*factor).toInt().coerceAtLeast(1),true)
                if(reduced!==bitmap){
                    bitmap.recycle()
                    bitmap=reduced
                }
            }
            return bitmap
        }catch(error:Exception){
            bitmap.recycle()
            throw error
        }
    }

    /** Save a confirmed square avatar; metadata is stripped by JPEG encoding.
     * Existing file is untouched until the crop is confirmed.
     */
    fun saveCroppedAvatar(bitmap:Bitmap){
        require(bitmap.width==bitmap.height &&
            bitmap.width in 128..2048 && !bitmap.isRecycled){
            "O recorte deve ser quadrado."
        }
        val temp=File.createTempFile("avatar_crop_",".tmp",folder)
        try{
            temp.outputStream().use{out->
                require(bitmap.compress(Bitmap.CompressFormat.JPEG,90,out)){
                    "Não foi possível guardar a fotografia."
                }
            }
            require(temp.length() in 1..8_000_000L){
                "Fotografia demasiado grande."
            }
            val destination=file("avatar")
            // Write a complete replacement only when editing is confirmed.
            if(!temp.renameTo(destination)){
                temp.copyTo(destination,overwrite=true)
            }
        }finally{temp.delete()}
    }

    fun save(kind:String,uri:Uri) {'''
assert s.count(old)==1,"Avatar media store method not found"
s=s.replace(old,new,1)
store.write_text(s,encoding="utf-8")

screen=base/"ProfileMediaActivity.kt"
s=screen.read_text(encoding="utf-8")
old='''            column.addView(outline(if(photo==null)"📷 Adicionar fotografia"
                else "📷 Substituir fotografia"){chooseImage(key)})
            if(photo!=null && (key=="cc_front" || key=="cc_back")) {'''
new='''            column.addView(outline(if(photo==null)"📷 Adicionar fotografia"
                else "📷 Substituir fotografia"){chooseImage(key)})
            if(key=="avatar" && photo!=null){
                column.addView(outline("✂️ Recortar / ajustar fotografia"){
                    // Edit the existing stored avatar, preserving the old photo
                    // if the editor is cancelled.
                    showAvatarCrop(null,null)
                })
            }
            if(photo!=null && (key=="cc_front" || key=="cc_back")) {'''
assert s.count(old)==1,"Avatar button location not found"
s=s.replace(old,new,1)

old='''    private fun storeImage(uri:Uri,temporary:File?=null){
        try{
            media.save(target,uri)'''
new='''    private fun storeImage(uri:Uri,temporary:File?=null){
        if(target=="avatar"){
            showAvatarCrop(uri,temporary)
            return
        }
        try{
            media.save(target,uri)'''
assert s.count(old)==1,"Imported images saver not found"
s=s.replace(old,new,1)

anchor='''    private fun scanSavedCitizenCard(side:String){'''
method='''    /**
     * Preview and crop a photo before replacing the saved avatar. Only the
     * avatar is cropped: CC front/back stay complete for legibility and OCR.
     */
    private fun showAvatarCrop(uri:Uri?,temporary:File?){
        val bitmap=try{
            if(uri!=null)media.loadCropSource(uri)
            else media.photo("avatar",2200)
                ?:error("Não há fotografia de perfil para recortar.")
        }catch(e:Exception){
            temporary?.delete()
            showError("Não foi possível abrir a fotografia: "+e.message)
            return
        }
        val crop=AvatarCropView(this,bitmap).apply{
            contentDescription="Mover, ampliar ou rodar a fotografia até "+
                "o rosto ficar centrado no círculo."
        }
        val panel=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(14),dp(8),dp(14),dp(4))
            addView(label(
                "Arrasta a fotografia para centrar o rosto. "+
                "Usa dois dedos para ampliar ou os botões de zoom. "+
                "A linha circular mostra como ficará a foto do perfil.",
                13f,false,muted).apply{
                setPadding(dp(2),0,dp(2),dp(9))
            })
            addView(crop,LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,dp(320)))
        }
        val controls=LinearLayout(this).apply{
            orientation=LinearLayout.HORIZONTAL
        }
        controls.addView(outline("−"){crop.setZoom(1f/1.22f)},
            LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f))
        controls.addView(outline("+"){crop.setZoom(1.22f)},
            LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f))
        controls.addView(outline("⟳ Rodar"){crop.rotateRight()},
            LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,2f))
        controls.addView(outline("Repor"){crop.resetCrop()},
            LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,2f))
        panel.addView(controls)

        val dialog=MaterialAlertDialogBuilder(this)
            .setTitle("Recortar fotografia de perfil")
            .setView(panel)
            .setPositiveButton("Guardar recorte",null)
            .setNegativeButton("Cancelar",null)
            .create()
        dialog.setOnDismissListener{
            crop.release()
            temporary?.delete()
        }
        dialog.show()
        dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE)
            .setOnClickListener{
                try{
                    val cropped=crop.makeSquare(900)
                    try{
                        media.saveCroppedAvatar(cropped)
                    }finally{cropped.recycle()}
                    Toast.makeText(this,
                        "Fotografia de perfil atualizada.",
                        Toast.LENGTH_SHORT).show()
                    dialog.dismiss()
                    draw()
                }catch(e:Exception){
                    showError("Não foi possível guardar o recorte: "+e.message)
                }
            }
    }

'''
assert s.count(anchor)==1,"CC OCR method not found"
s=s.replace(anchor,method+anchor,1)
screen.write_text(s,encoding="utf-8")

gradle=Path("build-src/MediAgenda_Android_v1/app/build.gradle.kts")
s=gradle.read_text(encoding="utf-8")
assert 'applicationId = "com.mediagenda.app.stable"' in s
assert s.count('versionCode = 32')==1 and s.count('versionName = "1.9.22"')==1
gradle.write_text(s.replace('versionCode = 32','versionCode = 33',1)
    .replace('versionName = "1.9.22"','versionName = "1.9.23"',1),
    encoding="utf-8")
print("SaúdePrática v1.9.23: crop avatar after gallery or camera, recrop existing, pan/pinch, zoom and rotate; CC images unchanged.")
