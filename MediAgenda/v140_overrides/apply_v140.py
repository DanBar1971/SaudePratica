#!/usr/bin/env python3
"""SaúdePrática v1.9.120: phased Atalhos, Ajuda and Diabetes MVP.

Runs after v139. Do not change signing, package identity, alarm scheduling,
clinical guidance or any previously stored medication/profile records.
"""
from pathlib import Path
from shutil import copyfile
import re

APP=Path("build-src/MediAgenda_Android_v1/app")
SRC=APP/"src/main/java/com/mediagenda/app"
PATCH=Path("MediAgenda/v140_overrides")

def replace_once(path, old, new, label):
    s=path.read_text(encoding="utf-8")
    n=s.count(old)
    if n!=1:
        raise AssertionError(f"{label}: expected one anchor, got {n}")
    path.write_text(s.replace(old,new,1),encoding="utf-8")

for filename in ("DiabetesActivity.kt","ImportantShortcutsV2Activity.kt"):
    copyfile(PATCH/filename,SRC/filename)

# Dashboard: move official SNS 24 and IPO Lisboa app launches to Atalhos
# Important and add a Diabetes card for the selected profile.
main=SRC/"MainActivity.kt"
s=main.read_text(encoding="utf-8")
for name in ("SNS 24","IPO Lisboa"):
    pattern=r'(?m)^[ \t]*DashboardModule\([^\n]*"'+re.escape(name)+r'"[^\n]*\n'
    s,n=re.subn(pattern,"",s)
    assert n==1,(name,"dashboard card",n)
# Remove old Home customization entries and keep all other module prefs.
s,n=re.subn(r'"SNS 24"\s*,\s*"IPO Lisboa"\s*,','"Diabetes",',s)
assert n==1,("dashboard checklist labels",n)
anchor='            DashboardModule("👓", "Saúde Visual",'
assert s.count(anchor)==1,("main diabetes anchor",s.count(anchor))
s=s.replace(anchor,'''            DashboardModule("🩸", "Diabetes",
                "Glicemia, HbA1c e evolução") {
                startActivity(Intent(this,DiabetesActivity::class.java)
                    .putExtra(DiabetesActivity.EXTRA_PROFILE_ID,activeProfileId))
            },
'''+anchor,1)

# Keep existing shortcuts untouched; add the new explicit app/website manager.
# Existing legacy shortcuts remain stored, and can be migrated separately.
option_anchor='        box.addView(infoCard("💡", "Dicas e Informações",'
assert s.count(option_anchor)==1,("options anchor",s.count(option_anchor))
s=s.replace(option_anchor,'''        box.addView(infoCard("🔗", "Atalhos Importantes · Apps e Web",
            "Escolher aplicações instaladas ou endereços web") {
            startActivity(Intent(this,ImportantShortcutsV2Activity::class.java))
        })
        box.addView(infoCard("🌍", "Página oficial da SaúdePrática",
            "Abrir ou partilhar o link da aplicação") {
            val official="https://danbar1971.github.io/SaudePratica/"
            MaterialAlertDialogBuilder(this)
                .setTitle("SaúdePrática · Website")
                .setItems(arrayOf("Abrir página oficial","Partilhar página")){_,chosen->
                    if(chosen==0)startActivity(Intent(Intent.ACTION_VIEW,Uri.parse(official)))
                    else startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).apply{
                        type="text/plain";putExtra(Intent.EXTRA_TEXT,official)
                    },"Partilhar SaúdePrática"))
                }.setNegativeButton("Cancelar",null).show()
        })
'''+option_anchor,1)

# Move the existing Senior Mode entry INTO Aspect and Language without
# creating a second setting or changing the original preference.
senior='''        box.addView(infoCard("🧓", "Acessibilidade · Modo Sénior",
            if(seniorMode) "Ativo · letras e botões maiores no ecrã inicial" else "Ativar uma utilização mais simples e legível") {
            showOptionsGroup("acessibilidade")
        })
'''
assert s.count(senior)==1,("senior entry",s.count(senior))
s=s.replace(senior,"",1)
theme='        box.addView(infoCard("◐", "Aspeto da aplicação",'
assert s.count(theme)==1,("theme entry",s.count(theme))
s=s.replace(theme,senior+theme,1)

# Reuse the sole existing Atalhos location, now opening the Apps/Web manager.
# Legacy data is imported by that manager the first time it opens.
legacy='''        box.addView(infoCard("🔗", "Atalhos Importantes",
            "Adicionar, editar e apagar links web · ADSE, CGA, IRS e APATI") {
            startActivity(Intent(this,ImportantShortcutsActivity::class.java)
                .putExtra(ImportantShortcutsActivity.EXTRA_MANAGE,true))
        })'''
assert s.count(legacy)==1,("legacy options card",s.count(legacy))
s=s.replace(legacy,'''        box.addView(infoCard("🔗", "Atalhos Importantes",
            "Aplicações instaladas e websites · organizar atalhos") {
            startActivity(Intent(this,ImportantShortcutsV2Activity::class.java))
        })''',1)
# Home also opens the new manager; old activity remains available for
# rollback and its original preferences are not overwritten.
s=s.replace('Intent(this,ImportantShortcutsActivity::class.java)',
            'Intent(this,ImportantShortcutsV2Activity::class.java)')
# Do not display a second shortcuts entry in Help/Information.
extra='''        box.addView(infoCard("🔗", "Atalhos Importantes · Apps e Web",
            "Escolher aplicações instaladas ou endereços web") {
            startActivity(Intent(this,ImportantShortcutsV2Activity::class.java))
        })
'''
assert s.count(extra)==1,("duplicate shortcuts menu",s.count(extra))
s=s.replace(extra,"",1)

# The existing About information and all other options are preserved.
main.write_text(s,encoding="utf-8")

# Android 11+ app visibility: query launcher apps without QUERY_ALL_PACKAGES.
manifest=APP/"src/main/AndroidManifest.xml"
m=manifest.read_text(encoding="utf-8")
activities='''        <activity android:name="com.mediagenda.app.DiabetesActivity"
            android:exported="false" />
        <activity android:name="com.mediagenda.app.ImportantShortcutsV2Activity"
            android:exported="false" />
'''
assert m.count("</application>")==1
m=m.replace("</application>",activities+"    </application>",1)
query='''        <intent>
            <action android:name="android.intent.action.MAIN" />
            <category android:name="android.intent.category.LAUNCHER" />
        </intent>
'''
if "<queries>" in m:
    m=m.replace("<queries>","<queries>\n"+query,1)
else:
    assert m.count("<application")==1
    m=m.replace("<application","<queries>\n"+query+"    </queries>\n    <application",1)
manifest.write_text(m,encoding="utf-8")

# Update the detailed, five-language offline Help guide.
helpfile=SRC/"SupportHelpActivity.kt"
h=helpfile.read_text(encoding="utf-8")
help_anchor="        val shortcutGuide=panel()"
assert h.count(help_anchor)==1,("help chapter",h.count(help_anchor))
h=h.replace(help_anchor,'''        val diabetesGuide=panel()
        diabetesGuide.addView(text(tr(
            "🩸 Diabetes · Diário por perfil",
            "🩸 Diabetes · Diary by profile",
            "🩸 Diabète · Journal par profil",
            "🩸 Diabetes · Tagebuch pro Profil",
            "🩸 Diabetes · Diario por perfil"),18f))
        diabetesGuide.addView(text(tr(
            "No Início abre Diabetes e escolhe Registar glicemia ou Registar HbA1c. Indica valor, unidade, data e contexto. Consulta o gráfico de 30 dias e partilha o CSV. Premir um registo continuamente permite eliminá-lo. Não mede açúcar pela câmara, não calcula doses de insulina e ainda não sincroniza estes registos.",
            "From Home, open Diabetes and enter blood glucose or laboratory HbA1c. Check units, date and context, review the 30-day chart and share the CSV. Long-press a reading to delete. No camera glucose measurement, insulin calculator or diary sync yet.",
            "Accueil → Diabète : saisissez glycémie ou HbA1c, unité, date et contexte. Graphique sur 30 jours et partage CSV. Appui long pour supprimer. Aucun dosage automatique d'insuline ni synchronisation.",
            "Start → Diabetes: Blutzucker oder Labor-HbA1c mit Einheit, Zeit und Kontext eingeben. 30-Tage-Grafik und CSV. Langes Tippen löscht. Keine automatische Insulindosis oder Synchronisierung.",
            "Inicio → Diabetes: registra glucosa o HbA1c, unidad, fecha y contexto. Gráfico de 30 días y CSV. Mantén pulsado para borrar. Sin cálculo de insulina ni sincronización."),13f))
        addCard(parent,diabetesGuide)
        val linksGuide=panel()
        linksGuide.addView(text(tr(
            "🔗 Atalhos Importantes",
            "🔗 Important shortcuts",
            "🔗 Raccourcis importants",
            "🔗 Wichtige Verknüpfungen",
            "🔗 Accesos importantes"),18f))
        linksGuide.addView(text(tr(
            "Em Mais → Atalhos Importantes · Apps e Web, adiciona uma aplicação instalada ou um website. Podes editar, eliminar ou mover atalhos. SNS 24 e IPO Lisboa estão disponíveis no início da lista. A página oficial pode ser aberta ou partilhada em Mais.",
            "In More → Important shortcuts, select installed apps or websites, reorder and edit them. SNS 24 and IPO Lisboa are listed initially. Open/share the official website from More.",
            "Plus → Raccourcis importants : choisissez des applications ou sites, puis réorganisez-les. SNS 24 et IPO Lisboa sont proposés.",
            "Mehr → Wichtige Verknüpfungen: Apps oder Webseiten wählen und sortieren. SNS 24 und IPO Lisboa sind vorausgewählt.",
            "Más → Accesos importantes: elige apps o webs y ordénalos. SNS 24 e IPO Lisboa aparecen de inicio."),13f))
        addCard(parent,linksGuide)
'''+help_anchor,1)
helpfile.write_text(h,encoding="utf-8")

# Expand Smart Help offline Q&A without sending medical data or making diagnoses.
smart=SRC/"SmartHelpActivity.kt"
s=smart.read_text(encoding="utf-8")
quick_anchor='        quick(text("Como sincronizar os telemóveis?"'
assert s.count(quick_anchor)==1
s=s.replace(quick_anchor,'''        quick(text("Como registar a glicemia?","How to log glucose?",
            "Comment noter la glycémie ?","Wie Blutzucker eintragen?",
            "¿Cómo registrar glucosa?"))
        quick(text("Como criar um atalho de aplicação?","How to add an app shortcut?",
            "Créer un raccourci d'app ?","App-Verknüpfung erstellen?",
            "¿Cómo añadir acceso a una app?"))
'''+quick_anchor,1)
response_anchor='        val response=when {\n'
assert s.count(response_anchor)==1
s=s.replace(response_anchor,response_anchor+'''            listOf("glic","diabet","glucos","blutzucker","hba1c").any{q.contains(it)}->text(
                "No menu Início escolhe Diabetes → Registar glicemia. Indica a unidade correta (mg/dL ou mmol/L), data e relação com a refeição. Há histórico e CSV. A HbA1c é um resultado de laboratório separado. Para hipoglicemia segue o teu plano clínico e não dependas dos avisos desta app.",
                "Home → Diabetes → Log glucose. Select the correct units, date and meal context. View history or share CSV. HbA1c is a separate laboratory result. Follow your medical emergency plan.",
                "Accueil → Diabète : saisissez valeur, unité, date et repas. Journal et CSV ; HbA1c est séparée. Suivez le protocole médical.",
                "Start → Diabetes: Wert, Einheit, Zeit und Mahlzeit eintragen. Verlauf und CSV; HbA1c ist getrennt. Persönlichen Notfallplan beachten.",
                "Inicio → Diabetes: registra valor, unidad, fecha y comida. Historial y CSV; HbA1c por separado. Sigue tu plan médico.")
            listOf("atalho","shortcut","raccourci","verknupf","acceso directo").any{q.contains(it)}->text(
                "Em Mais → Atalhos Importantes · Apps e Web, escolhe + Atalho de aplicação para ver as apps instaladas ou + Atalho de website para guardar um endereço. Usa ⋮ para organizar, editar ou eliminar.",
                "More → Important shortcuts → Add app or Add website. Tap ⋮ to move, edit or remove.",
                "Plus → Raccourcis importants : ajouter une app ou un site. Menu ⋮ pour organiser.",
                "Mehr → Wichtige Verknüpfungen: App oder Website hinzufügen. Menü ⋮ zum Sortieren.",
                "Más → Accesos importantes: añade una app o web y organiza con ⋮.")
            listOf("nutric","alimen","calori","carbo","hidrato","food","aliment","nahrung").any{q.contains(it)}->text(
                "No módulo Nutrição regista a refeição e confirma manualmente os ingredientes, porções e valores estimados. Uma fotografia ou IA pode errar. Para gerir diabetes, verifica especialmente os hidratos de carbono; o catálogo português PortFIR ainda está em integração.",
                "In Nutrition, check ingredients, servings and AI estimates manually. For diabetes review carbohydrates. The PortFIR food database integration is planned.",
                "Dans Nutrition, vérifiez ingrédients, portions et estimations IA. Pour le diabète, vérifiez les glucides. PortFIR est en préparation.",
                "Bei Ernährung Zutaten, Portionen und KI-Schätzungen prüfen. Kohlenhydrate kontrollieren; PortFIR folgt.",
                "En Nutrición revisa ingredientes, porciones y estimaciones de IA. Comprueba hidratos; PortFIR está pendiente.")
''',1)
smart.write_text(s,encoding="utf-8")

gradle=APP/"build.gradle.kts"
replace_once(gradle,"versionCode = 129","versionCode = 130","versionCode")
replace_once(gradle,'versionName = "1.9.119"','versionName = "1.9.120"',"versionName")
print("v1.9.120: Android Diabetes diary, shortcut picker, dashboard and bilingual-safe Help; alarm engine untouched.")
