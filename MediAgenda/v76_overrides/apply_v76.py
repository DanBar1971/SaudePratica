"""SaúdePrática 1.9.58: fix inaccessible Senior mode choices on Xiaomi.

The old MaterialAlertDialog combined setMessage and setSingleChoiceItems. On
several Android/Material layouts the message consumes the dialog's list area,
so the user only sees Cancel. Replace it with inline, large, always-visible
choice cards under Opções > Acessibilidade; no modal to obscure choices.
"""
from pathlib import Path

root=Path('build-src/MediAgenda_Android_v1')
base=root/'app/src/main/java/com/mediagenda/app'

def change(p, old, new, label):
    txt=p.read_text(encoding='utf-8')
    n=txt.count(old)
    assert n==1, f'v1.9.58 {label}: anchor count {n}'
    p.write_text(txt.replace(old,new,1),encoding='utf-8')

main=base/'MainActivity.kt'
old='''    private fun showSeniorSettings() {
        MaterialAlertDialogBuilder(this)
            .setTitle("🧓 Modo Sénior / Terceira Idade")
            .setMessage("Simplifica o ecrã inicial: apresenta primeiro Medicação, Tomas, Agenda, " +
                "Atividade e Saúde, Emergência e Opções. Usa cartões maiores e texto mais legível. " +
                "Podes escolher «Ver todos os módulos» quando precisares. " +
                "Não altera os dados, lembretes nem as permissões de segurança.")
            .setSingleChoiceItems(arrayOf("Modo normal", "Modo Sénior"),
                if(seniorMode) 1 else 0) { dialog,which ->
                seniorPrefs().edit().putBoolean("enabled",which==1).apply()
                seniorExpanded=false
                dialog.dismiss()
                showOptionsGroup("acessibilidade")
            }
            .setNegativeButton("Cancelar",null).show()
    }
'''
new='''    /** Large in-page controls: avoid combining setMessage + setSingleChoiceItems in
     * MaterialAlertDialog (the list was invisible on some Xiaomi phones).
     * Mode preference changes only the UI, never medications or profile data.
     */
    private fun selectSeniorMode(enabled: Boolean) {
        if (seniorMode == enabled) return
        seniorPrefs().edit().putBoolean("enabled", enabled).apply()
        seniorExpanded=false
        showOptionsGroup("acessibilidade")
        Toast.makeText(this, if (enabled) "Modo Sénior ativado. Abre o Início para o experimentar."
            else "Modo normal ativado.", Toast.LENGTH_LONG).show()
    }
'''
change(main,old,new,'replace invisible senior dialog')
old2='''            "acessibilidade" -> {
                box.addView(infoCard("🧓", "Modo Sénior",
                    if(seniorMode) "Ativo · cartões grandes e módulos essenciais" else
                        "Desativado · tocar para ativar modo simplificado") {
                    showSeniorSettings()
                })
                box.addView(infoCard("🆘", "Acesso rápido à Emergência",
                    "Alergias, contactos e informações úteis") {healthRecords("emergency")})
'''
new2='''            "acessibilidade" -> {
                box.addView(infoCard("🧓", "Ativar Modo Sénior",
                    if(seniorMode) "✓ Selecionado · cartões e texto maiores, módulos essenciais" else
                        "Mostrar primeiro Medicação, Tomas, Agenda, Atividade e Saúde e Emergência") {
                    selectSeniorMode(true)
                })
                box.addView(infoCard("📱", "Usar modo normal",
                    if(!seniorMode) "✓ Selecionado · apresentação habitual" else
                        "Voltar ao menu principal completo com cartões normais") {
                    selectSeniorMode(false)
                })
                if (seniorMode) box.addView(infoCard("🏠", "Experimentar Modo Sénior",
                    "Abrir agora o ecrã inicial com os cartões maiores") { showHome() })
                box.addView(infoCard("ℹ️", "Como funciona",
                    "O modo não altera registos, alarmes ou o PIN. " +
                    "No Início, usa «Ver todos os módulos» para aceder aos restantes.") {
                    startActivity(Intent(this,SupportHelpActivity::class.java)
                        .putExtra(SupportHelpActivity.MODE,SupportHelpActivity.HELP))
                })
                box.addView(infoCard("🆘", "Acesso rápido à Emergência",
                    "Alergias, contactos e informações úteis") {healthRecords("emergency")})
'''
change(main,old2,new2,'always-visible mode choices')
# Make essential dashboard items visible in senior mode even if previously hidden
old3='''        val visibleModules=options.filter {
            it.title=="Opções" || (it.title !in hiddenModules &&
                !(it.title=="Situação Clínica" &&
                    "Saúde Ocupacional" in hiddenModules) &&
                (!seniorMode || seniorExpanded || it.title in setOf(
                    "Medicação","Tomas","Agenda","Atividade e Saúde","Emergência")))
        }
'''
new3='''        val essentialModules=setOf("Medicação","Tomas","Agenda","Atividade e Saúde","Emergência")
        val visibleModules=options.filter {
            it.title=="Opções" || (seniorMode && !seniorExpanded && it.title in essentialModules) ||
                (it.title !in hiddenModules &&
                    !(it.title=="Situação Clínica" && "Saúde Ocupacional" in hiddenModules) &&
                    (!seniorMode || seniorExpanded))
        }
'''
change(main,old3,new3,'senior essential modules always visible')

help=base/'SupportHelpActivity.kt'
replacements=[
    ('Em Acessibilidade ativa Modo Sénior para mostrar primeiro os módulos essenciais, com cartões e letras maiores.',
     'Em Opções → Acessibilidade escolhe «Ativar Modo Sénior» ou «Usar modo normal»; a seleção fica visível no próprio ecrã. No modo Sénior aparecem os módulos essenciais com cartões e letras maiores.'),
    ('Accessibility → Senior mode shows essential modules first with larger cards and text.',
     'Options → Accessibility offers always-visible Enable Senior mode / Normal mode choices. Senior mode shows essential modules first with larger cards and text.'),
    ('Accessibilité → Mode senior agrandit les cartes et le texte et affiche les modules essentiels en premier.',
     'Accessibilité → choisissez Activer le mode senior ou Mode normal directement à l’écran. Le mode senior affiche de plus grandes cartes et les modules essentiels.'),
    ('Barrierefreiheit → Seniorenmodus zeigt wichtige Module und größere Schaltflächen; alle Module bleiben erreichbar.',
     'Barrierefreiheit → Seniorenmodus aktivieren oder Normalmodus direkt auf dem Bildschirm wählen. Größere Karten zeigen die wichtigsten Module; alle Module bleiben erreichbar.'),
    ('Accesibilidad → Modo sénior muestra los módulos esenciales con texto y botones más grandes.',
     'Accesibilidad → elige Activar modo sénior o Modo normal directamente en pantalla. El modo sénior muestra los módulos esenciales con texto y botones más grandes.')
]
for i,(a,b) in enumerate(replacements): change(help,a,b,f'help language {i}')

build=root/'app/build.gradle.kts'
change(build,'versionCode = 67','versionCode = 68','version code')
change(build,'versionName = "1.9.57"','versionName = "1.9.58"','version name')
assert 'showSeniorSettings' not in main.read_text()
assert 'selectSeniorMode(true)' in main.read_text()
print('v1.9.58: senior mode choices inline, no modal; essential cards visible; Help updated in 5 languages')