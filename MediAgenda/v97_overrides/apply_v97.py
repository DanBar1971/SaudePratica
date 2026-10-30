"""SaúdePrática v1.9.79: module Lares e Apoio à Terceira Idade.

Safe, profile-specific manual workflow for ERPI / SAD / Day Centre, ADSE monthly
invoice tracking, APATI defaults, and shared Digital Documents storage.
Do not claim auto submission, payment, or notifications in this iteration.
"""
from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"

def change(path,old,new,label):
    content=path.read_text(encoding="utf-8")
    count=content.count(old)
    if count != 1:
        raise RuntimeError(f"v97 {label}: expected unique anchor, got {count}")
    path.write_text(content.replace(old,new,1),encoding="utf-8")

activity=Path("MediAgenda/v97_overrides/CareHomeActivity.kt")
assert "class CareHomeActivity" in activity.read_text(encoding="utf-8")
(base/"CareHomeActivity.kt").write_text(activity.read_text(encoding="utf-8"),encoding="utf-8")

manifest=root/"app/src/main/AndroidManifest.xml"
change(manifest,
       '        <activity android:name=".ImportantShortcutsActivity" android:exported="false" />',
       '        <activity android:name=".ImportantShortcutsActivity" android:exported="false" />\n'
       '        <activity android:name=".CareHomeActivity" android:exported="false" />',
       "activity registration")

main=base/"MainActivity.kt"
change(main,
       '        "Despesas de Saúde","Atalhos Importantes"\n    )',
       '        "Despesas de Saúde","Atalhos Importantes","Lares e Apoio à Terceira Idade"\n    )',
       "dashboard module configurability")

change(main,
       '            DashboardModule("🔗", "Atalhos Importantes", "ADSE, CGA, IRS e outros links") {',
       '''            DashboardModule("🏡", "Lares e Apoio à Terceira Idade",
                "ERPI, Centro de Dia, SAD, faturas e ADSE") {
                startActivity(Intent(this,CareHomeActivity::class.java)
                    .putExtra(CareHomeActivity.EXTRA_PROFILE_ID,activeProfileId))
            },
            DashboardModule("🔗", "Atalhos Importantes", "ADSE, CGA, IRS e outros links") {''',
       "home entry")

help=base/"SupportHelpActivity.kt"
change(help,
       '        val shortcutGuide=panel()',
       '''        val careHomeGuide=panel()
        careHomeGuide.addView(text(tr(
            "🏡 Lares e Apoio à Terceira Idade",
            "🏡 Care homes and elder support",
            "🏡 Établissements et aide aux personnes âgées",
            "🏡 Pflegeheime und Seniorenhilfe",
            "🏡 Residencias y apoyo a mayores"),18f))
        careHomeGuide.addView(text(tr(
            "No início abre Lares, associa uma instituição ao perfil, escolhe ERPI, Apoio Domiciliário ou Centro de Dia, regista a mensalidade e importa a fatura PDF para Documentos Digitais. Os estados ADSE são manuais; nunca é submetido um pedido automaticamente.",
            "Open Care homes from Home, choose an institution and service, track monthly invoices and save PDFs in Digital Documents. ADSE submissions and reimbursement statuses must be confirmed manually.",
            "Ouvrez Maisons de retraite, choisissez un établissement, suivez les factures et enregistrez les PDF dans Documents numériques. Les états ADSE sont saisis manuellement.",
            "Unter Pflegeheime die Einrichtung wählen, Rechnungen erfassen und PDFs in Digitale Dokumente speichern. ADSE-Status wird manuell bestätigt.",
            "Abre Residencias, elige centro, registra facturas y guarda PDFs en Documentos digitales. Los estados ADSE se confirman manualmente."),14f,muted))
        addCard(parent,careHomeGuide)
        val shortcutGuide=panel()''',
       "help documentation")

gradle=root/"app/build.gradle.kts"
change(gradle,"versionCode = 88","versionCode = 89","new versionCode")
change(gradle,'versionName = "1.9.78"','versionName = "1.9.79"',"new versionName")
print("SaúdePrática 1.9.79: CareHomeActivity + profile-specific ADSE monthly records")
