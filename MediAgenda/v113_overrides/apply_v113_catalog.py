"""SaúdePrática 1.9.94 Fase D: local clinic directory search.
Use the existing Portugal district/municipality catalogue; remember user-added
facilities without sending healthcare profile information to online services.
"""
from pathlib import Path
base=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app")

def replace(file,old,new,label):
    p=base/file
    s=p.read_text(encoding="utf-8")
    n=s.count(old)
    if n!=1:raise RuntimeError("Fase D facilities "+label+": "+str(n))
    p.write_text(s.replace(old,new,1),encoding="utf-8")

replace("HealthcareCatalog.kt",
'''    val types=listOf("Consulta", "Exame", "Exame complementar de diagnóstico",''',
'''    private const val LOCAL_PREFS="saudepratica_local_health_units_v1"
    /** Patient-independent, only manually chosen facility names. */
    private fun saved(context:Context):List<Facility> {
        val json=context.getSharedPreferences(LOCAL_PREFS,Context.MODE_PRIVATE)
            .getString("entries","[]") ?: "[]"
        return runCatching{
            val all=org.json.JSONArray(json)
            (0 until all.length()).mapNotNull{i->
                val item=all.optJSONObject(i)?:return@mapNotNull null
                val name=item.optString("name").take(120)
                val district=item.optString("district").take(80)
                val municipality=item.optString("municipality").take(80)
                if(name.isBlank()||district.isBlank()||municipality.isBlank())null
                else Facility(name,district,municipality)
            }
        }.getOrDefault(emptyList())
    }

    fun remember(context:Context,name:String,district:String,municipality:String) {
        val cleanName=name.trim().take(120)
        require(cleanName.length in 3..120)
        require(district in districts(context) &&
            municipality in municipalities(context,district)) {
            "Distrito ou concelho não reconhecido."
        }
        val current=saved(context)
        val candidate=Facility(cleanName,district,municipality)
        if((known+current).any{
            same(it.name,cleanName) && same(it.district,district) &&
                same(it.municipality,municipality)})return
        val list=(current+candidate).takeLast(150)
        val encoded=org.json.JSONArray()
        list.forEach{facility->
            encoded.put(JSONObject().put("name",facility.name)
                .put("district",facility.district)
                .put("municipality",facility.municipality))
        }
        check(context.getSharedPreferences(LOCAL_PREFS,Context.MODE_PRIVATE)
            .edit().putString("entries",encoded.toString()).commit()) {
                "Não foi possível guardar a unidade local."
            }
    }

    fun facilities(context:Context,district:String,municipality:String):List<Facility> =
        (known+saved(context)).filter{
            same(it.district,district) && same(it.municipality,municipality)
        }.distinctBy{normalize(it.name)}.sortedBy{it.name}

    /** Search by name or area. No GPS needed; works without Internet. */
    fun search(context:Context,query:String):List<Facility> {
        val term=normalize(query)
        if(term.length<2)return emptyList()
        return (known+saved(context)).filter{
            normalize(it.name).contains(term) ||
            normalize(it.municipality).contains(term) ||
            normalize(it.district).contains(term)
        }.distinctBy{normalize(it.name)+"|"+normalize(it.municipality)}
            .sortedWith(compareBy<Facility>{it.district}.thenBy{it.municipality}
                .thenBy{it.name}).take(80)
    }

    val types=listOf("Consulta", "Exame", "Exame complementar de diagnóstico",''',
"local clinics catalogue")

replace("MainActivity.kt",
'''        val options = listOf("📍 Usar localização do telemóvel") + districts
        MaterialAlertDialogBuilder(this).setTitle("1/3 · Escolher distrito ou região")
            .setItems(options.toTypedArray()) { _, index ->
                if (index == 0) requestHealthcareGps(onSelected)
                else chooseHealthcareMunicipality(districts[index-1],onSelected)
            }.setNegativeButton("Cancelar",null).show()''',
'''        val options = listOf("🔎 Procurar hospital / USF por nome",
            "📍 Usar localização do telemóvel") + districts
        MaterialAlertDialogBuilder(this).setTitle("Escolher unidade de saúde")
            .setItems(options.toTypedArray()) { _, index ->
                when(index){
                    0 -> searchHealthcareFacility(onSelected)
                    1 -> requestHealthcareGps(onSelected)
                    else -> chooseHealthcareMunicipality(districts[index-2],onSelected)
                }
            }.setNegativeButton("Cancelar",null).show()''',
"national search entry")

replace("MainActivity.kt",
'''    private fun chooseHealthcareFacility(district:String,municipality:String,onSelected:(String)->Unit) {
        val facilities=HealthcareCatalog.facilities(district,municipality)''',
'''    private fun searchHealthcareFacility(onSelected:(String)->Unit){
        val field=android.widget.EditText(this).apply{
            hint="Ex.: Vila Franca de Xira, Santa Maria, IPO"
            setSingleLine(true)
            setPadding(dp(16),dp(12),dp(16),dp(12))
        }
        MaterialAlertDialogBuilder(this).setTitle("Pesquisar unidade · catálogo local")
            .setMessage("Pesquisa por hospital, USF, concelho ou distrito. "+
                "A lista local não substitui o registo oficial ERS.")
            .setView(field).setNegativeButton("Cancelar",null)
            .setPositiveButton("Pesquisar"){_,_->
                val hits=HealthcareCatalog.search(this,field.text.toString())
                if(hits.isEmpty()){
                    MaterialAlertDialogBuilder(this).setTitle("Sem resultados locais")
                        .setMessage("Não encontrei essa unidade no catálogo. "+
                            "Podes pesquisar no diretório oficial ERS ou "+
                            "introduzir a unidade pelo distrito e concelho.")
                        .setPositiveButton("Distrito / Concelho"){_,_->
                            chooseHealthcareDistrict(onSelected)
                        }.setNeutralButton("Abrir ERS"){_,_->
                            openUrl(HealthcareCatalog.ersUrl)
                        }.setNegativeButton("Fechar",null).show()
                }else{
                    val names=hits.map{
                        it.name+" · "+it.municipality+" ("+it.district+")"
                    }.toTypedArray()
                    MaterialAlertDialogBuilder(this).setTitle("Unidades encontradas")
                        .setItems(names){_,which->onSelected(hits[which].name)}
                        .setNeutralButton("Nova pesquisa"){_,_->
                            searchHealthcareFacility(onSelected)
                        }.setNegativeButton("Cancelar",null).show()
                }
            }.show()
    }

    private fun chooseHealthcareFacility(district:String,municipality:String,onSelected:(String)->Unit) {
        val facilities=HealthcareCatalog.facilities(this,district,municipality)''',
"search facilities")

replace("MainActivity.kt",
'''                    facilities.size -> enterHealthcareFacility(municipality,onSelected)''',
'''                    facilities.size -> enterHealthcareFacility(district,municipality,onSelected)''',
"pass area to custom facility")

replace("MainActivity.kt",
'''    private fun enterHealthcareFacility(municipality:String,onSelected:(String)->Unit) {''',
'''    private fun enterHealthcareFacility(district:String,municipality:String,
        onSelected:(String)->Unit) {''',
"custom area sig")

replace("MainActivity.kt",
'''                if(name.isNotEmpty())onSelected(name)
            }.setNegativeButton("Cancelar",null).show()
    }

    private fun requestHealthcareGps''',
'''                if(name.isNotEmpty()){
                    runCatching{
                        HealthcareCatalog.remember(this,name,district,municipality)
                    }.onFailure{
                        Toast.makeText(this,"Unidade selecionada, mas não guardada: "+
                            (it.message?:"erro"),Toast.LENGTH_LONG).show()
                    }
                    onSelected(name)
                }
            }.setNegativeButton("Cancelar",null).show()
    }

    private fun requestHealthcareGps''',
"persist clinic without patient details")

print("Fase D 1.9.94: local hospital/name search, no location requirement, saved facilities")
