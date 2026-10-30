# SaúdePrática — Android, Windows e iPhone (futuro)

Website público e repositório multiplataforma **SaúdePrática**, em português de Portugal. Android disponível, Windows experimental com instalador e iOS planeado.

**Website:** https://danbar1971.github.io/SaudePratica/

**Código e APKs da aplicação:** https://github.com/DanBar1971/SaudePratica

A página apresenta as três plataformas. O download Android usa a última release estável; o Windows tem releases experimentais independentes e um instalador `SaudePratica-Setup.exe`. A APK mais recente encontra-se em `https://github.com/DanBar1971/SaudePratica/releases/latest/download/SaudePratica.apk`.

As três imagens de marca oficiais estão em `assets/` e foram recuperadas do repositório original. As demonstrações usam **dados fictícios**, não dados reais de saúde. O website não guarda nem recebe registos médicos. **Não colocar ficheiros de assinatura, chaves privadas, API keys ou dados de pacientes neste repositório público.**

## Publicação

Em **Settings → Pages → Build and deployment → Source**, selecionar **GitHub Actions**. O workflow `.github/workflows/pages.yml` publica o site sempre que estes ficheiros são alterados no ramo `main`. Não é necessário escolher templates nem um domínio próprio.

## Desenvolvimento multiplataforma

O projeto principal reúne o código-fonte Android em `MediAgenda/`, as 43 releases Android históricas, o website e as pastas `windows/`, `ios/` e `shared/`. O Windows tem uma primeira versão experimental com instalador; iPhone ainda não está disponível.

O processo de assinatura Android depende do mesmo certificado original e de um segredo configurado neste repositório. Não criar outra identidade de assinatura.
