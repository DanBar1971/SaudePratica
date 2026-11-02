# SaúdePrática — Android, Windows e iPhone (futuro)

Website público e repositório multiplataforma **SaúdePrática**, em português de Portugal. Android disponível, Windows experimental com instalador e iOS planeado.

**Continuidade do projeto:** [Estado atual, releases, builds e regras para os próximos chats](ESTADO_ATUAL.md). Consultar antes de iniciar novos trabalhos ou pedir novamente ficheiros e chaves.

## Descargas diretas

| Plataforma | Estado | Instalação |
| --- | --- | --- |
| **Android** | Disponível | [SaudePratica.apk — versão Android mais recente](https://github.com/DanBar1971/SaudePratica/releases/latest/download/SaudePratica.apk) |
| **Android (testes)** | **Experimental 1.9.127** | [**SaudePratica.apk — versão experimental assinada**](https://github.com/DanBar1971/SaudePratica/releases/download/v1.9.127-preview/SaudePratica.apk) |
| **Windows 10/11 (x64)** | **Experimental 0.7.2** | [**SaudePratica-Setup.exe — descarregar o instalador Windows**](https://github.com/DanBar1971/SaudePratica/releases/download/windows-v0.7.2-preview/SaudePratica-Setup.exe) |
| **iPhone / iOS** | Planeado | Ainda sem aplicação para descarregar |

Para Windows, consultar também a [release Windows específica](https://github.com/DanBar1971/SaudePratica/releases/tag/windows-v0.7.2-preview), e **não a lista genérica de releases Android/Windows**. A página oficial identifica sempre cada plataforma e a ligação do instalador. A versão Windows 0.7.2 permite backups .spbackup manuais com palavra-passe, mas ainda não sincroniza automaticamente com o Android; os avisos de Agenda já funcionam localmente no Windows com sessão iniciada, mas os alarmes de medicação continuam apenas no Android.

**Website:** https://danbar1971.github.io/SaudePratica/

**Código e APKs da aplicação:** https://github.com/DanBar1971/SaudePratica

A página apresenta as três plataformas. O download Android usa a última release estável; o Windows tem releases experimentais independentes e um instalador `SaudePratica-Setup.exe`. A APK mais recente encontra-se em `https://github.com/DanBar1971/SaudePratica/releases/latest/download/SaudePratica.apk`.

As três imagens de marca oficiais estão em `assets/` e foram recuperadas do repositório original. As demonstrações usam **dados fictícios**, não dados reais de saúde. O website não guarda nem recebe registos médicos. **Não colocar ficheiros de assinatura, chaves privadas, API keys ou dados de pacientes neste repositório público.**

## Publicação

Em **Settings → Pages → Build and deployment → Source**, selecionar **GitHub Actions**. O workflow `.github/workflows/pages.yml` publica o site sempre que estes ficheiros são alterados no ramo `main`. Não é necessário escolher templates nem um domínio próprio.

## Desenvolvimento multiplataforma

O projeto principal reúne o código-fonte Android em `MediAgenda/`, as 43 releases Android históricas, o website e as pastas `windows/`, `ios/` e `shared/`. O Windows tem uma primeira versão experimental com instalador; iPhone ainda não está disponível.

Todas as APKs Android de atualização devem conservar o **certificado original** e ser verificadas antes da release. Não guardar chaves privadas, passwords ou códigos de recuperação neste repositório público. A pré-visualização 1.9.127 foi reconstruída e publicada com delta público sem segredos.
