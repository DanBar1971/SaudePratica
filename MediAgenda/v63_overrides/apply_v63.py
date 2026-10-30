from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1')
base=root/'app/src/main/java/com/mediagenda/app'
def one(file,old,new,label):
    src=file.read_text(encoding='utf-8')
    count=src.count(old)
    if count!=1:raise RuntimeError('SaudePratica v1.9.44 '+label+': '+str(count))
    file.write_text(src.replace(old,new,1),encoding='utf-8')

main=base/'MainActivity.kt'
old='''        dialog = MaterialAlertDialogBuilder(this)
            .setTitle(if (firstRun) "Bem-vindo à SaúdePrática" else "Editar perfil")
            .setView(scroll(box))
            .setPositiveButton("Guardar", null)
            .apply {
                if (!firstRun) {
                    setNegativeButton("Cancelar", null)
                    if (profiles.all().any { it.id == activeProfileId }) {
                        setNeutralButton("🗑 Eliminar", null)
                    }
                }
            }
            .show()
'''
new='''        // This editor has dozens of fields. Limit ONLY the scrollable area;
        // Material dialog action buttons remain in a separate footer.
        // Without a height constraint Xiaomi lays out the long form beyond
        // the screen and clips Cancel/Delete while leaving Save partly visible.
        val editorHeight=minOf(dp(410),
            (resources.displayMetrics.heightPixels*0.43f).toInt())
            .coerceAtLeast(dp(190))
        val editorScroll=scroll(box).apply {
            isFillViewport=false
            isVerticalScrollBarEnabled=true
            layoutParams=android.widget.FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,editorHeight)
        }
        dialog = MaterialAlertDialogBuilder(this)
            .setTitle(if (firstRun) "Bem-vindo à SaúdePrática" else "Editar perfil")
            .setView(editorScroll)
            .setPositiveButton("Guardar", null)
            .apply {
                if (!firstRun) {
                    setNegativeButton("Cancelar", null)
                    // Always render the Delete control in the existing editor;
                    // resolve and check the active profile at click time.
                    setNeutralButton("Eliminar", null)
                }
            }
            .show()
        dialog.window?.apply {
            setSoftInputMode(
                android.view.WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE or
                android.view.WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_HIDDEN)
            // Force a bounded total dialog window on Xiaomi/MIUI. AppCompat
            // may replace the custom ScrollView LayoutParams, so the window
            // height itself must also be capped to keep all 3 actions visible.
            setLayout((resources.displayMetrics.widthPixels*0.92f).toInt(),
                (resources.displayMetrics.heightPixels*0.78f).toInt())
        }
'''
one(main,old,new,'bounded profile edit dialog with permanent actions')
# Neutral click handler already checks the actual selected profile and then
# requires exact profile-name confirmation and PIN, if enabled.
help=base/'SmartHelpActivity.kt'
one(help,
    'if(keyboard){scroller.post{scroller.fullScroll(ScrollView.FOCUS_DOWN)}}',
    '''if(keyboard){
                // fullScroll(FOCUS_DOWN) moves keyboard focus into selectable
                // chat bubbles, so typed letters never reach the EditText.
                // Scroll pixels only; preserve the user's input focus.
                scroller.post{scroller.scrollTo(0,transcript.height)}
            }''',
    'do not steal EditText keyboard focus when IME opens')
one(help,
    'scroller.post{scroller.fullScroll(ScrollView.FOCUS_DOWN)}',
    'scroller.post{scroller.scrollTo(0,transcript.height)}',
    'do not steal focus on incoming message')
# Prevent selectable chat bubbles from stealing focus during transient IME
# window insets in Android OEM keyboard implementations.
one(help,
    '            setTextIsSelectable(true)\n',
    '            setTextIsSelectable(false)\n',
    'render messages nonfocusable; writing remains in question input')
gradle=root/'app/build.gradle.kts'
one(gradle,'versionCode = 53','versionCode = 54','versionCode')
one(gradle,'versionName = "1.9.43"','versionName = "1.9.44"','versionName')
print('v1.9.44 profile form uses bounded scrolling and consistent buttons; help preserves keyboard focus')
