from pathlib import Path
f=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app/MainActivity.kt")
s=f.read_text(encoding="utf-8")
def edit(old,new,label):
 global s
 if old not in s:raise RuntimeError("v1.9.6 profile missing "+label)
 s=s.replace(old,new,1)
edit('''        val birth = input("Data de nascimento (DD/MM/AAAA)", extendedProfileDraft?.get("birth_date")
            ?: prefs.getString("birth_date", "").orEmpty())
        val nif = input("NIF (9 dígitos)",''',
'''        val birth = input("Data de nascimento (DD/MM/AAAA)", extendedProfileDraft?.get("birth_date")
            ?: prefs.getString("birth_date", "").orEmpty())
        val gender = input("Género (opcional)", extendedProfileDraft?.get("gender")
            ?: prefs.getString("gender", "").orEmpty())
        val height = input("Altura em centímetros (opcional)", extendedProfileDraft?.get("height_cm")
            ?: prefs.getString("height_cm", "").orEmpty())
        val nif = input("NIF (9 dígitos)",''',"new fields")
edit('''        listOf(name, fullName, birth, nif, sns, adse, niss, address, healthUnit)''',
'''        listOf(name, fullName, birth, gender, height, nif, sns, adse, niss, address, healthUnit)''',"profile form order")
edit('''                "birth_date" to birth.edit.text.toString().trim(),
                "adse"''',
'''                "birth_date" to birth.edit.text.toString().trim(),
                "gender" to gender.edit.text.toString().trim(),
                "height_cm" to height.edit.text.toString().trim(),
                "adse"''',"keep scan draft")
edit('''            val socialSecurity = niss.edit.text.toString().filter(Char::isDigit)''',
'''            val heightRaw = height.edit.text.toString().trim()
            val heightValue = heightRaw.replace(',', '.').toDoubleOrNull()
            if (heightRaw.isNotEmpty() &&
                (heightValue == null || !heightValue.isFinite() || heightValue !in 40.0..250.0)) {
                height.edit.error = "Introduza a altura em cm (por exemplo, 170 ou 170,5)."
                return@setOnClickListener
            }
            val socialSecurity = niss.edit.text.toString().filter(Char::isDigit)''',
"height validation")
edit('''                .putString("birth_date", dateRaw)
                .putString("adse"''',
'''                .putString("birth_date", dateRaw)
                .putString("gender", gender.edit.text.toString().trim())
                .putString("height_cm", heightRaw)
                .putString("adse"''',"store profile attributes")
f.write_text(s,encoding="utf-8")
print("v1.9.6: per-person optional gender and height in cm, existing profile fields preserved.")
