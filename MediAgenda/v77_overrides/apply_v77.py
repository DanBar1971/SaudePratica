"""SaúdePrática v1.9.59: separate food-dish classifier, searchable corrections.
The Google AIY model is NOT an ingredient/allergen/calorie estimator.
"""
from pathlib import Path
root = Path('build-src/MediAgenda_Android_v1')
base = root/'app/src/main/java/com/mediagenda/app'
source = Path('MediAgenda/v77_overrides')

def change(path, old, new, label):
    text = path.read_text(encoding='utf8')
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'1.9.59 {label}: expected one match, found {count}')
    path.write_text(text.replace(old,new,1),encoding='utf8')

for name in ['MealAiActivity.kt','FoodDishClassifier.kt']:
    (base/name).write_text((source/name).read_text(encoding='utf8'),encoding='utf8')

assets=root/'app/src/main/assets'
assert (assets/'saude_food_v1.tflite').stat().st_size > 20_000_000, 'Food model missing'
assert (assets/'saude_food_labels.csv').stat().st_size > 30_000, 'Label map missing'

gradle=root/'app/build.gradle.kts'
change(gradle,'    implementation("com.google.mlkit:image-labeling:17.0.9")',
       '    implementation("com.google.mlkit:image-labeling:17.0.9")\n    implementation("org.tensorflow:tensorflow-lite:2.17.0")', 'Lite interpreter')
change(gradle,'versionCode = 68','versionCode = 69','version code')
change(gradle,'versionName = "1.9.58"','versionName = "1.9.59"','version name')

help=base/'SupportHelpActivity.kt'
changes=[
('O reconhecimento de alimentos funciona offline no telemóvel com o ML Kit, sem API, contas ou envio de fotografias. O modelo pode não distinguir todos os ingredientes: escolhe os alimentos, indica os gramas e confirma a estimativa de calorias antes de guardar.',
 'O modelo alimentar especializado identifica sugestões de pratos offline a partir da fotografia. Confirma a sugestão para indicar a porção; se necessário, procura alimentos pelo nome. A fotografia não permite identificar os ingredientes escondidos nem calcular as calorias sem porções e dados nutricionais.'),
('On-device ML Kit suggests food labels offline, without accounts or API keys. Select the actual foods, edit gram portions and review approximate calories; no photo is uploaded.',
 'A specialized offline food model suggests dish names automatically after a photo. Confirm a dish or search for ingredients by name; review gram portions and approximate calories. The model cannot infer hidden ingredients or allergens.'),
("ML Kit fonctionne hors ligne sur le téléphone, sans compte ni API. Sélectionnez les aliments, indiquez les grammes et vérifiez les calories estimées. Aucune photo n'est envoyée.",
 "Un modèle alimentaire spécialisé suggère des plats après la photo, hors ligne. Confirmez le plat ou recherchez les aliments par nom; vérifiez les portions et calories. Les ingrédients cachés ne sont pas identifiés."),
('ML Kit erkennt Lebensmittel offline auf dem Telefon, ohne Konto oder API. Bitte Lebensmittel und Portionsgrößen auswählen und die geschätzten Kalorien prüfen. Fotos werden nicht hochgeladen.',
 'Ein spezialisiertes Offline-Modell schlägt Gerichte auf Fotos vor. Gericht bestätigen oder Lebensmittel suchen; Portionsgrößen und Kalorien prüfen. Verborgene Zutaten werden nicht erkannt.'),
('ML Kit identifica posibles alimentos sin conexión ni claves API. Selecciona ingredientes, indica los gramos y revisa las calorías estimadas. Las fotos no se envían.',
 'Un modelo alimentario especializado propone platos al fotografiarlos, sin conexión. Confirma el plato o busca ingredientes por nombre, e indica los gramos. No puede conocer ingredientes ocultos ni calorías exactas.')
]
for n,(old,new) in enumerate(changes): change(help,old,new,f'help locale {n}')
print('v1.9.59: specialized Google food model + model labelmap bundled, auto suggestions, searchable correction, Help x5')