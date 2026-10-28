# SaúdePrática — Website oficial

Website público da aplicação Android **SaúdePrática** em português de Portugal.

**Website:** https://danbar1971.github.io/SaudePratica/

**Código e APKs da aplicação:** https://github.com/DanBar1971/AndroidAppDev

A página estática apresenta as funcionalidades da app e liga à APK mais recente através de `https://github.com/DanBar1971/AndroidAppDev/releases/latest/download/SaudePratica.apk`.

As três imagens de marca oficiais estão em `assets/` e foram recuperadas do repositório original. As demonstrações usam **dados fictícios**, não dados reais de saúde. O website não guarda nem recebe registos médicos. **Não colocar ficheiros de assinatura, chaves privadas, API keys ou dados de pacientes neste repositório público.**

## Publicação

Em **Settings → Pages → Build and deployment → Source**, selecionar **GitHub Actions**. O workflow `.github/workflows/pages.yml` publica o site sempre que estes ficheiros são alterados no ramo `main`. Não é necessário escolher templates nem um domínio próprio.

## Desenvolvimento Android

O código, as Releases e o sistema de atualizações continuam no repositório `DanBar1971/AndroidAppDev`; este repositório destina-se apenas ao website.
