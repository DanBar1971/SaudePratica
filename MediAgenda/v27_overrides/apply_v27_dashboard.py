from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1")
source=root/"app/src/main/java/com/mediagenda/app"
(source/"data/ProfileMediaStore.kt").write_text(
    Path("MediAgenda/v27_overrides/ProfileMediaStore.kt").read_text(encoding="utf-8"),encoding="utf-8")
(source/"ProfileMediaActivity.kt").write_text(
    Path("MediAgenda/v27_overrides/ProfileMediaActivity.kt").read_text(encoding="utf-8"),encoding="utf-8")

file=source/"MainActivity.kt"
s=file.read_text(encoding="utf-8")
def sub(old,new,label):
    global s
    if old not in s: raise RuntimeError("v1.9.8 missing "+label+": "+old[:120])
    s=s.replace(old,new,1)

sub('''import com.mediagenda.app.data.ProfileStore''',
'''import com.mediagenda.app.data.ProfileStore
import com.mediagenda.app.data.ProfileMediaStore''',"avatar repository import")

sub('''    private var extendedProfileDraft: Map<String, String>? = null''',
'''    private var extendedProfileDraft: Map<String, String>? = null
    private val editProfileImages = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) {
        // After selecting a portrait / CC image, reopen the same draft without
        // discarding unsaved identity or care-home fields.
        if (profiles.all().any { it.id == activeProfileId }) showProfileDialog(false)
    }
    private fun userAvatar(profileId: String, size: Int = 100): android.graphics.Bitmap? =
        runCatching { ProfileMediaStore(this, profileId).photo("avatar", size) }.getOrNull()''',
"result launcher and avatar")

sub('''            DashboardModule("🥗", "Alimentação", "Regime do tratamento") { openWellness("diet") },
            DashboardModule("👓", "Óculos", "Graduação e receita") { openWellness("glasses") },''',
'''            DashboardModule("🥗", "Nutrição", "Plano alimentar e restrições") { openWellness("diet") },
            DashboardModule("👓", "Saúde Visual", "Graduação e receita óptica") { openWellness("glasses") },''',
"better module names")

sub('''            DashboardModule("✚", "Farmácias", "Perto de mim e serviço") { showPharmacies() },
            DashboardModule("⚙", "Mais", "Utilizadores e opções") { showDataTools() }''',
'''            DashboardModule("✚", "Farmácias", "Perto de mim e serviço") { showPharmacies() },
            DashboardModule("🏥", "SNS 24", "Aplicação oficial de saúde") { openSns24() },
            DashboardModule("⚙", "Mais", "Utilizadores e opções") { showDataTools() }''',
"SNS 24 penultimate, Mais retained last")

sub('''        box.addView(infoCard("🏥", "Abrir SNS 24", "Atalho para a aplicação oficial SNS 24. Se não estiver instalada, pode instalá-la através da Google Play.") {
            openSns24()
        })
''','',"remove only SNS 24 from Mais")

sub('''        available.forEach { profile ->
            box.addView(infoCard("👤", profile.name, "Abrir a medicação e agenda deste utilizador") {
                activateProfile(profile)
            })
        }''',
'''        available.forEach { profile ->
            val card=materialCard(stroke=border,bg=surface,radius=19f,elevation=1f)
            val row=LinearLayout(this).apply {
                orientation=LinearLayout.HORIZONTAL
                gravity=Gravity.CENTER_VERTICAL
                setPadding(dp(13),dp(13),dp(13),dp(13))
            }
            val avatar=userAvatar(profile.id,160)
            if (avatar!=null) {
                row.addView(android.widget.ImageView(this).apply {
                    setImageBitmap(avatar)
                    scaleType=android.widget.ImageView.ScaleType.CENTER_CROP
                    clipToOutline=true
                    background=rounded(softGreen,30f)
                },LinearLayout.LayoutParams(dp(56),dp(56)))
            }else {
                row.addView(TextView(this).apply {
                    text="👤"
                    textSize=30f
                    gravity=Gravity.CENTER
                    background=rounded(softGreen,30f)
                },LinearLayout.LayoutParams(dp(56),dp(56)))
            }
            val words=LinearLayout(this).apply{
                orientation=LinearLayout.VERTICAL
                setPadding(dp(12),0,0,0)
            }
            words.addView(TextView(this).apply{
                text=profile.name
                textSize=18f
                setTextColor(mainTextColor)
                setTypeface(typeface,Typeface.BOLD)
            })
            val fullName=getSharedPreferences(profiles.preferencesFor(profile.id),MODE_PRIVATE)
                .getString("full_name","").orEmpty()
            words.addView(TextView(this).apply{
                text=fullName.ifBlank{"Abrir este utilizador"}
                textSize=13f
                setTextColor(muted)
                maxLines=2
            })
            row.addView(words,LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f))
            row.addView(TextView(this).apply{
                text="›";textSize=28f;setTextColor(primaryDark)
            })
            card.addView(row)
            card.setOnClickListener{activateProfile(profile)}
            box.addView(card,LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT)
                .apply{bottomMargin=dp(12)})
        }''',
"chooser avatar")

sub('''        val profile = profileName()
        if (profile.isNotBlank()) {
            top.addView(TextView(this).apply {
                text = profile.take(12)
                textSize = 12f
                setTextColor(primaryDark)
                gravity = Gravity.CENTER
                setPadding(dp(10), dp(7), dp(10), dp(7))
                background = rounded(softGreen, 22f)
                if (profiles.all().size > 1) {
                    setOnClickListener { showProfileSelection() }
                    contentDescription = "Mudar utilizador: $profile"
                }
            })
        }''',
'''        val profile = profileName()
        if (profile.isNotBlank()) {
            val profileBadge=LinearLayout(this).apply{
                orientation=LinearLayout.HORIZONTAL
                gravity=Gravity.CENTER_VERTICAL
                background=rounded(softGreen,22f)
                setPadding(dp(6),dp(5),dp(10),dp(5))
            }
            userAvatar(activeProfileId,80)?.let {bitmap->
                profileBadge.addView(android.widget.ImageView(this).apply{
                    setImageBitmap(bitmap)
                    scaleType=android.widget.ImageView.ScaleType.CENTER_CROP
                    clipToOutline=true
                    background=rounded(softGreen,18f)
                },LinearLayout.LayoutParams(dp(28),dp(28)).apply{marginEnd=dp(5)})
            }
            profileBadge.addView(TextView(this).apply{
                text=profile.take(12)
                textSize=12f
                setTextColor(primaryDark)
                gravity=Gravity.CENTER
            })
            if (profiles.all().size>1){
                profileBadge.setOnClickListener{showProfileSelection()}
                profileBadge.contentDescription="Mudar utilizador: $profile"
            }
            top.addView(profileBadge)
        }''',
"profile photo badge")

file.write_text(s,encoding="utf-8")
print("v1.9.8: SNS24 penultimate on Home only, Mais retained, names improved and profile photos displayed.")
