#!/usr/bin/env python3
"""SaúdePrática 1.9.110 — global dialog action layout, preserve all functionality.

Apply after v129. Deliberately does not edit Gemini calls, medicine, appointments,
user data, storage, Android package ID, or signing configuration.
"""
from pathlib import Path
ROOT=Path('build-src/MediAgenda_Android_v1/app')
PACKAGE=ROOT/'src/main/java/com/mediagenda/app'
ORIGINAL='import com.google.android.material.dialog.MaterialAlertDialogBuilder'
ALIAS='import com.mediagenda.app.SafeMaterialAlertDialogBuilder as MaterialAlertDialogBuilder'
fixed=[]
for file in PACKAGE.rglob('*.kt'):
    if file.name=='SafeMaterialAlertDialogBuilder.kt':
        continue
    code=file.read_text(encoding='utf-8')
    if ORIGINAL in code:
        count=code.count(ORIGINAL)
        assert count==1,(file,count)
        code=code.replace(ORIGINAL, ALIAS)
        file.write_text(code,encoding='utf-8')
        fixed.append(file.relative_to(PACKAGE).as_posix())
assert len(fixed)>=20,("Unexpected number of dialog activities",fixed)

builder=PACKAGE/'SafeMaterialAlertDialogBuilder.kt'
builder.write_text(r'''package com.mediagenda.app

import android.content.Context
import android.text.TextUtils
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.view.WindowManager
import android.widget.Button
import android.widget.LinearLayout
import androidx.appcompat.app.AlertDialog
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat

/** Layout-only safeguard for Material dialogs on Xiaomi/MIUI, large font sizes,
 * screen navigation bars and small displays. Preserves all original actions,
 * click listeners, dialog lifecycle, and per-screen input validation.
 *
 * The original dialog builder is still used; only presentation after show changes.
 * Custom dialogs with their own action footer (e.g. profile) are not reparented.
 */
class SafeMaterialAlertDialogBuilder @JvmOverloads constructor(
    context: Context, themeResId: Int = 0
): com.google.android.material.dialog.MaterialAlertDialogBuilder(context, themeResId) {
    override fun create(): AlertDialog {
        val dialog = super.create()
        val decor = dialog.window?.decorView
        // A layout listener, not setOnShowListener: never replace activity-level
        // show callbacks (several dialogs use them to validate input fields).
        decor?.addOnLayoutChangeListener(object: View.OnLayoutChangeListener {
            private var ran = false
            override fun onLayoutChange(
                view: View, left:Int, top:Int, right:Int, bottom:Int,
                oldLeft:Int, oldTop:Int, oldRight:Int, oldBottom:Int
            ) {
                if (ran || !dialog.isShowing || view.width<=0 || view.height<=0) return
                ran=true
                view.removeOnLayoutChangeListener(this)
                view.post { if (dialog.isShowing) SafeDialogActionLayout.apply(dialog) }
            }
        })
        return dialog
    }
}

internal object SafeDialogActionLayout {
    private fun dp(context: Context, v: Int): Int =
        (v*context.resources.displayMetrics.density+0.5f).toInt()

    fun apply(dialog: AlertDialog) {
        val win=dialog.window ?: return
        val context=dialog.context
        val actionButtons=listOf(
            dialog.getButton(AlertDialog.BUTTON_NEUTRAL),
            dialog.getButton(AlertDialog.BUTTON_NEGATIVE),
            dialog.getButton(AlertDialog.BUTTON_POSITIVE)
        ).filterNotNull().filter{it.visibility==View.VISIBLE && it.text.isNotBlank()}
        if(actionButtons.size>=2) {
            val parent=actionButtons.first().parent as? ViewGroup
            if(parent!=null && actionButtons.all{it.parent===parent}) {
                val row=LinearLayout(context).apply {
                    orientation=LinearLayout.HORIZONTAL
                    gravity=Gravity.CENTER_VERTICAL
                    setPadding(dp(context,5),dp(context,5),dp(context,5),dp(context,8))
                }
                // A single horizontal child also prevents AppCompat's
                // ButtonBarLayout from stacking its stock buttons vertically.
                actionButtons.forEach{button: Button ->
                    val fullLabel=button.text.toString()
                    parent.removeView(button)
                    button.apply {
                        minWidth=0
                        minimumWidth=0
                        setSingleLine(false)
                        maxLines=2
                        ellipsize=TextUtils.TruncateAt.END
                        textSize=if(fullLabel.length>22) 10.5f else 12f
                        isAllCaps=false
                        minHeight=dp(context,48)
                        minimumHeight=dp(context,48)
                        setPadding(dp(context,2),dp(context,2),dp(context,2),dp(context,2))
                        contentDescription=fullLabel
                        gravity=Gravity.CENTER
                    }
                    row.addView(button,LinearLayout.LayoutParams(0,dp(context,54),1f).apply{
                        marginStart=dp(context,1)
                        marginEnd=dp(context,1)
                    })
                }
                parent.removeAllViews()
                parent.addView(row,ViewGroup.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT))
                // Ensure the stock buttons are not measured as an overwide row.
                parent.layoutParams?.let{p->
                    p.width=ViewGroup.LayoutParams.MATCH_PARENT
                    p.height=ViewGroup.LayoutParams.WRAP_CONTENT
                    parent.layoutParams=p
                }
            }
        }
        // Avoid a fixed-height dialog for normal confirmations. Tall content is
        // clipped to a *scrollable* viewport only when it exceeds safe screen.
        // The underlying content is kept intact, including its ScrollView.
        val metrics=context.resources.displayMetrics
        val safeHeight=(metrics.heightPixels-dp(context,72)).coerceAtLeast(dp(context,300))
        val existingHeight=win.decorView.height
        if(actionButtons.isNotEmpty() && existingHeight>safeHeight) {
            win.setLayout(
                if(actionButtons.size>=2)(metrics.widthPixels*0.96f).toInt()
                else win.attributes.width,
                safeHeight
            )
        }else if(actionButtons.size>=2){
            win.setLayout((metrics.widthPixels*0.96f).toInt(),
                ViewGroup.LayoutParams.WRAP_CONTENT)
        }
        if(dialog.currentFocus is android.widget.EditText){
            win.setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE)
        }
        // No forced global padding on the decor: Android owns safe navigation
        // insets, and the footer already has a bottom inset of its own.
    }
}
''',encoding='utf-8')

# Profile editor already has a one-row 3-button footer, but the fixed dialog
# height could leave the row below the bottom of smaller Xiaomi displays.
main=PACKAGE/'MainActivity.kt'
s=main.read_text(encoding='utf-8')
old='(resources.displayMetrics.heightPixels*0.77f).toInt()'
assert s.count(old)==1,s.count(old)
s=s.replace(old,'(resources.displayMetrics.heightPixels*0.66f).toInt()',1)
main.write_text(s,encoding='utf-8')

# Dynamic version bump. Do not edit identity or API settings.
gradle=ROOT/'build.gradle.kts'
s=gradle.read_text(encoding='utf-8')
assert s.count('versionCode = 119')==1
assert s.count('versionName = "1.9.109"')==1
s=s.replace('versionCode = 119','versionCode = 120').replace('versionName = "1.9.109"','versionName = "1.9.110"')
gradle.write_text(s,encoding='utf-8')
print('1.9.110 layout-only dialog audit: %d activities; every Material dialog intercepted; profile footer retained; Gemini unchanged.'%len(fixed))
print('Activities:',', '.join(fixed))