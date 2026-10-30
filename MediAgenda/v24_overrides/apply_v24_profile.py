from pathlib import Path

f=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app/MainActivity.kt")
s=f.read_text(encoding="utf-8")
def edit(old,new,label):
 global s
 if old not in s:raise RuntimeError("v1.9.5 profile missing "+label)
 s=s.replace(old,new,1)

edit('''    private var profileDraft: Triple<String, String, String>? = null''',
'''    private var profileDraft: Triple<String, String, String>? = null
    private var extendedProfileDraft: Map<String, String>? = null''', "preserve draft")

edit('''        val name = input("Nome do perfil", draft?.first ?: profileName())
        val nif = input("NIF (9 dígitos)", draft?.second ?: prefs.getString("nif", "").orEmpty())
        val sns = input("Número de utente SNS (9 dígitos)", draft?.third ?: prefs.getString("sns_number", "").orEmpty())
        listOf(name, nif, sns).forEach { box.addView(it.container) }''',
'''        val name = input("Nome do perfil (nome curto)", draft?.first ?: profileName())
        val fullName = input("Nome completo", extendedProfileDraft?.get("full_name")
            ?: prefs.getString("full_name", "").orEmpty())
        val birth = input("Data de nascimento (DD/MM/AAAA)", extendedProfileDraft?.get("birth_date")
            ?: prefs.getString("birth_date", "").orEmpty())
        val nif = input("NIF (9 dígitos)", draft?.second ?: prefs.getString("nif", "").orEmpty())
        val sns = input("Número de utente SNS (9 dígitos)", draft?.third ?: prefs.getString("sns_number", "").orEmpty())
        val adse = input("Número ADSE (opcional)", extendedProfileDraft?.get("adse")
            ?: prefs.getString("adse", "").orEmpty())
        val niss = input("NISS (11 dígitos)", extendedProfileDraft?.get("niss")
            ?: prefs.getString("niss", "").orEmpty())
        val address = input("Morada", extendedProfileDraft?.get("address")
            ?: prefs.getString("address", "").orEmpty())
        val healthUnit = input("Unidade de saúde", extendedProfileDraft?.get("health_unit")
            ?: prefs.getString("health_unit", "").orEmpty())
        listOf(name, fullName, birth, nif, sns, adse, niss, address, healthUnit)
            .forEach { box.addView(it.container) }''', "extra fields")

edit('''            profileDraft = Triple(name.edit.text.toString().trim(),
                nif.edit.text.toString().filter { it.isDigit() },
                sns.edit.text.toString().filter { it.isDigit() })
            dialog?.dismiss()''',
'''            profileDraft = Triple(name.edit.text.toString().trim(),
                nif.edit.text.toString().filter { it.isDigit() },
                sns.edit.text.toString().filter { it.isDigit() })
            extendedProfileDraft = mapOf(
                "full_name" to fullName.edit.text.toString().trim(),
                "birth_date" to birth.edit.text.toString().trim(),
                "adse" to adse.edit.text.toString().trim(),
                "niss" to niss.edit.text.toString().trim(),
                "address" to address.edit.text.toString().trim(),
                "health_unit" to healthUnit.edit.text.toString().trim()
            )
            dialog?.dismiss()''', "draft optional fields for camera")

edit('''            if (n.isBlank()) {
                name.edit.error = "Indique um nome."
                return@setOnClickListener
            }
            try {''',
'''            if (n.isBlank()) {
                name.edit.error = "Indique um nome."
                return@setOnClickListener
            }
            val dateRaw = birth.edit.text.toString().trim()
            if (dateRaw.isNotBlank()) {
                val valid = runCatching {
                    java.time.LocalDate.parse(
                        dateRaw, DateTimeFormatter.ofPattern("dd/MM/uuuu")
                            .withResolverStyle(java.time.format.ResolverStyle.STRICT))
                }.isSuccess
                if (!valid) {
                    birth.edit.error = "Use uma data válida no formato DD/MM/AAAA."
                    return@setOnClickListener
                }
            }
            val socialSecurity = niss.edit.text.toString().filter(Char::isDigit)
            if (socialSecurity.isNotBlank() && socialSecurity.length != 11) {
                niss.edit.error = "O NISS deve conter 11 dígitos."
                return@setOnClickListener
            }
            try {''', "validate DOB NISS")

edit('''                .putString("sns_number", health)
                .apply()
            profileDraft = null''',
'''                .putString("sns_number", health)
                .putString("full_name", fullName.edit.text.toString().trim())
                .putString("birth_date", dateRaw)
                .putString("adse", adse.edit.text.toString().trim())
                .putString("niss", socialSecurity)
                .putString("address", address.edit.text.toString().trim())
                .putString("health_unit", healthUnit.edit.text.toString().trim())
                .apply()
            profileDraft = null
            extendedProfileDraft = null''', "persist extra profile fields")
f.write_text(s,encoding="utf-8")
print("SaúdePrática v1.9.5: optional extended patient profile fields, existing values preserved.")
