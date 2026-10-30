"""SaúdePrática v1.9.60 — remove duplicated entries from Acessibilidade."""
from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1')
main=root/'app/src/main/java/com/mediagenda/app/MainActivity.kt'
s=main.read_text(encoding='utf-8')
blocks=[
'''                box.addView(infoCard("ℹ️", "Como funciona",
                    "O modo não altera registos, alarmes ou o PIN. " +
                    "No Início, usa «Ver todos os módulos» para aceder aos restantes.") {
                    startActivity(Intent(this,SupportHelpActivity::class.java)
                        .putExtra(SupportHelpActivity.MODE,SupportHelpActivity.HELP))
                })
''',
'''                box.addView(infoCard("📖", "Ajuda passo a passo",
                    "Guia ilustrado para utilizadores e cuidadores") {
                    startActivity(Intent(this,SupportHelpActivity::class.java)
                        .putExtra(SupportHelpActivity.MODE,SupportHelpActivity.HELP))
                })
'''
]
for i,block in enumerate(blocks,1):
    n=s.count(block)
    assert n==1,f'v1.9.60 Accessibility card {i}: expected 1 match, found {n}'
    s=s.replace(block,'',1)
old='"acessibilidade" -> Triple("🧓","Acessibilidade","Modo Sénior e ajuda para utilizar a aplicação")'
new='"acessibilidade" -> Triple("🧓","Acessibilidade","Modo Sénior e acesso rápido à Emergência")'
assert s.count(old)==1
s=s.replace(old,new,1)
assert '"apoio" -> {' in s and '"acessibilidade" -> {' in s
assert '"Como funciona"' not in s and '"Ajuda passo a passo"' not in s
main.write_text(s,encoding='utf-8')
gradle=root/'app/build.gradle.kts'
g=gradle.read_text(encoding='utf-8')
assert g.count('versionCode = 69')==1 and g.count('versionName = "1.9.59"')==1
gradle.write_text(g.replace('versionCode = 69','versionCode = 70').replace('versionName = "1.9.59"','versionName = "1.9.60"'),encoding='utf-8')
print('SaúdePrática v1.9.60: duplicates removed from Acessibilidade; Ajuda e informações preserved')
