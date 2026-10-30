from pathlib import Path
base=Path('build-src/MediAgenda_Android_v1/app')
code=base/'src/main/java/com/mediagenda/app'
main=(code/'MainActivity.kt').read_text()
help=(code/'SupportHelpActivity.kt').read_text()
lang=(code/'i18n/AppLanguage.kt').read_text()
gradle=(base/'build.gradle.kts').read_text()
assert 'BUY_ME_A_COFFEE_URL="https://buymeacoffee.com/danielbarr7"' in help
assert 'PAYPAL_URL="https://www.paypal.com/paypalme/djjindungo"' in help
assert main.index('"☕ Buy Me a Coffee (primeira opção)"')<main.index('"PayPal (alternativa)"')
assert 'setItems(supportOptions)' in main
assert 'SupportHelpActivity.BUY_ME_A_COFFEE_URL' in main
assert 'SupportHelpActivity.PAYPAL_URL' in main
assert 'a aplicação não exige 10 €' in main
assert 'Apoiar o autor ☕' in main
assert 'Uma cerveja' not in main
assert 'versionCode = 117' in gradle and 'versionName = "1.9.107"' in gradle
assert 'applicationId = "com.mediagenda.app.stable"' in gradle
assert 'Buy Me a Coffee ou PayPal · apoio opcional' in lang
print('SaúdePrática 1.9.107 support regression checks OK')