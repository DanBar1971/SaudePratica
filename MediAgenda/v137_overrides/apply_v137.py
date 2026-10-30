#!/usr/bin/env python3
"""SaúdePrática v1.9.117 — hydration editor accessible at large Android font sizes.

Changes only the shared dialog presentation, not alarm delivery, TOMEI, patient
data, hydration storage, scheduler, or the signing identity.
"""
from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1/app")
base=root/"src/main/java/com/mediagenda/app"
dialog=base/"SafeMaterialAlertDialogBuilder.kt"
s=dialog.read_text(encoding="utf-8")

def once(old,new,label):
    global s
    n=s.count(old)
    assert n==1,(label,n)
    s=s.replace(old,new,1)

# A fixed 50dp height clips two-line buttons when Android's font scaling is
# large. Allow the buttons and footer row to grow, rather than hiding Guardar.
once("""                    row.addView(button,LinearLayout.LayoutParams(0,dp(context,50),1f).apply {
""","""                    // Respect accessibility font scaling without changing
                    // click listeners or the two-buttons-side-by-side layout.
                    val scaledMinHeight=maxOf(dp(context,56),
                        (dp(context,52)*context.resources.configuration.fontScale).toInt())
                    button.minHeight=scaledMinHeight
                    button.minimumHeight=scaledMinHeight
                    button.maxLines=3
                    row.addView(button,LinearLayout.LayoutParams(0,
                        ViewGroup.LayoutParams.WRAP_CONTENT,1f).apply {
""","flexible-height action buttons")

# v1.9.116 already expanded profile, medication and appointment editors.
# Include the previously overlooked hydration configuration in exactly the
# same fullscreen presentation, with stock negative/positive callbacks intact.
once("""        val fullEditor=formTitle=="editar perfil" ||
""","""        // Hydration settings were still an oversized floating window. At
        // large system font sizes the action bar could fall below the display.
        // Keep its existing scrollable form and make the dialog full-height.
        val hydrationEditor=listOf("hidrata", "hydrat", "wasser", "trink").any {
            formTitle.contains(it)
        } || (formTitle.contains("water") &&
            listOf("config", "setting").any{formTitle.contains(it)}) ||
            actionButtons.any{
                it.text.toString().contains("ativar e guardar",ignoreCase=true)
            }
        val fullEditor=hydrationEditor || formTitle=="editar perfil" ||
""","hydration full screen without changing save behavior")

dialog.write_text(s,encoding="utf-8")

gradle=root/"build.gradle.kts"
g=gradle.read_text(encoding="utf-8")
assert g.count("versionCode = 126")==1
assert g.count('versionName = "1.9.116"')==1
g=g.replace("versionCode = 126","versionCode = 127",1)
g=g.replace('versionName = "1.9.116"','versionName = "1.9.117"',1)
gradle.write_text(g,encoding="utf-8")
print("v1.9.117: hydration settings fullscreen; scalable action footer; alarm implementation untouched.")
