#!/usr/bin/env python3
"""v1.9.104 urgent fix: show selectable profiles; alarm association remains secondary.

Runs after all v1.9.102 patches; changes ONLY the profile picker UI and
Android version. Never edits user records or changes the signing package ID.
"""
from pathlib import Path
p=Path('build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app/MainActivity.kt')
s=p.read_text(encoding='utf-8')
old='''            card.addView(row)
            val ownerOfAlarms=com.mediagenda.app.notifications.DeviceAlarmRouting'''
new='''            // MaterialCardView is a FrameLayout: it must have ONE content child.
            // Adding the full-width association button directly to the card
            // overlaid the patient avatar/name and prevented profile selection.
            val cardContent=LinearLayout(this).apply{
                orientation=LinearLayout.VERTICAL
                isFocusable=false
            }
            row.isClickable=true
            row.isFocusable=true
            row.setOnClickListener{ activateProfile(profile) }
            cardContent.addView(row,LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT))
            val ownerOfAlarms=com.mediagenda.app.notifications.DeviceAlarmRouting'''
assert s.count(old)==1,('profile row/association anchor missing',s.count(old))
s=s.replace(old,new,1)
old2='''            card.addView(deviceButton)
            card.setOnClickListener{activateProfile(profile)}'''
new2='''            // Small independent action BELOW the selectable patient row.
            // It must never cover or intercept taps on the profile itself.
            deviceButton.textSize=12f
            deviceButton.isAllCaps=false
            deviceButton.minHeight=dp(42)
            cardContent.addView(deviceButton,LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT).apply{
                marginStart=dp(12)
                marginEnd=dp(12)
                bottomMargin=dp(8)
            })
            card.addView(cardContent,android.widget.FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT))
            card.setOnClickListener{activateProfile(profile)}'''
assert s.count(old2)==1,('old overlapping association button missing',s.count(old2))
s=s.replace(old2,new2,1)
assert 'card.addView(row)\n            val ownerOfAlarms' not in s
assert 'card.addView(deviceButton)' not in s
p.write_text(s,encoding='utf-8')

# Android 15/16 enforce edge-to-edge: the last wizard buttons must sit ABOVE
# the 3-button/gesture system bar and IME. Recompute per actual insets and avoid
# assumptions about navigation-bar height on Xiaomi HyperOS devices.
wizard=Path('build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app/ProfileWizardActivity.kt')
w=wizard.read_text(encoding='utf-8')
needle_import='import androidx.core.content.FileProvider'
assert w.count(needle_import)==1
w=w.replace(needle_import,needle_import+'''
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat''',1)
needle_root='''        val root=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL;setPadding(dp(18),dp(26),dp(18),dp(12));setBackgroundColor(bg)
        }'''
assert w.count(needle_root)==1
w=w.replace(needle_root,'''        // Drawing behind system bars requires window insets, or the navigation
        // bar covers Seguinte / Anterior on Android 16 / HyperOS 3.
        WindowCompat.setDecorFitsSystemWindows(window,false)
        window.setSoftInputMode(android.view.WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE)
        val root=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(18),dp(26),dp(18),dp(18))
            setBackgroundColor(bg)
        }
        ViewCompat.setOnApplyWindowInsetsListener(root){_,insets->
            val system=insets.getInsets(WindowInsetsCompat.Type.systemBars())
            val keyboard=insets.getInsets(WindowInsetsCompat.Type.ime())
            val safeTop=system.top+dp(12)
            val safeBottom=maxOf(system.bottom,keyboard.bottom)+dp(18)
            root.setPadding(dp(18),safeTop,dp(18),safeBottom)
            insets
        }''',1)
needle_end='''        root.addView(bottom)
        setContentView(root)
        render()'''
assert w.count(needle_end)==1
w=w.replace(needle_end,'''        bottom.setPadding(0,dp(6),0,dp(4))
        root.addView(bottom)
        setContentView(root)
        ViewCompat.requestApplyInsets(root)
        render()''',1)
assert 'maxOf(system.bottom,keyboard.bottom)+dp(18)' in w
wizard.write_text(w,encoding='utf-8')

gradle=Path('build-src/MediAgenda_Android_v1/app/build.gradle.kts')
g=gradle.read_text(encoding='utf-8')
assert g.count('versionCode = 113')==1 and g.count('versionName = "1.9.103"')==1

gradle.write_text(g.replace('versionCode = 113','versionCode = 114').replace('versionName = "1.9.103"','versionName = "1.9.104"'),encoding='utf-8')
print('v1.9.104 fixed profile selector overlay; cards remain tappable with separate alarm routing.')
