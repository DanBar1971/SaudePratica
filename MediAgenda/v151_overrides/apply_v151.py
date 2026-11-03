#!/usr/bin/env python3
"""v1.9.131: persistent Android download + opt-in online AI, same app identity.
Run after v150 in reconstructed Android source; no patient data ever forwarded.
"""
from pathlib import Path
from shutil import copyfile

app=Path("build-src/MediAgenda_Android_v1/app")
src=app/"src/main/java/com/mediagenda/app"
local=Path("MediAgenda/v151_overrides")
for name in ["SystemModelDownload.kt","OnlineAiClient.kt"]:
    copyfile(local/name,src/name)
agent=src/"AgentAssistantActivity.kt"
s=agent.read_text(encoding="utf-8")

def change(before,after,name):
    global s
    hits=s.count(before)
    if hits!=1:
        raise AssertionError(f"{name}: expected 1 anchor, found {hits}")
    s=s.replace(before,after,1)

change('''    private var smallDownloading = false
    private var busy = false''',
'''    private var smallDownloading = false
    private val modelDownload by lazy { SystemModelDownload(applicationContext) }
    private val onlineClient by lazy { OnlineAiClient(applicationContext) }
    private var onlineSelected get() = prefs.getBoolean("saude_online_ai_mode",false)
        set(value) {prefs.edit().putBoolean("saude_online_ai_mode",value).apply()}
    private var downloadFailureMessage:String?=null
    private var progressReady=false
    private lateinit var downloadPanel:LinearLayout
    private lateinit var downloadLabel:TextView
    private lateinit var downloadProgress:android.widget.ProgressBar
    private lateinit var downloadCancel:MaterialButton
    private val updateHandler=android.os.Handler(android.os.Looper.getMainLooper())
    private val downloadMonitor=object:Runnable {
        override fun run() {
            if(!isFinishing && !isDestroyed && progressReady){
                refreshDownload()
                updateHandler.postDelayed(this,1500L)
            }
        }
    }
    private var busy = false''',"download/client states")

change('''        outer.addView(status)
        scroll=ScrollView(this)''',
'''        outer.addView(status)
        // Persistent download status, fixed under title; never hidden in chat.
        downloadPanel=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(14),dp(10),dp(14),dp(9))
            background=rounded(if(dark)Color.argb(228,15,45,52) else
                Color.argb(230,255,255,255))
            visibility=View.GONE
        }
        downloadLabel=TextView(this).apply{
            textSize=13f;setTextColor(fg)
            setPadding(0,0,0,dp(7))
        }
        downloadPanel.addView(downloadLabel)
        downloadProgress=android.widget.ProgressBar(
            this,null,android.R.attr.progressBarStyleHorizontal).apply{
            max=100;progress=0
        }
        downloadPanel.addView(downloadProgress,LinearLayout.LayoutParams(-1,dp(11)))
        downloadCancel=button("Cancelar transferência"){
            MaterialAlertDialogBuilder(this)
                .setTitle("Cancelar o download da IA?")
                .setMessage("A transferência será cancelada. Poderás tentar novamente mais tarde.")
                .setNegativeButton("Continuar",null)
                .setPositiveButton("Cancelar"){_,_->
                    modelDownload.cancel()
                    downloadFailureMessage=null
                    refreshDownload()
                }.show()
        }
        downloadCancel.textSize=11f
        downloadPanel.addView(downloadCancel)
        outer.addView(downloadPanel,LinearLayout.LayoutParams(-1,-2).apply{bottomMargin=dp(8)})
        scroll=ScrollView(this)''',"persistent progress panel")

change('''        shortcuts.addView(three)
        // Optional 383 MB download.''',
'''        shortcuts.addView(three)
        // Internet assistant runs on owner's Cloudflare worker. No embedded keys.
        val onlineRow=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL}
        onlineRow.addView(button("🌐  IA Online · sem download"){
            manageOnline()
        },LinearLayout.LayoutParams(-1,dp(48)))
        shortcuts.addView(onlineRow)
        // Optional 383 MB download.''',"visible online choice")

change('''        setContentView(outer)
        // Respect Android navigation bar and IME with proper bottom insets.''',
'''        setContentView(outer)
        progressReady=true
        refreshDownload()
        // Respect Android navigation bar and IME with proper bottom insets.''',
"start progress")

change('''            smallReady -> generateSmall(value)''',
'''            onlineSelected && onlineClient.isConfigured() -> generateOnline(value)
            smallReady -> generateSmall(value)''',
"online first when selected")

# Warn users that the old legacy help is a menu of fixed answers, not AI.
change('''        three.addView(button(localized("Ajuda clássica","Classic help","Aide classique",''',
'''        three.addView(button(localized("Ajuda tradicional","Classic help","Aide classique",''',
"rename help shortcut")

start=s.index('''    /** User opts in to BOTH download and installation. No automatic fetch. */
    private fun manageSmallModel() {''')
stop=s.index('''    private fun generateSmall(question:String) {''',start)
replacement='''    /** Refresh remains active across screen recreation and network reconnects. */
    private fun refreshDownload(){
        if(!progressReady)return
        val state=modelDownload.snapshot()
        val show=state.active || state.phase==SystemModelDownload.Phase.FAILED ||
            downloadFailureMessage!=null
        downloadPanel.visibility=if(show)View.VISIBLE else View.GONE
        if(!show)return
        val received=String.format(Locale.getDefault(),"%.1f",state.bytes.toDouble()/1_000_000)
        val total=String.format(Locale.getDefault(),"%.1f",state.total.toDouble()/1_000_000)
        downloadLabel.text=(downloadFailureMessage ?: modelDownload.statusDescription(state))+
            "\\n"+received+" MB / "+total+" MB ("+state.percent+"%)"
        downloadProgress.isIndeterminate=state.phase==SystemModelDownload.Phase.VERIFYING
        downloadProgress.progress=state.percent
        downloadCancel.visibility=when(state.phase){
            SystemModelDownload.Phase.RUNNING,
            SystemModelDownload.Phase.PAUSED,
            SystemModelDownload.Phase.WAITING -> View.VISIBLE
            else -> View.GONE
        }
        if(state.phase==SystemModelDownload.Phase.DOWNLOADED &&
           !smallDownloading && downloadFailureMessage==null){
            smallDownloading=true
            downloadLabel.text="A verificar integridade do modelo (SHA-256)..."
            modelDownload.verify{ result->
                smallDownloading=false
                if(result.isSuccess){
                    downloadFailureMessage=null
                    bubble(false,"Download concluído e verificado. "+
                        "Agora toca em «IA local leve» para instalar e ativar o modelo.")
                    status.text="Perfil: "+profileName+" · IA leve pronta a instalar"
                }else{
                    downloadFailureMessage="Falha na verificação: "+
                        (result.exceptionOrNull()?.message?:"erro desconhecido")
                    bubble(false,downloadFailureMessage.orEmpty())
                }
                refreshDownload()
            }
        }
    }
    override fun onStart(){
        super.onStart()
        updateHandler.removeCallbacks(downloadMonitor)
        updateHandler.post(downloadMonitor)
    }
    override fun onStop(){
        updateHandler.removeCallbacks(downloadMonitor)
        super.onStop()
    }
    private fun manageSmallModel(){
        val engine=smallModel
        if(!engine.runtimeSupported()){
            bubble(false,"O motor de IA local não está disponível nesta arquitetura Android.")
            return
        }
        if(modelDownload.snapshot().active){
            refreshDownload()
            bubble(false,"O download já decorre no Android. "+
                "A percentagem e os MB aparecem no topo e na notificação do sistema.")
            return
        }
        if(smallReady){
            MaterialAlertDialogBuilder(this).setTitle("IA local leve ativa")
                .setMessage("O modelo está a responder offline. Queres removê-lo?")
                .setNegativeButton("Manter",null)
                .setPositiveButton("Remover"){_,_->
                    smallReady=false
                    engine.remove{res->
                        bubble(false,if(res.isSuccess)"Modelo removido." else
                            "Não foi possível remover o modelo.")
                    }
                }.show()
            return
        }
        if(engine.downloaded()){
            MaterialAlertDialogBuilder(this).setTitle("Instalar e ativar IA local?")
                .setMessage("O modelo Qwen3 0.6B foi descarregado. "+
                    "A aplicação vai verificar a assinatura digital SHA-256 "+
                    "e carregá-lo na memória do telemóvel. Continuar?")
                .setNegativeButton("Agora não",null)
                .setPositiveButton("Instalar e ativar"){_,_->
                    status.text="Perfil: "+profileName+" · A instalar IA local..."
                    engine.activate{res->
                        smallReady=res.isSuccess
                        status.text="Perfil: "+profileName+" · "+
                            (if(smallReady)"IA local disponível"
                             else "IA local não ativada")
                        bubble(false,if(smallReady)"IA local pronta! Podes conversar offline."
                        else "Falha ao ativar: "+(res.exceptionOrNull()?.message?:"erro desconhecido"))
                    }
                }.show()
            return
        }
        val options=arrayOf("Apenas Wi-Fi (recomendado)",
                            "Wi-Fi ou dados móveis (~383 MB)")
        var selection=0
        MaterialAlertDialogBuilder(this).setTitle("Descarregar IA local leve?")
            .setMessage("Modelo Qwen3 0.6B · cerca de 383 MB. "+
                "Necessitas de ~1 GB de espaço livre para descarregar e verificar. "+
                "A transferência usa o Gestor de Downloads do Android, apresenta "+
                "progresso e pode continuar quando saíres deste ecrã. "+
                "Depois terás de confirmar «Instalar e ativar». "+
                "O modelo é gratuito e totalmente opcional.")
            .setSingleChoiceItems(options,0){_,i->selection=i}
            .setNegativeButton("Agora não",null)
            .setPositiveButton("Descarregar"){_,_->
                try{
                    downloadFailureMessage=null
                    val state=modelDownload.begin(wifiOnly=selection==0)
                    refreshDownload()
                    status.text="Perfil: "+profileName+" · "+
                        modelDownload.statusDescription(state)
                    bubble(false,"Transferência iniciada no Android. "+
                        "O estado aparece no topo, mesmo que saias e voltes.")
                }catch(e:Exception){
                    downloadFailureMessage="Não foi possível iniciar o download: "+
                        (e.message?:"erro desconhecido")
                    refreshDownload()
                    bubble(false,downloadFailureMessage.orEmpty())
                }
            }.show()
    }
    private fun manageOnline(){
        if(!onlineClient.isConfigured()){
            MaterialAlertDialogBuilder(this).setTitle("IA Online · configuração privada")
                .setMessage("A IA Online não precisa de descarregar o modelo, "+
                    "mas requer um servidor Cloudflare Workers AI da SaúdePrática "+
                    "com endereço HTTPS e código de acesso privado. "+
                    "Só as perguntas que escreveres serão enviadas ao serviço. "+
                    "Nunca é enviado automaticamente o conteúdo dos perfis, "+
                    "medicamentos ou consultas.")
                .setPositiveButton("Configurar"){_,_->configureOnline()}
                .setNegativeButton("Agora não",null).show()
            return
        }
        MaterialAlertDialogBuilder(this).setTitle("Assistente SaúdePrática · IA Online")
            .setItems(arrayOf(
                if(onlineSelected)"IA Online já está selecionada" else "Usar IA Online",
                "Usar IA Local / Ajuda tradicional",
                "Alterar servidor e código de acesso",
                "Desligar e apagar a configuração online"
            )){_,item->
                when(item){
                    0->{onlineSelected=true
                        bubble(false,"IA Online selecionada. As próximas perguntas livres "+
                            "serão enviadas ao servidor configurado; os dados guardados "+
                            "na SaúdePrática nunca são enviados automaticamente.")
                        status.text="Perfil: "+profileName+" · IA Online selecionada"}
                    1->{onlineSelected=false
                        bubble(false,"Modo local selecionado. "+
                            "Nenhuma pergunta será enviada à Internet.")}
                    2->configureOnline()
                    3->MaterialAlertDialogBuilder(this)
                        .setTitle("Eliminar configuração da IA Online?")
                        .setMessage("O endereço e código de acesso guardados neste "+
                            "telemóvel serão eliminados.")
                        .setNegativeButton("Cancelar",null)
                        .setPositiveButton("Eliminar"){_,_->
                            onlineClient.disconnect()
                            onlineSelected=false
                            bubble(false,"IA Online desligada neste dispositivo.")
                        }.show()
                }
            }.show()
    }
    private fun configureOnline(){
        val form=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(22),dp(10),dp(22),dp(4))
        }
        val endpointInput=EditText(this).apply{
            hint="https://teu-worker.workers.dev/v1/ask"
            setSingleLine(true)
            textSize=14f
            inputType=android.text.InputType.TYPE_CLASS_TEXT or
                android.text.InputType.TYPE_TEXT_VARIATION_URI
            setText(onlineClient.endpoint())
        }
        val credentialInput=EditText(this).apply{
            hint="Código de acesso privado do serviço"
            setSingleLine(true)
            textSize=14f
            inputType=android.text.InputType.TYPE_CLASS_TEXT or
                android.text.InputType.TYPE_TEXT_VARIATION_PASSWORD
        }
        form.addView(endpointInput)
        form.addView(credentialInput)
        MaterialAlertDialogBuilder(this).setTitle("Configurar IA Online")
            .setMessage("Necessitas do servidor Cloudflare e respetivo código de "+
                "acesso. A SaúdePrática guarda o código com Android Keystore. "+
                "Não escrevas dados clínicos identificáveis nas perguntas online.")
            .setView(form)
            .setNegativeButton("Cancelar",null)
            .setPositiveButton("Guardar e utilizar"){_,_->
                try{
                    onlineClient.configure(endpointInput.text.toString(),
                        credentialInput.text.toString())
                    onlineSelected=true
                    status.text="Perfil: "+profileName+" · IA Online selecionada"
                    bubble(false,"IA Online configurada neste telemóvel. "+
                        "Podes fazer perguntas livres com Internet. As consultas "+
                        "à Agenda e Medicação continuam a ser locais.")
                }catch(e:Exception){
                    bubble(false,"Não foi possível configurar IA Online: "+
                        (e.message?:"erro desconhecido"))
                }
            }.show()
    }
    private fun generateOnline(question:String){
        if(busy)return
        if(!onlineClient.isConfigured()){
            manageOnline()
            return
        }
        busy=true
        status.text="Perfil: "+profileName+" · IA Online a responder..."
        onlineClient.ask(question){res->
            busy=false
            bubble(false,if(res.isSuccess)res.getOrNull().orEmpty()
                else "Falha na IA Online: "+
                    (res.exceptionOrNull()?.message?:"erro desconhecido")+
                    ". Podes continuar a usar a Ajuda tradicional.")
            status.text="Perfil: "+profileName+" · IA Online"+
                (if(res.isSuccess)" disponível" else " · erro de ligação")
        }
    }

'''
s=s[:start]+replacement+s[stop:]

change('''if(this::log.isInitialized) smallModel.close()
        model?.close();model=null''',
'''updateHandler.removeCallbacks(downloadMonitor)
        modelDownload.close()
        onlineClient.close()
        if(this::log.isInitialized) smallModel.close()
        model?.close();model=null''',"shutdown monitor and online")
change('''if (dark) Color.argb(185, 5, 24, 31)
                    else Color.argb(205, 245, 248, 250)''',
'''if (dark) Color.argb(115, 5, 24, 31)
                    else Color.argb(115, 245, 248, 250)''',"visible brand background")
change('''text=(if(user)"👤  " else "✨  ")+message''',
'''text=(if(user)"👤  " else "🤖  ")+message''',"avatar indicator")
agent.write_text(s,encoding="utf-8")

manifest=app/"src/main/AndroidManifest.xml"
m=manifest.read_text(encoding="utf-8")
# INTERNET permission exists in the 1.9.130 app. Assert it rather than add
# duplicate or overly broad permissions.
if 'android.permission.INTERNET' not in m:
    raise AssertionError("Network permission was unexpectedly removed")
gradle=app/"build.gradle.kts"
g=gradle.read_text(encoding="utf-8")
for old,new in [('versionCode = 140','versionCode = 141'),
                ('versionName = "1.9.130"','versionName = "1.9.131"')]:
    if g.count(old)!=1:raise AssertionError(f"Version anchor {old}, found {g.count(old)}")
    g=g.replace(old,new)
gradle.write_text(g,encoding="utf-8")

# The old FAQ is intentionally still available, but no longer falsely
# advertised as generative AI; explicitly mark it as traditional help.
helpfile=src/"SmartHelpActivity.kt"
h=helpfile.read_text(encoding="utf-8")
h=h.replace('✨ Ajuda inteligente','📚 Ajuda tradicional')
h=h.replace('Funciona offline. Respostas sobre a aplicação, sem enviar perguntas nem dados médicos.',
            'Ajuda tradicional offline, sem IA. O novo Assistente SaúdePrática está no menu principal da app.')
# Bring the classic offline FAQ into the same branded Android visual system.
# This is still clearly marked as rule-based help, not an online or local LLM.
legacy_bg='''            setBackgroundColor(darkBg)'''
assert h.count(legacy_bg)==1,h.count(legacy_bg)
h=h.replace(legacy_bg,'''            val imageId=resources.getIdentifier(
                "saude_background","drawable",packageName)
            if(imageId!=0){
                background=android.graphics.drawable.LayerDrawable(arrayOf(
                    resources.getDrawable(imageId,theme),
                    android.graphics.drawable.ColorDrawable(
                        android.graphics.Color.argb(115,8,28,37))))
            }else setBackgroundColor(darkBg)''',1)
# Earlier theme overlays may have already updated font size; preserve them.
title_line='''            textSize=23f;setTextColor(Color.WHITE)'''
if h.count(title_line)==1:
    h=h.replace(title_line,'''            textSize=21f;setTextColor(Color.WHITE)
            setOnClickListener{finish()}''',1)
h=h.replace('''this.text=text("📚 Ajuda tradicional"''',
'''this.text=text("‹  📚 Ajuda tradicional"''',1)
# Compact thematic quick buttons and ask button; never force solid system grey.
h=h.replace('''text=value;isAllCaps=false
                setOnClickListener{ask(value)}''',
'''text=value;isAllCaps=false;textSize=12f;minHeight=dp(42)
                backgroundTintList=android.content.res.ColorStateList.valueOf(Color.rgb(9,124,114))
                setTextColor(Color.WHITE)
                setOnClickListener{ask(value)}''',1)
h=h.replace('''            text=text("Perguntar","Ask","Demander","Fragen","Preguntar")
            setOnClickListener''',
'''            text=text("Perguntar","Ask","Demander","Fragen","Preguntar")
            isAllCaps=false;textSize=13f
            backgroundTintList=android.content.res.ColorStateList.valueOf(Color.rgb(9,124,114))
            setTextColor(Color.WHITE)
            setOnClickListener''',1)
helpfile.write_text(h,encoding="utf-8")

print("Android 1.9.131: resumable visible model download + protected opt-in Workers AI; original package and alarms retained.")
