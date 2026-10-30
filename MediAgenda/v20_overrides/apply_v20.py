from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
main=root/"app/src/main/java/com/mediagenda/app/MainActivity.kt"
gradle=root/"app/build.gradle.kts"
s=main.read_text(encoding="utf-8")
start=s.index("    private fun showAboutSaudePratica() {")
end=s.index("    private fun showMedicationAddOptions() {",start)
replacement=r'''    private fun showAboutSaudePratica() {
        val version = try {
            packageManager.getPackageInfo(packageName, 0).versionName ?: "1.9.1"
        } catch (_: Exception) { "1.9.1" }
        val teal = Color.rgb(0, 205, 193)
        val white = Color.WHITE
        val muted = Color.rgb(190, 210, 215)
        val density = resources.displayMetrics.density
        fun dp(n: Int) = (n * density + 0.5f).toInt()
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_HORIZONTAL
            setPadding(dp(24), dp(18), dp(24), dp(12))
        }
        val icon = android.widget.ImageView(this).apply {
            setImageResource(R.drawable.saude_icon)
            scaleType = android.widget.ImageView.ScaleType.FIT_CENTER
            layoutParams = LinearLayout.LayoutParams(dp(94), dp(94)).apply {
                bottomMargin = dp(12)
            }
        }
        layout.addView(icon)
        fun line(value: String, size: Float, color: Int, bold: Boolean = false, margin: Int = 0): android.widget.TextView {
            val tv = android.widget.TextView(this).apply {
                text = value
                textSize = size
                setTextColor(color)
                gravity = Gravity.CENTER
                if (bold) setTypeface(null, android.graphics.Typeface.BOLD)
                setPadding(0, dp(margin), 0, dp(3))
            }
            layout.addView(tv)
            return tv
        }
        line("SaúdePrática", 25f, white, true)
        line("tudo num só lugar", 13f, teal)
        line("Versão $version", 15f, white, false, 18)
        line("Android ${android.os.Build.VERSION.RELEASE} (API ${android.os.Build.VERSION.SDK_INT})", 13f, muted)
        line("Desenvolvido por", 12f, muted, false, 20)
        line("Daniel Barradas", 17f, white, true)
        line("daniel.barradas@gmail.com", 14f, teal, false, 10).apply {
            setOnClickListener {
                val intent = android.content.Intent(
                    android.content.Intent.ACTION_SENDTO,
                    Uri.parse("mailto:daniel.barradas@gmail.com")
                )
                try { startActivity(intent) } catch (_: Exception) {
                    android.widget.Toast.makeText(this@MainActivity, "Nenhuma aplicação de email disponível", android.widget.Toast.LENGTH_SHORT).show()
                }
            }
        }
        line("Medicação · Consultas · Documentos de saúde", 12f, muted, false, 20)
        MaterialAlertDialogBuilder(this)
            .setView(layout)
            .setPositiveButton("Fechar", null)
            .show()
    }

'''
s=s[:start]+replacement+s[end:]
main.write_text(s,encoding="utf-8")
g=gradle.read_text(encoding="utf-8")
assert 'versionCode = 10' in g and 'versionName = "1.9.0"' in g
g=g.replace('versionCode = 10','versionCode = 11',1).replace('versionName = "1.9.0"','versionName = "1.9.1"',1)
gradle.write_text(g,encoding="utf-8")
print("SaúdePrática v1.9.1: About layout updated")
