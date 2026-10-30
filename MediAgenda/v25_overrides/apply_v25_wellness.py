from pathlib import Path
f=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app/WellnessActivity.kt")
s=f.read_text(encoding="utf-8")
def edit(old,new,label):
 global s
 if old not in s:raise RuntimeError("v1.9.6 wellness missing "+label)
 s=s.replace(old,new,1)
edit('''import android.content.res.ColorStateList''','''import android.content.res.ColorStateList
import android.content.res.Configuration
import android.graphics.drawable.BitmapDrawable
import android.graphics.drawable.ColorDrawable
import android.graphics.drawable.LayerDrawable
import androidx.core.content.ContextCompat
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import com.google.android.material.card.MaterialCardView''',"imports")
edit('''    private val lightText = Color.rgb(234, 247, 250)
    private val muted = Color.rgb(172, 204, 212)''',
'''    private val isDark: Boolean get() = when (getSharedPreferences("mediagenda_ui", MODE_PRIVATE)
        .getString("theme_mode", "system")) {
        "dark" -> true
        "light" -> false
        else -> (resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK) ==
            Configuration.UI_MODE_NIGHT_YES
    }
    private val lightText get() = if(isDark) Color.rgb(244,249,251) else Color.rgb(20,34,51)
    private val muted get() = if(isDark) Color.rgb(201,218,225) else Color.rgb(78,96,112)
    private val cardColor get() = if(isDark) Color.rgb(29,44,56) else Color.WHITE
    private val cardBorder get() = if(isDark) Color.rgb(74,99,111) else Color.rgb(212,224,234)
    private val modalText get() = if(isDark) Color.rgb(245,249,251) else Color.rgb(22,40,55)
    private val modalCaption get() = if(isDark) Color.rgb(123,235,222) else Color.rgb(3,101,97)
    private fun wallpaper():android.graphics.drawable.Drawable {
        if(!isDark)return ColorDrawable(Color.rgb(245,248,250))
        val picture=ContextCompat.getDrawable(this,R.drawable.saude_background)
        if(picture is BitmapDrawable)picture.gravity=Gravity.FILL
        return if(picture!=null)LayerDrawable(arrayOf(picture,
            ColorDrawable(Color.argb(112,1,14,24)))) else ColorDrawable(dark)
    }''',"theme and background")
edit('''        setColor(Color.rgb(24, 48, 59))
        cornerRadius = dp(20).toFloat()
        setStroke(dp(1), Color.rgb(42, 78, 83))''',
'''        setColor(cardColor)
        cornerRadius = dp(20).toFloat()
        setStroke(dp(1),cardBorder)''',"card palette")
edit('''            setTextColor(Color.WHITE)
            backgroundTintList = ColorStateList.valueOf(Color.rgb(9, 114, 110))
            cornerRadius = dp(14)''',
'''            setTextColor(if(isDark) Color.rgb(135,243,230) else Color.rgb(3,109,102))
            backgroundTintList = ColorStateList.valueOf(Color.TRANSPARENT)
            strokeColor = ColorStateList.valueOf(if(isDark)Color.rgb(80,202,190) else Color.rgb(6,132,125))
            strokeWidth = dp(1)
            cornerRadius = dp(16)''',"outlined action")
edit('''        parent.addView(shell, LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
            bottomMargin = dp(12)
        })''',
'''        val card=MaterialCardView(this).apply {
            radius=dp(20).toFloat()
            strokeWidth=dp(1)
            strokeColor=cardBorder
            setCardBackgroundColor(cardColor)
            cardElevation=dp(1).toFloat()
            addView(shell)
        }
        parent.addView(card, LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
            bottomMargin = dp(12)
        })''',"consistent Material cards")
edit('''        window.statusBarColor = dark
        window.navigationBarColor = dark
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(17), dp(12), dp(17), dp(12))
            setBackgroundColor(dark)
        }
        val back = text("‹   SaúdePrática  /  Bem-estar", 17f, true, turquoise)
        back.setOnClickListener { finish() }
        root.addView(back)
        val scroller = ScrollView(this).apply {''',
'''        val root=LinearLayout(this).apply {
            orientation=LinearLayout.VERTICAL
            setPadding(dp(16),dp(12),dp(16),dp(8))
            background=wallpaper()
        }
        val top=LinearLayout(this).apply {
            orientation=LinearLayout.HORIZONTAL
            gravity=Gravity.CENTER_VERTICAL
        }
        top.addView(text("‹",34f,true,turquoise).apply {
            gravity=Gravity.CENTER
            contentDescription="Voltar ao Início"
            setOnClickListener{finish()}
        },LinearLayout.LayoutParams(dp(37),dp(62)))
        val heading=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
        heading.addView(text("SaúdePrática",16f,true,turquoise))
        heading.addView(text("Bem-estar",12f,false,muted))
        top.addView(heading,LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f))
        top.addView(text(profileName.take(12),12f,true,turquoise).apply{
            gravity=Gravity.CENTER
            setPadding(dp(10),dp(7),dp(10),dp(7))
            background=GradientDrawable().apply {
                cornerRadius=dp(20).toFloat()
                setColor(if(isDark)Color.rgb(20,68,65) else Color.rgb(226,247,243))
            }
        })
        root.addView(top)
        val scroller = ScrollView(this).apply {''',"consistent header")
edit('''        setContentView(root)
        when (intent.getStringExtra(EXTRA_SECTION)) {''',
'''        WindowCompat.setDecorFitsSystemWindows(window,false)
        window.statusBarColor=Color.TRANSPARENT
        window.navigationBarColor=Color.TRANSPARENT
        val controller=WindowInsetsControllerCompat(window,window.decorView)
        controller.isAppearanceLightStatusBars=!isDark
        controller.isAppearanceLightNavigationBars=!isDark
        controller.hide(WindowInsetsCompat.Type.navigationBars())
        ViewCompat.setOnApplyWindowInsetsListener(root) { view,insets ->
            val safe=insets.getInsets(WindowInsetsCompat.Type.statusBars() or
                WindowInsetsCompat.Type.navigationBars() or WindowInsetsCompat.Type.displayCutout())
            view.setPadding(dp(16)+safe.left,dp(12)+safe.top,
                dp(16)+safe.right,dp(8)+safe.bottom)
            insets
        }
        setContentView(root)
        ViewCompat.requestApplyInsets(root)
        when (intent.getStringExtra(EXTRA_SECTION)) {''',"safe status-bar insets")
edit('''Registar undefined ml''','''Registar ${store.glassMl} ml''',"hydrate label")
edit('''Retirar undefined ml''','''Retirar ${store.glassMl} ml''',"undo hydrate label")
edit('''Ligados: undefined–undefined, de undefined em undefined minutos.''',
     '''Ligados: ${store.waterStart}–${store.waterEnd}, de ${store.waterInterval} em ${store.waterInterval} minutos.''',"water interval label")
edit('''        form.addView(text(label, 13f, true, Color.rgb(21, 82, 80)),''',
'''        form.addView(text(label, 13f, true, modalCaption),''',"dialog labels")
edit('''            setTextColor(Color.rgb(20, 38, 47))
            setHintTextColor(Color.GRAY)
            backgroundTintList = ColorStateList.valueOf(Color.rgb(10, 145, 138))''',
'''            setTextColor(modalText)
            setHintTextColor(if(isDark)Color.rgb(165,184,194) else Color.rgb(84,107,116))
            backgroundTintList=ColorStateList.valueOf(
                if(isDark)Color.rgb(114,216,205) else Color.rgb(11,126,119))''',
"dialog entries")
f.write_text(s,encoding="utf-8")
print("v1.9.6 wellness: safe header, wallpaper, correct dark/light contrasts, real glass amounts")
