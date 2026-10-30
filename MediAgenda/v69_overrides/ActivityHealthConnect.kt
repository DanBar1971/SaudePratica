package com.mediagenda.app

import android.content.Intent
import android.content.pm.PackageManager
import android.content.res.ColorStateList
import android.content.res.Configuration
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.BitmapDrawable
import android.graphics.drawable.ColorDrawable
import android.graphics.drawable.GradientDrawable
import android.graphics.drawable.LayerDrawable
import android.health.connect.AggregateRecordsRequest
import android.health.connect.AggregateRecordsResponse
import android.health.connect.datatypes.AggregationType
import android.health.connect.HealthConnectException
import android.health.connect.HealthConnectManager
import android.health.connect.HealthPermissions
import android.health.connect.TimeInstantRangeFilter
import android.health.connect.datatypes.ActiveCaloriesBurnedRecord
import android.health.connect.datatypes.DistanceRecord
import android.health.connect.datatypes.SleepSessionRecord
import android.health.connect.datatypes.StepsRecord
import android.health.connect.datatypes.units.Energy
import android.health.connect.datatypes.units.Length
import android.os.Build
import android.os.Bundle
import android.os.OutcomeReceiver
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import com.google.android.material.button.MaterialButton
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.mediagenda.app.data.ProfileStore
import java.time.Instant
import java.time.LocalDate
import java.time.LocalTime
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Locale

/** Health Connect integration for Android 14+ (native, no Google account or uploads).
 * Permission is device-wide; the explicit in-app association is single-profile only.
 * No health measurements are copied into app storage.
 */
class ActivityHealthConnect : AppCompatActivity() {
    companion object { const val EXTRA_PROFILE_ID = "profile_id" }
    private lateinit var profileId: String
    private lateinit var profileName: String
    private lateinit var content: LinearLayout
    private var manager: HealthConnectManager? = null
    private var requestGeneration = 0
    private val prefs by lazy { getSharedPreferences("saudepratica_health_connect", MODE_PRIVATE) }
    private val connectedProfile get() = prefs.getString("linked_profile", "").orEmpty()
    private val permissions = arrayOf(
        HealthPermissions.READ_STEPS,
        HealthPermissions.READ_SLEEP,
        HealthPermissions.READ_DISTANCE,
        HealthPermissions.READ_ACTIVE_CALORIES_BURNED
    )
    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { granted ->
        if (granted.values.any { it } || hasAnyPermission()) {
            prefs.edit().putString("linked_profile", profileId).apply()
        }
        showScreen()
    }
    private val teal = Color.rgb(0, 198, 190)
    private val isDark: Boolean get() = when (getSharedPreferences("mediagenda_ui", MODE_PRIVATE)
        .getString("theme_mode", "system")) {
        "dark" -> true
        "light" -> false
        else -> (resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK) ==
            Configuration.UI_MODE_NIGHT_YES
    }
    private val fg get() = if (isDark) Color.rgb(245, 250, 251) else Color.rgb(22, 39, 52)
    private val secondary get() = if (isDark) Color.rgb(196, 219, 226) else Color.rgb(78, 96, 112)
    private val surface get() = if (isDark) Color.rgb(29, 44, 56) else Color.WHITE
    private val border get() = if (isDark) Color.rgb(74, 99, 111) else Color.rgb(214, 224, 234)
    private fun dp(value: Int) = (value * resources.displayMetrics.density + .5f).toInt()
    private fun label(t: String, size: Float = 14f, bold: Boolean = false, color: Int = fg) =
        TextView(this).apply {
            text = t; textSize = size; setTextColor(color)
            if (bold) setTypeface(null, Typeface.BOLD)
        }
    private fun wallpaper(): android.graphics.drawable.Drawable {
        if (!isDark) return ColorDrawable(Color.rgb(245, 248, 250))
        val image = ContextCompat.getDrawable(this, R.drawable.saude_background)
        if (image is BitmapDrawable) image.gravity = Gravity.FILL
        return if (image != null) LayerDrawable(arrayOf(image, ColorDrawable(Color.argb(112, 1, 14, 24))))
            else ColorDrawable(Color.rgb(5, 24, 33))
    }
    private fun rounded() = GradientDrawable().apply {
        setColor(surface); cornerRadius = dp(18).toFloat(); setStroke(dp(1), border)
    }
    private fun box(parent: LinearLayout, title: String, description: String? = null): LinearLayout {
        val child = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL; setPadding(dp(16), dp(14), dp(16), dp(15))
            background = rounded()
        }
        child.addView(label(title, 18f, true))
        if (description != null) child.addView(label(description, 13f, false, secondary))
        parent.addView(child, LinearLayout.LayoutParams(-1, -2).apply { bottomMargin = dp(12) })
        return child
    }
    private fun action(text: String, block: () -> Unit) = MaterialButton(this).apply {
        this.text = text; isAllCaps = false; textSize = 13f
        backgroundTintList = ColorStateList.valueOf(Color.TRANSPARENT)
        strokeColor = ColorStateList.valueOf(teal); strokeWidth = dp(1)
        setTextColor(if (isDark) Color.rgb(147, 239, 229) else Color.rgb(0, 110, 104))
        cornerRadius = dp(16); setOnClickListener { block() }
    }
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val requested = intent.getStringExtra(EXTRA_PROFILE_ID).orEmpty()
        val person = ProfileStore(this).all().firstOrNull { it.id == requested }
        if (person == null) { finish(); return }
        profileId = person.id; profileName = person.name
        if (Build.VERSION.SDK_INT >= 34) {
            manager = getSystemService(HealthConnectManager::class.java)
        }
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL; background = wallpaper()
            setPadding(dp(16), dp(12), dp(16), dp(8))
        }
        val top = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL }
        top.addView(label("‹", 34f, true, teal).apply { gravity = Gravity.CENTER; setOnClickListener { finish() } },
            LinearLayout.LayoutParams(dp(42), dp(62)))
        val title = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        title.addView(label("SaúdePrática", 16f, true, teal))
        title.addView(label("Atividade e Saúde", 13f, false, secondary))
        top.addView(title, LinearLayout.LayoutParams(0, -2, 1f))
        top.addView(label(profileName.take(12), 12f, true, teal).apply {
            setPadding(dp(10), dp(8), dp(10), dp(8)); background = rounded()
        })
        root.addView(top)
        val scroll = ScrollView(this).apply { clipToPadding = false }
        content = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL; setPadding(0, dp(15), 0, dp(22))
        }
        scroll.addView(content)
        root.addView(scroll, LinearLayout.LayoutParams(-1, 0, 1f))
        WindowCompat.setDecorFitsSystemWindows(window, false)
        window.statusBarColor = Color.TRANSPARENT; window.navigationBarColor = Color.TRANSPARENT
        WindowInsetsControllerCompat(window, window.decorView).apply {
            isAppearanceLightStatusBars = !isDark; isAppearanceLightNavigationBars = !isDark
        }
        ViewCompat.setOnApplyWindowInsetsListener(root) { view, insets ->
            val safe = insets.getInsets(WindowInsetsCompat.Type.statusBars() or
                WindowInsetsCompat.Type.navigationBars() or WindowInsetsCompat.Type.displayCutout())
            view.setPadding(dp(16) + safe.left, dp(12) + safe.top, dp(16) + safe.right, dp(8) + safe.bottom)
            insets
        }
        setContentView(root); ViewCompat.requestApplyInsets(root)
        showScreen()
    }
    override fun onResume() { super.onResume(); if (::content.isInitialized) showScreen() }
    private fun allowed(permission: String) =
        ContextCompat.checkSelfPermission(this, permission) == PackageManager.PERMISSION_GRANTED
    private fun hasAnyPermission() = Build.VERSION.SDK_INT >= 34 && permissions.any { allowed(it) }
    private fun canRead(): Boolean = manager != null && connectedProfile == profileId && hasAnyPermission()
    private fun showScreen() {
        requestGeneration++
        val current = requestGeneration
        content.removeAllViews()
        content.addView(label("🚶  Atividade e Saúde", 25f, true))
        content.addView(label("Passos, sono e energia · dados do Health Connect", 13f, false, secondary),
            LinearLayout.LayoutParams(-1, -2).apply { bottomMargin = dp(16) })
        if (Build.VERSION.SDK_INT < 34 || manager == null) {
            val info = box(content, "Health Connect não disponível",
                "Esta versão utiliza o Health Connect integrado no Android 14 ou mais recente.")
            info.addView(label("A SaúdePrática mantém as outras funcionalidades normalmente.", 13f))
            return
        }
        if (connectedProfile.isNotBlank() && connectedProfile != profileId) {
            val name = ProfileStore(this).all().firstOrNull { it.id == connectedProfile }?.name ?: "outro perfil"
            val info = box(content, "Ligação associada a outro perfil",
                "Este telemóvel já associou os seus dados de atividade ao perfil «$name». " +
                    "Não vamos mostrar esses dados no perfil $profileName.")
            info.addView(action("Mudar associação para $profileName") {
                MaterialAlertDialogBuilder(this).setTitle("Associar a este perfil?")
                    .setMessage("Os dados do Health Connect pertencem ao utilizador deste telemóvel. " +
                        "Confirma que são os dados de $profileName. A associação anterior será desfeita.")
                    .setNegativeButton("Cancelar", null)
                    .setPositiveButton("Confirmar") { _, _ ->
                        prefs.edit().remove("linked_profile").apply(); authorize()
                    }.show()
            })
            return
        }
        if (!canRead()) {
            val intro = box(content, "Ligar ao Health Connect",
                "Autoriza apenas a leitura dos dados que quiseres: passos, " +
                    "distância, calorias ativas e sono. A ligação é opcional.")
            intro.addView(action("🔐 Autorizar SaúdePrática") { authorize() })
            val privacy = box(content, "Privacidade e perfis",
                "Os dados são lidos neste telemóvel apenas quando abres ou atualizas " +
                    "este módulo. Não são enviados para servidores nem adicionados ao " +
                    "backup de saúde. A autorização Android pertence ao telemóvel; " +
                    "a SaúdePrática associa a leitura somente a um perfil de cada vez.")
            privacy.addView(action("Política de utilização dos dados") {
                startActivity(Intent(this, HealthPermissionsRationaleActivity::class.java))
            })
            return
        }
        val info = box(content, "Ligação ativa · $profileName",
            "Atualização a pedido. Os valores dependem de aplicações ou dispositivos " +
                "que forneçam dados ao Health Connect.")
        info.addView(action("↻ Atualizar dados") { showScreen() })
        val date = LocalDate.now()
        val summary = box(content, "Hoje · ${date.format(DateTimeFormatter.ofPattern("dd/MM/yyyy"))}")
        val stepsView = label("👣  Passos: a consultar…", 17f, true)
        val distanceView = label("📍  Distância: a consultar…", 16f)
        val caloriesView = label("🔥  Energia ativa: a consultar…", 16f)
        val sleepView = label("🌙  Sono (última noite): a consultar…", 16f)
        listOf(stepsView, distanceView, caloriesView, sleepView).forEach {
            it.setPadding(0, dp(9), 0, dp(5)); summary.addView(it)
        }
        val week = box(content, "Passos nos últimos 7 dias", "Sem dados significa que ainda não há registos disponíveis.")
        val rows = ArrayList<Pair<TextView, LinearLayout>>()
        repeat(7) { index ->
            val day = date.minusDays((6-index).toLong())
            val row = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL }
            val text = label(day.format(DateTimeFormatter.ofPattern("EEE", Locale("pt", "PT"))), 13f, true)
            row.addView(text, LinearLayout.LayoutParams(dp(50), dp(34)))
            val bar = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL }
            row.addView(bar, LinearLayout.LayoutParams(0, dp(34), 1f))
            week.addView(row)
            rows.add(text to bar)
        }
        val settings = box(content, "Permissões e associação",
            "Podes retirar o acesso nas Definições do Android a qualquer momento.")
        settings.addView(action("Gerir permissões no Android") { managePermissions() })
        settings.addView(action("Desligar deste perfil") {
            MaterialAlertDialogBuilder(this).setTitle("Desligar Health Connect?")
                .setMessage("A SaúdePrática deixará de ler dados neste perfil. " +
                    "Para revogar também a autorização Android, usa «Gerir permissões»." )
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("Desligar") { _, _ ->
                    prefs.edit().remove("linked_profile").apply(); showScreen()
                }.show()
        })
        val from = date.atStartOfDay(ZoneId.systemDefault()).toInstant()
        val until = Instant.now()
        if (allowed(HealthPermissions.READ_STEPS)) {
            loadMetric(StepsRecord.STEPS_COUNT_TOTAL, from, until) { value, problem ->
                if (current == requestGeneration) stepsView.text = if (problem != null) "👣  Passos: sem acesso" else
                    "👣  Passos: ${value?.let { String.format(Locale("pt", "PT"), "%,d", it) } ?: "sem registos"}"
            }
        } else stepsView.text = "👣  Passos: sem permissão"
        if (allowed(HealthPermissions.READ_DISTANCE)) {
            loadMetric(DistanceRecord.DISTANCE_TOTAL, from, until) { value, problem ->
                if (current == requestGeneration) distanceView.text = if (problem != null) "📍  Distância: sem acesso" else
                    "📍  Distância: ${value?.let { String.format(Locale("pt", "PT"), "%.2f km", it.inMeters / 1000.0) } ?: "sem registos"}"
            }
        } else distanceView.text = "📍  Distância: sem permissão"
        if (allowed(HealthPermissions.READ_ACTIVE_CALORIES_BURNED)) {
            loadMetric(ActiveCaloriesBurnedRecord.ACTIVE_CALORIES_TOTAL, from, until) { value, problem ->
                if (current == requestGeneration) caloriesView.text = if (problem != null) "🔥  Energia ativa: sem acesso" else
                    "🔥  Energia ativa: ${value?.let { String.format(Locale("pt", "PT"), "%.0f kcal", it.inCalories) } ?: "sem registos"}"
            }
        } else caloriesView.text = "🔥  Energia ativa: sem permissão"
        if (allowed(HealthPermissions.READ_SLEEP)) {
            val nightStart = date.minusDays(1).atTime(LocalTime.of(18, 0)).atZone(ZoneId.systemDefault()).toInstant()
            val nightEnd = date.atTime(LocalTime.NOON).atZone(ZoneId.systemDefault()).toInstant()
            loadMetric(SleepSessionRecord.SLEEP_DURATION_TOTAL, nightStart, nightEnd) { value, problem ->
                if (current == requestGeneration) sleepView.text = if (problem != null) "🌙  Sono: sem acesso" else
                    "🌙  Sono (última noite): ${value?.let { "${it/3_600_000}h ${(it/60_000)%60}m" } ?: "sem registos"}"
            }
        } else sleepView.text = "🌙  Sono: sem permissão"
        if (allowed(HealthPermissions.READ_STEPS)) repeat(7) { index ->
            val day = date.minusDays((6-index).toLong())
            val start = day.atStartOfDay(ZoneId.systemDefault()).toInstant()
            val stop = if (index == 6) Instant.now() else day.plusDays(1).atStartOfDay(ZoneId.systemDefault()).toInstant()
            loadMetric(StepsRecord.STEPS_COUNT_TOTAL, start, stop) { value, problem ->
                if (current != requestGeneration) return@loadMetric
                val (_, row) = rows[index]
                row.removeAllViews()
                if (problem != null || value == null) {
                    row.addView(label("—", 12f, false, secondary)); return@loadMetric
                }
                val bar = View(this).apply { background = GradientDrawable().apply {
                    setColor(teal); cornerRadius = dp(5).toFloat()
                } }
                val fill = value.coerceAtLeast(0).coerceAtMost(12000).toFloat() / 12000f
                row.addView(bar, LinearLayout.LayoutParams(0, dp(15), fill.coerceAtLeast(0.01f)))
                row.addView(View(this), LinearLayout.LayoutParams(0, dp(15), (1f - fill).coerceAtLeast(0.01f)))
                row.addView(label("  ${value}", 12f, false, fg))
            }
        }
    }
    private fun authorize() {
        if (Build.VERSION.SDK_INT < 34) return
        permissionLauncher.launch(permissions.filterNot { allowed(it) }.toTypedArray())
    }
    private fun managePermissions() {
        if (Build.VERSION.SDK_INT < 34) return
        val intent = Intent(HealthConnectManager.ACTION_MANAGE_HEALTH_PERMISSIONS)
            .putExtra(Intent.EXTRA_PACKAGE_NAME, packageName)
        try { startActivity(intent) } catch (_: Exception) {
            MaterialAlertDialogBuilder(this).setMessage("Abre Definições → Health Connect → Permissões de aplicações → SaúdePrática.")
                .setPositiveButton("OK", null).show()
        }
    }
    private fun <T: Any> loadMetric(type: AggregationType<T>, start: Instant, stop: Instant,
        result: (T?, Exception?) -> Unit) {
        val health = manager ?: return
        try {
            val range = TimeInstantRangeFilter.Builder().setStartTime(start).setEndTime(stop).build()
            val request = AggregateRecordsRequest.Builder<T>(range).addAggregationType(type).build()
            health.aggregate(request, mainExecutor,
                object : OutcomeReceiver<AggregateRecordsResponse<T>, HealthConnectException> {
                    override fun onResult(data: AggregateRecordsResponse<T>) {
                        result(data.get(type), null)
                    }
                    override fun onError(error: HealthConnectException) { result(null, error) }
                })
        } catch (e: Exception) { result(null, e) }
    }
}