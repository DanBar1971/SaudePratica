package com.mediagenda.app.sync

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.view.Gravity
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.google.android.gms.nearby.Nearby
import com.google.android.gms.nearby.connection.AdvertisingOptions
import com.google.android.gms.nearby.connection.ConnectionInfo
import com.google.android.gms.nearby.connection.ConnectionLifecycleCallback
import com.google.android.gms.nearby.connection.ConnectionResolution
import com.google.android.gms.nearby.connection.ConnectionsClient
import com.google.android.gms.nearby.connection.DiscoveredEndpointInfo
import com.google.android.gms.nearby.connection.DiscoveryOptions
import com.google.android.gms.nearby.connection.EndpointDiscoveryCallback
import com.google.android.gms.nearby.connection.Payload
import com.google.android.gms.nearby.connection.PayloadCallback
import com.google.android.gms.nearby.connection.PayloadTransferUpdate
import com.google.android.gms.nearby.connection.Strategy
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import java.io.File
import java.util.concurrent.Executors

/** Deliberately foreground-only: medical and identity data cannot be exchanged
 * without explicit approval on both phones and matching authentication digits.
 */
class NearbySyncActivity:AppCompatActivity(){
    private val service="com.mediagenda.app.stable.saudepratica.sync.v1"
    private val strategy=Strategy.P2P_POINT_TO_POINT
    private lateinit var connections:ConnectionsClient
    private lateinit var feedback:TextView
    private lateinit var discovered:LinearLayout
    private val worker=Executors.newSingleThreadExecutor()
    private val incoming=mutableMapOf<Long,Payload>()
    private val outgoing=mutableMapOf<Long,File>()
    private var connected:String?=null
    private var busy=false
    private var mode=""
    private val devices=linkedMapOf<String,String>()
    private val permissionRequest=registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()) { result->
        if(result.values.all{it} && requiredPermissions().all {
                ContextCompat.checkSelfPermission(this,it)==PackageManager.PERMISSION_GRANTED
            })begin()
        else show("As permissões de Bluetooth/Wi-Fi são necessárias para procurar telemóveis próximos.")
    }
    private fun dp(n:Int)=(n*resources.displayMetrics.density+0.5f).toInt()
    private fun txt(text:String,size:Float=16f):TextView=TextView(this).apply{
        this.text=text;textSize=size;setPadding(dp(8),dp(8),dp(8),dp(8))
    }
    private fun button(text:String,action:()->Unit)=Button(this).apply{
        this.text=text;isAllCaps=false;setOnClickListener{action()}
    }
    override fun onCreate(savedInstanceState:Bundle?){
        super.onCreate(savedInstanceState)
        title="Sincronização local"
        connections=Nearby.getConnectionsClient(this)
        val root=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL;setPadding(dp(20),dp(25),dp(20),dp(20))
        }
        root.addView(txt("🔄 Sincronização familiar",23f))
        root.addView(txt("Entre dois telemóveis com SaúdePrática. Usa Bluetooth e Wi-Fi, " +
            "sem Internet ou backups manuais. Ambos têm de abrir este ecrã."))
        root.addView(txt("Partilha autorizada: perfis, dados de identificação, medicação, " +
            "tomas, consultas, análises, documentos e fotografias. As divergências " +
            "são guardadas sem substituir os registos existentes.",14f))
        root.addView(button("1 · Tornar este telemóvel visível") { consent("host") })
        root.addView(button("2 · Procurar telemóvel próximo") { consent("search") })
        root.addView(button("Parar / Desligar") { stop();show("Ligação terminada.") })
        feedback=txt("Escolhe uma das opções. Confirma o mesmo código nos dois equipamentos.",15f)
        root.addView(feedback)
        root.addView(txt("Telemóveis encontrados:",17f))
        discovered=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
        root.addView(discovered)
        root.addView(txt("A sincronização decorre apenas com este ecrã aberto. " +
            "Eliminar um registo num telemóvel não o elimina no outro. " +
            "Conflitos ficam arquivados para revisão.",13f))
        setContentView(ScrollView(this).apply{addView(root)})
    }
    private fun show(message:String){runOnUiThread{feedback.text=message}}
    private fun requiredPermissions():Array<String> = when {
        Build.VERSION.SDK_INT>=33->arrayOf(
            Manifest.permission.BLUETOOTH_SCAN,
            Manifest.permission.BLUETOOTH_ADVERTISE,
            Manifest.permission.BLUETOOTH_CONNECT,
            Manifest.permission.NEARBY_WIFI_DEVICES)
        Build.VERSION.SDK_INT>=31->arrayOf(
            Manifest.permission.BLUETOOTH_SCAN,
            Manifest.permission.BLUETOOTH_ADVERTISE,
            Manifest.permission.BLUETOOTH_CONNECT)
        Build.VERSION.SDK_INT>=29->arrayOf(Manifest.permission.ACCESS_FINE_LOCATION)
        else->arrayOf(Manifest.permission.ACCESS_COARSE_LOCATION)
    }
    private fun consent(newMode:String){
        MaterialAlertDialogBuilder(this)
            .setTitle("Autorizar sincronização familiar?")
            .setMessage("Serão enviados e recebidos dados de TODOS os perfis, " +
                "incluindo Cartão de Cidadão, fotografias e documentos de saúde. " +
                "Só deves ligar a um telemóvel de confiança. Nos dois telemóveis " +
                "terás de comparar e confirmar o mesmo código de segurança. " +
                "Não substituímos registos em conflito.")
            .setPositiveButton("Autorizo") { _,_->
                mode=newMode
                val permissions=requiredPermissions().filter{
                    ContextCompat.checkSelfPermission(this,it)!=PackageManager.PERMISSION_GRANTED
                }
                if(permissions.isEmpty())begin()else permissionRequest.launch(permissions.toTypedArray())
            }.setNegativeButton("Cancelar",null).show()
    }
    private fun begin(){
        stop()
        busy=false
        if(mode=="host"){
            show("A anunciar este telemóvel. No outro escolhe 'Procurar'.")
            connections.startAdvertising("SaúdePrática · "+Build.MODEL,service,connectionLifecycle,
                AdvertisingOptions.Builder().setStrategy(strategy).build())
                .addOnFailureListener{show("Erro ao anunciar: "+it.localizedMessage+
                    ". Verifica se Bluetooth e Wi-Fi estão ligados.")}
        }else{
            show("A procurar telemóveis SaúdePrática próximos…")
            connections.startDiscovery(service,discovery,
                DiscoveryOptions.Builder().setStrategy(strategy).build())
                .addOnFailureListener{show("Erro na procura: "+it.localizedMessage+
                    ". Verifica se Bluetooth e Wi-Fi estão ligados.")}
        }
    }
    private val discovery=object:EndpointDiscoveryCallback(){
        override fun onEndpointFound(endpointId:String,info:DiscoveredEndpointInfo){
            if(connected!=null)return
            devices[endpointId]=info.endpointName
            runOnUiThread{
                discovered.removeAllViews()
                devices.toMap().forEach{(id,label)->
                    discovered.addView(button("Ligar a $label"){
                        show("A pedir ligação a $label…")
                        connections.requestConnection("SaúdePrática · "+Build.MODEL,id,connectionLifecycle)
                            .addOnFailureListener{show("Falhou a ligação: "+it.localizedMessage)}
                    })
                }
            }
        }
        override fun onEndpointLost(endpointId:String){
            devices.remove(endpointId)
            runOnUiThread{discovered.removeAllViews()}
        }
    }
    private val connectionLifecycle=object:ConnectionLifecycleCallback(){
        override fun onConnectionInitiated(id:String,info:ConnectionInfo){
            runOnUiThread{
                MaterialAlertDialogBuilder(this@NearbySyncActivity)
                    .setTitle("Confirmar ligação segura")
                    .setMessage("Telemóvel: "+info.endpointName+"\n\n"+
                        "Código: "+info.authenticationDigits+"\n\n"+
                        "COMPARA os códigos nos dois telemóveis. " +
                        "Só aceita se forem IGUAIS e reconheceres o equipamento.")
                    .setCancelable(false)
                    .setPositiveButton("Os códigos coincidem") { _,_->
                        connections.acceptConnection(id,payloads)
                            .addOnFailureListener{show("Falha na confirmação: "+it.localizedMessage)}
                    }
                    .setNegativeButton("Recusar") { _,_->connections.rejectConnection(id) }
                    .show()
            }
        }
        override fun onConnectionResult(id:String,result:ConnectionResolution){
            if(result.status.isSuccess){
                connected=id
                connections.stopAdvertising();connections.stopDiscovery()
                show("Ligado com código confirmado. A preparar envio de dados…")
                worker.execute{
                    try{
                        val zip=NearbySyncStore(applicationContext).export()
                        runOnUiThread{
                            val payload=Payload.fromFile(zip)
                            outgoing[payload.id]=zip
                            connections.sendPayload(id,payload).addOnFailureListener{
                                outgoing.remove(payload.id)?.delete()
                                show("Falha ao enviar: "+it.localizedMessage)
                            }
                        }
                    }catch(t:Exception){show("Erro na preparação: "+t.message)}
                }
            } else show("Ligação recusada ou indisponível.")
        }
        override fun onDisconnected(id:String){
            connected=null
            show("Ligação terminada. Volta a ligar para sincronizar novamente.")
        }
    }
    private val payloads=object:PayloadCallback(){
        override fun onPayloadReceived(endpointId:String,payload:Payload){
            if(endpointId!=connected)return
            if(payload.type==Payload.Type.FILE){incoming[payload.id]=payload}
        }
        override fun onPayloadTransferUpdate(endpointId:String,update:PayloadTransferUpdate){
            if(endpointId!=connected)return
            val status=update.status
            if(status==PayloadTransferUpdate.Status.SUCCESS){
                outgoing.remove(update.payloadId)?.let{
                    it.delete();show("Dados enviados. A aguardar os dados do outro telemóvel…")
                }
                val file=incoming.remove(update.payloadId)?.asFile()?.asJavaFile()
                if(file!=null){
                    show("Dados recebidos. A validar e fundir com os registos existentes…")
                    worker.execute{
                        try{
                            val result=NearbySyncStore(applicationContext).receive(file)
                            show("✅ Sincronização concluída! " +
                                "Novos registos: ${result.added}. " +
                                "Ficheiros recebidos: ${result.files}. " +
                                "Perfis: ${result.profiles}. " +
                                "Conflitos preservados: ${result.conflicts}. " +
                                "Os dados já estão disponíveis na aplicação.")
                        }catch(t:Exception){show("Não foi possível importar: "+t.message)}
                        finally{file.delete()}
                    }
                }
            }else if(status==PayloadTransferUpdate.Status.FAILURE||
                status==PayloadTransferUpdate.Status.CANCELED){
                outgoing.remove(update.payloadId)?.delete()
                incoming.remove(update.payloadId)
                show("Transferência interrompida; os dados existentes não foram substituídos.")
            }
        }
    }
    private fun stop(){
        connections.stopAdvertising();connections.stopDiscovery();connections.stopAllEndpoints()
        connected=null
        devices.clear()
    }
    override fun onDestroy(){
        stop()
        worker.shutdown()
        super.onDestroy()
    }
}