from pathlib import Path
file=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app/MainActivity.kt")
s=file.read_text(encoding="utf-8")
def edit(old,new,label):
    global s
    if old not in s:raise RuntimeError("v1.9.8 extended profile missing "+label+": "+old[:110])
    s=s.replace(old,new,1)

edit('''        val healthUnit = input("Unidade de saúde", extendedProfileDraft?.get("health_unit")
            ?: prefs.getString("health_unit", "").orEmpty())
        listOf(name, fullName, birth, gender, height, nif, sns, adse, niss, address, healthUnit)
            .forEach { box.addView(it.container) }''',
'''        val healthUnit = input("Unidade de saúde", extendedProfileDraft?.get("health_unit")
            ?: prefs.getString("health_unit", "").orEmpty())
        val phone = input("Telemóvel / telefone pessoal", extendedProfileDraft?.get("phone")
            ?: prefs.getString("phone", "").orEmpty())
        val email = input("Email (opcional)", extendedProfileDraft?.get("email")
            ?: prefs.getString("email", "").orEmpty())
        val ccNumber = input("N.º Cartão de Cidadão (opcional)", extendedProfileDraft?.get("cc_number")
            ?: prefs.getString("cc_number", "").orEmpty())
        val ccValidity = input("Validade CC (DD/MM/AAAA)", extendedProfileDraft?.get("cc_valid_until")
            ?: prefs.getString("cc_valid_until", "").orEmpty())
        val familyRole = input("Familiar / responsável pelo perfil", extendedProfileDraft?.get("family_role")
            ?: prefs.getString("family_role", "").orEmpty())
        val contactName = input("Contacto de referência — Nome", extendedProfileDraft?.get("contact_name")
            ?: prefs.getString("contact_name", "").orEmpty())
        val contactPhone = input("Contacto de referência — Telefone", extendedProfileDraft?.get("contact_phone")
            ?: prefs.getString("contact_phone", "").orEmpty())
        val homeName = input("Lar / Residência — Nome", extendedProfileDraft?.get("care_home_name")
            ?: prefs.getString("care_home_name", "").orEmpty())
        val homeAddress = input("Lar / Residência — Morada", extendedProfileDraft?.get("care_home_address")
            ?: prefs.getString("care_home_address", "").orEmpty())
        val homePhone = input("Lar / Residência — Telefone", extendedProfileDraft?.get("care_home_phone")
            ?: prefs.getString("care_home_phone", "").orEmpty())
        val homeResponsible = input("Lar — Contacto / Responsável", extendedProfileDraft?.get("care_home_responsible")
            ?: prefs.getString("care_home_responsible", "").orEmpty())
        val homeNotes = input("Lar — Notas úteis (horários, quarto, etc.)", extendedProfileDraft?.get("care_home_notes")
            ?: prefs.getString("care_home_notes", "").orEmpty())

        box.addView(noteBox("Identificação e dados pessoais",
            "Informação privada do utilizador. Preencha apenas os campos de que necessita."))
        listOf(name, fullName, birth, gender, height, nif, sns, adse, niss, ccNumber,
            ccValidity, address, healthUnit).forEach { box.addView(it.container) }
        box.addView(noteBox("Contactos e responsável",
            "Permite encontrar rapidamente um familiar ou pessoa de referência."))
        listOf(phone, email, familyRole, contactName, contactPhone)
            .forEach { box.addView(it.container) }
        box.addView(noteBox("Lar ou residência assistida (opcional)",
            "Nome do lar, telefone, morada e a pessoa de contacto no local."))
        listOf(homeName, homeAddress, homePhone, homeResponsible, homeNotes)
            .forEach { box.addView(it.container) }''',
"added profile and nursing home fields")

edit('''        var dialog: androidx.appcompat.app.AlertDialog? = null
        box.addView(secondaryButton("📷 Fotografar verso do Cartão de Cidadão") {
            profileDraft = Triple(name.edit.text.toString().trim(),
                nif.edit.text.toString().filter { it.isDigit() },
                sns.edit.text.toString().filter { it.isDigit() })
            extendedProfileDraft = mapOf(
                "full_name" to fullName.edit.text.toString().trim(),
                "birth_date" to birth.edit.text.toString().trim(),
                "gender" to gender.edit.text.toString().trim(),
                "height_cm" to height.edit.text.toString().trim(),
                "adse" to adse.edit.text.toString().trim(),
                "niss" to niss.edit.text.toString().trim(),
                "address" to address.edit.text.toString().trim(),
                "health_unit" to healthUnit.edit.text.toString().trim()
            )
            dialog?.dismiss()
            captureCitizenCardBack()
        })''',
'''        var dialog: androidx.appcompat.app.AlertDialog? = null
        val rememberDraft = {
            profileDraft = Triple(name.edit.text.toString().trim(),
                nif.edit.text.toString().filter { it.isDigit() },
                sns.edit.text.toString().filter { it.isDigit() })
            extendedProfileDraft = mapOf(
                "full_name" to fullName.edit.text.toString().trim(),
                "birth_date" to birth.edit.text.toString().trim(),
                "gender" to gender.edit.text.toString().trim(),
                "height_cm" to height.edit.text.toString().trim(),
                "adse" to adse.edit.text.toString().trim(),
                "niss" to niss.edit.text.toString().trim(),
                "address" to address.edit.text.toString().trim(),
                "health_unit" to healthUnit.edit.text.toString().trim(),
                "phone" to phone.edit.text.toString().trim(),
                "email" to email.edit.text.toString().trim(),
                "cc_number" to ccNumber.edit.text.toString().trim(),
                "cc_valid_until" to ccValidity.edit.text.toString().trim(),
                "family_role" to familyRole.edit.text.toString().trim(),
                "contact_name" to contactName.edit.text.toString().trim(),
                "contact_phone" to contactPhone.edit.text.toString().trim(),
                "care_home_name" to homeName.edit.text.toString().trim(),
                "care_home_address" to homeAddress.edit.text.toString().trim(),
                "care_home_phone" to homePhone.edit.text.toString().trim(),
                "care_home_responsible" to homeResponsible.edit.text.toString().trim(),
                "care_home_notes" to homeNotes.edit.text.toString().trim()
            )
        }
        val picture=userAvatar(activeProfileId,300)
        if (picture!=null) {
            box.addView(android.widget.ImageView(this).apply{
                setImageBitmap(picture)
                scaleType=android.widget.ImageView.ScaleType.CENTER_CROP
                background=rounded(softGreen,20f)
                clipToOutline=true
            },LinearLayout.LayoutParams(dp(95),dp(95)).apply{gravity=Gravity.CENTER_HORIZONTAL})
        }
        box.addView(secondaryButton("📷 Foto de perfil e fotografias do Cartão de Cidadão") {
            if(profiles.all().none{it.id==activeProfileId}){
                Toast.makeText(this,"Guarde primeiro o novo utilizador.",Toast.LENGTH_LONG).show()
            }else{
                rememberDraft()
                dialog?.dismiss()
                editProfileImages.launch(Intent(this,ProfileMediaActivity::class.java)
                    .putExtra(ProfileMediaActivity.PROFILE,activeProfileId))
            }
        })
        box.addView(secondaryButton("🔎 Ler dados do verso do CC (OCR, sem guardar fotografia)") {
            rememberDraft()
            dialog?.dismiss()
            captureCitizenCardBack()
        })''',
"preserve all draft fields before images / OCR")

edit('''            val dateRaw = birth.edit.text.toString().trim()
            if (dateRaw.isNotBlank()) {''',
'''            val dateRaw = birth.edit.text.toString().trim()
            val ccExpiry=ccValidity.edit.text.toString().trim()
            if (ccExpiry.isNotBlank()){
                val valid=runCatching {
                    java.time.LocalDate.parse(ccExpiry,
                        DateTimeFormatter.ofPattern("dd/MM/uuuu")
                            .withResolverStyle(java.time.format.ResolverStyle.STRICT))
                }.isSuccess
                if(!valid){
                    ccValidity.edit.error="Indique uma data válida DD/MM/AAAA."
                    return@setOnClickListener
                }
            }
            val mail=email.edit.text.toString().trim()
            if(mail.isNotBlank()&&
                !android.util.Patterns.EMAIL_ADDRESS.matcher(mail).matches()){
                email.edit.error="Indique um email válido."
                return@setOnClickListener
            }
            if (dateRaw.isNotBlank()) {''',
"optional ID expiry and email validation")

edit('''                .putString("health_unit", healthUnit.edit.text.toString().trim())
                .apply()''',
'''                .putString("health_unit", healthUnit.edit.text.toString().trim())
                .putString("phone", phone.edit.text.toString().trim().take(120))
                .putString("email", mail.take(200))
                .putString("cc_number", ccNumber.edit.text.toString().trim().take(60))
                .putString("cc_valid_until", ccExpiry)
                .putString("family_role", familyRole.edit.text.toString().trim().take(200))
                .putString("contact_name", contactName.edit.text.toString().trim().take(200))
                .putString("contact_phone", contactPhone.edit.text.toString().trim().take(120))
                .putString("care_home_name", homeName.edit.text.toString().trim().take(200))
                .putString("care_home_address", homeAddress.edit.text.toString().trim().take(400))
                .putString("care_home_phone", homePhone.edit.text.toString().trim().take(120))
                .putString("care_home_responsible", homeResponsible.edit.text.toString().trim().take(200))
                .putString("care_home_notes", homeNotes.edit.text.toString().trim().take(600))
                .apply()''',
"store added fields")

file.write_text(s,encoding="utf-8")
print("v1.9.8: extensible profile with contact/care-home/CC metadata, private portrait and two-sided CC photos; old values retained.")
