"""Non-destructive source checks after applying v121 profile UX patch."""
from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1')
app=root/'app/src/main/java/com/mediagenda/app'
wizard=(app/'ProfileWizardActivity.kt').read_text()
main=(app/'MainActivity.kt').read_text()
clinical=(app/'WorkMedicineActivity.kt').read_text()
media=(app/'data/ProfileMediaStore.kt').read_text()
assert (root/'app/src/main/AndroidManifest.xml').read_text().count('android:name=".ProfileWizardActivity"')==1
for text in ['"cc_front"','"cc_back"','"avatar"','saveCcPhotos','ProfileCitizenCardOcr.propose','DeviceAlarmRouting.assign','getSharedPreferences(ProfileStore(this).preferencesFor(created.id)','RESULT_PROFILE_ID']:
    assert text in wizard, text
assert 'newProfileWizard.launch(Intent(this,ProfileWizardActivity::class.java))' in main
assert 'val avatarBig=userAvatar(activeProfileId,500)' in main
assert 'dp(112),dp(76)' in main
assert 'ProfileMediaStore(this,activeProfileId).photo(kind,240)' in main
assert '🏥 Editar números na Situação Clínica' in main
for text in ['"observation_number"','"observations_by_unit"','putString("observations_by_unit"','putString("observation_number"']:
    assert text in clinical, text
assert 'fun save(kind:String,uri:Uri)' in media
assert 'versionCode = 112' in (root/'app/build.gradle.kts').read_text()
assert 'versionName = "1.9.102"' in (root/'app/build.gradle.kts').read_text()
print('v121 checks passed: wizard, CC images, local patient assignment, clinical data keys and version')
