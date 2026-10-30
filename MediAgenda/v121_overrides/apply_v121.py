"""SaúdePrática v1.9.102: guided profile creation and clinical identifiers relocation."""
from pathlib import Path
R=Path('build-src/MediAgenda_Android_v1');APP=R/'app/src/main/java/com/mediagenda/app'
def patch(file,old,new,label):
    f=APP/file;s=f.read_text();count=s.count(old)
    if count!=1:raise RuntimeError(f'{label}: expected 1 anchor, found {count}')
    f.write_text(s.replace(old,new,1))

# New Activity supplied as source in the v121 override folder (not private profile data).
source=(Path(__file__).parent/'ProfileWizardActivity.kt').read_text()
assert 'class ProfileWizardActivity' in source
(APP/'ProfileWizardActivity.kt').write_text(source)

manifest=R/'app/src/main/AndroidManifest.xml'
s=manifest.read_text();old='<activity android:name=".ProfileMediaActivity" android:exported="false" />'
assert s.count(old)==1
manifest.write_text(s.replace(old,old+'\n        <activity android:name=".ProfileWizardActivity" android:exported="false" />'))

patch(Path('MainActivity.kt'),
'''    private var profileDraft: Triple<String, String, String>? = null''',
'''    private val newProfileWizard=registerForActivityResult(ActivityResultContracts.StartActivityForResult()){ result->
        if(result.resultCode==Activity.RESULT_OK){
            val id=result.data?.getStringExtra(ProfileWizardActivity.RESULT_PROFILE_ID)
            val created=profiles.all().firstOrNull{it.id==id}
            if(created!=null)activateProfile(created)
        }
    }
    private var profileDraft: Triple<String, String, String>? = null''',
'profile wizard callback')
start='''    private fun showCreateProfileDialog() {
        val box = formBox()
        val name = input("Nome do novo perfil", "")
        box.addView(name.container)
        val dialog = MaterialAlertDialogBuilder(this)
            .setTitle("Adicionar perfil")
            .setMessage("Cada perfil terá medicação, consultas e dados separados. Não é necessária palavra-passe.")
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
                showError(e.message ?: "Não foi possível criar o perfil.")
            }
        }
    }'''
patch(Path('MainActivity.kt'),start,
'''    private fun showCreateProfileDialog() {
        newProfileWizard.launch(Intent(this,ProfileWizardActivity::class.java))
    }''',
'profile wizard replaces single-step create dialog')

patch(Path('MainActivity.kt'),
'''        val draft = profileDraft
        val box = formBox()

        val name = input("Nome do perfil (nome curto)", draft?.first ?: profileName())''',
'''        val draft = profileDraft
        val box = formBox()
        box.addView(noteBox("👤 Ficha do perfil", "Informação organizada por secções. As fotografias abrem em tamanho grande; os números clínicos estão em Situação Clínica."))
        val avatarBig=userAvatar(activeProfileId,500)
        box.addView(android.widget.ImageView(this).apply{
            scaleType=android.widget.ImageView.ScaleType.CENTER_CROP
            background=rounded(softGreen,22f);clipToOutline=true
            if(avatarBig!=null)setImageBitmap(avatarBig)else setImageResource(R.drawable.saude_icon)
            contentDescription="Fotografia do perfil. Toque para editar."
            setOnClickListener{
                startActivity(Intent(this@MainActivity,ProfileMediaActivity::class.java)
                    .putExtra(ProfileMediaActivity.PROFILE,activeProfileId))
            }
        },LinearLayout.LayoutParams(dp(132),dp(132)).apply{
            gravity=Gravity.CENTER_HORIZONTAL;bottomMargin=dp(8)
        })
        val ccThumbs=LinearLayout(this).apply{
            orientation=LinearLayout.HORIZONTAL;gravity=Gravity.CENTER_HORIZONTAL
        }
        for(kind in listOf("cc_front","cc_back")){
            val picture=runCatching{ProfileMediaStore(this,activeProfileId).photo(kind,240)}.getOrNull()
            if(picture!=null){
                ccThumbs.addView(android.widget.ImageView(this).apply{
                    scaleType=android.widget.ImageView.ScaleType.CENTER_CROP
                    setImageBitmap(picture)
                    background=rounded(softGreen,14f);clipToOutline=true
                    contentDescription=if(kind=="cc_front")"Ver frente do CC" else "Ver verso do CC"
                    setOnClickListener{
                        startActivity(Intent(this@MainActivity,DocumentOrientationActivity::class.java)
                            .putExtra(DocumentOrientationActivity.PROFILE,activeProfileId)
                            .putExtra(DocumentOrientationActivity.GROUP,"identity")
                            .putExtra(DocumentOrientationActivity.FILENAME,kind+".jpg")
                            .putExtra(DocumentOrientationActivity.TITLE,contentDescription.toString())
                            .putExtra(DocumentOrientationActivity.VIEW_ONLY,true))
                    }
                },LinearLayout.LayoutParams(dp(112),dp(76)).apply{
                    marginStart=dp(6);marginEnd=dp(6);bottomMargin=dp(12)
                })
            }
        }
        box.addView(ccThumbs)

        val name = input("Nome do perfil (nome curto)", draft?.first ?: profileName())''',
'large avatar top and mini CC thumbnails')

patch(Path('MainActivity.kt'),
'''        box.addView(noteBox("Identificação e dados pessoais",
            "Informação privada do utilizador. Preencha apenas os campos de que necessita."))
        listOf(name, fullName, birth, gender, height, nationality, birthPlace,
            father, mother, nif, sns, adse, niss, ccNumber,
            ccValidity, address, postalCode, healthUnit,
            observationNumber).forEach { box.addView(it.container) }
        box.addView(noteBox("Números de observação por hospital ou clínica",
            "Guarda vários números: um por linha como «Hospital / Clínica | N.º». " +
            "Escolhe distrito e concelho antes da unidade. O catálogo local é inicial e não substitui a ERS."))
        box.addView(observationsByUnit.container)
        box.addView(secondaryButton("＋ Pesquisar unidade · Distrito → Concelho") {
            chooseHealthcareDistrict { chosen ->
                val before=observationsByUnit.edit.text.toString().trim()
                observationsByUnit.edit.setText(if(before.isEmpty())"$chosen | " else "$before\\n$chosen | ")
            }
        })
        box.addView(secondaryButton("🔎 Ver diretório completo oficial ERS") {
            startActivity(Intent(Intent.ACTION_VIEW,Uri.parse(HealthcareCatalog.ersUrl)))
        })''',
'''        box.addView(noteBox("Identificação e dados pessoais",
            "Informação privada. Podes tocar na fotografia e nas miniaturas do CC para ver em grande."))
        listOf(name,fullName,birth,gender,height).forEach{box.addView(it.container)}
        box.addView(noteBox("Cartão de Cidadão e identificação",
            "Documento opcional. As fotografias ficam apenas neste perfil e só são mostradas mediante acesso à aplicação."))
        listOf(ccNumber,ccValidity,nationality,birthPlace,father,mother,nif,sns,adse,niss)
            .forEach{box.addView(it.container)}
        box.addView(noteBox("Morada e unidade de saúde",
            "Os números de observação e de processo clínico foram movidos para Situação Clínica."))
        listOf(address,postalCode,healthUnit).forEach{box.addView(it.container)}
        // Legacy observation fields remain populated and are saved unchanged;
        // only their EDITOR is now in Situação Clínica, to prevent migration loss.
        box.addView(secondaryButton("🏥 Editar números na Situação Clínica") {
            startActivity(Intent(this,WorkMedicineActivity::class.java)
                .putExtra(WorkMedicineActivity.EXTRA_PROFILE_ID,activeProfileId))
        })''',
'clinical numbers leave personal profile, existing values preserved')

# Prevent duplicated avatar at bottom; big picture is at top.
patch(Path('MainActivity.kt'),
'''        val picture=userAvatar(activeProfileId,300)
        if (picture!=null) {
            box.addView(android.widget.ImageView(this).apply{
                setImageBitmap(picture)
                scaleType=android.widget.ImageView.ScaleType.CENTER_CROP
                background=rounded(softGreen,20f)
                clipToOutline=true
            },LinearLayout.LayoutParams(dp(95),dp(95)).apply{gravity=Gravity.CENTER_HORIZONTAL})
        }
''',
'''        // Large profile photo is rendered once, at the top of the editor.
''',
'avoid duplicate lower avatar')
patch(Path('MainActivity.kt'),
'''                (resources.displayMetrics.heightPixels*0.61f).toInt()
                    .coerceAtLeast(dp(270)))''',
'''                (resources.displayMetrics.heightPixels*0.77f).toInt()
                    .coerceAtLeast(dp(300)))''',
'expand profile editor vertically')
patch(Path('MainActivity.kt'),
'''            setLayout((resources.displayMetrics.widthPixels*0.92f).toInt(),
                ViewGroup.LayoutParams.WRAP_CONTENT)''',
'''            setLayout((resources.displayMetrics.widthPixels*0.97f).toInt(),
                ViewGroup.LayoutParams.WRAP_CONTENT)''',
'expand profile editor width')

# Clinical numbers now edit in Situação Clínica, reusing original profile prefs/keys.
patch(Path('WorkMedicineActivity.kt'),
'''        body.removeAllViews()
        val items=runCatching{store.all()}.getOrElse{''',
'''        body.removeAllViews()
        val clinicalPrefs=getSharedPreferences(ProfileStore(this).preferencesFor(patientId),MODE_PRIVATE)
        val obs=clinicalPrefs.getString("observations_by_unit","").orEmpty()
        val old=clinicalPrefs.getString("observation_number","").orEmpty()
        val clinicalCard=card("Números de observação e processo de tratamento",
            "Regista por hospital ou clínica; estes números pertencem à situação clínica do perfil, não à identificação pessoal.")
        clinicalCard.addView(text(if(obs.isNotBlank())obs else
            if(old.isNotBlank())"N.º antigo: "+old else "Nenhum número de observação registado.",
            13f,false,teal))
        clinicalCard.addView(button("✎ Editar números clínicos"){
            val sheet=LinearLayout(this).apply{
                orientation=LinearLayout.VERTICAL;setPadding(dp(18),dp(8),dp(18),dp(8))
            }
            val byUnit=multiline("Hospital / Clínica | N.º de observação",obs)
            val previous=field("N.º de observação antigo (opcional)",old)
            sheet.addView(byUnit);sheet.addView(previous)
            MaterialAlertDialogBuilder(this).setTitle("Situação Clínica · Identificadores")
                .setMessage("Um hospital por linha. As alterações só se aplicam ao perfil atual.")
                .setView(sheet).setNegativeButton("Cancelar",null)
                .setPositiveButton("Guardar"){_,_->
                    val ok=clinicalPrefs.edit()
                        .putString("observations_by_unit",byUnit.text.toString().take(8000))
                        .putString("observation_number",previous.text.toString().trim().take(100))
                        .commit()
                    if(ok)redraw()else message("Não foi possível guardar os números clínicos.")
                }.show()
        })
        val items=runCatching{store.all()}.getOrElse{''',
'clinical numbers UI')

# A few new wizard labels are added to the existing 5-language table. Full audit follows.
patch(Path('i18n/AppLanguage.kt'),
    '    private val source="""\n',
    '''    private val source="""
Novo perfil	New profile	Nouveau profil	Neues Profil	Nuevo perfil
Identificação	Identification	Identification	Identifikation	Identificación
Cartão de Cidadão	Citizen card	Carte d’identité	Personalausweis	Tarjeta de identidad
Perfis e funções	Profiles and roles	Profils et rôles	Profile und Rollen	Perfiles y funciones
Confirmar e guardar	Review and save	Vérifier et enregistrer	Prüfen und speichern	Revisar y guardar
Este perfil é um cuidador familiar	This profile is a family caregiver	Ce profil est aidant familial	Dieses Profil betreut Angehörige	Este perfil es cuidador familiar
Criar perfil	Create profile	Créer un profil	Profil erstellen	Crear perfil
Números de observação e processo de tratamento	Clinical reference and treatment numbers	Références et dossiers cliniques	Klinische Fall- und Behandlungsnummern	Números de observación y tratamiento
''',
'profile translations')

build=R/'app/build.gradle.kts';s=build.read_text()
assert s.count('versionCode = 111')==1 and s.count('versionName = "1.9.101"')==1
build.write_text(s.replace('versionCode = 111','versionCode = 112').replace('versionName = "1.9.101"','versionName = "1.9.102"'))
print('Applied SaúdePrática v1.9.102 profile wizard, clinical numbers, large photo and CC thumbs')
