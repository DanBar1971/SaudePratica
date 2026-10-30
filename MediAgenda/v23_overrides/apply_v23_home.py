from pathlib import Path

root = Path("build-src/MediAgenda_Android_v1")
main = root/"app/src/main/java/com/mediagenda/app/MainActivity.kt"
manifest = root/"app/src/main/AndroidManifest.xml"
gradle = root/"app/build.gradle.kts"
wellnessFile = root/"app/src/main/java/com/mediagenda/app/data/WellnessStore.kt"
wellnessActivity = root/"app/src/main/java/com/mediagenda/app/WellnessActivity.kt"
wellnessFile.write_text(
    Path("MediAgenda/v23_overrides/WellnessStore.kt").read_text(encoding="utf-8"),
    encoding="utf-8")
wellnessActivity.write_text(
    Path("MediAgenda/v23_overrides/WellnessActivity.kt").read_text(encoding="utf-8"),
    encoding="utf-8")

def sub(s, old, new, label):
    if old not in s:
        raise RuntimeError(f"SaúdePrática 1.9.4 missing {label}: {old[:100]}")
    return s.replace(old, new, 1)

s = main.read_text(encoding="utf-8")
s = sub(s, '''    private fun showMedication() {''',
'''    private data class DashboardModule(
        val icon: String, val title: String, val subtitle: String, val action: () -> Unit
    )

    /**
     * Scalable 2-column menu, rather than squeezing every feature into the
     * bottom navigation. Each dashboard tile has a working destination.
     */
    private fun showHome() {
        content.removeAllViews()
        screenHeader("⌂", "Início", "A sua saúde, tudo num só lugar")

        val scroll = ScrollView(this).apply {
            overScrollMode = View.OVER_SCROLL_NEVER
            clipToPadding = false
        }
        val box = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        val who = profileName().ifBlank { "Utilizador" }
        box.addView(TextView(this).apply {
            text = "Olá, $who!"
            textSize = 23f
            setTypeface(typeface, Typeface.BOLD)
            setTextColor(mainTextColor)
            setPadding(dp(4), dp(10), 0, dp(4))
        })
        val numMeds = repo.loadMedications().size
        val numAppointments = repo.loadAppointments().count { !it.done }
        box.addView(TextView(this).apply {
            text = "$numMeds medicamento(s)  ·  $numAppointments marcação(ões) por concluir"
            textSize = 13f
            setTextColor(muted)
            setPadding(dp(4), 0, 0, dp(17))
        })

        val options = listOf(
            DashboardModule("💊", "Medicação", "Tomas e avisos") { showMedication() },
            DashboardModule("📅", "Agenda", "Consultas e exames") { showAgenda() },
            DashboardModule("📂", "Documentos", "PDFs e imagens") { showDocuments() },
            DashboardModule("💧", "Beber água", "Hidratação") { openWellness("water") },
            DashboardModule("🥗", "Alimentação", "Regime do tratamento") { openWellness("diet") },
            DashboardModule("👓", "Óculos", "Graduação e receita") { openWellness("glasses") },
            DashboardModule("✚", "Farmácias", "Perto de mim e serviço") { showPharmacies() },
            DashboardModule("⚙", "Mais", "Utilizadores e opções") { showDataTools() }
        )
        options.chunked(2).forEach { pair ->
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

    private fun showMedication() {''', "dashboard UI")

s = sub(s,
    '''        renderBottomNav(0)
    }

    private fun nextMedicationTime(''',
    '''        renderBottomNav(1)
    }

    private fun nextMedicationTime(''', "medication nav index")

s = sub(s,
    '''        renderBottomNav(1)
    }

    private var documentPurpose''',
    '''        renderBottomNav(2)
    }

    private var documentPurpose''', "agenda nav index")

s = sub(s,
    '''        renderBottomNav(3)
    }

    private fun activateProfile(''',
    '''        renderBottomNav(0)
    }

    private fun activateProfile(''', "pharmacies nav index")

s = sub(s,
    '''        reschedule()
        showMedication()
    }

    private fun showProfileSelection()''',
    '''        reschedule()
        showHome()
    }

    private fun showProfileSelection()''', "start at dashboard")

s = sub(s,
'''        val tabs = listOf(
            Triple("💊", "Medicação") { showMedication() },
            Triple("📅", "Agenda") { showAgenda() },
            Triple("📂", "Docs") { showDocuments() },
            Triple("✚", "Farmácias") { showPharmacies() },
            Triple("⚙", "Mais") { showDataTools() }
        )''',
'''        val tabs = listOf(
            Triple("⌂", "Início") { showHome() },
            Triple("💊", "Medicação") { showMedication() },
            Triple("📅", "Agenda") { showAgenda() },
            Triple("📂", "Docs") { showDocuments() },
            Triple("⚙", "Mais") { showDataTools() }
        )''', "bottom navigation")

s = sub(s, '''        box.addView(infoCard("ℹ️", "Acerca",''',
'''        box.addView(infoCard("💧", "Hidratação", "Registos e lembretes personalizados") {
            openWellness("water")
        })
        box.addView(infoCard("👓", "Graduação dos óculos", "Guardar os valores da receita por utilizador") {
            openWellness("glasses")
        })
        box.addView(infoCard("🥗", "Alimentação e Regime", "Guardar as indicações de alimentação durante tratamentos") {
            openWellness("diet")
        })
        box.addView(infoCard("ℹ️", "Acerca",''', "more new modules")

s = sub(s,
    '''            profileDraft = null
            dialog.dismiss()
            reschedule()
            showMedication()
        }
    }''',
    '''            profileDraft = null
            dialog.dismiss()
            reschedule()
            showHome()
        }
    }''', "after changing user profile")

main.write_text(s,encoding="utf-8")

m = manifest.read_text(encoding="utf-8")
m = sub(m,
'''        <activity android:name=".DocumentsActivity"''',
'''        <activity android:name=".WellnessActivity" android:exported="false" />
        <activity android:name=".DocumentsActivity"''', "new activity")
manifest.write_text(m,encoding="utf-8")

g = gradle.read_text(encoding="utf-8")
if 'applicationId = "com.mediagenda.app.stable"' not in g:
    raise RuntimeError("Refusing to change app ID and existing user data")
if 'versionCode = 13' not in g or 'versionName = "1.9.3"' not in g:
    raise RuntimeError("Expected v1.9.3 base not found")
g = g.replace('versionCode = 13','versionCode = 14',1)
g = g.replace('versionName = "1.9.3"','versionName = "1.9.4"',1)
gradle.write_text(g,encoding="utf-8")
print("SaúdePrática 1.9.4: dashboard, hydration, optical prescription, treatment diet form.")
