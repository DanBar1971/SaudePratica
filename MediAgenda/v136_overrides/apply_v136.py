#!/usr/bin/env python3
"""SaúdePrática v1.9.116 — compact profiles, clean clinical fields,
and full-height editor dialogs with cancellation only by explicit buttons.
Conservative UI-only migration: never erase saved profile values or medical files.
"""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1/app")
base=root/"src/main/java/com/mediagenda/app"
main=base/"MainActivity.kt"
s=main.read_text(encoding="utf-8")
def one(old,new,label):
    global s
    n=s.count(old)
    assert n==1,(label,n)
    s=s.replace(old,new,1)

# 1. Remove redundant CC explanation; preserve photo thumbnails and ALL IDs.
one('''        box.addView(noteBox("Cartão de Cidadão e identificação",
            "Documento opcional. As fotografias ficam apenas neste perfil e só são mostradas mediante acesso à aplicação."))
''',"","remove CC information callout")

# 2. Immediately after NISS, show health unit, followed by address and postcode.
one('''        box.addView(noteBox("Morada e unidade de saúde",
            "Os números de observação e de processo clínico foram movidos para Situação Clínica."))
        listOf(address,postalCode,healthUnit).forEach{box.addView(it.container)}''',
'''        listOf(healthUnit,address,postalCode).forEach{box.addView(it.container)}''',
"health unit after NISS")

# 3. Remove unnecessary UI for contact refs and residential home.
# Values remain loaded/saved unchanged in preference stores. Keep personal phone + email.
one('''        box.addView(noteBox("Contactos e responsável",
            "Permite encontrar rapidamente um familiar ou pessoa de referência."))
        listOf(phone, email, familyRole, contactName, contactPhone)
            .forEach { box.addView(it.container) }
        box.addView(noteBox("Lar ou residência assistida (opcional)",
            "Nome do lar, telefone, morada e a pessoa de contacto no local."))
        listOf(homeName, homeAddress, homePhone, homeResponsible, homeNotes)
            .forEach { box.addView(it.container) }''',
'''        // Os contactos pessoais continuam úteis. Os campos antigos de
        // responsável/lar não são apagados do armazenamento, só ocultados.
        listOf(phone, email).forEach { box.addView(it.container) }''',
"hide residential-home and old reference contacts from edit form")

# 4. Reduce chooser visual noise; neither name nor legal identity is changed in storage.
one('''        box.addView(android.widget.ImageView(this).apply {
            setImageResource(R.drawable.saude_icon)
            scaleType = android.widget.ImageView.ScaleType.FIT_CENTER
        }, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(130)))
''',"","remove oversized chooser splash")
one('''            setPadding(dp(4), dp(18), dp(4), dp(24))''',
'''            setPadding(dp(7), dp(8), dp(7), dp(24))''',"compact chooser padding")
one('''            setPadding(dp(8), dp(18), dp(8), dp(18))''',
'''            setPadding(dp(8), dp(10), dp(8), dp(18))''',"compact chooser title")
one('''                    "🤲 Cuidador da família · "+fullName.ifBlank{"Abrir este perfil"}
                    else fullName.ifBlank{"Abrir este perfil"}''',
'''                    "🤲 Cuidador da família"
                    else "Toca no perfil para entrar"''',"only short names in chooser")

# Replace inherited compound 'secondaryButton' overlay and alarm routing action.
# Alarm association remains in profile ficha checkbox, untouched.
start=s.index('            val ownerOfAlarms=com.mediagenda.app.notifications.DeviceAlarmRouting')
end=s.index('            card.addView(cardContent,android.widget.FrameLayout.LayoutParams(',start)
repl='''            // Uma única ação FICHA. Evita sobreposição de dois textos
            // e o estado "Associado" flutuante dos botões anteriores.
            val optionsRow=LinearLayout(this).apply{
                orientation=LinearLayout.HORIZONTAL
                gravity=Gravity.END or Gravity.CENTER_VERTICAL
                setPadding(dp(12),0,dp(12),dp(9))
            }
            if(com.mediagenda.app.notifications.DeviceAlarmRouting.explicit(this)==profile.id){
                optionsRow.addView(TextView(this).apply{
                    text="📱 Neste telemóvel"
                    textSize=11f
                    setTextColor(muted)
                    gravity=Gravity.CENTER_VERTICAL
                },LinearLayout.LayoutParams(0,dp(40),1f))
            }else{
                optionsRow.addView(android.view.View(this),
                    LinearLayout.LayoutParams(0,dp(40),1f))
            }
            val fichaButton=com.google.android.material.button.MaterialButton(this).apply{
                text="✎ FICHA"
                textSize=13f
                isAllCaps=false
                minHeight=dp(40)
                minimumHeight=dp(40)
                cornerRadius=dp(12)
                insetTop=0
                insetBottom=0
                setTextColor(Color.WHITE)
                backgroundTintList=android.content.res.ColorStateList.valueOf(
                    Color.rgb(21,129,119))
                setOnClickListener{
                    activateProfile(profile)
                    android.os.Handler(android.os.Looper.getMainLooper())
                        .post{showProfileDialog(false)}
                }
            }
            optionsRow.addView(fichaButton,LinearLayout.LayoutParams(
                dp(112),dp(40)))
            cardContent.addView(optionsRow,LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT))
'''
s=s[:start]+repl+s[end:]

# Keep select action separate from ficha. The row doesn't open an editor by itself.
main.write_text(s,encoding="utf-8")

# 5. Form dialogs: display as proper full-screen sheets, never exposing the
# underlying dashboard. Preserve all original validation callbacks, and stop
# tap-outside/Back from discarding edits. Cancelar/Guardar remain the way out.
safe=base/"SafeMaterialAlertDialogBuilder.kt"
d=safe.read_text(encoding="utf-8")
before='''        // Keep the footer inside a usable screen area on small displays.
        val metrics=context.resources.displayMetrics'''
after='''        // Extensive editors have a real full-screen window, not a floating
        // alert. This central rule covers the profile, medicines, appointments
        // and agenda records without changing any save/delete implementation.
        val formTitle=dialog.findViewById<android.widget.TextView>(
            androidx.appcompat.R.id.alertTitle)?.text?.toString()
            ?.trim()?.lowercase(java.util.Locale.ROOT).orEmpty()
        val clinicalForm=listOf("medica", "medicamento", "marcaç", "marcac",
            "agendamento", "consulta", "appointment", "medication").any{
            formTitle.contains(it)
        }
        val editorAction=listOf("editar", "nova", "novo", "adicionar",
            "criar", "alterar", "registar", "agendar", "edit", "new",
            "add", "nova marcação", "novo medicamento").any{
            formTitle.contains(it)
        }
        val fullEditor=formTitle=="editar perfil" ||
            formTitle=="bem-vindo à saúdeprática" ||
            (clinicalForm && editorAction)
        if(fullEditor){
            // Existing action footers and all field input validation remain.
            dialog.setCanceledOnTouchOutside(false)
            dialog.setCancelable(false)
            win.setDimAmount(0f)
            win.setBackgroundDrawable(android.graphics.drawable.ColorDrawable(
                android.graphics.Color.rgb(29,29,36)))
            win.setGravity(Gravity.FILL)
            win.setLayout(ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT)
            win.setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE)
            return
        }
        // Keep the footer inside a usable screen area on small displays.
        val metrics=context.resources.displayMetrics'''
assert d.count(before)==1,("full screen layout insertion point",d.count(before))
safe.write_text(d.replace(before,after,1),encoding="utf-8")

gradle=root/"build.gradle.kts"
g=gradle.read_text(encoding="utf-8")
assert g.count("versionCode = 125")==1 and g.count('versionName = "1.9.115"')==1
g=g.replace("versionCode = 125","versionCode = 126",1)
g=g.replace('versionName = "1.9.115"','versionName = "1.9.116"',1)
gradle.write_text(g,encoding="utf-8")
print("SaúdePrática v1.9.116: clean profile screen, single FICHA action, full-screen editors.")
