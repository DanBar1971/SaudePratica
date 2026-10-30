from pathlib import Path
f=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app/DocumentsActivity.kt")
s=f.read_text(encoding="utf-8")
def sub(old,new,label):
 global s
 if old not in s:raise RuntimeError("v1.9.5 docs missing "+label)
 s=s.replace(old,new,1)

sub('''import androidx.core.content.FileProvider''',
'''import androidx.core.content.FileProvider
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import com.google.android.material.card.MaterialCardView''', "UI imports")

sub('''        val background = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(if (dark) Color.rgb(3, 20, 29) else Color.rgb(244, 247, 249))
            setPadding(dp(16), dp(12), dp(16), dp(8))
        }''',
'''        val background = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(16), dp(12), dp(16), dp(8))
            if (dark) {
                val backdrop=ContextCompat.getDrawable(this@DocumentsActivity, R.drawable.saude_background)
                if (backdrop is android.graphics.drawable.BitmapDrawable)
                    backdrop.gravity=Gravity.FILL
                this.background = if (backdrop != null) android.graphics.drawable.LayerDrawable(
                    arrayOf(backdrop, android.graphics.drawable.ColorDrawable(Color.argb(105,3,14,23)))
                ) else android.graphics.drawable.ColorDrawable(Color.rgb(3,20,29))
            } else setBackgroundColor(Color.rgb(244,247,249))
        }''', "background consistency")

sub('''        val heading = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        heading.addView(label("📂 Documentos Digitais", 22f, true, textColor))
        heading.addView(label(user.name + " · PDFs e imagens", 13f, false, subColor))
        top.addView(heading, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        background.addView(top)

        val actions = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        actions.addView(actionButton("📷 Digitalizar", {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA)
                == PackageManager.PERMISSION_GRANTED) captureDocument()
            else cameraPermission.launch(Manifest.permission.CAMERA)
        }), LinearLayout.LayoutParams(0, dp(52), 1f))
        actions.addView(actionButton("📎 Anexar PDF / imagem", {
            picker.launch(arrayOf("application/pdf", "image/*"))
        }), LinearLayout.LayoutParams(0, dp(52), 1f).apply { marginStart = dp(8) })
        background.addView(actions, LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
            topMargin = dp(18); bottomMargin = dp(12)
        })''',
'''        val heading = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        heading.addView(label("SaúdePrática", 13f, true, turquoise))
        heading.addView(label("📂  Documentos Digitais", 26f, true, textColor))
        heading.addView(label("PDFs, imagens e documentos pessoais", 13f, false, subColor))
        top.addView(heading, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        top.addView(label(user.name.take(12), 12f, true, turquoise).apply {
            gravity=Gravity.CENTER
            setPadding(dp(10),dp(7),dp(10),dp(7))
            this.background=rounded(if (dark) Color.rgb(23,60,59) else Color.rgb(230,244,241))
        })
        background.addView(top)

        val actions = LinearLayout(this).apply {
            orientation=LinearLayout.HORIZONTAL
            gravity=Gravity.CENTER_VERTICAL
            setPadding(dp(4),dp(19),dp(4),dp(10))
        }
        val summary = LinearLayout(this).apply { orientation=LinearLayout.VERTICAL }
        summary.addView(label("Documentos", 18f, true, textColor))
        summary.addView(label("Guardados apenas para este utilizador", 12f, false, subColor))
        actions.addView(summary, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT,1f))
        actions.addView(MaterialButton(this).apply {
            text="+ Adicionar"
            textSize=12f; isAllCaps=false
            setTextColor(turquoise)
            backgroundTintList=ColorStateList.valueOf(Color.TRANSPARENT)
            strokeColor=ColorStateList.valueOf(turquoise)
            strokeWidth=dp(1)
            cornerRadius=dp(18)
            setOnClickListener {
                MaterialAlertDialogBuilder(this@DocumentsActivity)
                    .setTitle("Adicionar documento")
                    .setItems(arrayOf("📷 Digitalizar com a câmara","📎 Anexar PDF ou imagem")) { _, which ->
                        if (which==0) {
                            if (ContextCompat.checkSelfPermission(this@DocumentsActivity, Manifest.permission.CAMERA)
                                == PackageManager.PERMISSION_GRANTED) captureDocument()
                            else cameraPermission.launch(Manifest.permission.CAMERA)
                        } else picker.launch(arrayOf("application/pdf","image/*"))
                    }.setNegativeButton("Cancelar",null).show()
            }
        })
        background.addView(actions)''', "single add action and branded header")

sub('''        setContentView(background)
        refresh()''',
'''        WindowCompat.setDecorFitsSystemWindows(window,false)
        window.statusBarColor=Color.TRANSPARENT
        window.navigationBarColor=Color.TRANSPARENT
        val controller=WindowInsetsControllerCompat(window,window.decorView)
        controller.isAppearanceLightStatusBars=!dark
        controller.isAppearanceLightNavigationBars=!dark
        controller.hide(WindowInsetsCompat.Type.navigationBars())
        ViewCompat.setOnApplyWindowInsetsListener(background) { view, insets ->
            val safe=insets.getInsets(WindowInsetsCompat.Type.statusBars() or
                WindowInsetsCompat.Type.navigationBars() or
                WindowInsetsCompat.Type.displayCutout())
            view.setPadding(dp(16)+safe.left,dp(12)+safe.top,
                dp(16)+safe.right,dp(8)+safe.bottom)
            insets
        }
        setContentView(background)
        ViewCompat.requestApplyInsets(background)
        refresh()''', "immersive system bars")

sub('''        if (items.isEmpty()) {
            body.addView(label("Ainda não existem documentos.\\n\\nPode fotografar atestados, justificações, boletins ou importar PDFs recebidos por mensagem.", 15f, false, subColor)
                .apply { setPadding(dp(16), dp(26), dp(16), dp(26)) })
        }''',
'''        if (items.isEmpty()) {
            val empty = LinearLayout(this).apply {
                orientation=LinearLayout.VERTICAL
                gravity=Gravity.CENTER
                setPadding(dp(20),dp(28),dp(20),dp(28))
            }
            empty.addView(label("📂",35f,false,turquoise))
            empty.addView(label("Ainda não há documentos",17f,true,textColor).apply {
                gravity=Gravity.CENTER
                setPadding(0,dp(8),0,dp(6))
            })
            empty.addView(label(
                "Toque em + Adicionar para fotografar um documento ou importar um PDF ou imagem recebido por mensagem.",
                13f,false,subColor).apply { gravity=Gravity.CENTER })
            body.addView(empty)
        }''', "empty state")

sub('''            val row = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL
                background = rounded(if (dark) Color.rgb(25, 42, 53) else Color.WHITE)
                setPadding(dp(14), dp(16), dp(14), dp(16))
            }''',
'''            val row = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER_VERTICAL
                setPadding(dp(16),dp(16),dp(14),dp(16))
            }
            val card=MaterialCardView(this).apply {
                radius=dp(20).toFloat()
                strokeWidth=dp(1)
                strokeColor=if (dark) Color.rgb(54,73,89) else Color.rgb(227,232,239)
                setCardBackgroundColor(if (dark) Color.rgb(28,41,53) else Color.WHITE)
                cardElevation=dp(1).toFloat()
            }''', "consistent document cards")

sub('''            row.setOnClickListener { actionsFor(doc) }
            body.addView(row, LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                bottomMargin = dp(10)
            })''',
'''            card.addView(row)
            card.setOnClickListener { actionsFor(doc) }
            body.addView(card, LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                bottomMargin=dp(12)
            })''', "card layout")
f.write_text(s,encoding="utf-8")
print("v1.9.5: Documents now shares SaúdePrática wallpaper, toolbar, outlined add button, cards and immersive bars.")
