"""SaúdePrática 1.9.65 caregiver dashboard and streamlined medication form."""
from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1')
base=root/'app/src/main/java/com/mediagenda/app'
def change(path,old,new,label):
    s=path.read_text(encoding='utf-8')
    if s.count(old)!=1: raise RuntimeError(f'v83 {label}: anchor count {s.count(old)}')
    path.write_text(s.replace(old,new,1),encoding='utf-8')
main=base/'MainActivity.kt'
change(main,'dosePatternButton=secondaryButton("Tipo de toma: "+patterns.first{it.second==chosenPattern}.first){',
 'dosePatternButton=secondaryButton("Alterar tipo de toma"){','remove duplicated medication pattern')
change(main,'dosePatternButton.text="Tipo de toma: "+patterns[index].first',
 'dosePatternButton.text="Alterar tipo de toma"','remove duplicated selection text')
change(main,'        box.addView(infoCard("➕", "Adicionar perfil", "Criar um novo perfil de saúde, sem palavra-passe") {',
 '''        val caregiverPrefs=getSharedPreferences("saudepratica_caregiver_v1",MODE_PRIVATE)
        val caregiver=caregiverPrefs.getString("caregiver_id","")
        box.addView(infoCard("🩺", "Perfil cuidador",
            if(caregiver==activeProfileId) "Este perfil acompanha as tomas atrasadas da família"
            else "Definir este perfil como cuidador da família") {
            MaterialAlertDialogBuilder(this)
                .setTitle("Perfil cuidador")
                .setMessage("O cuidador pode consultar tomas atrasadas dos outros perfis existentes neste telemóvel. Só envia mensagens pelo WhatsApp quando escolheres enviar. Os dados não são partilhados automaticamente.")
                .setPositiveButton("Ativar cuidador"){_,_->
                    caregiverPrefs.edit().putString("caregiver_id",activeProfileId).apply()
                    com.mediagenda.app.notifications.IntakeBadgeManager.refresh(this,activeProfileId)
                    showDataTools()
                }.setNeutralButton("Desativar"){_,_->
                    caregiverPrefs.edit().remove("caregiver_id").apply()
                    com.mediagenda.app.notifications.IntakeBadgeManager.refresh(this,activeProfileId)
                    showDataTools()
                }.setNegativeButton("Cancelar",null).show()
        })
        box.addView(infoCard("➕", "Adicionar perfil", "Criar um novo perfil de saúde, sem palavra-passe") {''','caregiver settings')
health=base/'HealthRecordsActivity.kt'
change(health,'        val format=SimpleDateFormat("dd/MM/yyyy · HH:mm",Locale("pt","PT"))\n        val overdue=store.overdueIntakes()',
'''        val caregiverId=getSharedPreferences("saudepratica_caregiver_v1",MODE_PRIVATE)
            .getString("caregiver_id",null)
        if(caregiverId==profileId){
            val otherProfiles=ProfileStore(this).all().filter{it.id!=profileId}
            val familyOverdue=otherProfiles.flatMap{person->
                runCatching{PersonalHealthStore(this,person.id).overdueIntakes()
                    .map{person to it}}.getOrDefault(emptyList())
            }.sortedBy{it.second.fields["scheduled_at"]?.toLongOrNull()?:it.second.timestamp}
            body.addView(label("👨‍👩‍👧 Tomas atrasadas da família · "+familyOverdue.size,
                19f,true).apply{setPadding(dp(4),dp(16),0,dp(8))})
            body.addView(label("Apenas perfis disponíveis neste telemóvel. O WhatsApp abre uma mensagem para rever e enviar; nunca é enviada automaticamente.",
                12f,color=muted).apply{setPadding(dp(5),0,0,dp(10))})
            if(familyOverdue.isEmpty())body.addView(label(
                "Não há tomas atrasadas nos outros perfis.",13f,color=muted))
            familyOverdue.forEach{(person,item)->
                val shell=card()
                val column=LinearLayout(this).apply{
                    orientation=LinearLayout.VERTICAL
                    setPadding(dp(15),dp(14),dp(15),dp(14))
                }
                val due=item.fields["scheduled_at"]?.toLongOrNull()?:item.timestamp
                val whenText=SimpleDateFormat("dd/MM/yyyy · HH:mm",Locale("pt","PT"))
                    .format(Date(due))
                column.addView(label(person.name+" · "+item.title,16f,true))
                column.addView(label("⚠️ Por confirmar desde "+whenText,13f,
                    color=Color.rgb(255,171,105)))
                column.addView(button("WhatsApp · lembrar "+person.name){
                    val phone=getSharedPreferences(
                        ProfileStore(this).preferencesFor(person.id),MODE_PRIVATE)
                        .getString("phone","").orEmpty().filter{it.isDigit()}
                    val message="Olá "+person.name+
                        ", a SaúdePrática mostra a toma de "+item.title+
                        " prevista para "+whenText+" ainda por confirmar. "+
                        "Podes confirmar se já a tomaste?"
                    if(phone.isBlank()){
                        alert("Este perfil não tem número de telemóvel. Adiciona-o na ficha do perfil.")
                    }else{
                        val number=if(phone.length==9)"351"+phone else phone
                        val url="https://wa.me/"+number+"?text="+
                            android.net.Uri.encode(message)
                        try{startActivity(Intent(Intent.ACTION_VIEW,
                            android.net.Uri.parse(url)))}
                        catch(_:Exception){alert("Não foi possível abrir o WhatsApp.")}
                    }
                })
                shell.addView(column);addCard(shell)
            }
        }
        val format=SimpleDateFormat("dd/MM/yyyy · HH:mm",Locale("pt","PT"))
        val overdue=store.overdueIntakes()''','caregiver overdue and WhatsApp')
badge=base/'notifications/IntakeBadgeManager.kt'
change(badge,'        if(profileId!=null && selected!=profileId)return',
'''        if(profileId!=null && selected!=profileId &&
            prefs(context).getString("current_profile",null)!=
                context.getSharedPreferences("saudepratica_caregiver_v1",
                    Context.MODE_PRIVATE).getString("caregiver_id",null))return''',
    'refresh caregiver badge when family dose changes')
change(badge,'''            else PersonalHealthStore(context,selected).overdueIntakes().size''',
'''            else {
                val own=PersonalHealthStore(context,selected).overdueIntakes().size
                val caregiver=context.getSharedPreferences("saudepratica_caregiver_v1",
                    Context.MODE_PRIVATE).getString("caregiver_id",null)
                if(caregiver==selected) own+ProfileStore(context).all()
                    .filter{it.id!=selected}.sumOf{
                        PersonalHealthStore(context,it.id).overdueIntakes().size
                    } else own
            }''','caregiver badge aggregate')
change(main,'''        val lateTomas=runCatching { PersonalHealthStore(this,activeProfileId)
            .overdueIntakes().size }.getOrDefault(0)''',
'''        val lateTomas=runCatching {
            val caregiver=getSharedPreferences("saudepratica_caregiver_v1",MODE_PRIVATE)
                .getString("caregiver_id",null)==activeProfileId
            (if(caregiver)profiles.all() else profiles.all().filter{it.id==activeProfileId})
                .sumOf{PersonalHealthStore(this,it.id).overdueIntakes().size}
        }.getOrDefault(0)''','caregiver dashboard total')
build=root/'app/build.gradle.kts'
change(build,'versionCode = 74','versionCode = 75','versionCode')
change(build,'versionName = "1.9.64"','versionName = "1.9.65"','versionName')
print('v1.9.65 caregiver dashboard, manual WhatsApp reminders, profile badge and no duplicate pattern')
