from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1')
base=root/'app/src/main/java/com/mediagenda/app'
def once(p,old,new,label):
    text=p.read_text(encoding='utf-8')
    count=text.count(old)
    if count!=1:raise RuntimeError(f'v1.9.45 {label}: expected once, found {count}')
    p.write_text(text.replace(old,new,1),encoding='utf-8')

main=base/'MainActivity.kt'
old='''        // This editor has dozens of fields. Limit ONLY the scrollable area;
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

        if (!firstRun) {
            dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_NEUTRAL)
                ?.apply {
                    setTextColor(Color.parseColor("#D95048"))
                    setOnClickListener {
                        // Always resolve by stable ID, not by a typed or stale name.
                        val selected=profiles.all().firstOrNull { it.id==activeProfileId }
                        if(selected==null){
                            showError("Este utilizador já não existe.")
                        }else{
                            dialog.dismiss()
                            confirmDeleteSelectedProfile(selected)
                        }
                    }
                }
        }
        dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE).setOnClickListener {
'''
new='''        // Xiaomi/MIUI stacks three stock AlertDialog action buttons vertically.
        // The long editor makes that native footer taller than its viewport;
        // Delete disappears and Cancel gets clipped. The fix is a REAL, fixed
        // footer in a single bounded custom view, not another window-height tweak.
        val editorScroll=scroll(box).apply {
            isFillViewport=false
            isVerticalScrollBarEnabled=true
            descendantFocusability=android.view.ViewGroup.FOCUS_AFTER_DESCENDANTS
        }
        val editorFooter=LinearLayout(this).apply {
            orientation=LinearLayout.HORIZONTAL
            gravity=Gravity.CENTER_VERTICAL
            setPadding(dp(5),dp(7),dp(5),dp(7))
        }
        fun footerParams()=LinearLayout.LayoutParams(0,dp(52),1f).apply {
            marginStart=dp(2);marginEnd=dp(2)
        }
        val deleteProfileButton=secondaryButton("Eliminar") {}.apply {
            setTextColor(Color.parseColor("#D95048"))
            backgroundTintList=ColorStateList.valueOf(
                if(isDarkPalette)Color.parseColor("#3B3034")
                else Color.parseColor("#FFEEED"))
            textSize=13f
            visibility=if(firstRun)View.GONE else View.VISIBLE
        }
        val cancelProfileButton=secondaryButton("Cancelar") {}.apply {
            textSize=13f
            visibility=if(firstRun)View.GONE else View.VISIBLE
        }
        val saveProfileButton=primaryButton("Guardar") {}.apply {textSize=13f}
        if(!firstRun){
            editorFooter.addView(deleteProfileButton,footerParams())
            editorFooter.addView(cancelProfileButton,footerParams())
        }
        editorFooter.addView(saveProfileButton,footerParams())
        val editorBody=LinearLayout(this).apply {
            orientation=LinearLayout.VERTICAL
            isFocusableInTouchMode=true
            layoutParams=android.widget.FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                (resources.displayMetrics.heightPixels*0.61f).toInt()
                    .coerceAtLeast(dp(270)))
            addView(editorScroll,LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,0,1f))
            addView(editorFooter,LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,dp(66)))
        }
        dialog=MaterialAlertDialogBuilder(this)
            .setTitle(if(firstRun)"Bem-vindo à SaúdePrática" else "Editar perfil")
            .setView(editorBody)
            .show()
        dialog.window?.apply {
            setSoftInputMode(
                android.view.WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE or
                android.view.WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_HIDDEN)
            setLayout((resources.displayMetrics.widthPixels*0.92f).toInt(),
                ViewGroup.LayoutParams.WRAP_CONTENT)
        }
        editorBody.requestFocus()
        editorScroll.post{editorScroll.scrollTo(0,0)}
        cancelProfileButton.setOnClickListener{dialog.dismiss()}
        deleteProfileButton.setOnClickListener{
            // Resolve by stable ID; deletion is gated by name and optional PIN.
            val selected=profiles.all().firstOrNull { it.id==activeProfileId }
            if(selected==null){
                showError("Este utilizador já não existe.")
            }else{
                dialog.dismiss()
                confirmDeleteSelectedProfile(selected)
            }
        }
        saveProfileButton.setOnClickListener {
'''
once(main,old,new,'fixed-profile-dialog-UI')

nearby=base/'sync/NearbySyncActivity.kt'
once(nearby,'''        val scroll=ScrollView(this).apply{
            setBackgroundColor(back)
            clipToPadding=false
        }
''','''        val scroll=ScrollView(this).apply{
            clipToPadding=false
            // Match the main SaúdePrática dark wallpaper and translucent tint.
            if(dark){
                val art=ContextCompat.getDrawable(this@NearbySyncActivity,
                    com.mediagenda.app.R.drawable.saude_background)?.mutate()
                if(art!=null){
                    if(art is android.graphics.drawable.BitmapDrawable)
                        art.gravity=Gravity.FILL
                    background=android.graphics.drawable.LayerDrawable(arrayOf(
                        art,android.graphics.drawable.ColorDrawable(
                            Color.argb(105,3,14,23))))
                }else setBackgroundColor(back)
            }else setBackgroundColor(Color.parseColor("#F4F7F9"))
        }
''','sync-background')
once(nearby,'''            setPadding(dp(17),dp(16),dp(17),dp(28))''',
     '''            // Extra breathing room below the status bar, as in MainActivity.
            setPadding(dp(17),dp(34),dp(17),dp(28))''','sync-header-top')
once(nearby,'''        addButtonTo(body,"← Voltar à SaúdePrática",false){finish()}
''','''        // The arrow in the header is the only Back control.
''','sync-remove-duplicate-back')
once(nearby,'''                "Toca em «Voltar à SaúdePrática». Os ecrãs são atualizados " +
                "automaticamente ao regressar; não precisas de fechar a app.")''',
     '''                "Usa a seta de voltar no cabeçalho. Os ecrãs são atualizados " +
                "automaticamente ao regressar; não precisas de fechar a app.")''','sync-success-instruction')
gradle=root/'app/build.gradle.kts'
once(gradle,'versionCode = 54','versionCode = 55','version-code')
once(gradle,'versionName = "1.9.44"','versionName = "1.9.45"','version-name')
print('v1.9.45 fixed profile action footer and sync branded wallpaper/headroom')