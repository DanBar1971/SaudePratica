package com.mediagenda.app.sync

import android.Manifest
import android.content.res.ColorStateList
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.content.res.Configuration
import com.google.android.material.card.MaterialCardView
import com.google.android.material.button.MaterialButton
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
import java.util.UUID
import java.io.IOException
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
    private var sentOk=false
    private var receivedOk=false
    private var receivedSummary=""
    private val syncUi by lazy{getSharedPreferences(
        "saudepratica_nearby_sync_ui_v2",MODE_PRIVATE)}
    private val dark:Boolean get(){
        val chosen=getSharedPreferences("mediagenda_ui",MODE_PRIVATE)
            .getString("theme_mode","system")
        return when(chosen){
            "dark"->true
            "light"->false
            else->(resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK)==
                Configuration.UI_MODE_NIGHT_YES
        }
    }
    private val accent=Color.parseColor("#0E8276")
    private val headline get()=Color.parseColor(if(dark)"#F0F8FB" else "#132E3B")
    private val secondary get()=Color.parseColor(if(dark)"#BDCFD4" else "#5D6E78")
    private val surface get()=Color.parseColor(if(dark)"#1A2D37" else "#FFFFFF")
    private val back get()=Color.parseColor(if(dark)"#091C25" else "#F3F8F8")

    private val devices=linkedMapOf<String,String>()
    private val permissionRequest=registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()) { result->
        if(result.values.all{it} && requiredPermissions().all {
                ContextCompat.checkSelfPermission(this,it)==PackageManager.PERMISSION_GRANTED
            })begin()
        else show("⚠️ Permissões em falta: autoriza Bluetooth, Wi-Fi e " +
            "LOCALIZAÇÃO PRECISA quando o Android pedir. No Xiaomi, abre " +
            "Definições → Aplicações → SaúdePrática → Permissões → Localização " +
            "e seleciona 'Permitir durante a utilização' + 'Localização precisa'. " +
            "O Nearby exige esta permissão para descobrir dispositivos; " +
            "a SaúdePrática não consulta coordenadas GPS.")
    }
    private fun dp(n:Int)=(n*resources.displayMetrics.density+0.5f).toInt()
    private fun txt(value:String,size:Float=16f,strong:Boolean=false):TextView=
        TextView(this).apply{
            text=value;textSize=size
            setTextColor(if(strong)headline else secondary)
            setPadding(dp(8),dp(8),dp(8),dp(8))
            if(strong)setTypeface(typeface,Typeface.BOLD)
        }
    private fun card():MaterialCardView=MaterialCardView(this).apply{
        radius=dp(18).toFloat()
        cardElevation=dp(1).toFloat()
        setCardBackgroundColor(surface)
        strokeWidth=dp(1)
        strokeColor=Color.parseColor(if(dark)"#28444C" else "#E0ECEE")
        useCompatPadding=false
    }
    private fun button(text:String,primary:Boolean=true,action:()->Unit):MaterialButton=
        MaterialButton(this).apply{
            this.text=text
            textSize=15f
            isAllCaps=false
            minHeight=dp(55)
            cornerRadius=dp(15)
            insetTop=0;insetBottom=0
            setTextColor(if(primary)Color.WHITE else accent)
            backgroundTintList=ColorStateList.valueOf(
                if(primary)accent else Color.parseColor(if(dark)"#26474B" else "#E3F3F0"))
            setOnClickListener{action()}
        }
    private fun addButtonTo(group:LinearLayout,text:String,primary:Boolean=true,action:()->Unit){
        val b=button(text,primary,action)
        group.addView(b,LinearLayout.LayoutParams(-1,dp(55)).apply{
            bottomMargin=dp(11)
        })
    }
    override fun onCreate(savedInstanceState:Bundle?){
        super.onCreate(savedInstanceState)
        title="Sincronização familiar"
        window.statusBarColor=back
        window.navigationBarColor=back
        connections=Nearby.getConnectionsClient(this)
        val scroll=ScrollView(this).apply{
            setBackgroundColor(back)
            clipToPadding=false
        }
        val body=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(17),dp(16),dp(17),dp(28))
        }
        body.addView(txt("🔄 Sincronização familiar",23f,true))
        body.addView(txt("Troca segura entre dois telemóveis SaúdePrática · Bluetooth e Wi-Fi · sem Internet",14f))

        val guide=card()
        val guideBody=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(12),dp(10),dp(12),dp(10))
            addView(txt("COMO LIGAR OS DOIS TELEMÓVEIS",14f,true))
            addView(txt("1. No primeiro, toca em «Tornar visível».\n"+
                "2. No segundo, toca em «Procurar».\n"+
                "3. Seleciona o equipamento e confirma o código em AMBOS.",14f))
        }
        guide.addView(guideBody)
        body.addView(guide,LinearLayout.LayoutParams(-1,-2).apply{topMargin=dp(14)})
        val controls=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(0,dp(20),0,0)
        }
        addButtonTo(controls,"📡 1 · Tornar este telemóvel visível") { consent("host") }
        addButtonTo(controls,"🔎 2 · Procurar telemóvel próximo") { consent("search") }
        addButtonTo(controls,"✕ Parar / Desligar",false){
            stop()
            show("Ligação terminada.")
        }
        body.addView(controls)
        val stateCard=card()
        val stateBody=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(13),dp(9),dp(13),dp(11))
        }
        stateBody.addView(txt("ESTADO DA SINCRONIZAÇÃO",14f,true))
        feedback=txt("Pronto. Escolhe uma das opções acima.",15f)
        feedback.setTextColor(headline)
        stateBody.addView(feedback)
        stateCard.addView(stateBody)
        body.addView(stateCard,LinearLayout.LayoutParams(-1,-2).apply{topMargin=dp(5)})
        val nearbyCard=card()
        val nearbyBody=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(13),dp(10),dp(13),dp(10))
        }
        nearbyBody.addView(txt("TELEMÓVEIS ENCONTRADOS",14f,true))
        discovered=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
        nearbyBody.addView(discovered)
        nearbyCard.addView(nearbyBody)
        body.addView(nearbyCard,LinearLayout.LayoutParams(-1,-2).apply{topMargin=dp(14)})
        addButtonTo(body,"← Voltar à SaúdePrática",false){finish()}
        body.addView(txt("Os registos são fundidos sem substituir os existentes. " +
            "Os conflitos ficam guardados para revisão. Eliminações não são " +
            "transmitidas a outros telemóveis. Antes dos primeiros testes, " +
            "faz um backup de cada dispositivo.",12f))
        scroll.addView(body)
        setContentView(scroll)
    }
    private fun show(message:String){
        runOnUiThread{
            feedback.text=message
            val error=message.contains("erro",true)||
                message.contains("não foi possível",true)||
                message.contains("falha",true)||message.contains("permissões em falta",true)
            feedback.setTextColor(if(error)Color.parseColor(if(dark)"#FFC5C0" else "#B42318")
                else headline)
            if(error)feedback.setTypeface(null,Typeface.BOLD)
            else feedback.setTypeface(null,Typeface.NORMAL)
        }
    }
    private fun reportProgress(){
        if(receivedOk && sentOk){
            show("✅ ENVIO E RECEÇÃO CONCLUÍDOS nos dois sentidos. " +
                receivedSummary + "\n\n" +
                "Toca em «Voltar à SaúdePrática». Os ecrãs são atualizados " +
                "automaticamente ao regressar; não precisas de fechar a app.")
        }else if(receivedOk){
            show("✅ Dados recebidos e integrados neste telemóvel. " +
                receivedSummary + "\n\n" +
                "O envio para o outro telemóvel ainda não foi confirmado. " +
                "Mantém ambos os ecrãs abertos.")
        }else if(sentOk){
            show("✅ Dados enviados ao outro telemóvel. " +
                "Ainda falta receber e integrar os dados no sentido inverso; " +
                "mantém os dois ecrãs abertos.")
        }
    }
    private fun requiredPermissions():Array<String> = when {
        Build.VERSION.SDK_INT>=33->arrayOf(
            Manifest.permission.BLUETOOTH_SCAN,
            Manifest.permission.BLUETOOTH_ADVERTISE,
            Manifest.permission.BLUETOOTH_CONNECT,
            Manifest.permission.NEARBY_WIFI_DEVICES,
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION)
        Build.VERSION.SDK_INT>=31->arrayOf(
            Manifest.permission.BLUETOOTH_SCAN,
            Manifest.permission.BLUETOOTH_ADVERTISE,
            Manifest.permission.BLUETOOTH_CONNECT,
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION)
        Build.VERSION.SDK_INT>=29->arrayOf(
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION)
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
        sentOk=false
        receivedOk=false
        receivedSummary=""
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
                .addOnFailureListener{
                    show("⚠️ Não foi possível iniciar a procura: "+it.localizedMessage+
                        ". Se aparecer 8036 (FINE_LOCATION), abre Definições → " +
                        "Aplicações → SaúdePrática → Permissões → Localização e " +
                        "ativa 'Localização precisa'. Confirma também o Bluetooth " +
                        "ligado e tenta novamente, sem fechar a app.")
                }
        }
    }
    private val discovery=object:EndpointDiscoveryCallback(){
        override fun onEndpointFound(endpointId:String,info:DiscoveredEndpointInfo){
            if(connected!=null)return
            devices[endpointId]=info.endpointName
            runOnUiThread{
                discovered.removeAllViews()
                devices.toMap().forEach{(id,label)->
                    addButtonTo(discovered,"📲 Ligar a $label",false){
                        show("A pedir ligação a $label…")
                        connections.requestConnection("SaúdePrática · "+Build.MODEL,id,connectionLifecycle)
                            .addOnFailureListener{show("Falhou a ligação: "+it.localizedMessage)}
                    }
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
            if(sentOk&&receivedOk)reportProgress()
            else show("⚠️ Ligação terminada antes de confirmar a sincronização " +
                "completa nos dois sentidos. Volta a ligar para repetir.")
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
                    it.delete()
                    sentOk=true
                    reportProgress()
                }
                val payload=incoming.remove(update.payloadId)
                if(payload!=null && payload.type==Payload.Type.FILE){
                    show("Transferência concluída. A copiar e validar os dados recebidos…")
                    worker.execute{
                        // Nearby writes to Downloads/.nearby under scoped storage.
                        // asJavaFile() cannot be read on Android 10+; asUri() grants
                        // ContentResolver access to this app without file permissions.
                        val dir=File(cacheDir,"saudepratica_sync_received").apply{mkdirs()}
                        val local=File(dir,"incoming_${UUID.randomUUID()}.zip")
                        var receivedUri:android.net.Uri?=null
                        try{
                            val remote=payload.asFile()
                                ?:throw IOException("Payload de ficheiro inválido.")
                            receivedUri=remote.asUri()
                            val uri=receivedUri
                                ?:throw IOException("Nearby não disponibilizou a imagem de ficheiro recebida.")
                            val input=contentResolver.openInputStream(uri)
                                ?:throw IOException("Não foi possível abrir o ficheiro de sincronização recebido.")
                            input.use { source ->
                                local.outputStream().buffered().use { dest ->
                                    val buffer=ByteArray(32768)
                                    var total=0L
                                    while(true){
                                        val read=source.read(buffer)
                                        if(read<0)break
                                        total+=read
                                        if(total>320L*1024*1024)throw IOException(
                                            "Transferência acima do limite de 320 MB.")
                                        dest.write(buffer,0,read)
                                    }
                                }
                            }
                            if(local.length()<20L)throw IOException("Transferência incompleta.")
                            val result=NearbySyncStore(applicationContext).receive(local)
                            syncUi.edit().putLong("last_import_complete",
                                System.currentTimeMillis()).commit()
                            receivedSummary="Novos registos: ${result.added}; " +
                                "ficheiros: ${result.files}; perfis: ${result.profiles}; " +
                                "conflitos preservados: ${result.conflicts}."
                            receivedOk=true
                            reportProgress()
                        }catch(t:Exception){
                            android.util.Log.e("SaudePraticaNearby",
                                "Receção ou fusão falhou",t)
                            show("Não foi possível concluir a sincronização: " +
                                (t.localizedMessage?:t.javaClass.simpleName)+
                                ". Os registos existentes foram preservados. " +
                                "Mantém backups dos dois telemóveis enquanto testamos.")
                        }finally{
                            local.delete()
                            receivedUri?.let{runCatching{
                                contentResolver.delete(it,null,null)
                            }}
                        }
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