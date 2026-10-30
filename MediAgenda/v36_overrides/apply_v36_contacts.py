from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1")
source=root/"app/src/main/java/com/mediagenda/app"

def transform(path, old, new, label):
    s=path.read_text(encoding="utf-8")
    if old not in s:
        raise RuntimeError("v1.9.17: missing "+label)
    path.write_text(s.replace(old,new,1),encoding="utf-8")

main=source/"MainActivity.kt"
transform(main,
'''import android.provider.Settings''',
'''import android.provider.Settings
import android.provider.ContactsContract
import android.app.Activity
import android.view.inputmethod.InputMethodManager
import android.text.InputType''',
"MainActivity contact picker imports")

transform(main,
'''    private var extendedProfileDraft: Map<String, String>? = null''',
'''    private var extendedProfileDraft: Map<String, String>? = null

    // Android's phone-number picker grants access only to the number
    // explicitly selected by the user. No READ_CONTACTS permission is needed.
    private var pendingPhoneTarget: TextInputEditText? = null
    private var pendingContactNameTarget: TextInputEditText? = null
    private val phoneContactPicker = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            val selected = result.data?.data
            if (selected != null) {
                try {
                    val columns = arrayOf(
                        ContactsContract.CommonDataKinds.Phone.NUMBER,
                        ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME
                    )
                    contentResolver.query(selected, columns, null, null, null)?.use { cursor ->
                        if (cursor.moveToFirst()) {
                            val phone = cursor.getString(cursor.getColumnIndexOrThrow(
                                ContactsContract.CommonDataKinds.Phone.NUMBER)).orEmpty()
                            val displayName = cursor.getString(cursor.getColumnIndexOrThrow(
                                ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME)).orEmpty()
                            if (phone.isNotBlank()) {
                                pendingPhoneTarget?.setText(phone.trim())
                                if (pendingContactNameTarget?.text.isNullOrBlank() &&
                                    displayName.isNotBlank()) {
                                    pendingContactNameTarget?.setText(displayName.trim())
                                }
                            } else {
                                Toast.makeText(this,"O contacto selecionado não tem número.",
                                    Toast.LENGTH_LONG).show()
                            }
                        }
                    } ?: Toast.makeText(this,"Não foi possível ler o contacto.",
                        Toast.LENGTH_LONG).show()
                } catch (_: SecurityException) {
                    Toast.makeText(this,"Não foi possível aceder ao contacto escolhido.",
                        Toast.LENGTH_LONG).show()
                } catch (_: Exception) {
                    Toast.makeText(this,"Não foi possível preencher este telefone.",
                        Toast.LENGTH_LONG).show()
                }
            }
        }
        pendingPhoneTarget=null
        pendingContactNameTarget=null
    }

    private fun chooseProfilePhone(target: TextInputEditText,
                                   name: TextInputEditText? = null) {
        pendingPhoneTarget=target
        pendingContactNameTarget=name
        val picker=Intent(Intent.ACTION_PICK,
            ContactsContract.CommonDataKinds.Phone.CONTENT_URI)
        try {
            phoneContactPicker.launch(picker)
        } catch (_: Exception) {
            pendingPhoneTarget=null
            pendingContactNameTarget=null
            Toast.makeText(this,"Não foi possível abrir os contactos do telemóvel.",
                Toast.LENGTH_LONG).show()
        }
    }

    private fun attachProfilePhonePicker(field: Field, name: Field? = null) {
        val edit=field.edit
        edit.inputType=InputType.TYPE_CLASS_PHONE
        // Tap on the number itself to open the phone's contacts.
        // The pencil icon at left still allows free manual entry.
        edit.isFocusable=false
        edit.isClickable=true
        edit.setOnClickListener { chooseProfilePhone(edit,name?.edit) }
        field.container.endIconMode=TextInputLayout.END_ICON_CUSTOM
        field.container.setEndIconDrawable(android.R.drawable.ic_menu_call)
        field.container.setEndIconContentDescription("Escolher da agenda de contactos")
        field.container.setEndIconOnClickListener {
            chooseProfilePhone(edit,name?.edit)
        }
        field.container.setStartIconDrawable(android.R.drawable.ic_menu_edit)
        field.container.setStartIconContentDescription("Escrever número manualmente")
        field.container.setStartIconOnClickListener {
            edit.setOnClickListener(null)
            edit.isFocusableInTouchMode=true
            edit.isFocusable=true
            edit.requestFocus()
            (getSystemService(INPUT_METHOD_SERVICE) as InputMethodManager)
                .showSoftInput(edit,InputMethodManager.SHOW_IMPLICIT)
        }
    }''',
"phone picker and edit helper")

transform(main,
'''        val homeNotes = input("Lar — Notas úteis (horários, quarto, etc.)", extendedProfileDraft?.get("care_home_notes")
            ?: prefs.getString("care_home_notes", "").orEmpty())

        box.addView(noteBox''',
'''        val homeNotes = input("Lar — Notas úteis (horários, quarto, etc.)", extendedProfileDraft?.get("care_home_notes")
            ?: prefs.getString("care_home_notes", "").orEmpty())

        attachProfilePhonePicker(phone)
        attachProfilePhonePicker(contactPhone, contactName)
        attachProfilePhonePicker(homePhone, homeResponsible)

        box.addView(noteBox''',
"phone widgets")

records=source/"HealthRecordsActivity.kt"
transform(records,
'''import android.content.res.Configuration''',
'''import android.content.res.Configuration
import android.app.Activity
import android.content.Intent
import android.provider.ContactsContract
import android.text.InputType
import android.view.inputmethod.InputMethodManager
import androidx.activity.result.contract.ActivityResultContracts''',
"emergency contact imports")

transform(records,
'''    private var category="symptoms"''',
'''    private var category="symptoms"
    private var pendingEmergencyPhone:EditText?=null
    private val emergencyContactPicker=registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ){result->
        if(result.resultCode==Activity.RESULT_OK){
            val uri=result.data?.data
            if(uri!=null){
                try{
                    contentResolver.query(uri,arrayOf(
                        ContactsContract.CommonDataKinds.Phone.NUMBER),null,null,null)?.use{cursor->
                        if(cursor.moveToFirst()){
                            val value=cursor.getString(cursor.getColumnIndexOrThrow(
                                ContactsContract.CommonDataKinds.Phone.NUMBER)).orEmpty()
                            if(value.isNotBlank())pendingEmergencyPhone?.setText(value.trim())
                        }
                    }
                }catch(_:Exception){
                    Toast.makeText(this,"Não foi possível obter o telefone escolhido.",
                        Toast.LENGTH_LONG).show()
                }
            }
        }
        pendingEmergencyPhone=null
    }
    private fun selectEmergencyPhone(edit:EditText){
        pendingEmergencyPhone=edit
        try{
            emergencyContactPicker.launch(Intent(Intent.ACTION_PICK,
                ContactsContract.CommonDataKinds.Phone.CONTENT_URI))
        }catch(_:Exception){
            pendingEmergencyPhone=null
            Toast.makeText(this,"Não foi possível abrir os contactos.",
                Toast.LENGTH_LONG).show()
        }
    }''',
"emergency picker callback")

transform(records,
'''            key to edit
        }
        val scroll=ScrollView(this);scroll.addView(box)''',
'''            if(category=="emergency" && key=="contact_phone"){
                edit.inputType=InputType.TYPE_CLASS_PHONE
                edit.isFocusable=false
                edit.isClickable=true
                edit.setOnClickListener { selectEmergencyPhone(edit) }
                val buttons=LinearLayout(this).apply{
                    orientation=LinearLayout.HORIZONTAL
                    gravity=Gravity.CENTER_VERTICAL
                }
                val pick=button("📇 Contactos"){selectEmergencyPhone(edit)}
                val manual=button("✎ Escrever"){ 
                    edit.setOnClickListener(null)
                    edit.isFocusableInTouchMode=true
                    edit.isFocusable=true
                    edit.requestFocus()
                    (getSystemService(INPUT_METHOD_SERVICE) as InputMethodManager)
                        .showSoftInput(edit,InputMethodManager.SHOW_IMPLICIT)
                }
                buttons.addView(pick,LinearLayout.LayoutParams(0,
                    ViewGroup.LayoutParams.WRAP_CONTENT,1f))
                buttons.addView(manual,LinearLayout.LayoutParams(0,
                    ViewGroup.LayoutParams.WRAP_CONTENT,1f))
                box.addView(buttons)
            }
            key to edit
        }
        val scroll=ScrollView(this);scroll.addView(box)''',
"emergency phone selection in edit form")

gradle=root/"app/build.gradle.kts"
g=gradle.read_text(encoding="utf-8")
assert 'applicationId = "com.mediagenda.app.stable"' in g
assert 'versionCode = 26' in g and 'versionName = "1.9.16"' in g
gradle.write_text(g.replace('versionCode = 26','versionCode = 27',1)
    .replace('versionName = "1.9.16"','versionName = "1.9.17"',1),encoding="utf-8")
print("SaúdePrática v1.9.17: phone-number selection from native Android contacts in profile and emergency. No contacts permission; manual editing remains.")
