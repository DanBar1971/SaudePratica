"""SaúdePrática v1.9.80: user-ordered shortcuts, concise dashboard cards,
shared care-home institution and explicit multi-resident profiles.

All billing, notes, care valence and medical documents stay tied to stable
resident profile IDs. Legacy institution settings are copied non-destructively.
"""
from pathlib import Path

root=Path('build-src/MediAgenda_Android_v1')
base=root/'app/src/main/java/com/mediagenda/app'

def replace(path,old,new,label):
    s=path.read_text(encoding='utf-8')
    count=s.count(old)
    if count!=1: raise RuntimeError(f'v98 {label}: anchor count {count}')
    path.write_text(s.replace(old,new,1),encoding='utf-8')

shortcuts=base/'ImportantShortcutsActivity.kt'
replace(shortcuts,
'''        card.addView(row)
        body.addView(card,LinearLayout.LayoutParams(-1,-2)''',
'''        val stack=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
        stack.addView(row)
        if(manage){
            val ordering=LinearLayout(this).apply{
                orientation=LinearLayout.HORIZONTAL
                setPadding(dp(10),0,dp(10),dp(9))
            }
            val current=read().indexOfFirst{it.id==link.id}
            val total=read().size
            val up=button(tr("↑ Subir","↑ Up","↑ Monter","↑ Hoch","↑ Subir")){
                moveShortcut(link,-1)
            }.apply{isEnabled=current>0;alpha=if(isEnabled)1f else 0.4f}
            val down=button(tr("↓ Descer","↓ Down","↓ Descendre","↓ Runter","↓ Bajar")){
                moveShortcut(link,1)
            }.apply{isEnabled=current>=0 && current<total-1
                alpha=if(isEnabled)1f else 0.4f}
            ordering.addView(up,LinearLayout.LayoutParams(0,dp(44),1f))
            ordering.addView(down,LinearLayout.LayoutParams(0,dp(44),1f))
            stack.addView(ordering)
        }
        card.addView(stack)
        body.addView(card,LinearLayout.LayoutParams(-1,-2)''', 'shortcuts reorder controls')
replace(shortcuts,'''    private fun open(raw:String){''','''    /** Save a positional swap, preserving all custom links and IDs. */
    private fun moveShortcut(link:Link,step:Int){
        val items=read()
        val from=items.indexOfFirst{it.id==link.id}
        val to=from+step
        if(from<0 || to !in items.indices)return
        java.util.Collections.swap(items,from,to)
        save(items)
        render()
    }

    private fun open(raw:String){''','shortcut reorder function')

main=base/'MainActivity.kt'
replace(main,'"ERPI, Centro de Dia, SAD, faturas e ADSE"','"Lar, faturas e ADSE"','brief carehome desc')
replace(main,'"ADSE, CGA, IRS e outros links"','"Links úteis"','brief shortcuts desc')

care=base/'CareHomeActivity.kt'
replace(care,
'''    private var pendingMonth=""
    private val prefs by lazy { getSharedPreferences("saudepratica_care_home_v1_" + profileId,MODE_PRIVATE) }''',
'''    private var pendingMonth=""
    private var pendingResidentId=""
    // The institution is shared; each person's valence, bills and notes remain private.
    private val facility get()=getSharedPreferences(
        "saudepratica_care_home_institution_v2",MODE_PRIVATE)
    private val prefs get()=getSharedPreferences(
        "saudepratica_care_home_v1_"+profileId,MODE_PRIVATE)
    private fun residents()=facility.getStringSet("residents",emptySet())
        .orEmpty().filter{ id -> ProfileStore(this).all().any{it.id==id} }.toSet()
    private fun residentLabel(id:String)=ProfileStore(this).all().firstOrNull{it.id==id}
        ?.name.orEmpty()
    private fun migrateInstitution(){
        if(facility.contains("institution_migrated"))return
        val users=ProfileStore(this).all()
        val previous=users.map{
            getSharedPreferences("saudepratica_care_home_v1_"+it.id,MODE_PRIVATE)
        }.firstOrNull{ !it.getString("institution","").isNullOrBlank() }
        val edit=facility.edit()
        if(previous!=null)for(key in listOf("institution","address","phone","email","website"))
            edit.putString(key,previous.getString(key,"").orEmpty())
        // Do not guess which user lives in the home; selection is always explicit.
        check(edit.putBoolean("institution_migrated",true).commit())
    }
    private fun manageResidents(){
        val available=ProfileStore(this).all()
        val existing=residents()
        val chosen=available.map{it.id in existing}.toBooleanArray()
        MaterialAlertDialogBuilder(this).setTitle("Quem vive neste lar?")
            .setMultiChoiceItems(available.map{it.name}.toTypedArray(),chosen){_,index,value->
                chosen[index]=value
            }.setNegativeButton("Cancelar",null)
            .setPositiveButton("Guardar"){_,_->
                val selected=available.filterIndexed{index,_->chosen[index]}
                    .map{it.id}.toSet()
                if(!facility.edit().putStringSet("residents",selected).commit()){
                    notifyUser("Não foi possível guardar os residentes.")
                }else{
                    // Never silently associate the currently active health profile.
                    if(profileId !in selected)profileId=selected.firstOrNull().orEmpty()
                    profileName=residentLabel(profileId)
                    facility.edit().putString("last_resident_id",profileId).apply()
                }
                render()
            }.show()
    }
    private fun chooseResident(){
        val people=ProfileStore(this).all().filter{it.id in residents()}
        if(people.isEmpty()){manageResidents();return}
        MaterialAlertDialogBuilder(this).setTitle("Escolher residente")
            .setItems(people.map{it.name}.toTypedArray()){_,index->
                profileId=people[index].id
                profileName=people[index].name
                facility.edit().putString("last_resident_id",profileId).apply()
                render()
            }.setNegativeButton("Cancelar",null).show()
    }''', 'shared home resident prefs')
replace(care,
'''        val selected=pendingMonth
        if(!selected.matches(Regex("[0-9]{4}-[0-9]{2}")))return@registerForActivityResult
        runCatching{
            val store=HealthDocumentStore(this,profileId)
            val document=store.add(uri,"Lar · Fatura "+selected)
            val item=invoice(selected)
            item.put("document_id",document.id)
            item.put("document_name",document.name)
            item.put("state","RECEBIDA")
            saveInvoice(selected,item)''',
'''        val selected=pendingMonth
        val target=pendingResidentId
        if(!selected.matches(Regex("[0-9]{4}-[0-9]{2}")) ||
            target !in residents() || target!=profileId)return@registerForActivityResult
        runCatching{
            val store=HealthDocumentStore(this,target)
            val document=store.add(uri,"Lar · Fatura "+selected)
            val item=invoice(selected)
            item.put("document_id",document.id)
            item.put("document_name",document.name)
            item.put("state","RECEBIDA")
            saveInvoice(selected,item)''','protect pending document target')
replace(care,
'''        profileId=profile.id
        profileName=profile.name
        val root=''','''        profileId=profile.id
        profileName=profile.name
        migrateInstitution()
        val linked=residents()
        val last=facility.getString("last_resident_id","").orEmpty()
        profileId=when{
            last in linked -> last
            profileId in linked -> profileId
            else -> ProfileStore(this).all().firstOrNull{it.id in linked}?.id.orEmpty()
        }
        profileName=residentLabel(profileId)
        val root=''','select only linked resident')
replace(care,'"🏡 Lares e Apoio à Terceira Idade",21f,true','"🏡 Lares e Apoio",21f,true','shorter header')
replace(care,
'''    private fun institution()=prefs.getString("institution","").orEmpty()''',
'''    private fun institution()=facility.getString("institution","").orEmpty()''','shared institution getter')
replace(care,
'''        val mail=Uri.parse("mailto:"+Uri.encode(prefs.getString("email",''',
'''        val mail=Uri.parse("mailto:"+Uri.encode(facility.getString("email",''','shared email')
replace(care,
'''        val subject="Pedido de fatura mensal do lar — "+monthLabel()''',
'''        val subject="Pedido de fatura do lar — "+profileName+" — "+monthLabel()''','email resident subject')
replace(care,
'''            monthLabel()+", para apresentação à ADSE.\\n\\nCom os melhores cumprimentos."''',
'''            monthLabel()+", relativa ao/à residente "+profileName+
            ", para apresentação à ADSE.\\n\\nCom os melhores cumprimentos."''','email resident body')
for key in ["address","phone","email","website"]:
    replace(care, f'field(prefs.getString("{key}"',f'field(facility.getString("{key}"',f'shared {key} editor')
replace(care,
'''                prefs.edit()
                    .putString("institution",''',
'''                facility.edit()
                    .putString("institution",''','shared APATI default')
replace(care,
'''                prefs.edit().putString("institution",clean)''',
'''                facility.edit().putString("institution",clean)''','shared manual institution')
# Single card display obtains the institution data from the shared registry.
for key in ["address","phone","website"]:
    replace(care, f'val {"site" if key=="website" else key}=prefs.getString("{key}"', f'val {"site" if key=="website" else key}=facility.getString("{key}"',f'shared {key} display')
replace(care,
'''        body.removeAllViews()
        addCard("Perfil: "+profileName){card->
            card.addView(label("Instituição: "+institution().ifBlank{"Por configurar"},16f,true))
            card.addView(label("Valência: "+when(valence()){
                "ERPI"->"ERPI · Residência";"SAD"->"Apoio domiciliário";else->"Centro de Dia"
            },14f))
            card.addView(button("⚙ Editar instituição e contactos"){editInstitution()})
            card.addView(button("Escolher ERPI / SAD / Centro de Dia"){editValence()})''',
'''        body.removeAllViews()
        addCard("🏡 Instituição"){card->
            card.addView(label(institution().ifBlank{"Por configurar"},16f,true))
            card.addView(label("Esta ficha e os contactos são comuns aos residentes do lar.",12f))
            card.addView(button("⚙ Editar instituição e contactos"){editInstitution()})''','shared institution card')
replace(care,
'''        addCard("🧾 Faturas e ADSE"){card->''',
'''        addCard("👥 Residentes do lar"){card->
            val people=ProfileStore(this).all().filter{it.id in residents()}
            if(people.isEmpty())card.addView(label(
                "Ainda não selecionaste quem vive neste lar. Seleciona Camy ou os outros familiares.",14f))
            else {
                card.addView(label("Residentes: "+people.joinToString(", "){it.name},13f))
                card.addView(label("Residente em acompanhamento: "+profileName,16f,true))
                card.addView(button("👤 Escolher residente"){chooseResident()})
            }
            card.addView(button("＋ Associar / retirar residentes"){manageResidents()})
        }
        if(profileId !in residents()){
            addCard("📂 Faturas e cuidados"){card->
                card.addView(label("Seleciona primeiro quem está no lar. As faturas e documentos ficam sempre no perfil do residente.",14f))
            }
            return
        }
        addCard("👤 Valência de "+profileName){card->
            card.addView(label(when(valence()){
                "ERPI"->"ERPI · Residência";"SAD"->"Apoio domiciliário";else->"Centro de Dia"
            },15f))
            card.addView(button("Alterar ERPI / SAD / Centro de Dia"){editValence()})
        }
        addCard("🧾 Faturas e ADSE · "+profileName){card->''','resident selectors and guard')
replace(care,
'''                pendingMonth=monthKey()
                picker.launch''','''                pendingMonth=monthKey()
                pendingResidentId=profileId
                picker.launch''','record pending attachment owner')
replace(care,
'''        addCard("📅 Visitas, cuidados e notas"){card->''',
'''        addCard("📅 Visitas, cuidados e notas · "+profileName){card->''','resident notes label')

build=root/'app/build.gradle.kts'
replace(build,'versionCode = 89','versionCode = 90','version code')
replace(build,'versionName = "1.9.79"','versionName = "1.9.80"','version name')
print('v1.9.80 shortcuts reorder, concise cards, shared institution & explicit multi-residents')

# Always restore official SaúdePrática artwork before compilation.
# Portable base64 PNG resources are held in the repository; no private keys.
import base64, struct, re
artdir=Path("MediAgenda/v98_overrides/branding")
resdir=root/"app/src/main/res/drawable-nodpi"
resdir.mkdir(parents=True,exist_ok=True)
for name in ("saude_background","saude_icon","saude_splash"):
    data=base64.b64decode((artdir/(name+".png.b64")).read_text(encoding="ascii"))
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError("Invalid SaúdePrática artwork: "+name)
    width,height=struct.unpack(">II",data[16:24])
    if width<900 or height<900 or len(data)<50000:
        raise RuntimeError("Missing original quality image: "+name)
    (resdir/(name+".png")).write_bytes(data)
    print("Original image restored:",name,width,height,len(data))

# Ensure launcher resolves to official artwork, not the placeholder mipmap.
manifest=root/"app/src/main/AndroidManifest.xml"
source=manifest.read_text(encoding="utf-8")
source,n=re.subn(r'android:icon="@(?:mipmap|drawable)/[^"]+"',
                 'android:icon="@drawable/saude_icon"',source,count=1)
if n!=1: raise RuntimeError("No Android launcher icon attribute")
source=re.sub(r'android:roundIcon="@(?:mipmap|drawable)/[^"]+"',
              'android:roundIcon="@drawable/saude_icon"',source,count=1)
manifest.write_text(source,encoding="utf-8")
print("SaúdePrática official launcher and splash graphics: restored")
