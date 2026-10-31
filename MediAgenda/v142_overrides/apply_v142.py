#!/usr/bin/env python3
"""SaúdePrática v1.9.122: consistent light/dark across native Android screens.

Applied after v141; no change to clinical records, alerts, package, photos
or medication/appointment input values. Fail on changed upstream anchors.
"""
from pathlib import Path

APP=Path("build-src/MediAgenda_Android_v1/app")
SRC=APP/"src/main/java/com/mediagenda/app"
def update(name,changes):
    file=SRC/name
    s=file.read_text(encoding="utf-8")
    for before,after in changes:
        count=s.count(before)
        if count!=1:
            raise AssertionError(f"{name}: expected one source anchor, got {count}: {before[:100]}")
        s=s.replace(before,after,1)
    file.write_text(s,encoding="utf-8")
    print("Theme audited and patched:",name)

# Enforce saved theme *before* any secondary activity or dialog is constructed.
update("SaudePraticaApplication.kt",[(
"""import android.os.Bundle
""",
"""import android.os.Bundle
import androidx.appcompat.app.AppCompatDelegate
"""),(
"""    override fun onCreate() {
        super.onCreate()
        registerActivityLifecycleCallbacks(this)
    }""",
"""    override fun onCreate() {
        super.onCreate()
        val mode=getSharedPreferences("mediagenda_ui", MODE_PRIVATE)
            .getString("theme_mode","system")
        AppCompatDelegate.setDefaultNightMode(when(mode){
            "light"->AppCompatDelegate.MODE_NIGHT_NO
            "dark"->AppCompatDelegate.MODE_NIGHT_YES
            else->AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM
        })
        registerActivityLifecycleCallbacks(this)
    }""")])

# Real root cause: the shared full-screen form helper forced dark on *all*
# medication / profile / appointments, even if the actual theme was light.
# Use explicit app preference, not the OEM system setting when user overrides it.
update("SafeMaterialAlertDialogBuilder.kt",[(
"""import android.content.Context
""",
"""import android.content.Context
import android.content.res.Configuration
"""),(
"""            win.setBackgroundDrawable(android.graphics.drawable.ColorDrawable(
                android.graphics.Color.rgb(29,29,36)))""",
"""            val setting=context.getSharedPreferences("mediagenda_ui",
                Context.MODE_PRIVATE).getString("theme_mode","system")
            val dark=when(setting){
                "dark"->true
                "light"->false
                else->(context.resources.configuration.uiMode and
                    Configuration.UI_MODE_NIGHT_MASK)==Configuration.UI_MODE_NIGHT_YES
            }
            // The form's fields already use the requested palette. Background
            // MUST use the same palette or dark text is invisible on light mode.
            win.setBackgroundDrawable(android.graphics.drawable.ColorDrawable(
                if(dark)Color.rgb(29,41,53) else Color.WHITE))""")])

# Solid input backgrounds and explicit text/labels improve the legibility of
# every shared form. This affects medication, appointments and profiles.
update("MainActivity.kt",[(
"""            boxBackgroundMode = TextInputLayout.BOX_BACKGROUND_OUTLINE
            boxStrokeColor = primary
""",
"""            boxBackgroundMode = TextInputLayout.BOX_BACKGROUND_OUTLINE
            boxStrokeColor = primary
            boxBackgroundColor = surface
            defaultHintTextColor = ColorStateList.valueOf(muted)
            setHintTextColor(ColorStateList.valueOf(muted))
"""),(
"""            setTextColor(mainTextColor)
            textSize = 15f
            if(multiline)""",
"""            setTextColor(mainTextColor)
            setHintTextColor(muted)
            textSize = 15f
            if(multiline)""")])

# Help should not be permanently dark when the user selected Claro.
update("SmartHelpActivity.kt",[(
"""import android.graphics.Color
""",
"""import android.graphics.Color
import android.content.res.Configuration
"""),(
"""    private val darkBg=Color.rgb(9,28,37)
    private val surface=Color.rgb(26,45,55)
    private val accent=Color.rgb(14,130,118)
    private val pale=Color.rgb(238,249,245)""",
"""    private val dark:Boolean get()=when(getSharedPreferences("mediagenda_ui",MODE_PRIVATE)
        .getString("theme_mode","system")){
        "dark"->true;"light"->false
        else->(resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK)==
            Configuration.UI_MODE_NIGHT_YES
    }
    private val darkBg:Int get()=if(dark)Color.rgb(9,28,37) else Color.rgb(245,248,250)
    private val surface:Int get()=if(dark)Color.rgb(26,45,55) else Color.WHITE
    private val accent=Color.rgb(14,130,118)
    private val pale:Int get()=if(dark)Color.rgb(238,249,245) else Color.rgb(22,39,52)
    private val hintColor:Int get()=if(dark)Color.rgb(189,207,212) else Color.rgb(92,110,123)"""),(
"""            setTextColor(if(primary)Color.WHITE else pale)
            backgroundTintList=android.content.res.ColorStateList.valueOf(
                if(primary)accent else Color.rgb(37,70,77))""",
"""            setTextColor(if(primary)Color.WHITE else if(dark)Color.rgb(238,249,245)
                else Color.rgb(5,107,101))
            backgroundTintList=android.content.res.ColorStateList.valueOf(
                if(primary)accent else if(dark)Color.rgb(37,70,77)
                else Color.rgb(228,245,243))"""),(
"""        window.statusBarColor=darkBg
        window.navigationBarColor=darkBg""",
"""        window.statusBarColor=darkBg
        window.navigationBarColor=darkBg
        androidx.core.view.WindowInsetsControllerCompat(window,window.decorView).apply{
            isAppearanceLightStatusBars=!dark
            isAppearanceLightNavigationBars=!dark
        }"""),(
"""            setTextColor(Color.rgb(96,217,201))""",
"""            setTextColor(if(dark)Color.rgb(96,217,201) else Color.rgb(6,123,116))"""),(
"""            textSize=23f;setTextColor(Color.WHITE)""",
"""            textSize=23f;setTextColor(pale)"""),(
"""            textSize=13f;setTextColor(Color.rgb(189,207,212))""",
"""            textSize=13f;setTextColor(hintColor)"""),(
"""            setTextColor(Color.WHITE)
            setHintTextColor(Color.rgb(189,207,212))""",
"""            setTextColor(pale)
            setHintTextColor(hintColor)""")])

# The guide and contact UI also had a fixed dark skin.
update("SupportHelpActivity.kt",[(
"""import android.graphics.Color
""",
"""import android.graphics.Color
import android.content.res.Configuration
"""),(
"""    private val paletteBackground=Color.rgb(8,28,37)
    private val paletteCard=Color.rgb(26,48,61)
    private val light=Color.rgb(237,249,246)
    private val muted=Color.rgb(192,210,214)
    private val accent=Color.rgb(112,219,192)""",
"""    private val dark:Boolean get()=when(getSharedPreferences("mediagenda_ui",MODE_PRIVATE)
        .getString("theme_mode","system")){
        "dark"->true;"light"->false
        else->(resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK)==
            Configuration.UI_MODE_NIGHT_YES
    }
    private val paletteBackground:Int get()=if(dark)Color.rgb(8,28,37)
        else Color.rgb(245,248,250)
    private val paletteCard:Int get()=if(dark)Color.rgb(26,48,61) else Color.WHITE
    private val light:Int get()=if(dark)Color.rgb(237,249,246)
        else Color.rgb(22,39,52)
    private val muted:Int get()=if(dark)Color.rgb(192,210,214)
        else Color.rgb(91,105,119)
    private val accent:Int get()=if(dark)Color.rgb(112,219,192)
        else Color.rgb(207,242,236)"""),(
"""        strokeColor=Color.rgb(55,103,106)
        setCardBackgroundColor(paletteCard)""",
"""        strokeColor=if(dark)Color.rgb(55,103,106) else Color.rgb(211,227,230)
        setCardBackgroundColor(paletteCard)""")])

# Archive of information cards had a fixed pale translucent header and white
# cards even on dark mode. Preserve poster images but match surrounding chrome.
update("HealthTipsActivity.kt",[(
"""import android.os.Bundle
""",
"""import android.os.Bundle
import android.content.res.Configuration
import android.graphics.drawable.ColorDrawable
import android.graphics.drawable.LayerDrawable
import androidx.core.content.ContextCompat
"""),(
"""    private val dateFormat=SimpleDateFormat("dd/MM/yyyy", Locale("pt","PT"))""",
"""    private val dateFormat=SimpleDateFormat("dd/MM/yyyy", Locale("pt","PT"))
    private val dark:Boolean get()=when(getSharedPreferences("mediagenda_ui",MODE_PRIVATE)
        .getString("theme_mode","system")){
        "dark"->true;"light"->false
        else->(resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK)==
            Configuration.UI_MODE_NIGHT_YES
    }
    private val surface:Int get()=if(dark)Color.rgb(29,44,56) else Color.WHITE
    private val ink:Int get()=if(dark)Color.rgb(244,250,251)
        else Color.rgb(21,45,59)
    private val muted:Int get()=if(dark)Color.rgb(192,215,224)
        else Color.rgb(84,103,118)"""),(
"""        setTextColor(Color.rgb(21,45,59))""",
"""        setTextColor(ink)"""),(
"""            background=shape(Color.argb(241,255,255,255))""",
"""            background=shape(surface)"""),(
"""            setBackgroundResource(R.drawable.saude_background)""",
"""            val picture=ContextCompat.getDrawable(this@HealthTipsActivity,
                R.drawable.saude_background)
            background=if(dark && picture!=null)LayerDrawable(arrayOf(
                picture,ColorDrawable(Color.argb(112,1,14,24))))
                else ColorDrawable(Color.rgb(245,248,250))"""),(
"""            setBackgroundColor(Color.argb(240,241,249,248))""",
"""            setBackgroundColor(if(dark)Color.rgb(19,39,51)
                else Color.rgb(235,247,247))""")])

# Calendar must follow the saved in-app theme, not simply the OEM night flag.
update("MonthlyCalendarActivity.kt",[(
"""    private val dark get()=(resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK)==Configuration.UI_MODE_NIGHT_YES""",
"""    private val dark:Boolean get()=when(getSharedPreferences("mediagenda_ui",MODE_PRIVATE)
        .getString("theme_mode","system")){
        "dark"->true
        "light"->false
        else->(resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK)==
            Configuration.UI_MODE_NIGHT_YES
    }""")])

gradle=APP/"build.gradle.kts"
g=gradle.read_text(encoding="utf-8")
assert g.count("versionCode = 131")==1
assert g.count('versionName = "1.9.121"')==1
gradle.write_text(g.replace("versionCode = 131","versionCode = 132",1)
    .replace('versionName = "1.9.121"','versionName = "1.9.122"',1),encoding="utf-8")
print("Theme-consistency corrective release v1.9.122 prepared. Alarm and clinical stores unchanged.")
