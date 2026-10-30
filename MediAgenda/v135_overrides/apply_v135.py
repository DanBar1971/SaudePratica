#!/usr/bin/env python3
"""SaúdePrática v1.9.115 — confirmação de eliminação de perfil apenas com PIN.

Não altera o identificador do perfil, o método de remoção, alarmes,
dados persistidos, identidade Android nem certificado de assinatura.
"""
from pathlib import Path

base=Path("build-src/MediAgenda_Android_v1/app")
main=base/"src/main/java/com/mediagenda/app/MainActivity.kt"
s=main.read_text(encoding="utf-8")

def once(old:str,new:str,label:str):
    global s
    count=s.count(old)
    assert count==1, (label,count)
    s=s.replace(old,new,1)

once(
'''    private fun confirmDeleteSelectedProfile(profile:HealthProfile) {
        val form=formBox()
        form.addView(noteBox("Ação irreversível — " + profile.name,''',
'''    private fun confirmDeleteSelectedProfile(profile:HealthProfile) {
        // Eliminar exige sempre o PIN; nunca permitir uma via sem autenticação.
        val pinStore=AppPinStore(this)
        if(!pinStore.enabled()){
            showError("Para eliminar um perfil, ativa primeiro o PIN da SaúdePrática nas Opções.")
            return
        }
        val form=formBox()
        // Em perfis repetidos, o identificador distingue dois nomes idênticos.
        val profileCode=if(profile.id=="legacy")"original" else profile.id.takeLast(8)
        form.addView(noteBox("Ação irreversível — " + profile.name + " · " + profileCode,''',
"require PIN and show selected profile unique identifier"
)

once(
'''        val phrase=input("Para confirmar, escreve: " + profile.name, "")
        form.addView(phrase.container)
        val pinStore=AppPinStore(this)
        val pin=if(pinStore.enabled())input("PIN da SaúdePrática (4 dígitos)", "") else null
        pin?.let{
            it.edit.inputType=InputType.TYPE_CLASS_NUMBER or
                InputType.TYPE_NUMBER_VARIATION_PASSWORD
            form.addView(it.container)
        }''',
'''        // Só PIN: não é necessário escrever nomes compridos ou repetidos.
        val pin=input("PIN da SaúdePrática (4 dígitos)", "")
        pin.edit.inputType=InputType.TYPE_CLASS_NUMBER or
            InputType.TYPE_NUMBER_VARIATION_PASSWORD
        form.addView(pin.container)''',
"remove required typed profile name"
)

once(
'''            .setTitle("Eliminar definitivamente " + profile.name + "?")''',
'''            .setTitle("Eliminar perfil?")''',
"short title fits on smaller telemóveis"
)

once(
'''            if(phrase.edit.text.toString().trim()!=profile.name){
                phrase.edit.error="Escreve exatamente o nome do perfil."
                return@setOnClickListener
            }
            if(pin!=null&&!pinStore.verify(pin.edit.text.toString())){''',
'''            if(!pinStore.verify(pin.edit.text.toString())){''',
"check mandatory PIN without typed name"
)

main.write_text(s,encoding="utf-8")
gradle=base/"build.gradle.kts"
g=gradle.read_text(encoding="utf-8")
assert g.count("versionCode = 124")==1, "Unexpected source versionCode"
assert g.count('versionName = "1.9.114"')==1, "Unexpected source versionName"
g=g.replace("versionCode = 124","versionCode = 125",1)
g=g.replace('versionName = "1.9.114"','versionName = "1.9.115"',1)
gradle.write_text(g,encoding="utf-8")
print("v1.9.115 — eliminar perfil: PIN obrigatório, sem escrever nome; alvo preservado pelo ID.")
