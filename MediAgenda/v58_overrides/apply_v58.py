from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1')
base=root/'app/src/main/java/com/mediagenda/app'
newclass=Path('MediAgenda/v58_overrides/MedicationBoxCameraActivity.kt')
(base/'MedicationBoxCameraActivity.kt').write_bytes(newclass.read_bytes())

def patch(path,old,new,label):
    text=path.read_text(encoding='utf-8')
    count=text.count(old)
    if count!=1:raise RuntimeError(f'1.9.39 {label}: expected 1 anchor got {count}')
    path.write_text(text.replace(old,new,1),encoding='utf-8')

main=base/'MainActivity.kt'
# No external camera app needed for photographing a medicine box. The camera
# returns a file ONLY after CameraX has validated and written the JPEG.
patch(main,
'''    private fun captureMedicationBoxPhoto() {
        pendingPhotoMode = PhotoMode.MEDICATION_BOX
        capturePhotoWithPermission()
    }''',
'''    private val internalBoxCamera=registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ){ result ->
        if(result.resultCode!=Activity.RESULT_OK)return@registerForActivityResult
        val path=result.data?.getStringExtra(
            MedicationBoxCameraActivity.EXTRA_CAPTURED_FILE)?:return@registerForActivityResult
        val folder=File(filesDir,"medication_photos").canonicalFile
        val candidate=runCatching{File(path).canonicalFile}.getOrNull()
        val options=android.graphics.BitmapFactory.Options().apply{
            inJustDecodeBounds=true
        }
        if(candidate!=null && candidate.parentFile==folder &&
            candidate.name.matches(Regex("""medicamento_[0-9]+\\.jpg""")) &&
            candidate.isFile && candidate.length()>1024L){
            android.graphics.BitmapFactory.decodeFile(candidate.absolutePath,options)
        }
        if(candidate==null||options.outWidth<40||options.outHeight<40){
            showError("A câmara não conseguiu devolver uma fotografia válida. " +
                "Volta a tentar ou escolhe uma imagem da galeria.")
            return@registerForActivityResult
        }
        val uri=runCatching{FileProvider.getUriForFile(this,
            BuildConfig.APPLICATION_ID+".fileprovider",candidate)}
            .getOrElse{Uri.fromFile(candidate)}
        // Run after the in-app camera has closed: don't display the dialog
        // while the camera Activity is still animating away.
        window.decorView.post { if(!isFinishing)askAboutCapturedMedicationPhoto(uri) }
    }

    private fun captureMedicationBoxPhoto() {
        // The Xiaomi external camera sometimes reports success/cancellation
        // without ever writing the FileProvider's output image. Capture inside
        // SaúdePrática instead: no ACTION_IMAGE_CAPTURE, no file picker.
        cameraCaptureState.edit().remove("mode").remove("uri")
            .remove("started").apply()
        internalBoxCamera.launch(Intent(this,MedicationBoxCameraActivity::class.java))
    }''',
'internal medication camera flow')

# Latest photo is a real file, including captures made in the new camera.
# Legacy getUriForFile validation had no diagnostic for missing files.
patch(main,
'''        return uri.takeIf { validCapturedBoxFile(it)!=null }
    }
    private var pendingIdentityPhotoFile''',
'''        return uri.takeIf { validCapturedBoxFile(it)!=null }
    }
    private var pendingIdentityPhotoFile''',
'legacy recovery preservation') if False else None

manifest=root/'app/src/main/AndroidManifest.xml'
patch(manifest,
'        <activity android:name=".MainActivity" android:exported="false" />',
'''        <activity android:name=".MainActivity" android:exported="false" />
        <activity android:name=".MedicationBoxCameraActivity"
            android:exported="false" android:screenOrientation="unspecified" />''',
'register internal camera')
gradle=root/'app/build.gradle.kts'
patch(gradle,
'    implementation("androidx.biometric:biometric:1.1.0")',
'''    implementation("androidx.biometric:biometric:1.1.0")
    implementation("androidx.camera:camera-core:1.5.3")
    implementation("androidx.camera:camera-camera2:1.5.3")
    implementation("androidx.camera:camera-lifecycle:1.5.3")
    implementation("androidx.camera:camera-view:1.5.3")''',
'CameraX dependencies')
patch(gradle,'versionCode = 48','versionCode = 49','version code')
patch(gradle,'versionName = "1.9.38"','versionName = "1.9.39"','version name')
print('v1.9.39: internal CameraX camera writes JPEG directly; only success with verified file opens ML Kit or save dialog. External Xiaomi camera no longer used for medication-box OCR.')