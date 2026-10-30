from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1')
base=root/'app/src/main/java/com/mediagenda/app'
source=Path('MediAgenda/v72_overrides')

def replace(path,old,new,title):
    data=path.read_text(encoding='utf-8')
    count=data.count(old)
    if count!=1: raise RuntimeError(f'v1.9.54 {title}: expected 1 match; found {count}')
    path.write_text(data.replace(old,new,1),encoding='utf-8')

(base/'MealAiActivity.kt').write_text((source/'MealAiActivity.kt').read_text(encoding='utf-8'),encoding='utf-8')
wellness=base/'WellnessActivity.kt'
replace(wellness,
'''    private fun showDiet() {
        heading("🥗", "Nutrição e Regime", "Indicações de um profissional de saúde")
        val items = listOf(''',
'''    private fun showDiet() {
        heading("🥗", "Nutrição", "Plano alimentar e diário de refeições")
        card(content, "📷 Refeições · Fotografia e calorias",
            "Fotografa o prato ou escolhe uma imagem. A IA pode estimar porções e nutrientes; confere todos os valores antes de guardar. Também podes registar manualmente.",
            "🍽️ Fotografar ou registar refeição") {
            startActivity(Intent(this,MealAiActivity::class.java)
                .putExtra(MealAiActivity.EXTRA_PROFILE_ID,profileId))
        }
        val items = listOf(''', 'nutrition entry')

main=base/'MainActivity.kt'
replace(main,'DashboardModule("🥗", "Nutrição", "Plano alimentar e restrições")',
            'DashboardModule("🥗", "Nutrição", "Planos e diário de refeições")', 'dashboard subtitle')
manifest=root/'app/src/main/AndroidManifest.xml'
replace(manifest,'        <activity android:name=".WellnessActivity" android:exported="false" />',
        '        <activity android:name=".WellnessActivity" android:exported="false" />\n        <activity android:name=".MealAiActivity" android:exported="false" />', 'manifest activity')

help=base/'SupportHelpActivity.kt'
replace(help,
'''        parent.addView(text(tr("Aprende em sete passos, com imagens simples.",
            "Learn in seven illustrated steps.","Apprenez en sept étapes illustrées.",
            "Lernen Sie in sieben bebilderten Schritten.",
            "Aprende en siete pasos con imágenes sencillas."),14f,muted))''',
'''        parent.addView(text(tr("Aprende em oito passos, com imagens simples.",
            "Learn in eight illustrated steps.","Apprenez en huit étapes illustrées.",
            "Lernen Sie in acht bebilderten Schritten.",
            "Aprende en ocho pasos con imágenes sencillas."),14f,muted))''','help steps count')
replace(help,
'''            Step(R.drawable.guide_support,
                arrayOf("7. Ajuda e segurança","7. Help and security","7. Aide et sécurité","7. Hilfe und Sicherheit","7. Ayuda y seguridad"),''',
'''            Step(R.drawable.guide_home,
                arrayOf("7. Nutrição e refeições", "7. Nutrition and meals", "7. Nutrition et repas", "7. Ernährung und Mahlzeiten", "7. Nutrición y comidas"),
                arrayOf("Em Nutrição, consulta o plano alimentar e abre Fotografar ou registar refeição. Podes fotografar, escolher uma imagem ou introduzir dados manualmente. A análise por IA exige um serviço privado HTTPS configurado; confirma sempre porções e calorias antes de guardar. A fotografia só sai do telemóvel com a tua confirmação.",
                    "In Nutrition, open Photograph or record meal. You can take a photo, choose an image or enter meals manually. AI needs a configured private HTTPS service. Always check estimated portions and calories.",
                    "Dans Nutrition, photographiez un repas ou saisissez-le manuellement. L'IA requiert un service HTTPS privé configuré. Vérifiez toujours les quantités et calories estimées.",
                    "Unter Ernährung kannst du Mahlzeiten fotografieren oder manuell eintragen. Die KI benötigt einen konfigurierten privaten HTTPS-Dienst. Bitte die geschätzten Mengen prüfen.",
                    "En Nutrición puedes fotografiar comidas o registrarlas manualmente. La IA requiere un servicio HTTPS privado configurado. Comprueba siempre porciones y calorías.")),
            Step(R.drawable.guide_support,
                arrayOf("8. Ajuda e segurança","8. Help and security","8. Aide et sécurité","8. Hilfe und Sicherheit","8. Ayuda y seguridad"),''', 'nutrition help new step')

build=root/'app/build.gradle.kts'
replace(build,'versionCode = 63','versionCode = 64','version code')
replace(build,'versionName = "1.9.53"','versionName = "1.9.54"','version name')
print('v1.9.54: meal photo, private optional AI service, per-profile diary, manual correction and updated Help')