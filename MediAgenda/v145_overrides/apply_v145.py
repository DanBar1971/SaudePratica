#!/usr/bin/env python3
"""SaúdePrática 1.9.125: optimize Nearby transport only; preserve clinical models."""
from pathlib import Path
from hashlib import sha256

root=Path("build-src/MediAgenda_Android_v1/app")
source=root/"src/main/java/com/mediagenda/app"
activity=source/"sync/NearbySyncActivity.kt"
gradle=root/"build.gradle.kts"
safe=[
 "sync/NearbySyncStore.kt",
 "notifications/MedicationAlarmService.kt",
 "notifications/NotificationScheduler.kt",
 "notifications/NotificationReceiver.kt",
 "notifications/MedicationAlarmCoordinator.kt",
 "notifications/MedicationAlarmPreferences.kt",
 "notifications/IntakeActionReceiver.kt",
 "notifications/DeviceAlarmRouting.kt",
]
before={p:sha256((source/p).read_bytes()).hexdigest()
        for p in safe if (source/p).exists()}
assert len(before)>=6
a=activity.read_text(encoding="utf-8")
def change(old,new,label):
    global a
    count=a.count(old)
    assert count==1,(label,count)
    a=a.replace(old,new,1)

assert 'saudepratica.sync.v2' in a
assert 'NearbySyncStore(applicationContext).export(selectedProfileId)' in a
assert 'NearbySyncStore(applicationContext).receive(local,selectedProfileId)' in a

change("import com.google.android.gms.nearby.connection.ConnectionInfo",
       "import com.google.android.gms.nearby.connection.ConnectionInfo\n"
       "import com.google.android.gms.nearby.connection.ConnectionOptions\n"
       "import com.google.android.gms.nearby.connection.ConnectionType",
       "radio API")
change("import android.widget.ScrollView",
       "import android.widget.ScrollView\n"
       "import android.widget.ProgressBar\n"
       "import android.view.View\n"
       "import android.view.WindowManager",
       "progress UI imports")

change("    private lateinit var discovered:LinearLayout",
'''    private lateinit var discovered:LinearLayout
    private lateinit var transferBar:ProgressBar
    private lateinit var transferLabel:TextView
    private var senderFileTransferred=false
    private val receivedAck="SP_SYNC_V145_IMPORTED_OK"
    private val linkPrefs by lazy{
        getSharedPreferences("saudepratica_nearby_link_v145",MODE_PRIVATE)
    }
    // 0 preserves previous Nearby negotiation; 1 stable, 2 maximum speed.
    private fun linkMode()=linkPrefs.getInt("radio_mode",0).coerceIn(0,2)
    private fun modeName()=when(linkMode()){
        1->"Estável (preservar Wi-Fi)"
        2->"Velocidade máxima (pode alterar Wi-Fi)"
        else->"Padrão Nearby (como antes)"
    }
    private fun requestOptions():ConnectionOptions {
        val options=ConnectionOptions.Builder()
        if(linkMode()!=0){
            options.setConnectionType(if(linkMode()==1)
                ConnectionType.NON_DISRUPTIVE else ConnectionType.DISRUPTIVE)
            options.setLowPower(false)
        }
        return options.build()
    }
    private fun advertiseOptions():AdvertisingOptions{
        val options=AdvertisingOptions.Builder().setStrategy(strategy)
        if(linkMode()!=0){
            options.setConnectionType(if(linkMode()==1)
                ConnectionType.NON_DISRUPTIVE else ConnectionType.DISRUPTIVE)
            options.setLowPower(false)
        }
        return options.build()
    }
    private fun displayProgress(bytes:Long,total:Long){
        if(total<=0L)return
        // 100% requires successful clinical import, not radio transmission.
        val percent=((bytes.toDouble()/total.toDouble())
            .coerceIn(0.0,1.0)*99.0).toInt().coerceIn(0,99)
        runOnUiThread{
            transferBar.visibility=View.VISIBLE
            transferLabel.visibility=View.VISIBLE
            transferBar.progress=percent
            transferLabel.text="Transferência: "+percent+"% · "+
                (bytes.coerceAtLeast(0L)/1024L)+" / "+(total/1024L)+
                " KiB. A aguardar integração no destino."
        }
    }
    private fun awaitingImport(){
        runOnUiThread{
            transferBar.visibility=View.VISIBLE
            transferLabel.visibility=View.VISIBLE
            transferBar.progress=99
            transferLabel.text="99% · Dados transmitidos. A aguardar que o "+
                "destino confirme a integração clínica."
        }
    }
    private fun completeImport(message:String){
        runOnUiThread{
            transferBar.visibility=View.VISIBLE
            transferLabel.visibility=View.VISIBLE
            transferBar.progress=100
            transferLabel.text="100% · "+message
            window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        }
    }''',"isolated transport state")

change('        addButtonTo(controls,"✕ Parar / Desligar",false){',
'''        addButtonTo(controls,"⚙️ Modo da ligação Nearby",false){
            val choices=arrayOf(
                "Padrão Nearby (como na versão anterior)",
                "Estável: tentar preservar o Wi-Fi do router",
                "Rápido: pode desligar temporariamente o Wi-Fi do router")
            MaterialAlertDialogBuilder(this)
                .setTitle("Ligação e velocidade")
                .setSingleChoiceItems(choices,linkMode()){dialog,choice->
                    linkPrefs.edit().putInt("radio_mode",choice).apply()
                    dialog.dismiss()
                    show("Modo guardado: "+modeName()+
                        ". Será aplicado apenas no próximo emparelhamento.")
                }
                .setNegativeButton("Cancelar",null).show()
        }
        addButtonTo(controls,"↻ Repetir ligação",false){
            if(selectedProfileId.isBlank())
                show("Primeiro seleciona e autoriza um perfil.")
            else if(connected!=null)
                show("Já existe ligação. Usa Parar antes de tentar novamente.")
            else begin()
        }
        addButtonTo(controls,"✕ Parar / Desligar",false){''',"connection settings")

change('''        stateBody.addView(feedback)
        stateCard.addView(stateBody)''',
'''        stateBody.addView(feedback)
        transferBar=ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal).apply{
            max=100;progress=0;visibility=View.GONE
        }
        stateBody.addView(transferBar,LinearLayout.LayoutParams(-1,dp(12)).apply{
            topMargin=dp(10);bottomMargin=dp(5)
        })
        transferLabel=txt("",13f).apply{visibility=View.GONE}
        stateBody.addView(transferLabel)
        stateCard.addView(stateBody)''',"progress card")

change('''        sentOk=false
        receivedOk=false
        receivedSummary=""''',
'''        sentOk=false
        receivedOk=false
        senderFileTransferred=false
        receivedSummary=""
        transferBar.visibility=View.GONE
        transferLabel.visibility=View.GONE
        transferBar.progress=0
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)''',
"session begin")

change('AdvertisingOptions.Builder().setStrategy(strategy).build()',
       'advertiseOptions()', "radio advertising")
change('connections.requestConnection("SaúdePrática · "+Build.MODEL,id,connectionLifecycle)',
       'connections.requestConnection("SaúdePrática · "+Build.MODEL,id,connectionLifecycle,requestOptions())',
       "radio connecting")

change('''            devices.remove(endpointId)
            runOnUiThread{discovered.removeAllViews()}''',
'''            // A transient LOST event can occur during Xiaomi radio changes;
            // keep the last discovered candidate until explicit new search.
            if(connected==null)show(
                "Dispositivo temporariamente fora da procura. "+
                "Podes tentar ligar ou repetir a pesquisa.")''',
"temporary discovery drops")

change('''        override fun onDisconnected(id:String){
            connected=null
            if(sentOk||receivedOk)reportProgress()
            else show("⚠️ Ligação terminada antes de confirmar a sincronização " +
                "completa nos dois sentidos. Volta a ligar para repetir.")
        }''',
'''        override fun onDisconnected(id:String){
            if(connected!=id)return
            connected=null
            window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
            if(sentOk||receivedOk)reportProgress()
            else show(if(senderFileTransferred)
                "⚠️ Ficheiro enviado, mas integração no destino NÃO confirmada. "+
                "Verifica no outro telemóvel antes de repetir."
                else "⚠️ Ligação interrompida. Os dados existentes foram "+
                "preservados. Escolhe Repetir ligação e confirma o código.")
        }''',"disconnect safe messaging")

change('''            if(payload.type==Payload.Type.FILE){incoming[payload.id]=payload}''',
'''            if(payload.type==Payload.Type.BYTES && mode=="host"){
                val response=payload.asBytes()?.toString(Charsets.UTF_8).orEmpty()
                if(response==receivedAck && senderFileTransferred && !sentOk){
                    sentOk=true
                    completeImport("Destino confirmou a integração do perfil.")
                    reportProgress()
                }
            }else if(payload.type==Payload.Type.FILE && mode=="search"){
                incoming[payload.id]=payload
            }''',"receiver positive acknowledgment")

change('''            val status=update.status
            if(status==PayloadTransferUpdate.Status.SUCCESS){''',
'''            val status=update.status
            if(status==PayloadTransferUpdate.Status.IN_PROGRESS){
                displayProgress(update.bytesTransferred,update.totalBytes)
                return
            }
            if(status==PayloadTransferUpdate.Status.SUCCESS){''',"byte progress")

change('''                outgoing.remove(update.payloadId)?.let{
                    it.delete()
                    sentOk=true
                    reportProgress()
                }''',
'''                outgoing.remove(update.payloadId)?.let{
                    it.delete()
                    senderFileTransferred=true
                    awaitingImport()
                    show("Dados enviados pelo Nearby. A aguardar confirmação "+
                        "da integração do perfil no outro telemóvel…")
                }''',"no premature medical success")

change('''                            receivedOk=true
                            reportProgress()''',
'''                            receivedOk=true
                            completeImport("Dados recebidos e integrados neste perfil.")
                            reportProgress()
                            // Confirm ONLY after the exact existing profile
                            // merge successfully returned. No clinical payload
                            // appears inside the tiny acknowledgment message.
                            connections.sendPayload(endpointId,
                                Payload.fromBytes(receivedAck.toByteArray(Charsets.UTF_8)))
                                .addOnFailureListener{
                                    show("Integração local feita, mas não foi possível "+
                                        "confirmá-la no outro telemóvel.")
                                }''',"sender gets true destination import result")

change('''                show("Transferência interrompida; os dados existentes não foram substituídos.")''',
'''                window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
                show("Transferência interrompida, sem confirmação de integração. "+
                    "Os registos existentes foram preservados. Repetir ligação.")''',
"error doesn't report success")

change('''        connected=null
        devices.clear()
    }
    override fun onDestroy()''',
'''        connected=null
        devices.clear()
        window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
    }
    override fun onDestroy()''',
"clear wake condition on stop")

activity.write_text(a,encoding="utf-8")
g=gradle.read_text(encoding="utf-8")
assert g.count("versionCode = 134")==1
assert g.count('versionName = "1.9.124"')==1
g=g.replace("versionCode = 134","versionCode = 135",1)
g=g.replace('versionName = "1.9.124"','versionName = "1.9.125"',1)
gradle.write_text(g,encoding="utf-8")
after={p:sha256((source/p).read_bytes()).hexdigest() for p in before}
assert before==after,"Protected clinical/alarm data sources changed"
print("PASS v1.9.125: transport-only Nearby progress/ack/radio; clinical and alarm files untouched")
