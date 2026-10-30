from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
def replace_one(path,old,new,label):
    s=path.read_text(encoding="utf-8")
    if s.count(old)!=1 and not (label=="reset biometric after PIN change" and s.count(old)==2):
        raise RuntimeError("SaúdePrática v1.9.34 "+label+": "+str(s.count(old)))
    path.write_text(s.replace(old,new,1),encoding="utf-8")

pin=base/"data/AppPinStore.kt"
replace_one(pin,
    '''    fun enabled():Boolean=preferences.getString("digest",null)!=null &&
        preferences.getString("salt",null)!=null''',
    '''    fun enabled():Boolean=preferences.getString("digest",null)!=null &&
        preferences.getString("salt",null)!=null
    /** Biometric unlock is optional and can only be on while the app PIN exists. */
    fun biometricEnabled():Boolean=enabled() &&
        preferences.getBoolean("biometric_enabled",false)
    fun setBiometricEnabled(allowed:Boolean){
        require(!allowed || enabled()){"Ativa primeiro o PIN da aplicação."}
        check(preferences.edit().putBoolean("biometric_enabled",allowed).commit()){
            "Não foi possível guardar a opção biométrica."
        }
    }''',
    "biometric setting")
replace_one(pin,
    '''            .remove("failed").remove("blocked_until").commit()){''',
    '''            .remove("failed").remove("blocked_until")
            .putBoolean("biometric_enabled",false).commit()){''',
    "reset biometric after PIN change")
replace_one(pin,
    '''        check(preferences.edit().remove("salt").remove("digest")
            .remove("failed").remove("blocked_until").commit()){''',
    '''        check(preferences.edit().remove("salt").remove("digest")
            .remove("failed").remove("blocked_until")
            .remove("biometric_enabled").commit()){''',
    "clear biometric on PIN disable")

activity=base/"AppPinActivity.kt"
replace_one(activity,
    '''import androidx.appcompat.app.AppCompatActivity''',
    '''import androidx.appcompat.app.AppCompatActivity
import androidx.biometric.BiometricManager
import androidx.biometric.BiometricPrompt''',
    "biometric imports")
replace_one(activity,
    '''    private var authenticated=false
    private val teal=''',
    '''    private var authenticated=false
    private var enablingFingerprint=false
    private val biometricPrompt by lazy {
        BiometricPrompt(this,ContextCompat.getMainExecutor(this),
            object:BiometricPrompt.AuthenticationCallback(){
                override fun onAuthenticationSucceeded(
                    result:BiometricPrompt.AuthenticationResult
                ){
                    super.onAuthenticationSucceeded(result)
                    if(enablingFingerprint){
                        enablingFingerprint=false
                        runCatching{pin.setBiometricEnabled(true)}
                            .onSuccess{
                                message("Impressão digital ativada.")
                                showSettings()
                            }
                            .onFailure{message(it.message?:"Falha ao ativar biometria.")}
                    }else if(!settings && pin.enabled()){
                        proceed()
                    }
                }
                override fun onAuthenticationError(code:Int,messageText:CharSequence){
                    super.onAuthenticationError(code,messageText)
                    enablingFingerprint=false
                    if(code!=BiometricPrompt.ERROR_NEGATIVE_BUTTON &&
                        code!=BiometricPrompt.ERROR_USER_CANCELED &&
                        code!=BiometricPrompt.ERROR_CANCELED){
                        message("Impressão digital indisponível. Usa o PIN.")
                    }
                }
            })
    }
    private fun fingerprintAvailable():Boolean =
        BiometricManager.from(this).canAuthenticate(
            BiometricManager.Authenticators.BIOMETRIC_STRONG
        )==BiometricManager.BIOMETRIC_SUCCESS
    private fun requestFingerprint(activate:Boolean){
        if(!fingerprintAvailable()){
            message("Ativa uma impressão digital nas Definições do telemóvel.")
            return
        }
        enablingFingerprint=activate
        val prompt=BiometricPrompt.PromptInfo.Builder()
            .setTitle("SaúdePrática")
            .setSubtitle(if(activate)"Ativar desbloqueio por impressão digital"
                else "Desbloquear com impressão digital")
            .setAllowedAuthenticators(
                BiometricManager.Authenticators.BIOMETRIC_STRONG)
            .setNegativeButtonText(if(activate)"Cancelar" else "Usar PIN")
            .build()
        biometricPrompt.authenticate(prompt)
    }
    private val teal=''', "biometric Android prompt")
replace_one(activity,
    '''        if(!settings&&!pin.enabled())proceed()else refresh()
    }''',
    '''        if(!settings&&!pin.enabled())proceed()else refresh()
        if(!settings&&pin.biometricEnabled()){
            window.decorView.post {
                if(!isFinishing && !AppPinSession.unlocked)
                    requestFingerprint(false)
            }
        }
    }''',
    "prompt automatically on launch")
replace_one(activity,
    '''        add(box,action("Esqueci-me do PIN"){recover()})''',
    '''        if(!current && pin.biometricEnabled() && fingerprintAvailable()){
            add(box,action("☝ Desbloquear com impressão digital"){
                requestFingerprint(false)
            })
        }
        add(box,action("Esqueci-me do PIN"){recover()})''',
    "manual fingerprint alternative")
replace_one(activity,
    '''        add(box,action("Alterar PIN"){showCreate()})
        add(box,action("Desativar PIN"){''',
    '''        add(box,action("Alterar PIN"){showCreate()})
        if(pin.biometricEnabled()){
            add(box,action("✓ Impressão digital ativada — desativar"){
                runCatching{pin.setBiometricEnabled(false)}
                    .onSuccess{
                        message("Desbloqueio por impressão digital desativado.")
                        showSettings()
                    }
                    .onFailure{message(it.message?:"Falha ao desativar.")}
            })
        }else{
            add(box,action("☝ Ativar impressão digital"){
                requestFingerprint(true)
            })
        }
        add(box,action("Desativar PIN"){''',
    "fingerprint settings control")

gradle=root/"app/build.gradle.kts"
replace_one(gradle,
    '''    implementation("com.google.android.gms:play-services-nearby:19.3.0")''',
    '''    implementation("com.google.android.gms:play-services-nearby:19.3.0")
    implementation("androidx.biometric:biometric:1.1.0")''',
    "Jetpack biometric dependency")
replace_one(gradle,"versionCode = 43","versionCode = 44","version code")
replace_one(gradle,'versionName = "1.9.33"','versionName = "1.9.34"',"version name")
manifest=root/"app/src/main/AndroidManifest.xml"
replace_one(manifest,
    '''    <uses-permission android:name="android.permission.CAMERA" />''',
    '''    <uses-permission android:name="android.permission.CAMERA" />
    <uses-permission android:name="android.permission.USE_BIOMETRIC" />''',
    "biometric permission")
print("v1.9.34 fingerprint unlock with local opt-in, PIN fallback and no biometrics stored.")
