from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
src=root/"app/src/main/java/com/mediagenda/app"
(src/"data/ProfileStore.kt").write_text(Path("MediAgenda/v21_overrides/ProfileStore.kt").read_text(encoding="utf-8"),encoding="utf-8")
def sub(s,a,b):
 if a not in s:raise RuntimeError("v1.9.2 missing anchor "+a[:95])
 return s.replace(a,b,1)
f=src/"data/DataRepository.kt";s=f.read_text(encoding="utf-8")
s=sub(s,'class DataRepository(private val context: Context) {\n    private val medFile = File(context.filesDir, "medicacao.json")\n    private val agendaFile = File(context.filesDir, "agenda.json")',
'''class DataRepository(private val context: Context, private val profileId: String = "legacy") {
    private val profileDirectory: File =
        if (profileId == "legacy") context.filesDir
        else {
            require(profileId.matches(Regex("[0-9a-fA-F-]{36}"))) { "Identificador de perfil inválido" }
            File(context.filesDir, "saudepratica_profiles/$profileId").apply { mkdirs() }
        }
    private val medFile = File(profileDirectory, "medicacao.json")
    private val agendaFile = File(profileDirectory, "agenda.json")''')
f.write_text(s,encoding="utf-8")
f=src/"MainActivity.kt";s=f.read_text(encoding="utf-8")
s=sub(s,'import com.mediagenda.app.data.DataRepository','import com.mediagenda.app.data.DataRepository\nimport com.mediagenda.app.data.ProfileStore\nimport com.mediagenda.app.data.HealthProfile')
s=sub(s,'    private lateinit var repo: DataRepository','    private lateinit var repo: DataRepository\n    private val profiles by lazy { ProfileStore(this) }\n    private var activeProfileId = "legacy"')
s=sub(s,'''        repo = DataRepository(this)
        repo.ensureFiles()
        requestNotificationPermission()
        requestExactAlarmAccess()
        configureSystemBars()
        buildShell()
        if (profileName().isBlank()) showProfileDialog(firstRun = true)
        reschedule()
        showMedication()''','''        // Migrate the original user's files and profile without deleting data.
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
        }''')
s=sub(s,'    private fun showDataTools() {','''    private fun activateProfile(profile: HealthProfile) {
        activeProfileId = profile.id
        repo = DataRepository(this, profile.id)
        repo.ensureFiles()
        profileDraft = null
        bottomNav.visibility = View.VISIBLE
        reschedule()
        showMedication()
    }

    private fun showProfileSelection() {
        val available = profiles.all()
        if (available.size == 1) {
            activateProfile(available.first())
            return
        }
        content.removeAllViews()
        bottomNav.visibility = View.GONE
        val scroller = ScrollView(this).apply { overScrollMode = View.OVER_SCROLL_NEVER }
        val box = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(4), dp(18), dp(4), dp(24))
        }
        box.addView(android.widget.ImageView(this).apply {
            setImageResource(R.drawable.saude_icon)
            scaleType = android.widget.ImageView.ScaleType.FIT_CENTER
        }, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(130)))
        box.addView(TextView(this).apply {
            text = "Quem vai utilizar a SaúdePrática?"
            textSize = 22f
            setTypeface(typeface, Typeface.BOLD)
            gravity = Gravity.CENTER
            setTextColor(mainTextColor)
            setPadding(dp(8), dp(18), dp(8), dp(18))
        })
        available.forEach { profile ->
            box.addView(infoCard("👤", profile.name, "Abrir a medicação e agenda deste utilizador") {
                activateProfile(profile)
            })
        }
        scroller.addView(box)
        content.addView(scroller, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f))
    }

    private fun showCreateProfileDialog() {
        val box = formBox()
        val name = input("Nome do novo utilizador", "")
        box.addView(name.container)
        val dialog = MaterialAlertDialogBuilder(this)
            .setTitle("Adicionar utilizador")
            .setMessage("Cada utilizador terá medicamentos, consultas e dados separados. Não é necessária palavra-passe.")
            .setView(scroll(box))
            .setNegativeButton("Cancelar", null)
            .setPositiveButton("Criar", null)
            .show()
        dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE).setOnClickListener {
            try {
                val created = profiles.create(name.edit.text.toString())
                dialog.dismiss()
                activateProfile(created)
            } catch (e: IllegalArgumentException) {
                name.edit.error = e.message
            } catch (e: Exception) {
                showError(e.message ?: "Não foi possível criar o utilizador.")
            }
        }
    }

    private fun showDataTools() {''')
s=sub(s,'        box.addView(infoCard("👤", "Perfil", profileName().ifBlank { "Definir nome do perfil" }) { showProfileDialog(false) })','''        box.addView(infoCard("👤", "Perfil atual", profileName().ifBlank { "Definir nome do perfil" }) { showProfileDialog(false) })
        box.addView(infoCard("👥", "Escolher utilizador", profiles.all().size.toString() + " utilizador(es) registado(s)") {
            showProfileSelection()
        })
        box.addView(infoCard("➕", "Adicionar utilizador", "Criar um perfil com medicação e agenda próprias, sem palavra-passe") {
            showCreateProfileDialog()
        })''')
s=sub(s,'''                background = rounded(softGreen, 22f)
            })
        }
        content.addView(top)''','''                background = rounded(softGreen, 22f)
                if (profiles.all().size > 1) {
                    setOnClickListener { showProfileSelection() }
                    contentDescription = "Mudar utilizador: $profile"
                }
            })
        }
        content.addView(top)''')
s=sub(s,'''    private fun profileName(): String = getSharedPreferences("mediagenda_profile", MODE_PRIVATE).getString("name", "")?.trim().orEmpty()

    private fun showProfileDialog(firstRun: Boolean) {
        val prefs = getSharedPreferences("mediagenda_profile", MODE_PRIVATE)''','''    private fun profileName(): String = getSharedPreferences(profiles.preferencesFor(activeProfileId), MODE_PRIVATE)
        .getString("name", "")?.trim().orEmpty()

    private fun showProfileDialog(firstRun: Boolean) {
        val prefs = getSharedPreferences(profiles.preferencesFor(activeProfileId), MODE_PRIVATE)''')
s=sub(s,'''            prefs.edit()
                .putString("name", n)
                .putString("nif", fiscal)
                .putString("sns_number", health)
                .apply()
            profileDraft = null
            dialog.dismiss()
            showMedication()''','''            if (n.isBlank()) {
                name.edit.error = "Indique um nome."
                return@setOnClickListener
            }
            try {
                if (profiles.all().isEmpty()) {
                    val created = profiles.create(n)
                    activeProfileId = created.id
                    repo = DataRepository(this, created.id)
                    repo.ensureFiles()
                } else {
                    profiles.rename(activeProfileId, n)
                }
            } catch (e: IllegalArgumentException) {
                name.edit.error = e.message
                return@setOnClickListener
            }
            prefs.edit()
                .putString("name", n)
                .putString("nif", fiscal)
                .putString("sns_number", health)
                .apply()
            profileDraft = null
            dialog.dismiss()
            reschedule()
            showMedication()''')
s=sub(s,'    private fun reschedule() = NotificationScheduler(this).scheduleAll(repo.loadMedications(),repo.loadAppointments())','    private fun reschedule() = NotificationScheduler(this).scheduleAllProfiles()')
s=s.replace('setTitle(if (firstRun) "Bem-vindo à MediAgenda" else "Editar perfil")','setTitle(if (firstRun) "Bem-vindo à SaúdePrática" else "Editar perfil")')
s=s.replace('"Backup completo", "Cria um único JSON com medicação e agenda."','"Backup do utilizador atual", "Cria um JSON com medicação e agenda deste perfil."')
f.write_text(s,encoding="utf-8")
g=root/"app/build.gradle.kts";s=g.read_text(encoding="utf-8")
assert 'applicationId = "com.mediagenda.app.stable"' in s
assert 'versionCode = 11' in s and 'versionName = "1.9.1"' in s
g.write_text(s.replace('versionCode = 11','versionCode = 12',1).replace('versionName = "1.9.1"','versionName = "1.9.2"',1),encoding="utf-8")
print("SaúdePrática 1.9.2 multi-user profiles applied")
