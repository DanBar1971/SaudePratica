package com.mediagenda.app

import android.Manifest
import android.app.AlarmManager
import android.app.DatePickerDialog
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.content.res.Configuration
import android.content.res.ColorStateList
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.provider.ContactsContract
import android.app.Activity
import android.view.inputmethod.InputMethodManager
import android.text.InputType
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.app.AppCompatDelegate
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.google.android.gms.tasks.CancellationTokenSource
import com.google.mlkit.vision.codescanner.GmsBarcodeScannerOptions
import com.google.mlkit.vision.codescanner.GmsBarcodeScanning
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.barcode.BarcodeScanning
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import com.mediagenda.app.data.DataRepository
import com.mediagenda.app.data.ProfileStore
import com.mediagenda.app.data.ProfileDeletionStore
import com.mediagenda.app.data.AppPinStore
import com.mediagenda.app.i18n.AppLanguage
import com.mediagenda.app.data.FamilyBackupStore
import com.mediagenda.app.data.ProfileMediaStore
import com.mediagenda.app.data.MedicationPhotoLoader
import com.mediagenda.app.data.PersonalHealthStore
import com.mediagenda.app.data.HealthProfile
import com.mediagenda.app.model.Appointment
import com.mediagenda.app.model.Medication
import com.mediagenda.app.notifications.NotificationScheduler
import com.mediagenda.app.notifications.NotificationReceiver
import com.mediagenda.app.ocr.AppointmentOcrParser
import com.mediagenda.app.ocr.MultiAppointmentOcrParser
import com.mediagenda.app.ocr.IpoTableParser
import com.mediagenda.app.ocr.LocatedOcrLine
import com.mediagenda.app.ocr.PrescriptionOcrParser
import com.mediagenda.app.ocr.MedicationBoxOcrParser
import com.mediagenda.app.ocr.CitizenCardOcrParser
import com.google.android.material.button.MaterialButton
import com.google.android.material.card.MaterialCardView
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.android.material.textfield.TextInputEditText
import com.google.android.material.textfield.TextInputLayout
import java.io.File
import java.time.LocalTime
import java.time.LocalDateTime
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.util.Calendar
import java.util.Locale

class MainActivity : AppCompatActivity() {
    private lateinit var repo: DataRepository
    private val profiles by lazy { ProfileStore(this) }
    private var activeProfileId = "legacy"
    private lateinit var root: LinearLayout
    private lateinit var content: LinearLayout
    private lateinit var bottomNav: LinearLayout
    private var currentScreen = "Início"

    private enum class PhotoMode { AGENDA, PRESCRIPTION, MEDICATION_BOX, MEDICATION_ATTACH, ID_CARD_BACK }
    private var pendingPhotoMode: PhotoMode = PhotoMode.AGENDA
    private var pendingPhotoUri: Uri? = null
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
        if(!name.matches(Regex("medicamento_[0-9]+\\.jpg")))return null
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
    private var pendingIdentityPhotoFile: File? = null
    private var pendingMedicationPhotoTargetId: String? = null
    private var profileDraft: Triple<String, String, String>? = null
    private var extendedProfileDraft: Map<String, String>? = null

    // Android's phone-number picker grants access only to the number
    // explicitly selected by the user. No READ_CONTACTS permission is needed.
    private var pendingPhoneTarget: TextInputEditText? = null
    private var pendingContactNameTarget: TextInputEditText? = null
    private val familyExport = registerForActivityResult(
        ActivityResultContracts.CreateDocument("application/zip")
    ) { uri -> uri?.let { exportFamilyZip(it) } }
    private val familyImport = registerForActivityResult(
        ActivityResultContracts.OpenDocument()
    ) { uri -> uri?.let { askRestoreFamilyZip(it) } }

    private val phoneContactPicker = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            val selected = result.data?.data
            if (selected != null) {
                try {
                    val columns = arrayOf(
                        ContactsContract.CommonDataKinds.Phone.NUMBER,
                        ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME
                    )
                    contentResolver.query(selected, columns, null, null, null)?.use { cursor ->
                        if (cursor.moveToFirst()) {
                            val phone = cursor.getString(cursor.getColumnIndexOrThrow(
                                ContactsContract.CommonDataKinds.Phone.NUMBER)).orEmpty()
                            val displayName = cursor.getString(cursor.getColumnIndexOrThrow(
                                ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME)).orEmpty()
                            if (phone.isNotBlank()) {
                                pendingPhoneTarget?.setText(phone.trim())
                                if (pendingContactNameTarget?.text.isNullOrBlank() &&
                                    displayName.isNotBlank()) {
                                    pendingContactNameTarget?.setText(displayName.trim())
                                }
                            } else {
                                Toast.makeText(this,"O contacto selecionado não tem número.",
                                    Toast.LENGTH_LONG).show()
                            }
                        }
                    } ?: Toast.makeText(this,"Não foi possível ler o contacto.",
                        Toast.LENGTH_LONG).show()
                } catch (_: SecurityException) {
                    Toast.makeText(this,"Não foi possível aceder ao contacto escolhido.",
                        Toast.LENGTH_LONG).show()
                } catch (_: Exception) {
                    Toast.makeText(this,"Não foi possível preencher este telefone.",
                        Toast.LENGTH_LONG).show()
                }
            }
        }
        pendingPhoneTarget=null
        pendingContactNameTarget=null
    }

    private fun chooseProfilePhone(target: TextInputEditText,
                                   name: TextInputEditText? = null) {
        pendingPhoneTarget=target
        pendingContactNameTarget=name
        val picker=Intent(Intent.ACTION_PICK,
            ContactsContract.CommonDataKinds.Phone.CONTENT_URI)
        try {
            phoneContactPicker.launch(picker)
        } catch (_: Exception) {
            pendingPhoneTarget=null
            pendingContactNameTarget=null
            Toast.makeText(this,"Não foi possível abrir os contactos do telemóvel.",
                Toast.LENGTH_LONG).show()
        }
    }

    private fun attachProfilePhonePicker(field: Field, name: Field? = null) {
        val edit=field.edit
        edit.inputType=InputType.TYPE_CLASS_PHONE
        // Tap on the number itself to open the phone's contacts.
        // The pencil icon at left still allows free manual entry.
        edit.isFocusable=false
        edit.isClickable=true
        edit.setOnClickListener { chooseProfilePhone(edit,name?.edit) }
        field.container.endIconMode=TextInputLayout.END_ICON_CUSTOM
        field.container.setEndIconDrawable(android.R.drawable.ic_menu_call)
        field.container.setEndIconContentDescription("Escolher da agenda de contactos")
        field.container.setEndIconOnClickListener {
            chooseProfilePhone(edit,name?.edit)
        }
        field.container.setStartIconDrawable(android.R.drawable.ic_menu_edit)
        field.container.setStartIconContentDescription("Escrever número manualmente")
        field.container.setStartIconOnClickListener {
            edit.setOnClickListener(null)
            edit.isFocusableInTouchMode=true
            edit.isFocusable=true
            edit.requestFocus()
            (getSystemService(INPUT_METHOD_SERVICE) as InputMethodManager)
                .showSoftInput(edit,InputMethodManager.SHOW_IMPLICIT)
        }
    }
    private val editProfileImages = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) {
        // After selecting a portrait / CC image, reopen the same draft without
        // discarding unsaved identity or care-home fields.
        if (profiles.all().any { it.id == activeProfileId }) {
            if (it.resultCode == RESULT_OK) {
                // Critical fix: the form that launched the photo screen still
                // held blank/old draft values. OCR had committed new data to
                // preferences, but the stale draft masked/overwrote them.
                profileDraft = null
                extendedProfileDraft = null
            }
            showProfileDialog(false)
        }
    }
    private fun userAvatar(profileId: String, size: Int = 100): android.graphics.Bitmap? =
        runCatching { ProfileMediaStore(this, profileId).photo("avatar", size) }.getOrNull()
    private var activeMedicationDialog: androidx.appcompat.app.AlertDialog? = null
    private var pendingPrescriptionScan: String = ""

    private val isDarkPalette: Boolean
        get() = when (getSharedPreferences("mediagenda_ui", MODE_PRIVATE)
            .getString("theme_mode", "system")) {
            "dark" -> true
            "light" -> false
            else -> (resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK) ==
                Configuration.UI_MODE_NIGHT_YES
        }

    private val primary get() = Color.parseColor(if (isDarkPalette) "#0E8276" else "#0F766E")
    private val primaryDark get() = Color.parseColor(if (isDarkPalette) "#87EBDD" else "#0A5C56")
    private val blue get() = Color.parseColor(if (isDarkPalette) "#93C5FD" else "#2563EB")
    private val appBackground get() = Color.parseColor(if (isDarkPalette) "#101820" else "#F4F7F9")
    private val surface get() = Color.parseColor(if (isDarkPalette) "#1C2935" else "#FFFFFF")
    private val mainTextColor get() = Color.parseColor(if (isDarkPalette) "#F1F6FA" else "#132238")
    private val muted get() = Color.parseColor(if (isDarkPalette) "#BAC8D5" else "#667085")
    private val border get() = Color.parseColor(if (isDarkPalette) "#364959" else "#E3E8EF")
    private val softGreen get() = Color.parseColor(if (isDarkPalette) "#173C3B" else "#E6F4F1")
    private val softBlue get() = Color.parseColor(if (isDarkPalette) "#1D3349" else "#EAF1FF")
    private val softOrange get() = Color.parseColor(if (isDarkPalette) "#4A3522" else "#FFF4E5")
    private val danger get() = Color.parseColor(if (isDarkPalette) "#FF8585" else "#B42318")

    private val importJsonLauncher = registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        uri ?: return@registerForActivityResult
        runCatching { repo.importJson(uri) }
            .onSuccess {
                Toast.makeText(this, it, Toast.LENGTH_SHORT).show()
                reschedule(); showMedication()
            }
            .onFailure { showError(it.message ?: "Erro ao importar") }
    }
    private val exportMedJson = registerForActivityResult(ActivityResultContracts.CreateDocument("application/json")) { uri -> uri?.let { writeUri(it, repo.medicationJson()) } }
    private val exportAgendaJson = registerForActivityResult(ActivityResultContracts.CreateDocument("application/json")) { uri -> uri?.let { writeUri(it, repo.agendaJson()) } }
    private val exportBackupJson = registerForActivityResult(ActivityResultContracts.CreateDocument("application/json")) { uri -> uri?.let { writeUri(it, repo.fullBackupJson()) } }
    private val exportMedCsv = registerForActivityResult(ActivityResultContracts.CreateDocument("text/csv")) { uri -> uri?.let { writeUri(it, repo.medicationCsv()) } }
    private val exportAgendaCsv = registerForActivityResult(ActivityResultContracts.CreateDocument("text/csv")) { uri -> uri?.let { writeUri(it, repo.agendaCsv()) } }
    private var pendingMedicineGalleryId:String?=null
    // Gallery OCR is explicitly requested by the user, independent of the
    // existing "Anexar foto" flow that simply keeps a package photograph.
    private val smartBoxGalleryPicker=registerForActivityResult(
        ActivityResultContracts.OpenDocument()
    ){uri->
        if(uri!=null){
            runCatching {
                contentResolver.takePersistableUriPermission(uri,
                    Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            recognizeMedicationBox(uri)
        }
    }
    private val medicineGalleryPicker=registerForActivityResult(
        ActivityResultContracts.OpenDocument()
    ){uri->
        val target=pendingMedicineGalleryId
        pendingMedicineGalleryId=null
        if(uri==null||target.isNullOrBlank())return@registerForActivityResult
        runCatching{
            if(contentResolver.getType(uri)?.startsWith("image/")!=true)
                error("Escolhe uma imagem.")
            val stored=repo.loadMedications()
            val index=stored.indexOfFirst{it.id==target}
            if(index<0)error("Este medicamento não existe.")
            val directory=File(filesDir,"medication_photos").apply{mkdirs()}
            val file=File(directory,"galeria_"+java.util.UUID.randomUUID()+".jpg")
            try{
                val original=contentResolver.openInputStream(uri)?.use{
                    android.graphics.BitmapFactory.decodeStream(it)
                }?:error("A imagem não pôde ser lida.")
                if(original.width !in 1..10000||original.height !in 1..10000){
                    original.recycle()
                    error("Imagem inválida.")
                }
                val multiplier=minOf(1f,
                    1800f/maxOf(original.width,original.height).toFloat())
                val bitmap=if(multiplier<1f)
                    android.graphics.Bitmap.createScaledBitmap(original,
                        (original.width*multiplier).toInt().coerceAtLeast(1),
                        (original.height*multiplier).toInt().coerceAtLeast(1),true)
                    else original
                file.outputStream().use {
                    check(bitmap.compress(android.graphics.Bitmap.CompressFormat.JPEG,86,it))
                }
                if(bitmap!==original)bitmap.recycle()
                original.recycle()
                val local=file.absolutePath
                if(local !in stored[index].images)stored[index].images.add(local)
                repo.saveMedications(stored)
            }catch(e:Exception){file.delete();throw e}
        }.onSuccess{
            Toast.makeText(this,"Fotografia associada. Confirma que corresponde "+
                "à apresentação e dose certas.",Toast.LENGTH_LONG).show()
            showMedication()
        }.onFailure{showError(it.message?:"Não foi possível guardar a fotografia.")}
    }

    private val takePhoto = registerForActivityResult(ActivityResultContracts.TakePicture()) { ok ->
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
    }

    private val cameraPermissionLauncher = registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted) launchCamera(pendingPhotoMode)
        else Toast.makeText(this, "Sem permissão de câmara.", Toast.LENGTH_SHORT).show()
    }
    private val locationPermissionLauncher = registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { result ->
        if (result[Manifest.permission.ACCESS_FINE_LOCATION] == true || result[Manifest.permission.ACCESS_COARSE_LOCATION] == true) {
            openNearbyPharmaciesWithLocation()
        } else {
            Toast.makeText(this, "Sem localização. Vou abrir a pesquisa no mapa.", Toast.LENGTH_LONG).show()
            openGeoSearch(null, null)
        }
    }
    private val notificationPermissionLauncher = registerForActivityResult(ActivityResultContracts.RequestPermission()) { }

    override fun onCreate(savedInstanceState: Bundle?) {
        val themeMode = getSharedPreferences("mediagenda_ui", MODE_PRIVATE)
            .getString("theme_mode", "system")
        AppCompatDelegate.setDefaultNightMode(
            when (themeMode) {
                "dark" -> AppCompatDelegate.MODE_NIGHT_YES
                "light" -> AppCompatDelegate.MODE_NIGHT_NO
                else -> AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM
            }
        )
        super.onCreate(savedInstanceState)
        onBackPressedDispatcher.addCallback(this, object : androidx.activity.OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (currentScreen != "Início") showHome()
                else {
                    isEnabled = false
                    onBackPressedDispatcher.onBackPressed()
                }
            }
        })
        // Migrate the original user's files and profile without deleting data.
        val available = profiles.all()
        repo = DataRepository(this, "legacy")
        requestNotificationPermission()
        requestExactAlarmAccess()
        configureSystemBars()
        buildShell()
        when (available.size) {
            0 -> {
                repo.ensureFiles()
                showMedication()
                showProfileDialog(firstRun = true)
            }
            1 -> activateProfile(available.first())
            else -> showProfileSelection()
        }
    }

    override fun onResume() {
        super.onResume()
        val syncState=getSharedPreferences("saudepratica_nearby_sync_ui_v2",MODE_PRIVATE)
        val latest=syncState.getLong("last_import_complete",0L)
        val shown=syncState.getLong("main_last_shown",0L)
        if(latest>0 && latest>shown && ::content.isInitialized && ::repo.isInitialized){
            syncState.edit().putLong("main_last_shown",latest).apply()
            window.decorView.post{
                if(!isFinishing && !isDestroyed){
                    if(profiles.all().none{it.id==activeProfileId}){
                        showProfileSelection()
                    }else{
                        // Existing views contain old data; rebuild from disk.
                        showHome()
                    }
                    Toast.makeText(this,
                        "Sincronização recebida. Os dados apresentados foram atualizados.",
                        Toast.LENGTH_LONG).show()
                }
            }
        }
        // Fallback for camera apps that do not deliver a reliable ActivityResult.
        // If image bytes are really present, the same private capture is shown.
        window.decorView.postDelayed({
            if(!isFinishing && !isDestroyed)recoverSavedMedicationCameraCapture()
        },600L)
    }

    private fun configureSystemBars() {
        WindowCompat.setDecorFitsSystemWindows(window, false)
        window.statusBarColor = Color.TRANSPARENT
        window.navigationBarColor = Color.TRANSPARENT
        val controller = WindowInsetsControllerCompat(window, window.decorView)
        controller.isAppearanceLightStatusBars = !isDarkPalette
        controller.isAppearanceLightNavigationBars = !isDarkPalette
        controller.systemBarsBehavior =
            WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
        // Hide the Android navigation strip; it can briefly be revealed by swiping.
        controller.hide(WindowInsetsCompat.Type.navigationBars())
    }

    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus) configureSystemBars()
    }

    private fun buildShell() {
        root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            if (isDarkPalette) {
                val wallpaper = androidx.core.content.ContextCompat.getDrawable(
                    this@MainActivity, R.drawable.saude_background
                )
                if (wallpaper != null) {
                    if (wallpaper is android.graphics.drawable.BitmapDrawable) {
                        wallpaper.gravity = Gravity.FILL
                    }
                    background = android.graphics.drawable.LayerDrawable(
                        arrayOf(wallpaper, android.graphics.drawable.ColorDrawable(
                            Color.argb(105, 3, 14, 23)
                        ))
                    )
                } else {
                    setBackgroundColor(appBackground)
                }
            } else {
                setBackgroundColor(appBackground)
            }
        }
        content = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(16), dp(14), dp(16), dp(10))
        }
        bottomNav = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER
            setPadding(dp(8), dp(6), dp(8), dp(8))
            setBackgroundColor(surface)
            elevation = dp(10).toFloat()
        }
        root.addView(content, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f))
        // The dashboard already contains all the modules. Do not duplicate
        // those same buttons at the bottom of every screen.
        bottomNav.visibility = View.GONE
        // On Android 15 the app draws edge-to-edge. Keep content out of the
        // status bar, camera cutout, and transient Android navigation bar.
        ViewCompat.setOnApplyWindowInsetsListener(root) { view, insets ->
            val safe = insets.getInsets(
                WindowInsetsCompat.Type.statusBars() or
                    WindowInsetsCompat.Type.navigationBars() or
                    WindowInsetsCompat.Type.displayCutout()
            )
            view.setPadding(safe.left, safe.top, safe.right, safe.bottom)
            insets
        }
        setContentView(root)
        ViewCompat.requestApplyInsets(root)
    }

    private data class DashboardModule(
        val icon: String, val title: String, val subtitle: String, val action: () -> Unit
    )

    // Settings are per-user and do not erase any hidden module's data.
    private val dashboardLabels=listOf(
        "Medicação","Tomas","Agenda","Calendário","Documentos",
        "Situação Clínica","Beber água",
        "Ciclo Menstrual","Nutrição","Saúde Visual","Sintomas",
        "Medições","Vacinas","Emergência","Farmácias","SNS 24","IPO Lisboa",
        "Despesas de Saúde"
    )
    private fun dashboardPrefs()=getSharedPreferences(
        "saudepratica_modules_"+activeProfileId,MODE_PRIVATE)

    private fun showDashboardChecklist(){
        val hidden=dashboardPrefs().getStringSet("hidden",emptySet()).orEmpty()
        val options=dashboardLabels
        val choice=BooleanArray(options.size){options[it] !in hidden &&
            !(options[it]=="Situação Clínica" && "Saúde Ocupacional" in hidden)}
        // The Material AlertDialog API cannot display setMessage alongside
        // setMultiChoiceItems: its message panel replaces the list panel.
        // Use a dedicated scrolling view, with real CheckBox controls.
        val column=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(18),dp(8),dp(18),dp(12))
        }
        column.addView(TextView(this).apply{
            text="Marca os módulos que queres ver no Início. "+
                "Os dados dos módulos ocultos não são apagados. "+
                "O módulo Mais fica sempre disponível."
            textSize=13f
            setTextColor(mainTextColor)
            setPadding(0,0,0,dp(12))
        })
        options.forEachIndexed{index,name->
            android.widget.CheckBox(this).apply{
                text=name
                isChecked=choice[index]
                textSize=15f
                setTextColor(mainTextColor)
                buttonTintList=ColorStateList.valueOf(
                    if(isDarkPalette)Color.rgb(96,217,201)else Color.rgb(8,139,127))
                minHeight=dp(43)
                setOnCheckedChangeListener{_,value->choice[index]=value}
                column.addView(this,LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,dp(44)))
            }
        }
        val scroll=ScrollView(this).apply{
            addView(column)
            isVerticalScrollBarEnabled=true
        }
        val dialog=MaterialAlertDialogBuilder(this)
            .setTitle("Módulos do ecrã principal")
            .setView(scroll)
            .setPositiveButton("Guardar"){_,_->
                val invisible=options.filterIndexed{index,_->!choice[index]}.toSet()
                dashboardPrefs().edit().putStringSet("hidden",invisible).apply()
                showHome()
            }
            .setNeutralButton("Mostrar todos"){_,_->
                dashboardPrefs().edit().remove("hidden").apply()
                showHome()
            }
            .setNegativeButton("Cancelar",null).show()
        val display=resources.displayMetrics
        val height=(display.heightPixels*0.65f).toInt().coerceAtLeast(dp(260))
        scroll.layoutParams=android.widget.FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,height)
    }

    private fun exportFamilyZip(uri:Uri){
        val pending=MaterialAlertDialogBuilder(this)
            .setTitle("A criar backup completo")
            .setMessage("A guardar os perfis, fotografias, documentos e dados…")
            .setCancelable(false).show()
        Thread{
            val outcome=runCatching{FamilyBackupStore(this).export(uri)}
            runOnUiThread{
                if(!isFinishing)pending.dismiss()
                outcome.onSuccess{summary->
                    MaterialAlertDialogBuilder(this)
                        .setTitle("Backup completo criado")
                        .setMessage("Utilizadores: "+summary.profiles+
                            "\nFicheiros: "+summary.files+
                            "\n\nEste ZIP contém dados clínicos e documentos "+
                            "privados. Guarda-o num local protegido. "+
                            "O ficheiro não está encriptado e não inclui o PIN.")
                        .setPositiveButton("OK",null).show()
                }.onFailure{
                    showError("Não foi possível exportar o backup: "+it.message)
                }
            }
        }.start()
    }
    private fun askRestoreFamilyZip(uri:Uri){
        MaterialAlertDialogBuilder(this)
            .setTitle("Importar backup completo")
            .setMessage("ATENÇÃO: esta opção substitui TODOS os perfis "+
                "e respetivos dados neste telemóvel pelos do ficheiro ZIP. "+
                "Não mistura os dois conjuntos de utilizadores.\n\n"+
                "Cria primeiro um backup deste telemóvel, se já tiver dados. "+
                "O PIN atual deste dispositivo será mantido.")
            .setNegativeButton("Cancelar",null)
            .setPositiveButton("Substituir os dados"){_,_->restoreFamilyZip(uri)}
            .show()
    }
    private fun restoreFamilyZip(uri:Uri){
        val waiting=MaterialAlertDialogBuilder(this)
            .setTitle("A restaurar backup")
            .setMessage("A verificar o ZIP e a restaurar os ficheiros…")
            .setCancelable(false).show()
        Thread {
            val outcome=runCatching{FamilyBackupStore(this).restore(uri)}
            runOnUiThread{
                if(!isFinishing)waiting.dismiss()
                outcome.onSuccess{
                    runCatching{NotificationScheduler(this).scheduleAllProfiles()}
                    MaterialAlertDialogBuilder(this)
                        .setTitle("Restauro concluído")
                        .setMessage("Foram restaurados "+it.profiles+
                            " utilizadores e "+it.files+" ficheiros. "+
                            "A SaúdePrática vai reiniciar para mostrar os "+
                            "dados restaurados. O PIN deste telefone mantém-se.")
                        .setCancelable(false)
                        .setPositiveButton("Continuar"){_,_->
                            startActivity(Intent(this,SplashActivity::class.java)
                                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or
                                    Intent.FLAG_ACTIVITY_CLEAR_TASK))
                            finish()
                        }.show()
                }.onFailure{
                    showError("O restauro não foi concluído: "+it.message)
                }
            }
        }.start()
    }

    /**
     * Scalable 2-column menu, rather than squeezing every feature into the
     * bottom navigation. Each dashboard tile has a working destination.
     */
    private fun openCalendar(cycleMode:Boolean=false) {
        startActivity(Intent(this,MonthlyCalendarActivity::class.java)
            .putExtra(MonthlyCalendarActivity.PROFILE,activeProfileId)
            .putExtra(MonthlyCalendarActivity.MODE,if(cycleMode)"cycle" else "agenda"))
    }

    private fun upcomingAppointmentTime(ap:Appointment,
        now:LocalDateTime=LocalDateTime.now()):LocalDateTime? {
        val start=runCatching{LocalDate.parse(ap.date)}.getOrNull()?:return null
        val time=runCatching{LocalTime.parse(ap.time)}.getOrNull()?:return null
        val recur=ap.recurrence
        val until=runCatching{LocalDate.parse(recur.until)}.getOrNull()
        return (0..366).asSequence()
            .map{now.toLocalDate().plusDays(it.toLong())}
            .filter{!it.isBefore(start)}
            .filter{until==null||!it.isAfter(until)}
            .filter{day->
                when(recur.mode){
                    "weekdays"->day.dayOfWeek.value in 1..5
                    "weekly"->if(recur.weekdays.isEmpty())
                        day.dayOfWeek==start.dayOfWeek
                        else (day.dayOfWeek.value-1) in recur.weekdays
                    else->day==start
                }
            }.map{LocalDateTime.of(it,time)}
            .firstOrNull{it.isAfter(now)}
    }

    private fun showHome() {
        content.removeAllViews()
        screenHeader("⌂", "Início", "")

        val scroll = ScrollView(this).apply {
            overScrollMode = View.OVER_SCROLL_NEVER
            clipToPadding = false
        }
        val box = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        // Preserve the original compact status row beneath the personal
        // greeting. No bulky duplicate medication or agenda cards here.
        val totalMed=repo.loadMedications().size
        val outstanding=repo.loadAppointments().count{!it.done}
        box.addView(TextView(this).apply {
            text="$totalMed medicamento(s)  ·  $outstanding marcação(ões) por concluir"
            textSize=13f
            setTextColor(muted)
            setPadding(dp(4),dp(6),0,dp(15))
        })

        val options = listOf(
            DashboardModule("💊", "Medicação", "Tomas e avisos") { showMedication() },
            DashboardModule("✅", "Tomas", "Pendentes e confirmadas") { healthRecords("intakes") },
            DashboardModule("📅", "Agenda", "Consultas e exames") { showAgenda() },
            DashboardModule("🗓️", "Calendário", "Vista mensal e marcações") { openCalendar() },
            DashboardModule("📂", "Documentos", "PDFs e imagens") { showDocuments() },
            DashboardModule("🏥", "Situação Clínica", "Medicina do Trabalho") {
                startActivity(Intent(this,WorkMedicineActivity::class.java)
                    .putExtra(WorkMedicineActivity.EXTRA_PROFILE_ID,activeProfileId))
            },
            DashboardModule("🧾", "Despesas de Saúde", "Faturas, receitas e IRS") {
                startActivity(Intent(this,HealthExpensesActivity::class.java)
                    .putExtra(HealthExpensesActivity.EXTRA_PROFILE_ID,activeProfileId))
            },
            DashboardModule("💧", "Beber água", "Hidratação") { openWellness("water") },
            DashboardModule("🌸", "Ciclo Menstrual", "Período e pílula") { openCalendar(true) },
            DashboardModule("🥗", "Nutrição", "Plano alimentar e restrições") { openWellness("diet") },
            DashboardModule("👓", "Saúde Visual", "Graduação e receita óptica") { openWellness("glasses") },
            DashboardModule("🩺", "Sintomas", "Diário e efeitos secundários") { healthRecords("symptoms") },
            DashboardModule("📊", "Medições", "Tensão, glicemia e mais") { healthRecords("measurements") },
            DashboardModule("💉", "Vacinas", "Histórico de vacinação") { healthRecords("vaccines") },
            DashboardModule("🆘", "Emergência", "Alergias e contactos") { healthRecords("emergency") },
            DashboardModule("✚", "Farmácias", "Perto de mim e serviço") { showPharmacies() },
            DashboardModule("🏥", "SNS 24", "Aplicação oficial de saúde") { openSns24() },
            DashboardModule("🏨", "IPO Lisboa", "Abrir aplicação IPO Lisboa") { openIpoLisboa() },
            DashboardModule("⚙", "Mais", "Utilizadores e opções") { showDataTools() }
        )
        val hiddenModules=dashboardPrefs().getStringSet("hidden",emptySet())
            .orEmpty()
        val visibleModules=options.filter {
            it.title=="Mais" || (it.title !in hiddenModules &&
                !(it.title=="Situação Clínica" &&
                    "Saúde Ocupacional" in hiddenModules))
        }
        visibleModules.chunked(2).forEach { pair ->
            val row = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
            pair.forEach { module ->
                val card = materialCard(stroke = border, bg = surface, radius = 19f, elevation = 1f)
                val inside = LinearLayout(this).apply {
                    orientation = LinearLayout.VERTICAL
                    gravity = Gravity.CENTER_VERTICAL
                    setPadding(dp(15), dp(12), dp(10), dp(13))
                }
                inside.addView(TextView(this).apply {
                    text = module.icon
                    textSize = 29f
                })
                inside.addView(TextView(this).apply {
                    text = module.title
                    textSize = 16f
                    setTypeface(typeface, Typeface.BOLD)
                    setTextColor(mainTextColor)
                    setPadding(0, dp(8), 0, 0)
                })
                inside.addView(TextView(this).apply {
                    text = module.subtitle
                    textSize = 12f
                    setTextColor(muted)
                    maxLines = 2
                })
                card.addView(inside)
                card.setOnClickListener { module.action() }
                row.addView(card, LinearLayout.LayoutParams(
                    0, dp(145), 1f).apply {
                    marginStart = dp(3)
                    marginEnd = dp(3)
                    bottomMargin = dp(9)
                })
            }
            box.addView(row)
        }
        box.addView(TextView(this).apply {
            text = "As informações e os documentos são organizados por utilizador."
            textSize = 12f
            setTextColor(muted)
            setPadding(dp(6), dp(10), dp(6), dp(20))
        })
        scroll.addView(box)
        content.addView(scroll, LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f))
        renderBottomNav(0)
    }

    private fun openWellness(section: String) {
        startActivity(Intent(this, WellnessActivity::class.java)
            .putExtra(WellnessActivity.EXTRA_PROFILE_ID, activeProfileId)
            .putExtra(WellnessActivity.EXTRA_SECTION, section))
    }

    private fun healthRecords(kind: String) {
        startActivity(Intent(this, HealthRecordsActivity::class.java)
            .putExtra(HealthRecordsActivity.EXTRA_PROFILE_ID, activeProfileId)
            .putExtra(HealthRecordsActivity.EXTRA_CATEGORY, kind))
    }

    private fun showMedication() {
        content.removeAllViews()
        screenHeader("💊", "Medicação", "Organize a terapêutica e os avisos")

        val allItems = repo.loadMedications()
        val sorting = getSharedPreferences("saudepratica_med_sort", MODE_PRIVATE)
            .getString(activeProfileId, "name")
        val items = if (sorting == "date") allItems.sortedWith(
            compareBy<Medication> { nextMedicationTime(it) ?: LocalDateTime.MAX }
                .thenBy { it.medication.lowercase(Locale("pt", "PT")) }
        ) else allItems.sortedBy { it.medication.lowercase(Locale("pt", "PT")) }

        content.addView(sectionRow("Medicamentos", "${items.size} registados") {
            showMedicationAddOptions()
        })

        val sortRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(dp(3), 0, 0, dp(7))
        }
        sortRow.addView(TextView(this).apply {
            text = "Ordenar: "
            textSize = 12f
            setTextColor(muted)
        })
        sortRow.addView(secondaryButton(if (sorting == "date") "📅 Data / hora ▾" else "A–Z Nome ▾") {
            MaterialAlertDialogBuilder(this)
                .setTitle("Ordenar medicamentos")
                .setSingleChoiceItems(arrayOf("Nome (A–Z)", "Próxima data e hora"),
                    if (sorting == "date") 1 else 0) { dialog, selected ->
                    getSharedPreferences("saudepratica_med_sort", MODE_PRIVATE)
                        .edit().putString(activeProfileId, if (selected == 0) "name" else "date").apply()
                    dialog.dismiss()
                    showMedication()
                }.setNegativeButton("Cancelar", null).show()
        })
        content.addView(sortRow)

        if (items.isEmpty()) {
            content.addView(emptyState("Ainda não há medicação", "Toque em + Adicionar para fotografar uma caixa, ler uma guia ou inserir manualmente."),
                LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f))
        } else {
            val rv = RecyclerView(this).apply {
                layoutManager = LinearLayoutManager(this@MainActivity)
                overScrollMode = View.OVER_SCROLL_NEVER
                adapter = MedicationAdapter(items,
                    onClick = { editMedication(it) },
                    onTaken = { med ->
                        MaterialAlertDialogBuilder(this@MainActivity)
                            .setTitle("Confirmar toma de medicação")
                            .setMessage("Confirma que ${med.medication} foi realmente tomado agora? Este registo não altera os avisos programados.")
                            .setPositiveButton("Sim, tomei") { _,_ ->
                                runCatching {
                                    PersonalHealthStore(this@MainActivity,activeProfileId)
                                        .confirmIntake(med.id,med.medication)
                                }.onSuccess {
                                    Toast.makeText(this@MainActivity,"Toma confirmada.",Toast.LENGTH_SHORT).show()
                                    showMedication()
                                }.onFailure {
                                    showError(it.message?:"Não foi possível registar a toma.")
                                }
                            }.setNegativeButton("Cancelar",null).show()
                    },
                    lastTaken = { med ->
                        PersonalHealthStore(this@MainActivity,activeProfileId)
                            .latestIntakeFor(med.id)
                    },
                    onDelete = { med -> confirmDelete("Apagar ${med.medication}?") {
                        repo.saveMedications(repo.loadMedications().filterNot { it.id == med.id })
                        reschedule(); showMedication()
                    }})
            }
            content.addView(rv, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f))
        }
        renderBottomNav(1)
    }

    private fun nextMedicationTime(med: Medication): LocalDateTime? {
        val time = runCatching {
            LocalTime.parse(med.reminderTime.ifBlank { med.time })
        }.getOrNull() ?: return null
        val today = LocalDateTime.now()
        val start = runCatching { LocalDate.parse(med.repeatStart) }.getOrNull()
        val until = runCatching { LocalDate.parse(med.repeatUntil) }.getOrNull()
        val specialDays = med.schedule.flatMap { (month, days) ->
            days.mapNotNull { d ->
                runCatching { LocalDate.parse("$month-"+d.toString().padStart(2,'0')) }.getOrNull()
            }
        }.toSet()
        val mode = med.repeatMode.ifBlank { if (specialDays.isEmpty()) "daily" else "dates" }
        return (0..366).asSequence()
            .map { today.toLocalDate().plusDays(it.toLong()) }
            .filter { start == null || !it.isBefore(start) }
            .filter { until == null || !it.isAfter(until) }
            .filter { date ->
                when (mode) {
                    "daily" -> true
                    "weekly" -> med.repeatWeekdays.contains(date.dayOfWeek.value - 1)
                    "range" -> start != null && until != null
                    else -> specialDays.contains(date)
                }
            }
            .map { LocalDateTime.of(it, time) }
            .firstOrNull { it.isAfter(today) }
    }

    private fun showAgenda() {
        content.removeAllViews()
        screenHeader("📅", "Agenda", "Consultas, exames e tratamentos num só lugar")

        val items = repo.loadAppointments().sortedWith(compareBy<Appointment>{it.date}.thenBy{it.time})
        content.addView(sectionRow("Marcações", "${items.size} no total") {
            showAppointmentAddOptions()
        })

        if (items.isEmpty()) {
            content.addView(emptyState("Agenda vazia", "Toque em + Adicionar para fotografar uma folha ou inserir uma marcação."),
                LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f))
        } else {
            val rv = RecyclerView(this).apply {
                layoutManager = LinearLayoutManager(this@MainActivity)
                overScrollMode = View.OVER_SCROLL_NEVER
                adapter = AppointmentAdapter(items,
                    onClick = { editAppointment(it) },
                    onShare = { shareAppointment(it) },
                    onDelete = { ap -> confirmDelete("Apagar ${ap.activity.ifBlank { ap.department }}?") {
                        repo.saveAppointments(repo.loadAppointments().filterNot { it.id == ap.id })
                        reschedule(); showAgenda()
                    }})
            }
            content.addView(rv, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f))
        }
        renderBottomNav(2)
    }

    private var documentPurpose = "medication"
    private val documentPicker = registerForActivityResult(
        androidx.activity.result.contract.ActivityResultContracts.OpenDocument()
    ) { uri ->
        if (uri != null) importHealthDocument(uri, documentPurpose)
    }

    private fun pickHealthDocument(purpose: String) {
        documentPurpose = purpose
        documentPicker.launch(arrayOf("application/pdf", "image/*"))
    }

    private fun importHealthDocument(uri: Uri, purpose: String) {
        val mime = contentResolver.getType(uri).orEmpty()
        if (mime != "application/pdf" && !uri.toString().lowercase().endsWith(".pdf")) {
            processImportedHealthImage(uri, purpose)
            return
        }
        try {
            val descriptor = contentResolver.openFileDescriptor(uri, "r")
                ?: throw IllegalStateException("Documento inacessível")
            descriptor.use { fd ->
                android.graphics.pdf.PdfRenderer(fd).use { renderer ->
                    if (renderer.pageCount == 0) throw IllegalStateException("PDF vazio")
                    val pages = (0 until renderer.pageCount).map { "Página ${it+1}" }.toTypedArray()
                    MaterialAlertDialogBuilder(this)
                        .setTitle("Escolher página do PDF")
                        .setItems(pages) { _, selected ->
                            try {
                                // Reopen the PDF: the selection dialog outlives this descriptor.
                                contentResolver.openFileDescriptor(uri, "r")!!.use { selectedFd ->