from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1')
base=root/'app/src/main/java/com/mediagenda/app'
src=Path('MediAgenda/v74_overrides')

def change(path,old,new,label):
    s=path.read_text(encoding='utf-8')
    n=s.count(old)
    if n!=1: raise RuntimeError(f'v1.9.56 {label}: expected 1 anchor, got {n}')
    path.write_text(s.replace(old,new,1),encoding='utf-8')

(base/'MealAiActivity.kt').write_text((src/'MealAiActivity.kt').read_text(encoding='utf-8'),encoding='utf-8')
gradle=root/'app/build.gradle.kts'
change(gradle,'    implementation("com.google.mlkit:barcode-scanning:17.3.0")',
    '    implementation("com.google.mlkit:barcode-scanning:17.3.0")\n    implementation("com.google.mlkit:image-labeling:17.0.9")',
    'bundle offline image classifier')
change(gradle,'versionCode = 65','versionCode = 66','version code')
change(gradle,'versionName = "1.9.55"','versionName = "1.9.56"','version name')
help=base/'SupportHelpActivity.kt'
change(help,
    'A análise por IA será disponibilizada através do serviço central da SaúdePrática, sem chaves ou configurações individuais; confirma sempre porções e calorias antes de guardar. A fotografia só sai do telemóvel com a tua confirmação.',
    'O reconhecimento de alimentos funciona offline no telemóvel com o ML Kit, sem API, contas ou envio de fotografias. O modelo pode não distinguir todos os ingredientes: escolhe os alimentos, indica os gramas e confirma a estimativa de calorias antes de guardar.',
    'help PT')
change(help,
    'AI uses the central SaúdePrática service; no individual API setup is needed. Always review estimated portions and calories.',
    'On-device ML Kit suggests food labels offline, without accounts or API keys. Select the actual foods, edit gram portions and review approximate calories; no photo is uploaded.',
    'help EN')
change(help,
    "L'IA utilise le service central de SaúdePrática, sans configuration individuelle. Vérifiez toujours les quantités et calories estimées.",
    "ML Kit fonctionne hors ligne sur le téléphone, sans compte ni API. Sélectionnez les aliments, indiquez les grammes et vérifiez les calories estimées. Aucune photo n'est envoyée.",
    'help FR')
change(help,
    'Die KI verwendet den zentralen SaúdePrática-Dienst, ohne individuelle API-Einrichtung. Bitte die geschätzten Mengen prüfen.',
    'ML Kit erkennt Lebensmittel offline auf dem Telefon, ohne Konto oder API. Bitte Lebensmittel und Portionsgrößen auswählen und die geschätzten Kalorien prüfen. Fotos werden nicht hochgeladen.',
    'help DE')
change(help,
    'La IA utiliza el servicio central de SaúdePrática, sin configurar claves individuales. Comprueba siempre porciones y calorías.',
    'ML Kit identifica posibles alimentos sin conexión ni claves API. Selecciona ingredientes, indica los gramos y revisa las calorías estimadas. Las fotos no se envían.',
    'help ES')
print('v1.9.56: on-device ML Kit 17.0.9 image labeling and local food nutrition estimates; no API/server; Help updated 5 languages')