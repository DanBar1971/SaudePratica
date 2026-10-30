from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1')
base=root/'app/src/main/java/com/mediagenda/app'
source=Path('MediAgenda/v73_overrides')

def change(path, old, new, label):
    s=path.read_text(encoding='utf-8')
    n=s.count(old)
    if n!=1: raise RuntimeError(f'v1.9.55 {label}: expected 1 anchor, found {n}')
    path.write_text(s.replace(old,new,1),encoding='utf-8')

(base/'MealAiActivity.kt').write_text((source/'MealAiActivity.kt').read_text(encoding='utf-8'),encoding='utf-8')
help=base/'SupportHelpActivity.kt'
change(help,
    'A análise por IA exige um serviço privado HTTPS configurado; confirma sempre porções e calorias antes de guardar.',
    'A análise por IA será disponibilizada através do serviço central da SaúdePrática, sem chaves ou configurações individuais; confirma sempre porções e calorias antes de guardar.',
    'help PT')
change(help,
    'AI needs a configured private HTTPS service. Always check estimated portions and calories.',
    'AI uses the central SaúdePrática service; no individual API setup is needed. Always review estimated portions and calories.',
    'help EN')
change(help,
    "L'IA requiert un service HTTPS privé configuré. Vérifiez toujours les quantités et calories estimées.",
    "L'IA utilise le service central de SaúdePrática, sans configuration individuelle. Vérifiez toujours les quantités et calories estimées.",
    'help FR')
change(help,
    'Die KI benötigt einen konfigurierten privaten HTTPS-Dienst. Bitte die geschätzten Mengen prüfen.',
    'Die KI verwendet den zentralen SaúdePrática-Dienst, ohne individuelle API-Einrichtung. Bitte die geschätzten Mengen prüfen.',
    'help DE')
change(help,
    'La IA requiere un servicio HTTPS privado configurado. Comprueba siempre porciones y calorías.',
    'La IA utiliza el servicio central de SaúdePrática, sin configurar claves individuales. Comprueba siempre porciones y calorías.',
    'help ES')
gradle=root/'app/build.gradle.kts'
change(gradle,'versionCode = 64','versionCode = 65','version code')
change(gradle,'versionName = "1.9.54"','versionName = "1.9.55"','version name')
print('v1.9.55: central AI discovery, no end-user token/key fields, updated five-language help')