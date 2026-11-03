# SaúdePrática — Android, Windows e iPhone (futuro)

Website público e repositório multiplataforma **SaúdePrática**, em português de Portugal. Android disponível, Windows experimental com instalador e iOS planeado.

**Continuidade do projeto:** [Estado atual, releases, builds e regras para os próximos chats](ESTADO_ATUAL.md). Consultar antes de iniciar novos trabalhos ou pedir novamente ficheiros e chaves.

## Descargas diretas

| Plataforma | Estado | Instalação |
| --- | --- | --- |
| **Android v1.9.132** | Atualização normal | [SaudePratica.apk — versão Android mais recente](https://github.com/DanBar1971/SaudePratica/releases/latest/download/SaudePratica.apk) |
| **Windows 10/11 (x64)** | **Experimental 0.8.12** | [**SaudePratica-Setup.exe — descarregar o instalador Windows**](https://github.com/DanBar1971/SaudePratica/releases/download/windows-v0.8.12-preview/SaudePratica-Setup.exe) |
| **iPhone / iOS** | Planeado | Ainda sem aplicação para descarregar |

Para Windows, consultar também a [release Windows específica](https://github.com/DanBar1971/SaudePratica/releases/tag/windows-v0.8.12-preview), e **não a lista genérica de releases Android/Windows**. A página oficial identifica sempre cada plataforma e a ligação do instalador. A versão Windows 0.8.12 melhora a descoberta automática da app SaúdePrática Android principal (desde 1.9.132) por mDNS e UDP broadcast, com procura repetida e verificação HTTP do protocolo; continua a aceitar ligação por IP. Mantém a recuperação de SOS Emergência e Lares/Apoios do backup Android e a pesquisa de Farmácias de Serviço. Mantém os módulos Windows anteriores, incluindo Nutrição com importação de refeições e fotografias originais Android. Mantém Hidratação, Atividade e Saúde e Ciclo Menstrual com históricos por perfil. Mantém Situação Clínica e Despesas de Saúde, ambos com registos por perfil, anexos existentes, estados manuais, resumos e exportação CSV nas despesas. Mantém Calendário e Documentos em dois painéis, com marcações compactas e pré-visualização PDF/imagem e impressão, move Dicas/Backup/Sincronização para Opções e acrescenta um gestor de atalhos Web (inclui SNS 24 e IPO Lisboa). Mantém Tomas com leitura isolada por perfil e registo explícito de tomas, e mantém descoberta automática de um Android na mesma rede Wi-Fi, convite para ligar e confirmação por código no telemóvel, com ligação por IP alternativa. Esta primeira etapa é apenas um teste de comunicação, sem dados clínicos. A partir da Android 1.9.132, a descoberta e autorização do Windows estão na SaúdePrática principal em Backups e sincronização → Ligação Windows · Wi-Fi (teste), sem APK auxiliar. Mantém os botões e separadores mais uniformes a vários módulos, inclui setas de cinco minutos, listas editáveis para condições e repetições e aumenta a fotografia da embalagem. Também corrige horas duplicadas na medicação e mantém o cartão e a próxima toma coerentes. Permite escolher explicitamente uma hora anterior divergente; isto não altera alarmes Android. Mantém formulários compactos em separadores, com PDF/imagem e OCR local lado a lado, sugestões sujeitas a confirmação e campos técnicos ocultos. Mantém a ficha de medicação editável, incluindo prescrição, repetições, informação clínica, bula e documentos associados ao perfil. Corrige também o arranque antigo dos avisos. Mantém «ABRIR ❯» nos cartões de perfil, loading animado durante a leitura das fotografias, maximização ao arrancar, splash sem sobreposição e fotografias recuperadas da medicação e detalhes adicionais do registo Android em consulta. Também mostra corretamente os estados de suspensão e as horas dos avisos da medicação Android, agora separados do tipo de toma. O agente de Agenda tem ícone oficial e não abre splash; o menu do botão direito foi corrigido e validado com um clique real em «Sair dos avisos». Mantém a ficha Android completa, fotografias reais do CC e carregamento rápido dos perfis. Mantém o progresso dos backups e a atualização sem bloqueio pelo agente de avisos. Continua a permitir backups .spbackup manuais com palavra-passe, mas ainda não sincroniza automaticamente com o Android; os avisos de Agenda já funcionam localmente no Windows com sessão iniciada, mas os alarmes de medicação continuam apenas no Android.

**Website:** https://danbar1971.github.io/SaudePratica/

**Código e APKs da aplicação:** https://github.com/DanBar1971/SaudePratica

A página apresenta as três plataformas. O download Android usa sempre a última release normal v1.9.xxx; o Windows tem releases experimentais independentes e um instalador `SaudePratica-Setup.exe`. A APK mais recente encontra-se em `https://github.com/DanBar1971/SaudePratica/releases/latest/download/SaudePratica.apk`.

As três imagens de marca oficiais estão em `assets/` e foram recuperadas do repositório original. As demonstrações usam **dados fictícios**, não dados reais de saúde. O website não guarda nem recebe registos médicos. **Não colocar ficheiros de assinatura, chaves privadas, API keys ou dados de pacientes neste repositório público.**

## Regra de versões Android

Enquanto a SaúdePrática Android estiver em desenvolvimento, **todas as versões são publicadas com a numeração v1.9.xxx como releases normais**, visíveis em `releases/latest` e ao verificador de atualizações dentro da app. **Não usar tags `-preview` nem marcar versões Android como prerelease.** O salto para **v2.0** só acontece quando o utilizador determinar que o desenvolvimento está concluído. Preservar sempre o mesmo package name, certificado original e um versionCode crescente para instalar por cima das versões anteriores. O Windows continua a ter numeração e estado de publicação próprios.

## Publicação

Em **Settings → Pages → Build and deployment → Source**, selecionar **GitHub Actions**. O workflow `.github/workflows/pages.yml` publica o site sempre que estes ficheiros são alterados no ramo `main`. Não é necessário escolher templates nem um domínio próprio.

## Desenvolvimento multiplataforma

O projeto principal reúne o código-fonte Android em `MediAgenda/`, as 43 releases Android históricas, o website e as pastas `windows/`, `ios/` e `shared/`. O Windows tem uma primeira versão experimental com instalador; iPhone ainda não está disponível.

Todas as APKs Android de atualização devem conservar o **certificado original** e ser verificadas antes da release. Não guardar chaves privadas, passwords ou códigos de recuperação neste repositório público. A versão 1.9.127 foi reconstruída a partir da APK assinada com o certificado original, usando um delta público sem segredos, e promovida a release normal.

### Testar a ligação automática Windows ↔ Android (sem dados clínicos)

Instalar o Windows [0.8.12](https://github.com/DanBar1971/SaudePratica/releases/tag/windows-v0.8.12-preview) e a SaúdePrática Android [1.9.132](https://github.com/DanBar1971/SaudePratica/releases/tag/v1.9.132). No Android, abrir **Backups e sincronização → Ligação Windows · Wi-Fi (teste)** e tocar em **Tornar visível no Wi-Fi**. No Windows, abrir **Opções → Sincronização** e utilizar **Procurar novamente**; a pesquisa usa mDNS e, se necessário, UDP broadcast. Comparar os seis dígitos e autorizar no Android. O teste não transfere dados médicos nem usa canal cifrado; não abrir portas no router.
