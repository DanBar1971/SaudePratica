from pathlib import Path

root = Path("build-src/MediAgenda_Android_v1")
p = root / "app/src/main/java/com/mediagenda/app/MainActivity.kt"
s = p.read_text(encoding="utf-8")

def replace(old, new, where="MainActivity.kt"):
    global s
    if old not in s:
        raise RuntimeError("v1.5 patch target missing in " + where + ": " + old[:125])
    s = s.replace(old, new, 1)

replace("import android.content.pm.PackageManager\n",
        "import android.content.pm.PackageManager\nimport android.content.res.Configuration\n")
replace("import androidx.appcompat.app.AppCompatActivity\n",
        "import androidx.appcompat.app.AppCompatActivity\nimport androidx.appcompat.app.AppCompatDelegate\n")
replace("import androidx.core.content.FileProvider\n",
        "import androidx.core.content.FileProvider\nimport androidx.core.view.ViewCompat\nimport androidx.core.view.WindowCompat\nimport androidx.core.view.WindowInsetsCompat\nimport androidx.core.view.WindowInsetsControllerCompat\n")

# Use a real dark colour palette, not just an Android dialog style change.
start = s.index('    private val primary = Color.parseColor(')
end = s.index('\n\n    private val importJsonLauncher', start)
s = s[:start] + '''    private val isDarkPalette: Boolean
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
    private val danger get() = Color.parseColor(if (isDarkPalette) "#FF8585" else "#B42318")''' + s[end:]

replace('''    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)''',
'''    override fun onCreate(savedInstanceState: Bundle?) {
        val themeMode = getSharedPreferences("mediagenda_ui", MODE_PRIVATE)
            .getString("theme_mode", "system")
        AppCompatDelegate.setDefaultNightMode(
            when (themeMode) {
                "dark" -> AppCompatDelegate.MODE_NIGHT_YES
                "light" -> AppCompatDelegate.MODE_NIGHT_NO
                else -> AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM
            }
        )
        super.onCreate(savedInstanceState)''')

replace('''        buildShell()
        if (profileName().isBlank())''',
'''        configureSystemBars()
        buildShell()
        if (profileName().isBlank())''')

replace('''    private fun buildShell() {
        root = LinearLayout(this).apply {''',
'''    private fun configureSystemBars() {
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
        root = LinearLayout(this).apply {''')

replace('''        setContentView(root)
    }

    private fun showMedication()''',
'''        // On Android 15 the app draws edge-to-edge. Keep content out of the
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

    private fun showMedication()''')

# Add links and appearance controls on the main More screen.
anchor = '        box.addView(infoCard("👤", "Perfil", profileName().ifBlank { "Definir nome do perfil" }) { showProfileDialog(false) })'
replace(anchor, anchor + '''
        box.addView(infoCard("🏥", "Abrir SNS 24", "Atalho para a aplicação oficial SNS 24. Se não estiver instalada, pode instalá-la através da Google Play.") {
            openSns24()
        })
        box.addView(infoCard("◐", "Aspeto da aplicação", "Escolha entre automático, claro e escuro.") {
            showThemeDialog()
        })''')

replace('''    // --- Data / profile ---
    private fun showExportJsonDialog()''',
'''    // --- SNS 24 and app theme ---
    private fun openSns24() {
        val snsPackage = "pt.minsaude.spms.ces"
        val launchIntent = packageManager.getLaunchIntentForPackage(snsPackage)
        if (launchIntent != null) {
            runCatching { startActivity(launchIntent) }.onFailure {
                Toast.makeText(this, "Não foi possível abrir a app SNS 24.", Toast.LENGTH_LONG).show()
            }
            return
        }
        MaterialAlertDialogBuilder(this)
            .setTitle("SNS 24 não instalada")
            .setMessage("Instale a aplicação oficial SNS 24 da SPMS para abrir diretamente a partir da MediAgenda.")
            .setPositiveButton("Abrir Google Play") { _, _ ->
                val market = Intent(Intent.ACTION_VIEW, Uri.parse("market://details?id=$snsPackage"))
                runCatching { startActivity(market) }.onFailure {
                    openUrl("https://play.google.com/store/apps/details?id=$snsPackage")
                }
            }
            .setNegativeButton("Cancelar", null)
            .show()
    }

    private fun showThemeDialog() {
        val options = arrayOf("Automático (seguir o telemóvel)", "Claro", "Escuro")
        val modes = arrayOf("system", "light", "dark")
        val pref = getSharedPreferences("mediagenda_ui", MODE_PRIVATE)
        val current = modes.indexOf(pref.getString("theme_mode", "system"))
            .coerceAtLeast(0)
        MaterialAlertDialogBuilder(this)
            .setTitle("Aspeto da MediAgenda")
            .setSingleChoiceItems(options, current) { dialog, which ->
                pref.edit().putString("theme_mode", modes[which]).apply()
                dialog.dismiss()
                // Recreation refreshes both the Material theme and custom UI colours.
                recreate()
            }
            .setNegativeButton("Cancelar", null)
            .show()
    }

    // --- Data / profile ---
    private fun showExportJsonDialog()''')

p.write_text(s, encoding="utf-8")

# AppCompat Material DayNight theme, including dialogs and system default theme.
p = root / "app/src/main/res/values/themes.xml"
s = p.read_text(encoding="utf-8")
old = 'parent="Theme.Material3.Light.NoActionBar"'
if old not in s:
    raise RuntimeError("v1.5 Material theme parent missing")
s = s.replace(old, 'parent="Theme.Material3.DayNight.NoActionBar"')
p.write_text(s, encoding="utf-8")

# Package visibility on Android 11+ is required for getLaunchIntentForPackage().
p = root / "app/src/main/AndroidManifest.xml"
s = p.read_text(encoding="utf-8")
old = '    <application android:allowBackup='
if old not in s:
    raise RuntimeError("v1.5 manifest application tag missing")
s = s.replace(old,
    '    <queries><package android:name="pt.minsaude.spms.ces" /></queries>\n' + old, 1)
p.write_text(s, encoding="utf-8")

# Increment version while preserving app ID and existing stable signing key.
p = root / "app/build.gradle.kts"
s = p.read_text(encoding="utf-8")
if 'applicationId = "com.mediagenda.app.stable"' not in s:
    raise RuntimeError("Expected stable package ID is missing")
if 'versionCode = 5' not in s or 'versionName = "1.4.0"' not in s:
    raise RuntimeError("Expected MediAgenda v1.4 version missing")
s = s.replace('versionCode = 5', 'versionCode = 6')
s = s.replace('versionName = "1.4.0"', 'versionName = "1.5.0"')
p.write_text(s, encoding="utf-8")

print("MediAgenda v1.5: SNS 24 shortcut + immersive Android navigation + DayNight theme")
