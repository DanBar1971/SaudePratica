#!/usr/bin/env python3
"""SaúdePrática 1.9.111: consistent grouped dialog actions + visible hydration choices.
Applies AFTER v130. No behavioral changes to Gemini, prescriptions or persisted data.
"""
from pathlib import Path
ROOT=Path('build-src/MediAgenda_Android_v1/app')
BASE=ROOT/'src/main/java/com/mediagenda/app'

def once(path, old, new, name):
    content=path.read_text(encoding='utf-8')
    assert content.count(old)==1, (name,content.count(old))
    path.write_text(content.replace(old,new,1),encoding='utf-8')

# Correct root cause: MaterialAlertDialogBuilder.setMessage() consumes list space
# on some MIUI / Xiaomi dialogs built with setItems(). Existing selection handler
# is UNCHANGED, including persistence and reminders for the selected profile.
water=BASE/'WellnessActivity.kt'
once(water,'''            MaterialAlertDialogBuilder(this).setTitle("Mais água para hoje?")
                .setMessage("Só altera o objetivo. Confirma que não tens restrições de líquidos.")
                .setItems(options){_,choice->''','''            // MIUI can hide a setItems list when setMessage is also supplied.
            // Show the choices directly; the safety note is already on the card.
            MaterialAlertDialogBuilder(this).setTitle("Escolhe quanto acrescentar ao objetivo de hoje")
                .setItems(options){_,choice->''','water dialog options no longer hidden')
once(water,'"Os avisos poderão voltar a tocar ainda hoje dentro do horário escolhido.",','"Os avisos poderão voltar a tocar ainda hoje dentro do horário escolhido. " +\n            "Se tens restrições de líquidos, confirma com o profissional de saúde antes de aumentar.",','hydration safety preserved on card')

# Purely visual style for all two/three-button Material dialogs: uses exact
# reference colors, allocates equal horizontal space, and preserves callbacks.
dialog=BASE/'SafeMaterialAlertDialogBuilder.kt'
text=dialog.read_text(encoding='utf-8')
assert text.startswith('package com.mediagenda.app\n')
head=text[:text.index('internal object SafeDialogActionLayout {')]
head=head.replace('import android.text.TextUtils','''import android.text.TextUtils
import android.content.res.ColorStateList
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.graphics.drawable.RippleDrawable
import com.google.android.material.button.MaterialButton''')
layout=r'''internal object SafeDialogActionLayout {
    private fun dp(context: Context, v: Int): Int =
        (v*context.resources.displayMetrics.density+0.5f).toInt()

    // Palette sampled from the user's reference image: muted red for destructive
    // actions, slate blue for cancelling and jade teal for affirmative actions.
    private enum class Tone(val fill: Int, val foreground: Int) {
        DANGER(Color.rgb(59,49,53), Color.rgb(255,124,111)),
        CANCEL(Color.rgb(31,50,72), Color.rgb(162,193,229)),
        ACCEPT(Color.rgb(21,129,119), Color.rgb(226,255,250))
    }
    private fun toneFor(text: String): Tone {
        val label=text.trim().lowercase(java.util.Locale.ROOT)
        return when {
            // Semantic rules work even when button labels differ from examples.
            listOf("cancelar", "fechar", "voltar", "não", "nao", "cancel", "close",
                "back", "annuler", "abbrechen", "zurück", "cerrar", "retour",
                "terminar sem", "mais tarde").any { label.startsWith(it) } -> Tone.CANCEL
            listOf("eliminar", "apagar", "remover", "excluir", "limpar", "retirar",
                "delete", "remove", "erase", "supprimer", "effacer", "löschen",
                "borrar", "eliminar definitivamente").any { label.startsWith(it) } -> Tone.DANGER
            else -> Tone.ACCEPT
        }
    }
    private fun styleButton(button: Button) {
        val context=button.context
        val label=button.text.toString()
        val tone=toneFor(label)
        val radius=dp(context,16)
        button.apply {
            minWidth=0; minimumWidth=0
            minHeight=dp(context,48); minimumHeight=dp(context,48)
            isAllCaps=false
            setSingleLine(false)
            maxLines=2
            ellipsize=TextUtils.TruncateAt.END
            textSize=if(label.length>22) 11f else 13f
            gravity=Gravity.CENTER
            setTypeface(null,Typeface.BOLD)
            setPadding(dp(context,4),dp(context,3),dp(context,4),dp(context,3))
            contentDescription=label
            setTextColor(tone.foreground)
            if(this is MaterialButton){
                backgroundTintList=ColorStateList.valueOf(tone.fill)
                strokeWidth=0
                cornerRadius=radius
                insetTop=0; insetBottom=0
            }else{
                backgroundTintList=null
                val shape=GradientDrawable().apply {
                    setColor(tone.fill)
                    cornerRadius=radius.toFloat()
                }
                background=RippleDrawable(ColorStateList.valueOf(
                    Color.argb(45,255,255,255)),shape,null)
            }
        }
    }

    // Include custom 2/3-button rows within dialogs (e.g. profile editor), not
    // just stock MaterialAlertDialog buttons. Never replace their click listeners.
    private fun styleEmbeddedGroups(view: View, depth: Int=0) {
        if(depth>25 || view !is ViewGroup)return
        if(view is LinearLayout && view.orientation==LinearLayout.HORIZONTAL &&
            view.childCount in 2..3 &&
            (0 until view.childCount).all{view.getChildAt(it) is MaterialButton}) {
            (0 until view.childCount).forEach { index ->
                val btn=view.getChildAt(index) as MaterialButton
                if(btn.visibility==View.VISIBLE)styleButton(btn)
            }
        }
        for(i in 0 until view.childCount)styleEmbeddedGroups(view.getChildAt(i),depth+1)
    }

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
                    setPadding(dp(context,9),dp(context,6),dp(context,9),dp(context,9))
                }
                actionButtons.forEach { button ->
                    parent.removeView(button)
                    styleButton(button)
                    row.addView(button,LinearLayout.LayoutParams(0,dp(context,50),1f).apply {
                        marginStart=dp(context,3)
                        marginEnd=dp(context,3)
                    })
                }
                // Stock button panel had only three action buttons and spacers.
                parent.removeAllViews()
                parent.addView(row,ViewGroup.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT))
                parent.layoutParams?.let{ p ->
                    p.width=ViewGroup.LayoutParams.MATCH_PARENT
                    p.height=ViewGroup.LayoutParams.WRAP_CONTENT
                    parent.layoutParams=p
                }
            }
        }
        // Also colour single stock actions and any non-reparented buttons.
        actionButtons.forEach(::styleButton)
        styleEmbeddedGroups(win.decorView)

        // Keep the footer inside a usable screen area on small displays.
        val metrics=context.resources.displayMetrics
        val safeHeight=(metrics.heightPixels-dp(context,72)).coerceAtLeast(dp(context,300))
        val existingHeight=win.decorView.height
        if(actionButtons.isNotEmpty() && existingHeight>safeHeight) {
            win.setLayout(
                if(actionButtons.size>=2)(metrics.widthPixels*0.96f).toInt()
                else win.attributes.width,
                safeHeight
            )
        } else if(actionButtons.size>=2) {
            win.setLayout((metrics.widthPixels*0.96f).toInt(),
                ViewGroup.LayoutParams.WRAP_CONTENT)
        }
        if(dialog.currentFocus is android.widget.EditText) {
            win.setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE)
        }
    }
}
'''
dialog.write_text(head+layout,encoding='utf-8')

# v110 already uses a custom fixed profile footer. It is styled above via
# styleEmbeddedGroups, so no changes to profile save/delete functions needed.
# Keep all data structures and Android identity stable.
gradle=ROOT/'build.gradle.kts'
once(gradle,'versionCode = 120','versionCode = 121','versionCode bump')
once(gradle,'versionName = "1.9.110"','versionName = "1.9.111"','versionName bump')
print('v1.9.111: all stock 2/3-action dialog buttons and custom profile action rows styled; hydration setItems visible.')