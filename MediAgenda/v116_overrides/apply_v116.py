"""SaúdePrática v1.9.97: Gemini 503 retry and alarm timing diagnostics.

Keeps the established TOMEI -> TOMAS navigation untouched. Settings add a
shortcut to the existing encrypted Gemini configuration. The alarm check
never pretends Android can deliver exact times without OS permission.
"""
from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1')
base=root/'app/src/main/java/com/mediagenda/app'

def replace(rel,old,new,what):
    path=base/rel
    text=path.read_text(encoding='utf-8')
    n=text.count(old)
    if n!=1:
        raise RuntimeError(f'Fase Gemini/alarmes {what}: expected one anchor, got {n}')
    path.write_text(text.replace(old,new,1),encoding='utf-8')

replace('MealAiActivity.kt',
    'companion object { const val EXTRA_PROFILE_ID = "profile_id" }',
    '''companion object {
        const val EXTRA_PROFILE_ID = "profile_id"
        const val EXTRA_OPEN_GEMINI_SETTINGS = "open_gemini_settings"
    }''', 'settings intent')
replace('MealAiActivity.kt',
    '''        setContentView(root);ViewCompat.requestApplyInsets(root)
        draw()
''',
    '''        setContentView(root);ViewCompat.requestApplyInsets(root)
        draw()
        if(intent.getBooleanExtra(EXTRA_OPEN_GEMINI_SETTINGS,false)) {
            // Arriving from Opções > Segurança e notificações opens the
            // original encrypted key dialog; never displays the stored key.
            body.post { if(!isFinishing && !isDestroyed)configurarGemini() }
        }
''', 'open configuration from options')

replace('MainActivity.kt',
'''        box.addView(infoCard("❤️", "Health Connect · permissões e associação",
''',
'''        box.addView(infoCard("🔑", "Gemini · API Key e teste",
            if(PrivateGeminiKey.configured(this))
                "Chave cifrada neste telemóvel · testar ou substituir"
            else "Configurar chave privada para analisar fotografias") {
            startActivity(Intent(this,MealAiActivity::class.java)
                .putExtra(MealAiActivity.EXTRA_PROFILE_ID,activeProfileId)
                .putExtra(MealAiActivity.EXTRA_OPEN_GEMINI_SETTINGS,true))
        })
        box.addView(infoCard("❤️", "Health Connect · permissões e associação",
''', 'API key in security settings')

replace('MainActivity.kt',
'''        box.addView(noteBox("Avisos separados",
''',
'''        if(Build.VERSION.SDK_INT >= Build.VERSION_CODES.S){
            val exact=getSystemService(AlarmManager::class.java).canScheduleExactAlarms()
            box.addView(noteBox("⏱ Pontualidade dos alarmes de medicação",
                if(exact)"Alarmes exatos autorizados pelo Android. " +
                    "Esta permissão ajuda a tocar à hora agendada, mas " +
                    "o Xiaomi/HyperOS pode impor outras restrições."
                else "Alarmes exatos NÃO autorizados. O Android está a usar " +
                    "um aviso aproximado, que pode tocar um ou mais minutos " +
                    "depois. Autoriza o acesso especial abaixo."))
            if(!exact)box.addView(secondaryButton("⏱ Autorizar alarmes exatos no Android"){
                requestExactAlarmAccess()
            })
        }
        val timing=getSharedPreferences("saudepratica_alarm_timing_v1",MODE_PRIVATE)
        val expected=timing.getLong("scheduled",0L)
        val received=timing.getLong("received",0L)
        if(expected>0L && received>0L && received>=expected &&
            System.currentTimeMillis()-received < 7L*24*60*60*1000){
            val sec=(received-expected)/1000L
            box.addView(noteBox("Diagnóstico do último alarme de medicação",
                "Atraso de entrega pelo Android: "+sec+" segundos. " +
                "A abertura das TOMAS depois de TOMEI é independente " +
                "deste atraso. Não inclui o nome do utente ou medicamento."))
        }
        box.addView(noteBox("Avisos separados",
''', 'exact alarm status UI with diagnostic')

# Record timestamp immediately when Android delivers the receiver, ahead of
# image decoding, JSON and database access. A snoozed reminder has a different
# firing time from the original dose and is excluded from delay statistics.
replace('notifications/NotificationReceiver.kt',
'''    override fun onReceive(context: Context, intent: Intent) {
        val medicationId = intent.getStringExtra("medication_id")
''',
'''    override fun onReceive(context: Context, intent: Intent) {
        val medicationId = intent.getStringExtra("medication_id")
        val intended=intent.getLongExtra("scheduled_at",0L)
        if(!medicationId.isNullOrBlank() && intended>0L &&
            intent.action!="com.mediagenda.app.MED_ALARM_SNOOZED_FIRE" &&
            !intent.getBooleanExtra("demo_notice",false)){
            context.getSharedPreferences("saudepratica_alarm_timing_v1",
                Context.MODE_PRIVATE).edit()
                .putLong("scheduled",intended)
                .putLong("received",System.currentTimeMillis()).apply()
        }
''', 'measure actual AlarmManager delivery')

# Preserve alarm scheduling and route. No changes to MedicationAlarmActivity,
# its full-screen PendingIntent, TOMEI action or confirmation records.

gemini=base/'MealGeminiDirect.kt'
g=gemini.read_text(encoding='utf-8')
a=g.index('    private fun call(key:String,body:JSONObject):JSONObject{')
b=g.index('    private fun normalize(response:JSONObject):JSONObject{',a)
replacement='''    private class RetryableGeminiException(message:String):Exception(message)

    /** A 503 means overload, not necessarily a bad key. Retry with bounded
     * exponential delay and one alternative official stable Flash model.
     * Always sends to Google's Gemini API, never to an unaudited proxy.
     */
    private fun call(key:String,body:JSONObject):JSONObject{
        val models=listOf("gemini-3.8-flash","gemini-3.8-flash",
            "gemini-3.6-flash")
        var last:Throwable?=null
        for((attempt,model) in models.withIndex()){
            try {
                return sendOnce(key,body,model).put("model_used",model)
            }catch(e:RetryableGeminiException){
                last=e
            }catch(e:java.net.SocketTimeoutException){
                last=e
            }catch(e:java.net.SocketException){
                last=e
            }
            if(attempt<models.lastIndex) {
                try {Thread.sleep(if(attempt==0)1200L else 2500L)}
                catch(e:InterruptedException){
                    Thread.currentThread().interrupt()
                    throw IllegalStateException("Análise Gemini interrompida.",e)
                }
            }
        }
        error("O Gemini está temporariamente indisponível (HTTP 503 ou ligação instável). " +
            "Foram feitas novas tentativas e testado o modelo Flash alternativo. " +
            "Tenta novamente mais tarde ou utiliza o modo manual. " +
            "A tua chave API foi preservada.")
    }

    private fun sendOnce(key:String,body:JSONObject,model:String):JSONObject{
        require(model=="gemini-3.8-flash" || model=="gemini-3.6-flash")
        val endpoint="https://generativelanguage.googleapis.com/v1beta/models/"+
            model+":generateContent"
        val connection=URL(endpoint).openConnection() as HttpURLConnection
        connection.requestMethod="POST";connection.doOutput=true
        connection.instanceFollowRedirects=false
        connection.connectTimeout=12000;connection.readTimeout=36000
        connection.setRequestProperty("Content-Type","application/json; charset=utf-8")
        connection.setRequestProperty("Accept","application/json")
        connection.setRequestProperty("Cache-Control","no-store")
        connection.setRequestProperty("X-goog-api-key",key)
        return try{
            connection.outputStream.use{
                it.write(body.toString().toByteArray(Charsets.UTF_8))
            }
            val status=connection.responseCode
            if(status !in 200..299){
                when(status){
                    408,500,502,503,504->throw RetryableGeminiException(
                        "Gemini temporariamente indisponível (HTTP $status).")
                    400,401,403->error("O Google recusou a operação (HTTP $status). " +
                        "Confirma a autorização da chave e o acesso ao modelo.")
                    404->error("Modelo Gemini não disponível (HTTP 404).")
                    429->error("Limite ou quota Gemini atingidos (HTTP 429). " +
                        "Consulta o teu projeto no Google AI Studio.")
                    else->error("Falha Gemini HTTP $status.")
                }
            }
            val response=connection.inputStream.bufferedReader(Charsets.UTF_8).use{
                it.readText().take(120000)
            }
            JSONObject(response)
        }finally{connection.disconnect()}
    }
'''
gemini.write_text(g[:a]+replacement+g[b:],encoding='utf-8')

# v1.9.97 with unchanged applicationId, package, certificate and artwork.
gradle=root/'app/build.gradle.kts'
s=gradle.read_text(encoding='utf-8')
assert s.count('versionCode = 106')==1 and s.count('versionName = "1.9.96"')==1
s=s.replace('versionCode = 106','versionCode = 107',1)
s=s.replace('versionName = "1.9.96"','versionName = "1.9.97"',1)
gradle.write_text(s,encoding='utf-8')
print('1.9.97: exact alarm timing diagnostics; Gemini bounded retry and settings link. TOMEI untouched.')