from pathlib import Path

file=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app/MainActivity.kt")
s=file.read_text(encoding="utf-8")
def edit(old,new,label):
    global s
    if old not in s:raise RuntimeError("v1.9.10 CC fields missing "+label+": "+old[:105])
    s=s.replace(old,new,1)

edit('''        val gender = input("Género (opcional)", extendedProfileDraft?.get("gender")
            ?: prefs.getString("gender", "").orEmpty())
        val height = input''',
'''        val gender = input("Género (opcional)", extendedProfileDraft?.get("gender")
            ?: prefs.getString("gender", "").orEmpty())
        // Select rather than type a gender, preserving any legacy free-text
        // value as an option so older profile data isn't silently lost.
        val knownGenders=listOf("Não definido","Feminino","Masculino","Outro")
        val previousGender=gender.edit.text.toString().trim()
        val genderChoices=if(previousGender.isNotBlank() && previousGender !in knownGenders)
            knownGenders+previousGender else knownGenders
        gender.edit.visibility=View.GONE
        val genderSpinner=android.widget.Spinner(this).apply {
            adapter=android.widget.ArrayAdapter(this@MainActivity,
                android.R.layout.simple_spinner_dropdown_item,genderChoices)
            setSelection(genderChoices.indexOf(previousGender).takeIf{it>=0}?:0)
        }
        genderSpinner.onItemSelectedListener=object:android.widget.AdapterView.OnItemSelectedListener {
            override fun onNothingSelected(parent:android.widget.AdapterView<*>?){}
            override fun onItemSelected(parent:android.widget.AdapterView<*>?,view:View?,
                position:Int,id:Long){
                gender.edit.setText(if(position==0)"" else genderChoices[position])
            }
        }
        gender.container.addView(genderSpinner)
        val height = input''',"gender dropdown")

edit('''        val ccValidity = input("Validade CC (DD/MM/AAAA)", extendedProfileDraft?.get("cc_valid_until")
            ?: prefs.getString("cc_valid_until", "").orEmpty())
        val familyRole''',
'''        val ccValidity = input("Validade CC (DD/MM/AAAA)", extendedProfileDraft?.get("cc_valid_until")
            ?: prefs.getString("cc_valid_until", "").orEmpty())
        val nationality=input("Nacionalidade",extendedProfileDraft?.get("nationality")
            ?: prefs.getString("nationality","").orEmpty())
        val birthPlace=input("Naturalidade / Local de nascimento",extendedProfileDraft?.get("birth_place")
            ?: prefs.getString("birth_place","").orEmpty())
        val father=input("Nome do pai",extendedProfileDraft?.get("father_name")
            ?: prefs.getString("father_name","").orEmpty())
        val mother=input("Nome da mãe",extendedProfileDraft?.get("mother_name")
            ?: prefs.getString("mother_name","").orEmpty())
        val familyRole''',"citizen card additional fields")

edit('''        listOf(name, fullName, birth, gender, height, nif, sns, adse, niss, ccNumber,
            ccValidity, address, healthUnit).forEach { box.addView(it.container) }''',
'''        listOf(name, fullName, birth, gender, height, nationality, birthPlace,
            father, mother, nif, sns, adse, niss, ccNumber,
            ccValidity, address, healthUnit).forEach { box.addView(it.container) }''',
"show CC values")

edit('''                "cc_valid_until" to ccValidity.edit.text.toString().trim(),
                "family_role"''',
'''                "cc_valid_until" to ccValidity.edit.text.toString().trim(),
                "nationality" to nationality.edit.text.toString().trim(),
                "birth_place" to birthPlace.edit.text.toString().trim(),
                "father_name" to father.edit.text.toString().trim(),
                "mother_name" to mother.edit.text.toString().trim(),
                "family_role"''',"preserve new fields while opening camera / OCR")

edit('''                .putString("cc_valid_until", ccExpiry)
                .putString("family_role"''',
'''                .putString("cc_valid_until", ccExpiry)
                .putString("nationality", nationality.edit.text.toString().trim().take(100))
                .putString("birth_place", birthPlace.edit.text.toString().trim().take(150))
                .putString("father_name", father.edit.text.toString().trim().take(200))
                .putString("mother_name", mother.edit.text.toString().trim().take(200))
                .putString("family_role"''',"store extra CC fields")

file.write_text(s,encoding="utf-8")
print("v1.9.10: optional nationality, birthplace, parents, and gender drop-down; all existing values retained.")
