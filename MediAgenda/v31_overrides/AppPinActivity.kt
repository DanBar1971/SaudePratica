package com.mediagenda.app

import android.app.KeyguardManager
import android.content.Intent
import android.content.res.Configuration
import android.content.res.ColorStateList
import android.graphics.Color
import android.os.Bundle
import android.text.InputFilter
import android.text.InputType
import android.view.Gravity
import android.view.ViewGroup
import android.view.WindowManager
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import com.google.android.material.button.MaterialButton
import com.google.android.material.card.MaterialCardView
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.mediagenda.app.data.AppPinStore

class AppPinActivity:AppCompatActivity() {
    companion object {
        const val MODE="pin_mode"
        const val SETTINGS="settings"
        const val FROM_SPLASH="from_splash"
    }
    private lateinit var pin:AppPinStore
    private lateinit var content:LinearLayout
    private var settings=false
    private var authenticated=false
    private val teal=Color.rgb(5,162,150)
    private val dark get()=when(getSharedPreferences("mediagenda_ui",MODE_PRIVATE)
        .getString("theme_mode","system")){
        "dark"->true;"light"->false
        else->(resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK)==
            Configuration.UI_MODE_NIGHT_YES
    }
    private val fg get()=if(dark)Color.rgb(242,248,250)else Color.rgb(19,34,54)
    private val secondary get()=if(dark)Color.rgb(201,215,223)else Color.rgb(83,103,116)
    private fun dp(x:Int)=(x*resources.displayMetrics.density+.5f).toInt()
    private val recovery=registerForActivityResult(ActivityResultContracts.StartActivityForResult()){response->
        if(response.resultCode==RESULT_OK){
            runCatching{pin.remove()}.onSuccess{
                AppPinSession.unlocked=true
                AppPinSession.gateRequested=false
                message("PIN removido após desbloqueio do telemóvel.")
                if(settings)finish() else proceed()
            }.onFailure{message(it.message?:"Erro ao recuperar o PIN.")}
        }
    }
    override fun onCreate(savedInstanceState:Bundle?) {
        super.onCreate(savedInstanceState)
        pin=AppPinStore(this)
        settings=intent.getStringExtra(MODE)==SETTINGS
        AppPinSession.gateRequested=true
        window.addFlags(WindowManager.LayoutParams.FLAG_SECURE)
        val root=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            gravity=Gravity.CENTER
            setPadding(dp(18),dp(12),dp(18),dp(12))
            setBackgroundColor(if(dark)Color.rgb(5,22,32)else Color.rgb(246,249,250))
        }
        val scroll=ScrollView(this).apply{isFillViewport=true}
        content=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL;gravity=Gravity.CENTER
        }
        scroll.addView(content)
        root.addView(scroll,LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.MATCH_PARENT))
        WindowCompat.setDecorFitsSystemWindows(window,false)
        window.statusBarColor=Color.TRANSPARENT;window.navigationBarColor=Color.TRANSPARENT
        val controller=WindowInsetsControllerCompat(window,window.decorView)
        controller.isAppearanceLightStatusBars=!dark
        controller.isAppearanceLightNavigationBars=!dark
        ViewCompat.setOnApplyWindowInsetsListener(root){view,insets->
            val safe=insets.getInsets(WindowInsetsCompat.Type.statusBars() or
                WindowInsetsCompat.Type.navigationBars() or WindowInsetsCompat.Type.displayCutout())
            view.setPadding(dp(18)+safe.left,dp(12)+safe.top,
                dp(18)+safe.right,dp(12)+safe.bottom)
            insets
        }
        setContentView(root)
        ViewCompat.requestApplyInsets(root)
        if(!settings&&!pin.enabled())proceed()else refresh()
    }
    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if(settings)super.onBackPressed() else finishAffinity()
    }
    private fun label(v:String,size:Float=14f):TextView=TextView(this).apply{
        text=v;textSize=size;gravity=Gravity.CENTER
        setTextColor(fg)
    }
    private fun action(v:String,onClick:()->Unit):MaterialButton=MaterialButton(this).apply{
        text=v;textSize=14f;isAllCaps=false
        setTextColor(if(dark)Color.rgb(160,246,232)else Color.rgb(8,98,91))
        backgroundTintList=ColorStateList.valueOf(Color.TRANSPARENT)
        strokeColor=ColorStateList.valueOf(teal);strokeWidth=dp(1)
        cornerRadius=dp(15)
        setOnClickListener{onClick()}
    }
    private fun add(parent:LinearLayout,v:android.view.View){
        parent.addView(v,LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT)
            .apply{bottomMargin=dp(9)})
    }
    private fun pinField(v:String):EditText=EditText(this).apply{
        hint=v;gravity=Gravity.CENTER;textSize=24f
        inputType=InputType.TYPE_CLASS_NUMBER or InputType.TYPE_NUMBER_VARIATION_PASSWORD
        filters=arrayOf(InputFilter.LengthFilter(4))
        isSingleLine=true;setTextColor(fg);setHintTextColor(secondary)
        backgroundTintList=ColorStateList.valueOf(teal)
    }
    private fun contentBox(title:String,explanation:String):LinearLayout {
        content.removeAllViews()
        add(content,label("🔒",45f))
        add(content,label("SaúdePrática",26f))
        add(content,label(title,20f))
        add(content,label(explanation,13f).apply{setTextColor(secondary)})
        val card=MaterialCardView(this).apply{
            radius=dp(20).toFloat();strokeWidth=dp(1)
            strokeColor=if(dark)Color.rgb(79,103,117)else Color.rgb(213,227,235)
            setCardBackgroundColor(if(dark)Color.rgb(28,43,55)else Color.WHITE)
        }
        val box=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(20),dp(22),dp(20),dp(22))
        }
        card.addView(box)
        content.addView(card)
        return box
    }
    private fun message(t:String)=Toast.makeText(this,t,Toast.LENGTH_LONG).show()
    private fun refresh(){
        when {
            !settings->showVerify(false)
            !pin.enabled()->showCreate()
            !authenticated->showVerify(true)
            else->showSettings()
        }
    }
    private fun showVerify(current:Boolean){
        val box=contentBox(if(current)"Confirmar PIN atual" else "Introduz o PIN",
            if(current)"Para alterar o PIN, introduz o código atual."
            else "Proteção opcional de 4 dígitos.")
        val input=pinField("PIN")
        val error=label("",13f).apply{setTextColor(Color.rgb(239,119,119))}
        add(box,input);add(box,error)
        add(box,action(if(current)"Confirmar" else "Entrar"){
            val seconds=pin.blockedSeconds()
            if(seconds>0)error.text="Aguarda "+seconds+" segundos."
            else if(pin.verify(input.text.toString())){
                if(current){authenticated=true;showSettings()}else proceed()
            }else{
                input.text.clear()
                error.text="PIN incorreto. "+if(pin.blockedSeconds()>0)
                    "Aguarda "+pin.blockedSeconds()+" segundos." else "Tenta novamente."
            }
        })
        add(box,action("Esqueci-me do PIN"){recover()})
        add(box,action(if(current)"Cancelar" else "Sair"){
            if(current)finish() else finishAffinity()
        })
    }
    private fun showCreate(){
        val box=contentBox(if(pin.enabled())"Alterar PIN" else "Ativar PIN",
            "O PIN é opcional e será pedido ao voltar a abrir a SaúdePrática.")
        val first=pinField("Novo PIN")
        val second=pinField("Confirmar PIN")
        val error=label("",13f).apply{setTextColor(Color.rgb(239,119,119))}
        add(box,first);add(box,second);add(box,error)
        add(box,action("Guardar PIN"){
            val one=first.text.toString()
            val two=second.text.toString()
            when{
                !one.matches(Regex("""\d{4}"""))->error.text="O PIN tem de ter 4 dígitos."
                one!=two->error.text="Os PINs são diferentes."
                else->runCatching{pin.createOrReplace(one)}.onSuccess{
                    AppPinSession.unlocked=true
                    AppPinSession.gateRequested=false
                    message("PIN guardado. Será pedido ao reabrir a aplicação.")
                    finish()
                }.onFailure{error.text=it.message?:"Não foi possível guardar o PIN."}
            }
        })
        add(box,action("Cancelar"){if(pin.enabled()&&authenticated)showSettings()else finish()})
    }
    private fun showSettings(){
        val box=contentBox("PIN ativado",
            "A SaúdePrática pedirá o PIN para voltar a entrar.")
        add(box,action("Alterar PIN"){showCreate()})
        add(box,action("Desativar PIN"){
            MaterialAlertDialogBuilder(this).setTitle("Desativar PIN?")
                .setMessage("A SaúdePrática abrirá novamente sem pedir código.")
                .setPositiveButton("Desativar"){_,_->
                    runCatching{pin.remove()}.onSuccess{
                        AppPinSession.gateRequested=false
                        message("PIN desativado.");finish()
                    }.onFailure{message(it.message?:"Não foi possível remover o PIN.")}
                }.setNegativeButton("Cancelar",null).show()
        })
        add(box,action("Voltar"){finish()})
    }
    private fun recover(){
        val manager=getSystemService(KEYGUARD_SERVICE) as KeyguardManager
        if(!manager.isDeviceSecure){
            MaterialAlertDialogBuilder(this).setTitle("Recuperação")
                .setMessage("O telemóvel não tem um bloqueio seguro. Esta opção não consegue recuperar o PIN. Os dados da aplicação permanecem guardados.")
                .setPositiveButton("OK",null).show()
            return
        }
        @Suppress("DEPRECATION")
        val request=manager.createConfirmDeviceCredentialIntent("SaúdePrática",
            "Confirma o desbloqueio do telemóvel para remover o PIN da aplicação.")
        if(request!=null)recovery.launch(request)
        else message("A confirmação do dispositivo não está disponível.")
    }
    private fun proceed(){
        AppPinSession.unlocked=true
        AppPinSession.gateRequested=false
        if(intent.getBooleanExtra(FROM_SPLASH,false))
            startActivity(Intent(this,MainActivity::class.java))
        finish()
    }
}
