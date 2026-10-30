from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
activity=root/"app/src/main/java/com/mediagenda/app/ProfileMediaActivity.kt"
s=activity.read_text(encoding="utf-8")
old='''            if(proposals.isEmpty())
                showError("Não identifiquei dados legíveis. Fotografa o cartão inteiro, com boa luz e sem reflexos, ou preenche o perfil manualmente.")
            else showOcrReview(proposals)'''
new='''            if(proposals.isEmpty()) {
                if(frontText.isNotBlank() || backText.isNotBlank()){
                    MaterialAlertDialogBuilder(this)
                        .setTitle("Texto reconhecido, sem campos identificados")
                        .setMessage("O cartão foi lido parcialmente, mas não foi possível associar com segurança os dados aos campos. Podes consultar o texto reconhecido sem o guardar.")
                        .setPositiveButton("Ver texto lido") { _,_ ->
                            val view=TextView(this).apply{
                                text="FRENTE:\\n"+frontText+"\\n\\nVERSO:\\n"+backText
                                setTextIsSelectable(true)
                                setTextColor(if(dark)Color.WHITE else Color.rgb(18,35,48))
                                setPadding(dp(18),dp(16),dp(18),dp(16))
                            }
                            MaterialAlertDialogBuilder(this).setTitle("Leitura OCR neste telemóvel")
                                .setView(ScrollView(this).apply{addView(view)})
                                .setPositiveButton("Fechar",null).show()
                        }.setNegativeButton("Fechar",null).show()
                } else showError("O reconhecimento de texto não conseguiu ler nenhum campo. Tenta uma fotografia mais próxima, com luz uniforme e sem reflexos.")
            } else showOcrReview(proposals)'''
assert old in s,"Missing OCR empty-result handler"
s=s.replace(old,new,1)
activity.write_text(s,encoding="utf-8")
gradle=root/"app/build.gradle.kts"
g=gradle.read_text(encoding="utf-8")
assert 'applicationId = "com.mediagenda.app.stable"' in g
assert 'versionCode = 20' in g and 'versionName = "1.9.10"' in g
gradle.write_text(g.replace('versionCode = 20','versionCode = 21',1)
    .replace('versionName = "1.9.10"','versionName = "1.9.11"',1),encoding="utf-8")
print("v1.9.11 OCR: robust labelled columns and MRZ; readable OCR text can be inspected locally when no fields match.")
