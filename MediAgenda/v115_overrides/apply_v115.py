"""SaúdePrática v1.9.96: Fase E Health Connect + hydration, clarify Fase D.
Reference implementations: Android Health Samples (Apache-2.0), OpenVitals
(AGPL architecture inspiration ONLY; no copying), native HC framework on Android 14+.
"""
from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1');b=root/'app/src/main/java/com/mediagenda/app'
source=Path('MediAgenda/v115_overrides')
def patch(file,old,new,tag):
    path=b/file;s=path.read_text(encoding='utf-8');num=s.count(old)
    if num!=1:raise RuntimeError(f'Fase E {tag}: expected 1, found {num}')
    path.write_text(s.replace(old,new,1),encoding='utf-8')

# Health Connect native records, with no third-party permission or direct Mi Fitness API.
patch('ActivityHealthConnect.kt','import android.health.connect.AggregateRecordsResponse', '''import android.health.connect.AggregateRecordsResponse
import android.health.connect.ReadRecordsRequestUsingFilters
import android.health.connect.ReadRecordsResponse
import android.health.connect.datatypes.Record
import android.health.connect.datatypes.OxygenSaturationRecord
import android.health.connect.datatypes.WeightRecord
import android.health.connect.datatypes.RestingHeartRateRecord
import android.health.connect.datatypes.BloodPressureRecord
import android.health.connect.datatypes.RespiratoryRateRecord
import android.health.connect.datatypes.BodyTemperatureRecord
import com.mediagenda.app.data.BodyMeasurements
import android.widget.EditText''','HC imports')
patch('ActivityHealthConnect.kt','''        HealthPermissions.READ_TOTAL_CALORIES_BURNED
    )''','''        HealthPermissions.READ_TOTAL_CALORIES_BURNED,
        HealthPermissions.READ_OXYGEN_SATURATION,
        HealthPermissions.READ_WEIGHT,
        HealthPermissions.READ_RESTING_HEART_RATE,
        HealthPermissions.READ_BLOOD_PRESSURE,
        HealthPermissions.READ_RESPIRATORY_RATE,
        HealthPermissions.READ_BODY_TEMPERATURE
    )''','optional HC types')
patch('ActivityHealthConnect.kt','''permissions.any { allowed(it) }''','''(permissions+optionalPermissions).any { allowed(it) }''','additional perms contribute to active state')
patch('ActivityHealthConnect.kt','''        addWeeklyCharts(date, current)
        val from = date.atStartOfDay''','''        addWeeklyCharts(date, current)
        showExtendedMeasurements(current)
        val from = date.atStartOfDay''','extended records panel')
patch('ActivityHealthConnect.kt','''            "Energia total (opcional)" to HealthPermissions.READ_TOTAL_CALORIES_BURNED''','''            "Energia total (opcional)" to HealthPermissions.READ_TOTAL_CALORIES_BURNED,
            "Oxigénio SpO₂" to HealthPermissions.READ_OXYGEN_SATURATION,
            "Peso" to HealthPermissions.READ_WEIGHT,
            "Frequência cardíaca em repouso" to HealthPermissions.READ_RESTING_HEART_RATE,
            "Tensão arterial" to HealthPermissions.READ_BLOOD_PRESSURE,
            "Frequência respiratória" to HealthPermissions.READ_RESPIRATORY_RATE,
            "Temperatura corporal" to HealthPermissions.READ_BODY_TEMPERATURE''','settings permission labels')
# add input and reading methods before existing chart logic
marker='    private fun addWeeklyCharts(date: LocalDate, generation: Int) {'
extra='''    /** Each reading is displayed only when its specific permission was granted.
     * Data from Mi Fitness can be absent when the upstream app does not export it.
     * Health Connect records never leave the phone or go to app backups.
     */
    private fun showExtendedMeasurements(generation:Int){
        val panel=box(content,"Sinais vitais · Health Connect",
            "Medições disponibilizadas pelas aplicações autorizadas. Sem registos não significa zero. " +
            "O Mi Fitness pode não exportar o oxigénio ou todos os batimentos do relógio.")
        val start=LocalDate.now().minusDays(7).atStartOfDay(ZoneId.systemDefault()).toInstant()
        val end=Instant.now()
        fun cell(title:String):TextView=label("$title: a consultar…",15f).also{
            it.setPadding(0,dp(8),0,dp(5));panel.addView(it)
        }
        val oxygen=cell("🫁 SpO₂")
        val weight=cell("⚖ Peso no Health Connect")
        val rest=cell("❤️ Pulso em repouso")
        val pressure=cell("🩺 Tensão arterial")
        val breath=cell("🌬 Respiração")
        val temperature=cell("🌡 Temperatura")
        fun show(view:TextView,permission:String,formatter:()->Unit){
            if(!allowed(permission))view.text=view.text.toString().substringBefore(':')+": sem permissão"
            else formatter()
        }
        show(oxygen,HealthPermissions.READ_OXYGEN_SATURATION){
            readLatest(OxygenSaturationRecord::class.java,start,end){r,error->
                if(generation==requestGeneration)oxygen.text=when{
                    error!=null->"🫁 SpO₂: erro ao consultar"
                    r==null->"🫁 SpO₂: sem registos enviados ao Health Connect"
                    else->String.format(Locale("pt","PT"),"🫁 SpO₂: %.1f %%",r.percentage.value)
                }
            }
        }
        show(weight,HealthPermissions.READ_WEIGHT){
            readLatest(WeightRecord::class.java,start,end){r,error->
                if(generation==requestGeneration)weight.text=when{
                    error!=null->"⚖ Peso: erro ao consultar"
                    r==null->"⚖ Peso: sem registos partilhados"
                    else->String.format(Locale("pt","PT"),"⚖ Peso: %.1f kg",r.weight.inGrams / 1000.0)
                }
            }
        }
        show(rest,HealthPermissions.READ_RESTING_HEART_RATE){
            readLatest(RestingHeartRateRecord::class.java,start,end){r,error->
                if(generation==requestGeneration)rest.text=when{
                    error!=null->"❤️ Repouso: erro ao consultar"
                    r==null->"❤️ Repouso: sem registos"
                    else->"❤️ Repouso: ${r.beatsPerMinute} bpm"
                }
            }
        }
        show(pressure,HealthPermissions.READ_BLOOD_PRESSURE){
            readLatest(BloodPressureRecord::class.java,start,end){r,error->
                if(generation==requestGeneration)pressure.text=when{
                    error!=null->"🩺 Tensão: erro ao consultar"
                    r==null->"🩺 Tensão: sem registos"
                    else->String.format(Locale("pt","PT"),"🩺 Tensão: %.0f / %.0f mmHg",
                        r.systolic.inMillimetersOfMercury,r.diastolic.inMillimetersOfMercury)
                }
            }
        }
        show(breath,HealthPermissions.READ_RESPIRATORY_RATE){
            readLatest(RespiratoryRateRecord::class.java,start,end){r,error->
                if(generation==requestGeneration)breath.text=when{
                    error!=null->"🌬 Respiração: erro ao consultar"
                    r==null->"🌬 Respiração: sem registos"
                    else->String.format(Locale("pt","PT"),"🌬 Respiração: %.0f/min",r.rate)
                }
            }
        }
        show(temperature,HealthPermissions.READ_BODY_TEMPERATURE){
            readLatest(BodyTemperatureRecord::class.java,start,end){r,error->
                if(generation==requestGeneration)temperature.text=when{
                    error!=null->"🌡 Temperatura: erro ao consultar"
                    r==null->"🌡 Temperatura: sem registos"
                    else->String.format(Locale("pt","PT"),"🌡 Temperatura: %.1f °C",r.temperature.inCelsius)
                }
            }
        }
        val metrics=BodyMeasurements(this,profileId)
        val manual=box(content,"Peso manual e IMC (adultos)",
            "Registos privados deste perfil. O IMC é uma referência estatística, " +
            "não diagnostica saúde ou composição corporal.")
        val previous=metrics.recent()
        val latest=previous.firstOrNull()?.second
        manual.addView(label("Altura: "+if(metrics.heightCm()>0)"${metrics.heightCm().toInt()} cm" else "por indicar",15f))
        manual.addView(label("Último peso manual: "+(latest?.let{
            String.format(Locale("pt","PT"),"%.1f kg",it)
        }?:"não registado"),15f))
        latest?.let{kg->metrics.adultBmi(kg)?.let{bmi->
            manual.addView(label(String.format(Locale("pt","PT"),
                "IMC: %.1f · %s",bmi,metrics.adultBmiLabel(bmi)),14f))
        }}
        manual.addView(action("＋ Registar peso e altura"){editBodyMeasurements()})
        if(previous.size>=2){
            val history=previous.take(10).reversed()
            val min=history.minOf{it.second};val max=history.maxOf{it.second}
            manual.addView(label("Evolução do peso (últimos ${history.size} registos)",13f,true))
            history.forEach{(time,kg)->
                val day=java.time.Instant.ofEpochMilli(time).atZone(ZoneId.systemDefault())
                    .toLocalDate().format(DateTimeFormatter.ofPattern("dd/MM"))
                val fraction=if(max>min)((kg-min)/(max-min)*.82+.15).toFloat() else .6f
                val row=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL
                    gravity=Gravity.CENTER_VERTICAL}
                row.addView(label(day,12f),LinearLayout.LayoutParams(dp(48),dp(30)))
                row.addView(View(this).apply{background=GradientDrawable().apply{
                    setColor(teal);cornerRadius=dp(7).toFloat()
                }},LinearLayout.LayoutParams(0,dp(13),fraction))
                row.addView(View(this),LinearLayout.LayoutParams(0,dp(13),1f-fraction))
                row.addView(label(String.format(Locale("pt","PT"),"%.1f",kg),12f),
                    LinearLayout.LayoutParams(dp(48),dp(30)))
                manual.addView(row)
            }
        }
    }

    private fun editBodyMeasurements(){
        val metrics=BodyMeasurements(this,profileId)
        val layout=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL
            setPadding(dp(20),dp(12),dp(20),dp(8))}
        val height=EditText(this).apply{hint="Altura em cm (ex.: 172)"
            setText(metrics.heightCm().takeIf{it>0}?.toInt()?.toString().orEmpty())
            inputType=android.text.InputType.TYPE_CLASS_NUMBER or
                android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL}
        val weight=EditText(this).apply{hint="Peso em kg (ex.: 75,5)"
            inputType=android.text.InputType.TYPE_CLASS_NUMBER or
                android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL}
        layout.addView(height);layout.addView(weight)
        val dialog=MaterialAlertDialogBuilder(this).setTitle("Peso e altura")
            .setView(layout).setNegativeButton("Cancelar",null)
            .setPositiveButton("Guardar",null).show()
        dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE).setOnClickListener{
            try{
                val h=height.text.toString().replace(',','.').toDoubleOrNull()
                val kg=weight.text.toString().replace(',','.').toDoubleOrNull()
                if(h!=null)metrics.setHeight(h)
                require(kg!=null){"Indica um peso válido."}
                metrics.addWeight(kg);dialog.dismiss();showScreen()
            }catch(ex:Exception){weight.error=ex.message?:"Confirma os valores."}
        }
    }

    private fun <T:Record> readLatest(type:Class<T>,start:Instant,end:Instant,
        done:(T?,Exception?)->Unit){
        val health=manager?:return
        try{
            val filter=TimeInstantRangeFilter.Builder().setStartTime(start).setEndTime(end).build()
            val request=ReadRecordsRequestUsingFilters.Builder(type)
                .setTimeRangeFilter(filter).setPageSize(250).setAscending(false).build()
            health.readRecords(request,mainExecutor,
                object:OutcomeReceiver<ReadRecordsResponse<T>,HealthConnectException>{
                    override fun onResult(result:ReadRecordsResponse<T>){
                        done(result.records.firstOrNull(),null)
                    }
                    override fun onError(error:HealthConnectException){done(null,error)}
                })
        }catch(ex:Exception){done(null,ex)}
    }

'''
patch('ActivityHealthConnect.kt',marker,extra+marker,'extended native record reads and manual weight')
# Update existing weekly chart options to include heart-rate and weight aggregate series.
patch('ActivityHealthConnect.kt','''            Series("Sono", display = { "${it.toInt() / 60}h ${it.toInt() % 60}m" },
                average = { "${it.toInt() / 60}h ${it.toInt() % 60}m/noite" })''','''            Series("Sono", display = { "${it.toInt() / 60}h ${it.toInt() % 60}m" },
                average = { "${it.toInt() / 60}h ${it.toInt() % 60}m/noite" }),
            Series("Pulso", display = { "${it.toInt()} bpm" },
                average = { "${it.toInt()} bpm" }),
            Series("Peso", display = { String.format(Locale("pt","PT"),"%.1f kg",it) },
                average = { String.format(Locale("pt","PT"),"%.1f kg",it) })''','weekly dataset HR weight')
patch('ActivityHealthConnect.kt','''        listOf(listOf(0, 1), listOf(2, 3)).forEach { pair ->''','''        listOf(listOf(0, 1), listOf(2, 3), listOf(4, 5)).forEach { pair ->''','weekly selectors')
patch('ActivityHealthConnect.kt','''        querySeries(3, HealthPermissions.READ_SLEEP, SleepSessionRecord.SLEEP_DURATION_TOTAL,
            { it.toDouble() / 60000.0 }, true)''','''        querySeries(3, HealthPermissions.READ_SLEEP, SleepSessionRecord.SLEEP_DURATION_TOTAL,
            { it.toDouble() / 60000.0 }, true)
        querySeries(4, HealthPermissions.READ_HEART_RATE, HeartRateRecord.BPM_AVG,
            { it.toDouble() })
        querySeries(5, HealthPermissions.READ_WEIGHT, WeightRecord.WEIGHT_AVG,
            { it.inGrams / 1000.0 })''','weekly queries')

# Write new patient-isolated local measurements class.
(b/'data/BodyMeasurements.kt').write_text((source/'BodyMeasurements.kt').read_text(),encoding='utf-8')

# Manifest: granular permissions must be explicitly declared before Android grants them.
manifest=root/'app/src/main/AndroidManifest.xml';m=manifest.read_text()
anchor='<uses-permission android:name="android.permission.health.READ_HEART_RATE" />'
assert m.count(anchor)==1
adds='\n'.join('    <uses-permission android:name="android.permission.health.READ_'+name+'" />' for name in (
    'OXYGEN_SATURATION','WEIGHT','RESTING_HEART_RATE','BLOOD_PRESSURE','RESPIRATORY_RATE','BODY_TEMPERATURE'))
manifest.write_text(m.replace(anchor,anchor+'\n'+adds,1))

# Hydration: allow multiple incremental goals on the SAME day and reschedule even
# when the old goal already completed; do not reset the amount already drunk.
patch('data/WellnessStore.kt','''    fun todayMl(): Int {''','''    /** Adds fluid allowance only after explicit user confirmation.
     * Existing water drunk and reminder acknowledgements remain intact.
     */
    fun increaseTarget(extra:Int):Int{
        require(extra in 100..3000){"Acrescenta entre 100 ml e 3 litros."}
        val newTarget=(maxOf(optionalTargetMl,todayMl())+extra).coerceAtMost(10000)
        require(newTarget>todayMl()){"Já atingiste o limite configurável."}
        check(prefs.edit().putInt("water_target_ml",newTarget)
            .remove("water_goal_notified_date").commit()){
            "Não foi possível guardar o novo objetivo de hoje."
        }
        return newTarget
    }

    fun todayMl(): Int {''','increase hydration target')
patch('WellnessActivity.kt','''        card(content, "Corrigir registo", "Retirar o último copo adicionado, se te enganaste.",''','''        val fraction=if(goal>0)(amount.toDouble()/goal).coerceIn(0.0,1.0) else 0.0
        val progress=android.widget.ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal)
            .apply{max=1000;this.progress=(fraction*1000).toInt()
                progressTintList=ColorStateList.valueOf(turquoise)}
        content.addView(progress,LinearLayout.LayoutParams(-1,dp(12)).apply{
            bottomMargin=dp(12)})
        card(content,"Adicionar novo objetivo hoje",
            "Já bebeste $amount ml. Acrescenta mais água para hoje sem apagar os copos. " +
            "Os avisos poderão voltar a tocar ainda hoje dentro do horário escolhido.",
            "＋ Acrescentar água / Reagendar"){
            val options=arrayOf("＋ 250 ml","＋ 500 ml","＋ 750 ml","＋ 1000 ml","＋ 1500 ml")
            val values=intArrayOf(250,500,750,1000,1500)
            MaterialAlertDialogBuilder(this).setTitle("Mais água para hoje?")
                .setMessage("Só altera o objetivo. Confirma que não tens restrições de líquidos.")
                .setItems(options){_,choice->
                    runCatching{
                        val extra=values[choice]
                        val newTarget=(store.todayMl()+extra)
                        require(newTarget<=10000){"Limite de 10 litros no objetivo."}
                        store.increaseTarget(extra)
                        if(!store.waterEnabled){
                            store.saveWater(true,store.waterStart,store.waterEnd,
                                store.waterInterval,store.glassMl,store.optionalTargetMl)
                        }
                        NotificationScheduler(this).scheduleNextWater(profileId)
                    }.onSuccess{
                        Toast.makeText(this,"Novo objetivo guardado. Avisos atualizados.",
                            Toast.LENGTH_LONG).show()
                    }.onFailure{Toast.makeText(this,it.message?:"Erro ao atualizar",
                        Toast.LENGTH_LONG).show()}
                    showWater()
                }.setNegativeButton("Cancelar",null).show()
        }
        card(content, "Corrigir registo", "Retirar o último copo adicionado, se te enganaste.",''','hydration new daily goal and progress')

# Fase D: make paths discoverable on the Agenda screen and Documents label.
patch('MainActivity.kt','''        screenHeader("📅", "Agenda", "Consultas, exames e tratamentos num só lugar")

        val items''','''        screenHeader("📅", "Agenda", "Consultas, exames e tratamentos num só lugar")
        content.addView(infoCard("🏥", "Pesquisar unidades de saúde",
            "Pesquisar por nome, distrito, concelho ou GPS (opcional)."){
            showHealthcareSearchHelp()
        })
        content.addView(infoCard("📎", "Importar guia PDF ou fotografia",
            "Os originais são guardados automaticamente nos Documentos Digitais."){
            pickHealthDocument("agenda")
        })
        val items''','D agenda visible cards')
patch('MainActivity.kt','''    private fun showDocuments() {''','''    /** Dedicated discoverable entry to Fase D search, separate from appointment editor. */
    private fun showHealthcareSearchHelp(){
        MaterialAlertDialogBuilder(this).setTitle("Unidades de saúde · Fase D")
            .setMessage("Pesquisa hospitais, centros de saúde e USF ao criar uma consulta. " +
                "Podes procurar pelo nome, distrito ou concelho e guardar novas unidades. " +
                "O catálogo offline pode não estar completo.")
            .setPositiveButton("Criar marcação"){_,_->editAppointment(null)}
            .setNeutralButton("Ver catálogo e escolher unidade"){_,_->
                chooseHealthcareDistrict{unit->
                    MaterialAlertDialogBuilder(this).setTitle("Unidade encontrada")
                        .setMessage(unit+"\\nPara associar a uma consulta, cria ou edita uma marcação.")
                        .setPositiveButton("Criar marcação"){_,_->editAppointment(null)}
                        .setNegativeButton("Fechar",null).show()
                }
            }.setNegativeButton("Fechar",null).show()
    }

    private fun showDocuments() {''','D search explanation')
patch('MainActivity.kt','''DashboardModule("📂", "Documentos", "PDFs e imagens")''','''DashboardModule("📂", "Documentos", "Originais PDF e fotografias")''','D labels')

# Keep app update signature and graphics unchanged.
gradle=root/'app/build.gradle.kts';s=gradle.read_text();assert s.count('versionCode = 105')==1 and s.count('versionName = "1.9.95"')==1
s=s.replace('versionCode = 105','versionCode = 106',1).replace('versionName = "1.9.95"','versionName = "1.9.96"',1);gradle.write_text(s)
print('SaúdePrática 1.9.96: Health Connect additional vitals, weight/BMI chart, water goals and D navigation')