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
import android.health.connect.datatypes.HeartRateRecord
import android.health.connect.datatypes.TotalCaloriesBurnedRecord
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
    companion object {
        const val EXTRA_PROFILE_ID = "profile_id"
        const val EXTRA_SETTINGS = "show_health_settings"
    }
    private lateinit var profileId: String
    private lateinit var profileName: String
    private lateinit var content: LinearLayout
    private var manager: HealthConnectManager? = null
    private var requestGeneration = 0
    private var settingsMode = false
    private val prefs by lazy { getSharedPreferences("saudepratica_health_connect", MODE_PRIVATE) }
    private val connectedProfile get() = prefs.getString("linked_profile", "").orEmpty()
    private val permissions = arrayOf(
        HealthPermissions.READ_STEPS,
        HealthPermissions.READ_SLEEP,
        HealthPermissions.READ_DISTANCE,
        HealthPermissions.READ_ACTIVE_CALORIES_BURNED
    )
    // Extra permissions are optional and requested only via Mais > Health Connect.
    private val optionalPermissions = arrayOf(
        HealthPermissions.READ_HEART_RATE,
        HealthPermissions.READ_TOTAL_CALORIES_BURNED
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
        settingsMode = intent.getBooleanExtra(EXTRA_SETTINGS, false)
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
        title.addView(label(if (settingsMode) "Mais · Health Connect" else "Atividade e Saúde", 13f, false, secondary))
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
        content.addView(label(if (settingsMode) "🔐  Health Connect" else "🚶  Atividade e Saúde", 25f, true))
        content.addView(label(if (settingsMode) "Permissões e associação · $profileName"
            else "Passos, sono e energia · dados do Health Connect", 13f, false, secondary),
            LinearLayout.LayoutParams(-1, -2).apply { bottomMargin = dp(16) })
        if (Build.VERSION.SDK_INT < 34 || manager == null) {
            val info = box(content, "Health Connect não disponível",
                "Esta versão utiliza o Health Connect integrado no Android 14 ou mais recente.")
            info.addView(label("A SaúdePrática mantém as outras funcionalidades normalmente.", 13f))
            return
        }
        // All authorization and profile management lives in Mais, never in the dashboard.
        if (settingsMode) { showSettings(); return }
        if (connectedProfile.isNotBlank() && connectedProfile != profileId) {
            val name = ProfileStore(this).all().firstOrNull { it.id == connectedProfile }?.name
                ?: "outro perfil"
            box(content, "Dados associados a outro perfil",
                "O Health Connect está associado a «$name». Para alterar, abre Mais → Health Connect.")
            return
        }
        if (!canRead()) {
            box(content, "Health Connect sem autorização ativa",
                "Para veres passos, sono e calorias, abre Mais → Health Connect e autoriza " +
                    "a leitura para este perfil. Só pedimos acesso quando o escolheres.")
            return
        }
        val info = box(content, "Ligação ativa · $profileName",
            "Valores importados do Health Connect · atualização a pedido.")
        info.addView(action("↻ Atualizar dados") { showScreen() })
        val date = LocalDate.now()
        val summary = box(content, "Hoje · ${date.format(DateTimeFormatter.ofPattern("dd/MM/yyyy"))}")
        val stepsView = label("👣  Passos: a consultar…", 17f, true)
        val distanceView = label("📍  Distância: a consultar…", 16f)
        val caloriesView = label("🔥  Energia ativa: a consultar…", 16f)
        val sleepView = label("🌙  Sono (última noite): a consultar…", 16f)
        val heartView = label("❤️  Ritmo cardíaco médio: a consultar…", 16f)
        val totalEnergyView = label("⚡  Energia total: a consultar…", 16f)
        listOf(stepsView, distanceView, caloriesView, sleepView, heartView, totalEnergyView).forEach {
            it.setPadding(0, dp(9), 0, dp(5)); summary.addView(it)
        }
        val comparison = label("A comparar passos com ontem…", 12f, false, secondary)
        summary.addView(comparison)
        addWeeklyCharts(date, current)
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
                    "🔥  Energia ativa: ${value?.let { String.format(Locale("pt", "PT"), "%.0f kcal", it.inCalories / 1000.0) } ?: "sem registos"}"
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
        // Health Connect native Energy.inCalories is small calories, not kcal.
        if (allowed(HealthPermissions.READ_HEART_RATE)) {
            loadMetric(HeartRateRecord.BPM_AVG, from, until) { value, problem ->
                if (current == requestGeneration) heartView.text = if (problem != null)
                    "❤️  Ritmo cardíaco: sem acesso" else
                    "❤️  Ritmo cardíaco médio: ${value?.let { "$it bpm" } ?: "sem registos"}"
            }
        } else heartView.text = "❤️  Ritmo cardíaco: não autorizado (opcional)"
        if (allowed(HealthPermissions.READ_TOTAL_CALORIES_BURNED)) {
            loadMetric(TotalCaloriesBurnedRecord.ENERGY_TOTAL, from, until) { value, problem ->
                if (current == requestGeneration) totalEnergyView.text = if (problem != null)
                    "⚡  Energia total: sem acesso" else
                    "⚡  Energia total: ${value?.let {
                        String.format(Locale("pt", "PT"), "%.0f kcal", it.inCalories / 1000.0)
                    } ?: "sem registos"}"
            }
        } else totalEnergyView.text = "⚡  Energia total: não autorizada (opcional)"
        if (allowed(HealthPermissions.READ_STEPS)) {
            val yesterday = date.minusDays(1)
            loadMetric(StepsRecord.STEPS_COUNT_TOTAL,
                yesterday.atStartOfDay(ZoneId.systemDefault()).toInstant(),
                date.atStartOfDay(ZoneId.systemDefault()).toInstant()) { value, error ->
                if (current == requestGeneration) comparison.text = if (error != null || value == null)
                    "Sem comparação disponível para ontem" else
                    "Ontem: ${String.format(Locale("pt", "PT"), "%,d", value)} passos · hoje ainda em curso"
            }
        } else comparison.text = "Comparação indisponível"
    }

    private fun showSettings() {
        val linked = connectedProfile
        val selectedPerson = ProfileStore(this).all().firstOrNull { it.id == linked }?.name
            ?: "perfil não identificado"
        val status = when {
            linked.isBlank() -> "Não está associado a nenhum perfil."
            !hasAnyPermission() -> "Permissões Android retiradas. Associado anteriormente a $selectedPerson."
            linked == profileId -> "Ligação ativa para $profileName."
            else -> "Este telemóvel está associado a $selectedPerson."
        }
        val card = box(content, "Associação ao perfil", status +
            " A ligação é local e só um perfil recebe estes dados de cada vez.")
        when {
            linked.isNotBlank() && linked != profileId -> card.addView(action("Associar a $profileName") {
                MaterialAlertDialogBuilder(this).setTitle("Mudar associação?")
                    .setMessage("Os dados deste telemóvel passarão a ser mostrados apenas em $profileName. Confirma que lhe pertencem.")
                    .setNegativeButton("Cancelar", null)
                    .setPositiveButton("Associar") { _, _ ->
                        prefs.edit().putString("linked_profile", profileId).apply()
                        if (!hasAnyPermission()) authorize() else showScreen()
                    }.show()
            })
            !canRead() -> card.addView(action("🔐 Autorizar SaúdePrática") {
                if (linked.isBlank() && hasAnyPermission()) {
                    MaterialAlertDialogBuilder(this).setTitle("Associar os dados a $profileName?")
                        .setMessage("O Health Connect contém dados do utilizador deste telemóvel.")
                        .setNegativeButton("Cancelar", null)
                        .setPositiveButton("Associar") { _, _ ->
                            prefs.edit().putString("linked_profile", profileId).apply()
                            authorize()
                        }.show()
                } else authorize()
            })
        }
        val current = box(content, "Permissões de leitura", "Escolhe o que a SaúdePrática pode consultar. Não pedimos escrita de dados.")
        val available = listOf(
            "Passos" to HealthPermissions.READ_STEPS,
            "Distância" to HealthPermissions.READ_DISTANCE,
            "Calorias ativas" to HealthPermissions.READ_ACTIVE_CALORIES_BURNED,
            "Sono" to HealthPermissions.READ_SLEEP,
            "Frequência cardíaca (opcional)" to HealthPermissions.READ_HEART_RATE,
            "Energia total (opcional)" to HealthPermissions.READ_TOTAL_CALORIES_BURNED
        )
        available.forEach { (text, permission) ->
            current.addView(label((if (allowed(permission)) "✓ " else "○ ") + text,
                13f, false, if (allowed(permission)) fg else secondary))
        }
        if (canRead() && optionalPermissions.any { !allowed(it) }) {
            current.addView(action("Autorizar dados adicionais") {
                permissionLauncher.launch(optionalPermissions.filterNot { allowed(it) }.toTypedArray())
            })
        }
        current.addView(action("Gerir permissões no Android") { managePermissions() })
        if (linked == profileId) current.addView(action("Desligar deste perfil") {
            MaterialAlertDialogBuilder(this).setTitle("Desligar Health Connect?")
                .setMessage("A SaúdePrática deixa de mostrar estes dados no perfil. Para revogar também as permissões, usa as Definições do Android.")
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("Desligar") { _, _ ->
                    prefs.edit().remove("linked_profile").apply(); showScreen()
                }.show()
        })
        val privacy = box(content, "Privacidade", "Consulta apenas local, sem enviar dados para servidores nem para backups.")
        privacy.addView(action("Política de utilização dos dados") {
            startActivity(Intent(this, HealthPermissionsRationaleActivity::class.java))
        })
    }

    private fun addWeeklyCharts(date: LocalDate, generation: Int) {
        data class Series(
            val title: String,
            val values: Array<Double?> = arrayOfNulls(7),
            val display: (Double) -> String,
            val average: (Double) -> String
        )
        val chart = box(content, "Evolução dos últimos 7 dias",
            "Seleciona a medição. A comparação usa os registos disponíveis no Health Connect.")
        val datasets = listOf(
            Series("Passos", display = { String.format(Locale("pt", "PT"), "%.0f", it) },
                average = { String.format(Locale("pt", "PT"), "%.0f passos/dia", it) }),
            Series("Distância", display = { String.format(Locale("pt", "PT"), "%.2f km", it) },
                average = { String.format(Locale("pt", "PT"), "%.2f km/dia", it) }),
            Series("Energia ativa", display = { String.format(Locale("pt", "PT"), "%.0f kcal", it) },
                average = { String.format(Locale("pt", "PT"), "%.0f kcal/dia", it) }),
            Series("Sono", display = { "${it.toInt() / 60}h ${it.toInt() % 60}m" },
                average = { "${it.toInt() / 60}h ${it.toInt() % 60}m/noite" })
        )
        var selection = 0
        val selector = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        chart.addView(selector)
        val panel = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        chart.addView(panel)
        fun redraw() {
            panel.removeAllViews()
            val set = datasets[selection]
            val valid = set.values.filterNotNull()
            val avg = if (valid.isEmpty()) null else valid.average()
            val maximum = (valid.maxOrNull() ?: 0.0).coerceAtLeast(1.0)
            panel.addView(label("${set.title} · " + (avg?.let { "Média ${set.average(it)}" } ?: "Sem dados"),
                14f, true, teal).apply { setPadding(0, dp(12), 0, dp(8)) })
            val names = arrayOf("seg", "ter", "qua", "qui", "sex", "sáb", "dom")
            for (i in 0..6) {
                val day = date.minusDays((6 - i).toLong())
                val idx = day.dayOfWeek.value - 1
                val value = set.values[i]
                val row = LinearLayout(this).apply {
                    orientation = LinearLayout.HORIZONTAL
                    gravity = Gravity.CENTER_VERTICAL
                }
                val title = label(names[idx], 12f, true)
                title.gravity = Gravity.CENTER_VERTICAL
                row.addView(title, LinearLayout.LayoutParams(dp(38), dp(37)))
                val graphic = LinearLayout(this).apply {
                    orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL
                }
                row.addView(graphic, LinearLayout.LayoutParams(0, dp(37), 1f))
                if (value != null && value > 0) {
                    val fill = (value / maximum).toFloat().coerceIn(0.02f, 1f)
                    graphic.addView(View(this).apply {
                        background = GradientDrawable().apply {
                            setColor(teal); cornerRadius = dp(6).toFloat()
                        }
                    }, LinearLayout.LayoutParams(0, dp(16), fill))
                    graphic.addView(View(this), LinearLayout.LayoutParams(0, dp(16),
                        (1f - fill).coerceAtLeast(0.001f)))
                }
                val amount = label(value?.let { set.display(it) } ?: "—", 11f, false, secondary)
                amount.gravity = Gravity.END or Gravity.CENTER_VERTICAL
                row.addView(amount, LinearLayout.LayoutParams(dp(93), dp(37)))
                panel.addView(row)
            }
            panel.addView(label("O dia de hoje pode estar incompleto. Valores ausentes não contam para a média.",
                11f, false, secondary))
        }
        listOf(listOf(0, 1), listOf(2, 3)).forEach { pair ->
            val row = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
            pair.forEach { index ->
                val button = action(datasets[index].title) {
                    selection = index; redraw()
                }
                button.textSize = 11f
                row.addView(button, LinearLayout.LayoutParams(0, dp(46), 1f))
            }
            selector.addView(row)
        }
        redraw()
        fun <T: Any> querySeries(index: Int, permission: String, metric: AggregationType<T>,
            convert: (T) -> Double, sleep: Boolean = false) {
            if (!allowed(permission)) return
            repeat(7) { dayIndex ->
                val day = date.minusDays((6 - dayIndex).toLong())
                val start = if (sleep) day.minusDays(1).atTime(18, 0)
                    .atZone(ZoneId.systemDefault()).toInstant()
                    else day.atStartOfDay(ZoneId.systemDefault()).toInstant()
                val end = if (sleep) day.atTime(12, 0).atZone(ZoneId.systemDefault()).toInstant()
                    else if (dayIndex == 6) Instant.now()
                    else day.plusDays(1).atStartOfDay(ZoneId.systemDefault()).toInstant()
                loadMetric(metric, start, end) { result, error ->
                    if (generation != requestGeneration) return@loadMetric
                    if (error == null) datasets[index].values[dayIndex] = result?.let(convert)
                    if (index == selection) redraw()
                }
            }
        }
        querySeries(0, HealthPermissions.READ_STEPS, StepsRecord.STEPS_COUNT_TOTAL,
            { it.toDouble() })
        querySeries(1, HealthPermissions.READ_DISTANCE, DistanceRecord.DISTANCE_TOTAL,
            { it.inMeters / 1000.0 })
        querySeries(2, HealthPermissions.READ_ACTIVE_CALORIES_BURNED,
            ActiveCaloriesBurnedRecord.ACTIVE_CALORIES_TOTAL, { it.inCalories / 1000.0 })
        querySeries(3, HealthPermissions.READ_SLEEP, SleepSessionRecord.SLEEP_DURATION_TOTAL,
            { it.toDouble() / 60000.0 }, true)
    }

    private fun authorize() {
        if (Build.VERSION.SDK_INT < 34) return
        val needed = permissions.filterNot { allowed(it) }.toTypedArray()
        if (needed.isEmpty()) {
            prefs.edit().putString("linked_profile", profileId).apply()
            showScreen()
        } else permissionLauncher.launch(needed)
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