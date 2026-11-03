#!/usr/bin/env python3
"""Android v1.9.130: independently usable, explicit-download small local Qwen3.

Runs AFTER the fully verified v1.9.129 overlays. No clinical writes, no
alarm changes, no model-weight bundling. Original package/signature retained.
"""
from pathlib import Path
from shutil import copyfile

app = Path("build-src/MediAgenda_Android_v1/app")
src = app / "src/main/java/com/mediagenda/app"
overrides = Path("MediAgenda/v150_overrides")

def patch(path: Path, old: str, new: str, label: str):
    s = path.read_text(encoding="utf-8")
    occurrences = s.count(old)
    if occurrences != 1:
        raise AssertionError(f"{label}: expected exactly 1 original anchor, found {occurrences}")
    path.write_text(s.replace(old, new, 1), encoding="utf-8")

copyfile(overrides / "SmallOfflineModel.kt", src / "SmallOfflineModel.kt")
native = app / "src/main/cpp"
native.mkdir(parents=True, exist_ok=True)
copyfile(overrides / "saude_llm.cpp", native / "saude_llm.cpp")
copyfile(overrides / "CMakeLists.txt", native / "CMakeLists.txt")

agent = src / "AgentAssistantActivity.kt"
patch(agent,
'''    private var modelAvailableToDownload = false
    private var busy = false''',
'''    private var modelAvailableToDownload = false
    // Completely optional engine, independent of Google AICore / Gemini Nano.
    private val smallModel by lazy { SmallOfflineModel(applicationContext) }
    private var smallReady = false
    private var smallDownloading = false
    private var busy = false''',
"engine state")

patch(agent,
'''            setBackgroundColor(bg)
            setPadding(dp(12),dp(12),dp(12),dp(15))''',
'''            // The assistant is a normal SaúdePrática screen, using the same
            // official branded image under theme-aware translucent surfaces.
            val backdrop = resources.getIdentifier(
                "saude_background", "drawable", packageName)
            if (backdrop != 0) {
                val image = resources.getDrawable(backdrop, theme)
                val tint = android.graphics.drawable.ColorDrawable(
                    if (dark) Color.argb(185, 5, 24, 31)
                    else Color.argb(205, 245, 248, 250))
                background = android.graphics.drawable.LayerDrawable(
                    arrayOf(image, tint))
            } else setBackgroundColor(bg)
            setPadding(dp(12),dp(12),dp(12),dp(15))''',
"official branded background")

patch(agent,
'''        shortcuts.addView(three)
        outer.addView(shortcuts)''',
'''        shortcuts.addView(three)
        // Optional 383 MB download. Nothing happens without informed consent.
        val four=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL}
        four.addView(button("🧠  IA local leve · opcional (383 MB)") {
            manageSmallModel()
        },LinearLayout.LayoutParams(-1,dp(50)))
        shortcuts.addView(four)
        outer.addView(shortcuts)''',
"optional lightweight engine button")

patch(agent,
'''        setContentView(outer)
        window.setSoftInputMode(android.view.WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE)''',
'''        setContentView(outer)
        // Respect Android navigation bar and IME with proper bottom insets.
        androidx.core.view.ViewCompat.setOnApplyWindowInsetsListener(outer) { root,insets ->
            val safe=insets.getInsets(
                androidx.core.view.WindowInsetsCompat.Type.systemBars() or
                androidx.core.view.WindowInsetsCompat.Type.ime())
            root.setPadding(dp(12)+safe.left,dp(12)+safe.top,
                dp(12)+safe.right,dp(12)+safe.bottom)
            insets
        }
        androidx.core.view.ViewCompat.requestApplyInsets(outer)
        window.setSoftInputMode(android.view.WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE)''',
"system bottom inset")

patch(agent,
'''        text=label;isAllCaps=false;textSize=12f;minHeight=dp(46)''',
'''        text=label;isAllCaps=false;textSize=12f;minHeight=dp(44)
        cornerRadius=dp(14)
        setPadding(dp(8),dp(6),dp(8),dp(6))''',
"buttons consistent with app")

patch(agent,
'''            modelReady -> generateLocal(value)
            else -> bubble(false,''',
'''            smallReady -> generateSmall(value)
            modelReady -> generateLocal(value)
            else -> bubble(false,''',
"prefer opted-in small model")

patch(agent,
'''Neste dispositivo, as outras perguntas usam a Ajuda clássica enquanto a IA local não estiver disponível.''',
'''Para conversar offline podes descarregar opcionalmente a IA local leve (383 MB) ou usar a Ajuda clássica.''',
"guided message")

patch(agent,
'''Assistência guiada offline (IA indisponível)''',
'''Assistência guiada offline · IA leve opcional''',
"Nano unavailable explanatory status first")

# Also update catch-path and other instances in v149 with correct fallback.
s = agent.read_text(encoding="utf-8").replace(
    "Assistência guiada offline (IA indisponível)",
    "Assistência guiada offline · IA leve opcional")
agent.write_text(s, encoding="utf-8")

small_methods = '''
    /** User opts in to BOTH download and installation. No automatic fetch. */
    private fun manageSmallModel() {
        val engine=smallModel
        if(!engine.runtimeSupported()) {
            bubble(false,"O motor local ainda não é compatível com a arquitetura deste Android. "+
                "Podes continuar a consultar agendamentos e medicação sem IA.")
            return
        }
        if(smallDownloading) {
            bubble(false,"A descarga da IA está em curso. O progresso aparece por baixo do título.")
            return
        }
        if(smallReady) {
            MaterialAlertDialogBuilder(this)
                .setTitle("IA local leve ativa")
                .setMessage("As respostas são geradas neste telemóvel, sem Internet. "+
                    "As ações clínicas continuam a pedir confirmação na ficha original. "+
                    "Queres remover o modelo instalado?")
                .setNegativeButton("Manter",null)
                .setPositiveButton("Remover modelo"){_,_->
                    smallReady=false
                    engine.remove { result ->
                        bubble(false,if(result.isSuccess)
                            "Modelo removido. A ajuda e os registos continuam disponíveis."
                            else "Erro ao remover: "+result.exceptionOrNull()?.message)
                        status.text="Perfil: "+profileName+" · IA leve opcional"
                    }
                }.show()
            return
        }
        if(engine.downloaded()) {
            MaterialAlertDialogBuilder(this)
                .setTitle("Instalar e ativar IA local leve?")
                .setMessage("O modelo Qwen3 0.6B já foi descarregado (~383 MB). "+
                    "Agora será verificado e carregado na memória do telemóvel. "+
                    "Pode demorar e gastar bateria; não utiliza Internet para responder.")
                .setPositiveButton("Instalar e ativar"){_,_->
                    status.text="Perfil: "+profileName+" · A carregar IA local..."
                    engine.activate { result ->
                        smallReady=result.isSuccess
                        status.text="Perfil: "+profileName+" · "+
                            (if(smallReady) "IA local leve disponível"
                             else "IA leve não ativada")
                        bubble(false,if(smallReady)
                            "IA local leve ativada! Podes fazer perguntas simples offline. "+
                                "Os registos e os alarmes continuam independentes da IA."
                            else "Não foi possível ativar: "+
                                (result.exceptionOrNull()?.message?:"erro desconhecido"))
                    }
                }
                .setNeutralButton("Remover download"){_,_->
                    engine.remove { result ->
                        bubble(false,if(result.isSuccess) "Modelo removido."
                        else "Não foi possível remover o ficheiro.")
                    }
                }.setNegativeButton("Cancelar",null).show()
            return
        }
        MaterialAlertDialogBuilder(this)
            .setTitle("Descarregar IA local leve?")
            .setMessage("Modelo: Qwen3 0.6B · quantizado (4 bits)."+
                "\\nDownload: aproximadamente 383 MB (recomendamos Wi-Fi)."+
                "\\nEspaço livre necessário: pelo menos 600 MB."+
                "\\n\\nÉ gratuito, não requer conta ou subscrição. "+
                "O ficheiro é descarregado de Hugging Face e a assinatura SHA-256 "+
                "é confirmada antes da instalação. "+
                "Depois da descarga, toca novamente em «IA local leve» para "+
                "instalar e ativar o modelo. Nenhuma pergunta ou dado clínico "+
                "é enviado ao fornecedor. O download só começa se autorizares.")
            .setNegativeButton("Agora não",null)
            .setPositiveButton("Descarregar 383 MB"){_,_->
                smallDownloading=true
                status.text="Perfil: "+profileName+" · IA leve: 0% descarregado"
                engine.download(
                    onProgress={ percent ->
                        status.text="Perfil: "+profileName+
                            " · A descarregar IA leve: "+percent+"%"
                    },
                    onFinished={ result ->
                        smallDownloading=false
                        if(result.isSuccess) {
                            status.text="Perfil: "+profileName+
                                " · IA leve descarregada · por ativar"
                            bubble(false,"Download concluído e SHA-256 confirmado. "+
                                "Toca em «IA local leve» outra vez para instalar e ativar.")
                        } else {
                            status.text="Perfil: "+profileName+
                                " · IA leve opcional · descarga falhou"
                            bubble(false,"Não foi possível descarregar a IA: "+
                                (result.exceptionOrNull()?.message?:"erro desconhecido"))
                        }
                    })
            }.show()
    }

    private fun generateSmall(question:String) {
        if(busy)return
        busy=true
        status.text="Perfil: "+profileName+" · IA local leve a responder..."
        smallModel.ask(question) { result ->
            busy=false
            if(result.isSuccess) {
                bubble(false,result.getOrNull().orEmpty())
            } else bubble(false,"O modelo não conseguiu responder: "+
                (result.exceptionOrNull()?.message?:"erro desconhecido")+
                ". Podes continuar a usar a Ajuda clássica.")
            status.text="Perfil: "+profileName+
                (if(smallReady) " · IA local leve disponível"
                 else " · Ajuda offline")
        }
    }
'''
patch(agent,
'''    private fun manageLocalModel(){''',
small_methods + '''    private fun manageLocalModel(){''',
"optional explicit install manage and response logic")

patch(agent,
'''        model?.close();model=null
        super.onDestroy()''',
'''        // Model closure runs on its own serial worker (never block the UI).
        if(this::log.isInitialized) smallModel.close()
        model?.close();model=null
        super.onDestroy()''',
"free small inference lifecycle")

gradle = app / "build.gradle.kts"
patch(gradle,'versionCode = 139','versionCode = 140',"increment Android code")
patch(gradle,'versionName = "1.9.129"','versionName = "1.9.130"',"increment Android version")

s = gradle.read_text(encoding="utf-8")
s += '''
// Independent small-model runtime, CPU only. GGUF weights are NEVER shipped.
// Keep x86_64 for Android emulators and arm64-v8a for real phones.
android {
    ndkVersion = "27.2.12479018"
    defaultConfig {
        ndk {
            abiFilters += listOf("arm64-v8a", "x86_64")
        }
        externalNativeBuild {
            cmake {
                arguments += listOf(
                    "-DBUILD_SHARED_LIBS=OFF",
                    "-DLLAMA_BUILD_COMMON=OFF",
                    "-DLLAMA_BUILD_EXAMPLES=OFF",
                    "-DLLAMA_BUILD_TESTS=OFF",
                    "-DLLAMA_BUILD_TOOLS=OFF",
                    "-DLLAMA_OPENSSL=OFF",
                    "-DGGML_NATIVE=OFF",
                    "-DGGML_OPENMP=OFF",
                    "-DGGML_BACKEND_DL=OFF",
                    "-DGGML_LLAMAFILE=OFF",
                    "-DGGML_CPU_KLEIDIAI=OFF"
                )
            }
        }
    }
    externalNativeBuild {
        cmake {
            path = file("src/main/cpp/CMakeLists.txt")
            version = "3.22.1"
        }
    }
}
'''
gradle.write_text(s, encoding="utf-8")
print("1.9.130: optional 383 MB checksum-verified local AI, explicit install, no clinical writes.")
