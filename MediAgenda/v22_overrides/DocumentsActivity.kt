package com.mediagenda.app

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.content.res.ColorStateList
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.net.Uri
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.EditText
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import com.google.android.material.button.MaterialButton
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.mediagenda.app.data.HealthDocument
import com.mediagenda.app.data.HealthDocumentStore
import com.mediagenda.app.data.HealthProfile
import com.mediagenda.app.data.ProfileStore
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/** The document vault is deliberately separate from medication/agenda JSON.
 * Files are private and separated by active SaúdePrática profile.
 */
class DocumentsActivity : AppCompatActivity() {
    companion object { const val EXTRA_PROFILE_ID = "saudepratica_profile_id" }
    private lateinit var profile: HealthProfile
    private lateinit var store: HealthDocumentStore
    private lateinit var body: LinearLayout
    private var cameraFile: File? = null

    private val dark: Boolean
        get() = when (getSharedPreferences("mediagenda_ui", MODE_PRIVATE)
            .getString("theme_mode", "system")) {
                "dark" -> true
                "light" -> false
                else -> (resources.configuration.uiMode and
                    android.content.res.Configuration.UI_MODE_NIGHT_MASK) ==
                    android.content.res.Configuration.UI_MODE_NIGHT_YES
            }
    private val textColor get() = if (dark) Color.WHITE else Color.rgb(19, 34, 56)
    private val subColor get() = if (dark) Color.rgb(180, 203, 213) else Color.rgb(102, 112, 133)
    private val turquoise = Color.rgb(7, 163, 157)

    private val picker = registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) askNameAndSave(uri)
    }
    private val camera = registerForActivityResult(ActivityResultContracts.TakePicture()) { ok ->
        val file = cameraFile
        cameraFile = null
        if (ok && file != null) askNameAndSave(Uri.fromFile(file), file)
        else file?.delete()
    }
    private val cameraPermission = registerForActivityResult(ActivityResultContracts.RequestPermission()) { ok ->
        if (ok) captureDocument()
        else Toast.makeText(this, "Câmara não autorizada.", Toast.LENGTH_SHORT).show()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val users = ProfileStore(this).all()
        if (users.isEmpty()) {
            finish()
            return
        }
        val shared = sharedUri(intent)
        val requested = intent.getStringExtra(EXTRA_PROFILE_ID)
        if (shared != null && users.size > 1) {
            selectRecipient(users, shared)
        } else {
            val chosen = users.firstOrNull { it.id == requested } ?: users.first()
            choose(chosen)
            if (shared != null) askNameAndSave(shared)
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        sharedUri(intent)?.let { incoming ->
            val users = ProfileStore(this).all()
            if (users.size > 1) selectRecipient(users, incoming)
            else if (users.isNotEmpty()) { choose(users.first()); askNameAndSave(incoming) }
        }
    }

    private fun sharedUri(incoming: Intent?): Uri? {
        if (incoming?.action != Intent.ACTION_SEND) return null
        val mime = incoming.type.orEmpty()
        if (mime != "application/pdf" && !mime.startsWith("image/")) return null
        @Suppress("DEPRECATION")
        return incoming.getParcelableExtra(Intent.EXTRA_STREAM) as? Uri
    }

    private fun selectRecipient(users: List<HealthProfile>, uri: Uri) {
        MaterialAlertDialogBuilder(this)
            .setTitle("Guardar documento para...")
            .setItems(users.map { it.name }.toTypedArray()) { _, index ->
                choose(users[index])
                askNameAndSave(uri)
            }
            .setNegativeButton("Cancelar") { _, _ -> finish() }
            .setOnCancelListener { finish() }
            .show()
    }

    private fun dp(n: Int) = (n * resources.displayMetrics.density + .5f).toInt()

    private fun choose(user: HealthProfile) {
        profile = user
        store = HealthDocumentStore(this, user.id)
        val background = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(if (dark) Color.rgb(3, 20, 29) else Color.rgb(244, 247, 249))
            setPadding(dp(16), dp(12), dp(16), dp(8))
        }
        val top = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        val back = TextView(this).apply {
            text = "‹"
            textSize = 32f
            setTextColor(turquoise)
            gravity = Gravity.CENTER
            contentDescription = "Voltar"
            setOnClickListener { finish() }
        }
        top.addView(back, LinearLayout.LayoutParams(dp(45), dp(48)))
        val heading = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        heading.addView(label("📂 Documentos Digitais", 22f, true, textColor))
        heading.addView(label(user.name + " · PDFs e imagens", 13f, false, subColor))
        top.addView(heading, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        background.addView(top)

        val actions = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        actions.addView(actionButton("📷 Digitalizar", {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA)
                == PackageManager.PERMISSION_GRANTED) captureDocument()
            else cameraPermission.launch(Manifest.permission.CAMERA)
        }), LinearLayout.LayoutParams(0, dp(52), 1f))
        actions.addView(actionButton("📎 Anexar PDF / imagem", {
            picker.launch(arrayOf("application/pdf", "image/*"))
        }), LinearLayout.LayoutParams(0, dp(52), 1f).apply { marginStart = dp(8) })
        background.addView(actions, LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
            topMargin = dp(18); bottomMargin = dp(12)
        })
        val scroll = ScrollView(this)
        body = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        scroll.addView(body)
        background.addView(scroll, LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f))
        setContentView(background)
        refresh()
    }

    private fun label(value: String, size: Float, bold: Boolean, color: Int) =
        TextView(this).apply {
            text = value; textSize = size; setTextColor(color)
            if (bold) setTypeface(null, Typeface.BOLD)
        }

    private fun actionButton(value: String, clicked: () -> Unit) =
        MaterialButton(this).apply {
            text = value; isAllCaps = false; textSize = 12f
            backgroundTintList = ColorStateList.valueOf(Color.rgb(9, 119, 114))
            setTextColor(Color.WHITE)
            cornerRadius = dp(14)
            setOnClickListener { clicked() }
        }

    private fun rounded(color: Int) = GradientDrawable().apply {
        cornerRadius = dp(17).toFloat()
        setColor(color)
    }

    private fun refresh() {
        body.removeAllViews()
        val items = try { store.all() } catch (e: Exception) {
            message("Erro ao ler documentos: " + e.message)
            emptyList()
        }
        body.addView(label("${items.size} documento(s) guardado(s)", 13f, false, subColor)
            .apply { setPadding(dp(6), 0, 0, dp(12)) })
        if (items.isEmpty()) {
            body.addView(label("Ainda não existem documentos.\n\nPode fotografar atestados, justificações, boletins ou importar PDFs recebidos por mensagem.", 15f, false, subColor)
                .apply { setPadding(dp(16), dp(26), dp(16), dp(26)) })
        }
        val formatter = SimpleDateFormat("dd/MM/yyyy · HH:mm", Locale("pt", "PT"))
        items.forEach { doc ->
            val row = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL
                background = rounded(if (dark) Color.rgb(25, 42, 53) else Color.WHITE)
                setPadding(dp(14), dp(16), dp(14), dp(16))
            }
            row.addView(label(if (doc.mimeType == "application/pdf") "📄" else "🖼️", 27f, false, textColor),
                LinearLayout.LayoutParams(dp(54), ViewGroup.LayoutParams.WRAP_CONTENT))
            val content = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
            content.addView(label(doc.name, 16f, true, textColor))
            content.addView(label(
                formatter.format(Date(doc.createdAt)) + " · " +
                    if (doc.mimeType == "application/pdf") "PDF" else "Imagem",
                12f, false, subColor
            ))
            row.addView(content, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
            row.addView(label("⋮", 25f, true, turquoise))
            row.setOnClickListener { actionsFor(doc) }
            body.addView(row, LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                bottomMargin = dp(10)
            })
        }
        body.addView(label("Os documentos são privados e separados por utilizador. O backup JSON da medicação e agenda não inclui os documentos: guarde uma cópia dos ficheiros importantes.", 12f, false, subColor)
            .apply { setPadding(dp(12), dp(18), dp(12), dp(20)) })
    }

    private fun captureDocument() {
        try {
            val directory = File(cacheDir, "saudepratica_document_scans").apply { mkdirs() }
            val photo = File.createTempFile("scan_", ".jpg", directory)
            cameraFile = photo
            val uri = FileProvider.getUriForFile(this, "$packageName.documents", photo)
            camera.launch(uri)
        } catch (e: Exception) {
            cameraFile?.delete()
            cameraFile = null
            message("Não foi possível fotografar: " + e.message)
        }
    }

    private fun askNameAndSave(uri: Uri, tempPhoto: File? = null) {
        val input = EditText(this).apply {
            setSingleLine(true)
            setText(if (tempPhoto != null) "Documento digitalizado" else store.suggestedName(uri))
            setSelectAllOnFocus(true)
            setPadding(dp(16), dp(6), dp(16), dp(6))
        }
        val dialog = MaterialAlertDialogBuilder(this)
            .setTitle("Nome do documento")
            .setMessage("Ex.: Atestado Multiuso, Boletim de Vacinas, Justificação de Comparência...")
            .setView(input)
            .setNegativeButton("Cancelar") { _, _ -> tempPhoto?.delete() }
            .setOnCancelListener { tempPhoto?.delete() }
            .setPositiveButton("Guardar", null)
            .show()
        dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE).setOnClickListener {
            try {
                store.add(uri, input.text.toString())
                tempPhoto?.delete()
                dialog.dismiss()
                refresh()
                Toast.makeText(this, "Documento guardado.", Toast.LENGTH_SHORT).show()
            } catch (e: Exception) { input.error = e.message ?: "Erro ao guardar documento" }
        }
    }

    private fun actionsFor(doc: HealthDocument) {
        MaterialAlertDialogBuilder(this).setTitle(doc.name)
            .setItems(arrayOf("👁 Abrir", "📤 Partilhar / guardar cópia", "✎ Mudar nome", "🗑 Apagar")) { _, which ->
                when (which) {
                    0 -> {
                        try {
                            startActivity(Intent.createChooser(Intent(Intent.ACTION_VIEW).apply {
                                setDataAndType(store.contentUri(doc), doc.mimeType)
                                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                            }, "Abrir documento"))
                        } catch (e: Exception) { message("Não foi possível abrir: " + e.message) }
                    }
                    1 -> {
                        try {
                            startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).apply {
                                type = doc.mimeType
                                putExtra(Intent.EXTRA_STREAM, store.contentUri(doc))
                                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                            }, "Partilhar documento"))
                        } catch (e: Exception) { message("Não foi possível partilhar: " + e.message) }
                    }
                    2 -> renameDocument(doc)
                    else -> MaterialAlertDialogBuilder(this).setTitle("Apagar documento?")
                        .setMessage("Eliminar definitivamente «${doc.name}»?")
                        .setPositiveButton("Apagar") { _, _ ->
                            try { store.delete(doc); refresh() }
                            catch (e: Exception) { message("Erro ao apagar: " + e.message) }
                        }.setNegativeButton("Cancelar", null).show()
                }
            }.setNegativeButton("Fechar", null).show()
    }

    private fun renameDocument(doc: HealthDocument) {
        val input = EditText(this).apply { setSingleLine(true); setText(doc.name) }
        val dialog = MaterialAlertDialogBuilder(this).setTitle("Mudar nome")
            .setView(input).setNegativeButton("Cancelar", null)
            .setPositiveButton("Guardar", null).show()
        dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE).setOnClickListener {
            try { store.rename(doc, input.text.toString()); dialog.dismiss(); refresh() }
            catch (e: Exception) { input.error = e.message ?: "Nome inválido" }
        }
    }

    private fun message(value: String) {
        MaterialAlertDialogBuilder(this).setTitle("SaúdePrática")
            .setMessage(value).setPositiveButton("OK", null).show()
    }
}
