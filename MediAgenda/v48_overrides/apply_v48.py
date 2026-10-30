from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
def sub(file,old,new,label):
    txt=file.read_text(encoding="utf-8")
    if txt.count(old)!=1:
        raise RuntimeError("v1.9.29 "+label+" anchor "+str(txt.count(old)))
    file.write_text(txt.replace(old,new,1),encoding="utf-8")
(base/"SmartFields.kt").write_text(
    Path("MediAgenda/v48_overrides/SmartFields.kt").read_text(encoding="utf-8"),
    encoding="utf-8")
main=base/"MainActivity.kt"
sub(main,'''        layout.addView(edit)
        return Field(layout, edit)''',
    '''        layout.addView(edit)
        SmartFields.attach(this,edit,label,enabled=!multiline)
        return Field(layout, edit)''',"main picker")
sub(main,'''        val healthUnit = input("Unidade de saúde",''',
    '''        val observationNumber = input("N.º de observação (opcional)",
            extendedProfileDraft?.get("observation_number")
                ?: prefs.getString("observation_number","").orEmpty())
        val healthUnit = input("Unidade de saúde",''',"profile field")
sub(main,'''            ccValidity, address, postalCode, healthUnit).forEach''',
    '''            ccValidity, address, postalCode, healthUnit,
            observationNumber).forEach''',"profile visible")
sub(main,'''                "health_unit" to healthUnit.edit.text.toString().trim(),''',
    '''                "health_unit" to healthUnit.edit.text.toString().trim(),
                "observation_number" to observationNumber.edit.text.toString().trim(),''',
    "profile draft")
sub(main,'''                .putString("health_unit", healthUnit.edit.text.toString().trim())''',
    '''                .putString("health_unit", healthUnit.edit.text.toString().trim())
                .putString("observation_number",
                    observationNumber.edit.text.toString().trim().take(100))''',
    "profile save")
sub(main,'''        attachProfilePhonePicker(homePhone, homeResponsible)

        box.addView''',
    '''        attachProfilePhonePicker(homePhone, homeResponsible)
        homeResponsible.container.endIconMode=TextInputLayout.END_ICON_CUSTOM
        homeResponsible.container.setEndIconDrawable(android.R.drawable.ic_menu_call)
        homeResponsible.container.setEndIconContentDescription(
            "Escolher responsável do lar nos contactos")
        homeResponsible.container.setEndIconOnClickListener{
            chooseProfilePhone(homePhone.edit,homeResponsible.edit)
        }

        box.addView''',"carehome contact")
sub(base/"ClinicalLabsActivity.kt",
    '        setPadding(dp(2),dp(6),dp(2),dp(7))',
    '        setPadding(dp(2),dp(6),dp(2),dp(7))\n        SmartFields.attach(this@ClinicalLabsActivity,this,hint)',
    "clinical date")
sub(base/"WorkMedicineActivity.kt",
    '        setPadding(dp(3),dp(8),dp(3),dp(8))',
    '        setPadding(dp(3),dp(8),dp(3),dp(8))\n        SmartFields.attach(this@WorkMedicineActivity,this,label)',
    "occupational date time")
sub(base/"HealthExpensesActivity.kt",
    '''        backgroundTintList=ColorStateList.valueOf(blue)
    }
    private fun notice''',
    '''        backgroundTintList=ColorStateList.valueOf(blue)
        SmartFields.attach(this@HealthExpensesActivity,this,hint)
    }
    private fun notice''',
    "expenses date")
sub(base/"WellnessActivity.kt",
    '''        form.addView(input)
        return EditableField(key, input)''',
    '''        SmartFields.attach(this,input,label,enabled=!multi)
        form.addView(input)
        return EditableField(key, input)''',
    "wellness time")
records=base/"HealthRecordsActivity.kt"
sub(records,'''                box.addView(this)
            }
            if(category=="emergency" && key=="contact_phone"){''',
    '''                box.addView(this)
            }
            if(key!="contact_phone")
                SmartFields.attach(this,edit,caption)
            if(category=="emergency" &&
                (key=="contact_phone" || key=="second_contact")){''',
    "health history and emergency phone")
gradle=root/"app/build.gradle.kts"
sub(gradle,'versionCode = 38','versionCode = 39',"version code")
sub(gradle,'versionName = "1.9.28"','versionName = "1.9.29"',"version name")
print("v1.9.29: native calendar/time, contacts with manual entry and profile observation number.")
