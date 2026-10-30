#!/usr/bin/env python3
"""SaúdePrática v1.9.107: Buy Me a Coffee first, PayPal second, no fixed donation.
Runs after v126. Keeps profile data, signing identity and medical records intact.
"""
from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1/app')
base=root/'src/main/java/com/mediagenda/app'

def once(path,old,new,label):
    s=path.read_text(encoding='utf-8')
    count=s.count(old)
    assert count==1,(label,count)
    path.write_text(s.replace(old,new,1),encoding='utf-8')

support=base/'SupportHelpActivity.kt'
once(support,
'        const val PAYPAL_URL="https://www.paypal.com/paypalme/djjindungo"',
'''        const val PAYPAL_URL="https://www.paypal.com/paypalme/djjindungo"
        const val BUY_ME_A_COFFEE_URL="https://buymeacoffee.com/danielbarr7"''',
'official support URL')

main=base/'MainActivity.kt'
old='''        box.addView(infoCard("☕", "Apoiar o autor ☕",
            "Oferecer um café via PayPal (opcional)") {
            MaterialAlertDialogBuilder(this)
                .setTitle("☕ Apoiar o autor")
                .setMessage("Se gostas da SaúdePrática, podes oferecer uma "+
                    "café ao autor. É totalmente opcional e não altera "+
                    "as funcionalidades da aplicação. O PayPal abre fora da app.")
                .setPositiveButton("Abrir PayPal"){_,_->
                    runCatching{
                        startActivity(Intent(Intent.ACTION_VIEW,Uri.parse(
                            SupportHelpActivity.PAYPAL_URL)))
                    }.onFailure { showError("Não foi possível abrir o PayPal.") }
                }
                .setNegativeButton("Cancelar",null).show()
        })'''
new='''        box.addView(infoCard("☕", "Apoiar o autor ☕",
            "Buy Me a Coffee ou PayPal · apoio opcional") {
            // Support is always voluntary and no price (in particular no €10)
            // is passed to either provider. The provider's checkout owns the
            // amount, currency, payment and confirmation screens.
            val supportOptions=arrayOf(
                AppLanguage.t(this,"☕ Buy Me a Coffee (primeira opção)"),
                AppLanguage.t(this,"PayPal (alternativa)")
            )
            MaterialAlertDialogBuilder(this)
                .setTitle(AppLanguage.t(this,"☕ Apoiar o autor"))
                .setMessage(AppLanguage.t(this,
                    "Apoia a SaúdePrática se quiseres. Escolhe o valor na página de pagamento; a aplicação não exige 10 € nem faz pagamentos automaticamente."))
                .setItems(supportOptions){_,which->
                    val target=if(which==0)SupportHelpActivity.BUY_ME_A_COFFEE_URL
                        else SupportHelpActivity.PAYPAL_URL
                    // Always open the genuine external provider; never collect
                    // payment details inside SaúdePrática.
                    runCatching{
                        startActivity(Intent(Intent.ACTION_VIEW,Uri.parse(target)))
                    }.onFailure {
                        showError(AppLanguage.t(this,"Não foi possível abrir a página de apoio."))
                    }
                }
                .setNegativeButton(AppLanguage.t(this,"Cancelar"),null)
                .show()
        })'''
once(main,old,new,'two support providers, with BMC first')

lang=base/'i18n/AppLanguage.kt'
entries='''Buy Me a Coffee ou PayPal · apoio opcional	Buy Me a Coffee or PayPal · optional support	Buy Me a Coffee ou PayPal · soutien facultatif	Buy Me a Coffee oder PayPal · freiwillige Unterstützung	Buy Me a Coffee o PayPal · apoyo opcional
☕ Apoiar o autor	☕ Support the author	☕ Soutenir l’auteur	☕ Autor unterstützen	☕ Apoyar al autor
☕ Buy Me a Coffee (primeira opção)	☕ Buy Me a Coffee (recommended first)	☕ Buy Me a Coffee (première option)	☕ Buy Me a Coffee (erste Option)	☕ Buy Me a Coffee (primera opción)
PayPal (alternativa)	PayPal (alternative)	PayPal (alternative)	PayPal (Alternative)	PayPal (alternativa)
Apoia a SaúdePrática se quiseres. Escolhe o valor na página de pagamento; a aplicação não exige 10 € nem faz pagamentos automaticamente.	Support SaúdePrática if you wish. Choose the amount on the payment page; the app does not require €10 or make automatic payments.	Soutenez SaúdePrática si vous le souhaitez. Choisissez le montant sur la page de paiement ; l’application n’impose pas 10 € et n’effectue aucun paiement automatique.	Unterstütze SaúdePrática freiwillig. Wähle den Betrag auf der Zahlungsseite; die App verlangt keine 10 € und tätigt keine automatischen Zahlungen.	Apoya SaúdePrática si lo deseas. Elige el importe en la página de pago; la aplicación no exige 10 € ni realiza pagos automáticos.
Não foi possível abrir a página de apoio.	Could not open the support page.	Impossible d’ouvrir la page de soutien.	Die Unterstützungsseite konnte nicht geöffnet werden.	No se pudo abrir la página de apoyo.
'''
s=lang.read_text(encoding='utf-8')
anchor='    private val source="""\n'
assert s.count(anchor)==1
# Every row is Portuguese + English + French + German + Spanish.
assert all(len(line.split('\t'))==5 for line in entries.splitlines())
s=s.replace(anchor,anchor+entries,1)
lang.write_text(s,encoding='utf-8')

gradle=root/'build.gradle.kts'
g=gradle.read_text(encoding='utf-8')
assert g.count('versionCode = 116')==1
assert g.count('versionName = "1.9.106"')==1
gradle.write_text(g.replace('versionCode = 116','versionCode = 117')
    .replace('versionName = "1.9.106"','versionName = "1.9.107"'),encoding='utf-8')
print('SaúdePrática 1.9.107: first Buy Me a Coffee, then PayPal, no 10€ preset, five languages.')