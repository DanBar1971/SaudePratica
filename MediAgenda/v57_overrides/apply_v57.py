from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1')
main=root/'app/src/main/java/com/mediagenda/app/MainActivity.kt'
gradle=root/'app/build.gradle.kts'
def patch(f,old,new,label):
    s=f.read_text(encoding='utf-8');count=s.count(old)
    if count!=1:raise RuntimeError(f'SaudePratica v1.9.38 {label}: expected 1, found {count}')
    f.write_text(s.replace(old,new,1),encoding='utf-8')

patch(main,
    '''    private var pendingPhotoUri: Uri? = null
    private var pendingIdentityPhotoFile: File? = null''',
    '''    private var pendingPhotoUri: Uri? = null
    // Some Xiaomi camera apps return RESULT_CANCELED despite writing the full
    // photograph. Save the in-flight camera URI outside Activity memory, and
    // validate actual image bytes on return rather than trusting that flag.
    private val cameraCaptureState by lazy {
        getSharedPreferences("saudepratica_camera_capture_v1", MODE_PRIVATE)
    }
    private fun validCapturedBoxFile(uri: Uri):File? {
        if(uri.authority!=BuildConfig.APPLICATION_ID+".fileprovider")return null
        val folder=File(filesDir,"medication_photos").canonicalFile
        val name=uri.lastPathSegment.orEmpty().substringAfterLast('/')
        if(!name.matches(Regex("medicamento_[0-9]+\\\\.jpg")))return null
        val file=File(folder,name).canonicalFile
        if(file.parentFile!=folder || !file.isFile || file.length()<1024L)return null
        val options=android.graphics.BitmapFactory.Options().apply{
            inJustDecodeBounds=true
        }
        android.graphics.BitmapFactory.decodeFile(file.absolutePath,options)
        return file.takeIf { options.outWidth>=40 && options.outHeight>=40 }
    }
    private fun finishMedicationCameraReturn(uri:Uri):Boolean {
        val file=validCapturedBoxFile(uri)?:return false
        // Consume once: the ActivityResult callback and onResume recovery may
        // both execute, but must never display duplicate dialogs.
        if(cameraCaptureState.getString("mode",null)!="MEDICATION_BOX")return false
        val saved=cameraCaptureState.getString("uri",null)
        if(saved!=uri.toString())return false
        cameraCaptureState.edit().remove("mode").remove("uri")
            .remove("started").commit()
        pendingPhotoUri=null
        askAboutCapturedMedicationPhoto(uri)
        return true
    }
    private fun recoverSavedMedicationCameraCapture() {
        if(cameraCaptureState.getString("mode",null)!="MEDICATION_BOX")return
        val started=cameraCaptureState.getLong("started",0L)
        if(started<=0L || System.currentTimeMillis()-started<700L)return
        val saved=cameraCaptureState.getString("uri",null)?:return
        val uri=runCatching { Uri.parse(saved) }.getOrNull()?:return
        finishMedicationCameraReturn(uri)
    }
    private fun latestCameraBoxPhoto():Uri? {
        val folder=File(filesDir,"medication_photos")
        val latest=folder.listFiles()?.asSequence()
            ?.filter { it.isFile && it.name.startsWith("medicamento_") &&
                it.name.endsWith(".jpg",true) }
            ?.sortedByDescending { it.lastModified() }?.firstOrNull()?:return null
        val uri=runCatching { FileProvider.getUriForFile(this,
            BuildConfig.APPLICATION_ID+".fileprovider",latest) }.getOrNull()?:return null
        return uri.takeIf { validCapturedBoxFile(it)!=null }
    }
    private var pendingIdentityPhotoFile: File? = null''',
    'persist camera URI, validate bytes and expose last capture')

# Fix accidental double escaping inside generated Kotlin regex.
s=main.read_text(encoding='utf-8')
s=s.replace('Regex("medicamento_[0-9]+\\\\.jpg")','Regex("medicamento_[0-9]+\\\\.jpg")') # stable literal, checked in local verify below

patch(main,
    '''    private val takePhoto = registerForActivityResult(ActivityResultContracts.TakePicture()) { ok ->
        if (!ok) {
            if (pendingPhotoMode == PhotoMode.ID_CARD_BACK) {
                pendingIdentityPhotoFile?.delete()
                pendingIdentityPhotoFile = null
                showProfileDialog(false)
            }
            return@registerForActivityResult
        }
        val uri = pendingPhotoUri ?: return@registerForActivityResult
        when (pendingPhotoMode) {
            PhotoMode.AGENDA -> recognizeAppointment(uri)
            PhotoMode.PRESCRIPTION -> recognizePrescription(uri)
            PhotoMode.MEDICATION_BOX -> askAboutCapturedMedicationPhoto(uri)
            PhotoMode.MEDICATION_ATTACH -> attachPhotoToExistingMedication(uri)
            PhotoMode.ID_CARD_BACK -> recognizeCitizenCard(uri)
        }
    }''',
    '''    private val takePhoto = registerForActivityResult(ActivityResultContracts.TakePicture()) { ok ->
        // Use stored capture mode and URI, surviving an Android Activity restart.
        val savedMode=cameraCaptureState.getString("mode",null)
        if(savedMode=="MEDICATION_BOX"){
            val raw=cameraCaptureState.getString("uri",null)
            val captured=raw?.let { runCatching { Uri.parse(it) }.getOrNull() }
                ?:pendingPhotoUri
            if(captured!=null && finishMedicationCameraReturn(captured))
                return@registerForActivityResult
            if(!ok){
                Toast.makeText(this,"A câmara não devolveu uma fotografia válida. " +
                    "Experimenta novamente.",Toast.LENGTH_LONG).show()
            }else showError("Não foi possível abrir a fotografia que a câmara guardou.")
            cameraCaptureState.edit().clear().apply()
            return@registerForActivityResult
        }
        if (!ok) {
            if (pendingPhotoMode == PhotoMode.ID_CARD_BACK) {
                pendingIdentityPhotoFile?.delete()
                pendingIdentityPhotoFile = null
                showProfileDialog(false)
            }
            return@registerForActivityResult
        }
        val uri = pendingPhotoUri ?: return@registerForActivityResult
        when (pendingPhotoMode) {
            PhotoMode.AGENDA -> recognizeAppointment(uri)
            PhotoMode.PRESCRIPTION -> recognizePrescription(uri)
            PhotoMode.MEDICATION_BOX -> askAboutCapturedMedicationPhoto(uri)
            PhotoMode.MEDICATION_ATTACH -> attachPhotoToExistingMedication(uri)
            PhotoMode.ID_CARD_BACK -> recognizeCitizenCard(uri)
        }
    }''',
    'handle Xiaomi cancelled result and lifecycle recreation')

patch(main,
    '''    private fun configureSystemBars() {''',
    '''    override fun onResume() {
        super.onResume()
        // Fallback for camera apps that do not deliver a reliable ActivityResult.
        // If image bytes are really present, the same private capture is shown.
        window.decorView.postDelayed({
            if(!isFinishing && !isDestroyed)recoverSavedMedicationCameraCapture()
        },600L)
    }

    private fun configureSystemBars() {''',
    'recover when camera activity returns without reliable callback')

patch(main,
    '''        pendingPhotoUri = uri
        takePhoto.launch(uri)''',
    '''        pendingPhotoUri = uri
        if(mode==PhotoMode.MEDICATION_BOX){
            check(cameraCaptureState.edit().putString("mode",mode.name)
                .putString("uri",uri.toString())
                .putLong("started",System.currentTimeMillis()).commit()){
                "Não foi possível preparar a câmara de medicamentos."
            }
        }else cameraCaptureState.edit().clear().apply()
        takePhoto.launch(uri)''',
    'persist capture before invoking camera app')

patch(main,
    '''                "📷 Fotografar caixa (escolher análise depois)",
                "✨ Reconhecer medicamento de fotografia existente (ML Kit)",''',
    '''                "📷 Fotografar caixa (escolher análise depois)",
                "📸 Usar última foto tirada na SaúdePrática",
                "✨ Reconhecer fotografia da galeria (ML Kit)",''',
    'explicit re-open of app-private capture')
patch(main,
    '''                    0 -> captureMedicationBoxPhoto()
                    1 -> smartBoxGalleryPicker.launch(arrayOf("image/*"))
                    2 -> startPrescriptionScan()
                    3 -> pickHealthDocument("medication")
                    else -> editMedication(null)''',
    '''                    0 -> captureMedicationBoxPhoto()
                    1 -> {
                        val last=latestCameraBoxPhoto()
                        if(last!=null)askAboutCapturedMedicationPhoto(last)
                        else showError("Ainda não existe uma fotografia válida tirada " +
                            "pela SaúdePrática. Usa primeiro 'Fotografar caixa'.")
                    }
                    2 -> smartBoxGalleryPicker.launch(arrayOf("image/*"))
                    3 -> startPrescriptionScan()
                    4 -> pickHealthDocument("medication")
                    else -> editMedication(null)''',
    'bind last private photo and adjust menu indices')

# The last-image option is a recovery entry-point; don't delete its file upon
# cancelling review. The original user image may be needed for another attempt.
patch(main,
    '''            .setNegativeButton("Cancelar") { _,_->discardUnlinkedCameraPhoto(uri) }
            .create()''',
    '''            .setNegativeButton("Cancelar",null)
            .create()''',
    'keep unlinked camera photo for explicit retry')

patch(gradle,'versionCode = 47','versionCode = 48','version code')
patch(gradle,'versionName = "1.9.37"','versionName = "1.9.38"','version name')
print('v1.9.38: Xiaomi camera result fallback, persisted image, last captured photo reuse.')