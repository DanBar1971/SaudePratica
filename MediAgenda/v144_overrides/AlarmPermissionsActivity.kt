package com.mediagenda.app

import android.Manifest
import android.app.AlarmManager
import android.app.NotificationManager
import android.content.Intent
import android.content.pm.PackageManager
import android.content.res.ColorStateList
import android.content.res.Configuration
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.ColorDrawable
import android.graphics.drawable.GradientDrawable
import android.graphics.drawable.LayerDrawable
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.PowerManager
import android.provider.Settings
import android.view.Gravity
import android.view.View
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import com.google.android.material.button.MaterialButton
import com.mediagenda.app.notifications.MedicationAlarmService

/**
 * Non-invasive Android/Redmi permissions diagnostics.
 *
 * IMPORTANT: No changes to the alarm receiver, scheduling, foreground service,
 * activity, channels, timing, sound, vibrations or notification construction.
 * This screen only reports granted permissions and opens OS settings after tap.
 */
class AlarmPermissionsActivity : AppCompatActivity() {
    private val teal=Color.rgb(0,184,173)
    private val dark:Boolean get()=when(
        getSharedPreferences("mediagenda_ui",MODE_PRIVATE)
            .getString("theme_mode","system")){
        "dark"->true
        "light"->false
        else->(resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK)==
            Configuration.UI_MODE_NIGHT_YES
    }
    private val ink:Int get()=if(dark)Color.rgb(245,250,251) else Color.rgb(26,44,56)
    private val hint:Int get()=if(dark)Color.rgb(198,215,222) else Color.rgb(82,103,117)
    private val surface:Int get()=if(dark)Color.rgb(29,44,56) else Color.WHITE
    private val line:Int get()=if(dark)Color.rgb(74,99,111) else Color.rgb(214,226,234)
    private lateinit var contents:LinearLayout
    private val requestNotifications=registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ){render()}

    private fun dp(n:Int)=(n*resources.displayMetrics.density+0.5f).toInt()
    private fun text(s:String,size:Float=15f,strong:Boolean=false,color:Int=ink)=
        TextView(this).apply {
            text=s;textSize=size;setTextColor(color)
            if(strong)setTypeface(typeface,Typeface.BOLD)
            setPadding(dp(5),dp(6),dp(5),dp(6))
        }
    private fun rounded()=GradientDrawable().apply {
        setColor(surface);cornerRadius=dp(17).toFloat()
        setStroke(dp(1),line)
    }
    private fun button(title:String,action:()->Unit)=MaterialButton(this).apply {
        text=title;isAllCaps=false;textSize=14f
        cornerRadius=dp(14);minHeight=dp(48)
        strokeWidth=dp(1);strokeColor=ColorStateList.valueOf(teal)
        backgroundTintList=ColorStateList.valueOf(Color.TRANSPARENT)
        setTextColor(if(dark)Color.rgb(149,242,230) else Color.rgb(0,113,105))
        setOnClickListener{action()}
    }
    private fun panel(title:String,subtitle:String,actionTitle:String?=null,action:(()->Unit)?=null){
        val card=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL;background=rounded()
            setPadding(dp(14),dp(13),dp(14),dp(12))
        }
        card.addView(text(title,17f,true))
        card.addView(text(subtitle,13f,false,hint))
        if(actionTitle!=null && action!=null){
            card.addView(button(actionTitle,action))
        }
        contents.addView(card,LinearLayout.LayoutParams(-1,-2).apply{
            bottomMargin=dp(11)
        })
    }
    private fun appDetails()=Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
        Uri.parse("package:$packageName"))
    private fun open(target:Intent, fallback:Intent=appDetails()){
        runCatching{startActivity(target)}.onFailure{
            runCatching{startActivity(fallback)}.onFailure{
                Toast.makeText(this,
                    "Abre Definições → Aplicações → SaúdePrática.",
                    Toast.LENGTH_LONG).show()
            }
        }
    }
    override fun onCreate(savedInstanceState:Bundle?){
        super.onCreate(savedInstanceState)
        WindowCompat.setDecorFitsSystemWindows(window,false)
        window.statusBarColor=Color.TRANSPARENT
        window.navigationBarColor=Color.TRANSPARENT
        WindowInsetsControllerCompat(window,window.decorView).apply {
            isAppearanceLightStatusBars=!dark
            isAppearanceLightNavigationBars=!dark
        }
        val root=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            background=if(dark){
                val original=ContextCompat.getDrawable(this@AlarmPermissionsActivity,
                    R.drawable.saude_background)
                if(original==null)ColorDrawable(Color.rgb(5,24,33))
                else LayerDrawable(arrayOf(original,
                    ColorDrawable(Color.argb(126,1,14,24))))
            }else ColorDrawable(Color.rgb(245,248,250))
        }
        ViewCompat.setOnApplyWindowInsetsListener(root){v,insets->
            val safe=insets.getInsets(WindowInsetsCompat.Type.statusBars() or
                WindowInsetsCompat.Type.navigationBars() or
                WindowInsetsCompat.Type.displayCutout())
            v.setPadding(dp(14)+safe.left,dp(8)+safe.top,
                dp(14)+safe.right,dp(10)+safe.bottom)
            insets
        }
        val header=LinearLayout(this).apply{
            orientation=LinearLayout.HORIZONTAL
            gravity=Gravity.CENTER_VERTICAL
        }
        header.addView(button("‹ Voltar"){finish()},
            LinearLayout.LayoutParams(-2,dp(52)))
        header.addView(text("Permissões e alarmes",20f,true),
            LinearLayout.LayoutParams(0,-2,1f).apply{leftMargin=dp(10)})
        root.addView(header)
        val scroll=ScrollView(this).apply{clipToPadding=false}
        contents=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(2),dp(8),dp(2),dp(20))
        }
        scroll.addView(contents)
        root.addView(scroll,LinearLayout.LayoutParams(-1,0,1f))
        setContentView(root)
        ViewCompat.requestApplyInsets(root)
    }
    override fun onResume(){
        super.onResume()
        if(::contents.isInitialized)render()
    }
    private fun render(){
        contents.removeAllViews()
        contents.addView(text("Diagnóstico de acesso ao Android",21f,true))
        contents.addView(text(
            "Se o som toca, o alarme já está a disparar. Se a ficha não aparece " +
            "com o telemóvel bloqueado, verifica sobretudo as notificações " +
            "em ecrã completo e as permissões próprias do Redmi/MIUI.",
            14f,false,hint),
            LinearLayout.LayoutParams(-1,-2).apply{bottomMargin=dp(12)})

        val notifications=NotificationManagerCompat.from(this)
            .areNotificationsEnabled() &&
            (Build.VERSION.SDK_INT<33 || ContextCompat.checkSelfPermission(this,
                Manifest.permission.POST_NOTIFICATIONS)==PackageManager.PERMISSION_GRANTED)
        panel(if(notifications)"✓ Notificações autorizadas"
              else "⚠ Notificações bloqueadas",
            "Autoriza notificações da SaúdePrática, incluindo as do ecrã bloqueado.",
            if(!notifications&&Build.VERSION.SDK_INT>=33)
                "Pedir autorização" else "Abrir notificações Android"){
                if(!notifications&&Build.VERSION.SDK_INT>=33 &&
                    ContextCompat.checkSelfPermission(this,
                        Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)
                    requestNotifications.launch(Manifest.permission.POST_NOTIFICATIONS)
                else open(Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).apply{
                    putExtra(Settings.EXTRA_APP_PACKAGE,packageName)
                })
            }

        val nm=getSystemService(NotificationManager::class.java)
        if(Build.VERSION.SDK_INT>=34){
            val allowed=runCatching{nm.canUseFullScreenIntent()}.getOrDefault(false)
            panel(if(allowed)"✓ Ecrã completo autorizado"
                  else "⚠ Ecrã completo não autorizado",
                "Permite à SaúdePrática mostrar a ficha TOMEI/ADIAR " +
                "sobre o ecrã bloqueado, quando o Android o permitir.",
                "Abrir acesso especial ao ecrã completo"){
                open(Intent(Settings.ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT,
                    Uri.parse("package:$packageName")))
            }
        }else{
            panel("Ecrã completo · permissões do Redmi",
                "Neste Android, a autorização especial do Android 14 não existe. " +
                "Verifica «Mostrar no ecrã bloqueado» e «Abrir janelas " +
                "em segundo plano» nas outras permissões Xiaomi.",
                "Abrir permissões da SaúdePrática"){
                open(appDetails())
            }
        }

        val alarm=runCatching{
            getSystemService(AlarmManager::class.java)
        }.getOrNull()
        if(Build.VERSION.SDK_INT>=31){
            val exact=runCatching{alarm?.canScheduleExactAlarms()==true}
                .getOrDefault(false)
            panel(if(exact)"✓ Alarmes exatos autorizados"
                  else "⚠ Alarmes exatos por autorizar",
                "Esta permissão controla o agendamento pontual. " +
                "Se o som já toca à hora certa, é menos provável que seja " +
                "a causa de não aparecer a ficha.",
                "Abrir alarmes e lembretes"){
                open(Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM,
                    Uri.parse("package:$packageName")))
            }
        }else{
            panel("Alarmes exatos", "Geridos pelo Android deste telemóvel; " +
                "não existe o acesso especial introduzido no Android 12.")
        }

        val channel=nm.getNotificationChannel(MedicationAlarmService.CHANNEL)
        val channelLabel=when{
            channel==null->"Canal do alarme ainda não criado"
            channel.importance==NotificationManager.IMPORTANCE_NONE->
                "⚠ Canal de medicação bloqueado"
            channel.importance<NotificationManager.IMPORTANCE_HIGH->
                "⚠ Canal de medicação sem prioridade elevada"
            else->"✓ Canal de medicação com prioridade elevada"
        }
        panel(channelLabel,
            "Verifica os avisos no ecrã bloqueado, pop-ups e a " +
            "prioridade de «ALARMES DE MEDICAÇÃO — ecrã completo». " +
            "O Android pode manter uma configuração antiga do canal.",
            "Abrir canal de alarmes"){
            open(Intent(Settings.ACTION_CHANNEL_NOTIFICATION_SETTINGS).apply {
                putExtra(Settings.EXTRA_APP_PACKAGE,packageName)
                putExtra(Settings.EXTRA_CHANNEL_ID,MedicationAlarmService.CHANNEL)
            },Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).apply{
                putExtra(Settings.EXTRA_APP_PACKAGE,packageName)
            })
        }

        val power=getSystemService(PowerManager::class.java)
        val exempt=runCatching{power.isIgnoringBatteryOptimizations(packageName)}
            .getOrDefault(false)
        panel(if(exempt)"✓ Sem otimização padrão de bateria"
              else "Bateria · verificar limitações",
            "Alguns Redmi restringem atividades em segundo plano " +
            "mesmo quando o Android indica que a app não está otimizada. " +
            "Confirma «Sem restrições» na bateria da SaúdePrática.",
            "Abrir definições de bateria"){
            open(Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS))
        }

        val xiaomi=Build.MANUFACTURER.contains("xiaomi",true) ||
            Build.BRAND.contains("redmi",true) ||
            Build.BRAND.contains("poco",true)
        if(xiaomi){
            panel("Redmi / MIUI / HyperOS · permissões adicionais",
                "Em Definições → Aplicações → Gerir aplicações → SaúdePrática, " +
                "procura «Outras permissões»: Mostrar no ecrã bloqueado, " +
                "Mostrar janelas pop-up e Abrir novas janelas em segundo plano. " +
                "Verifica também Início automático e Bateria → Sem restrições. " +
                "Os nomes variam conforme a versão do MIUI.",
                "Abrir informação e permissões da app"){
                open(appDetails())
            }
        }else{
            panel("Permissões adicionais do fabricante",
                "Alguns Android exigem autorização separada para apresentar " +
                "janelas em segundo plano e no ecrã bloqueado.",
                "Abrir informação da app"){open(appDetails())}
        }
        panel("Verificar o alarme sem alterar as tomas",
            "Depois de configurar, regressa a Opções → Segurança e notificações " +
            "→ Notificações → Testar alarme de medicação. O teste existente " +
            "não regista nenhuma toma. Testa com o Redmi bloqueado e com " +
            "o ecrã apagado. Este ecrã não modifica o motor dos alarmes.")
    }
}
