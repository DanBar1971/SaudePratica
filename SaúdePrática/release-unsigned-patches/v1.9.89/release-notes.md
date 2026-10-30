# SaúdePrática v1.9.89 — Atualizador com download visível

## Correção principal

- Substituído o download privado da APK, efetuado num Thread dependente da Activity, pelo **DownloadManager do Android**.
- O ficheiro completo fica acessível em **Ficheiros → Downloads** com o nome `SaudePratica-v1.9.89-...apk`; pode ser recuperado e aberto manualmente.
- O Android mostra o progresso nas notificações e continua a transferência em segundo plano mesmo com a SaúdePrática fechada.
- Ao concluir, aparece a notificação **«SaúdePrática: APK descarregada»**. Ao tocar, o utilizador pode pedir a validação e instalação.
- Antes de instalar, a aplicação verifica o **SHA-256** publicado na Release, o package ID, a versão crescente e o certificado Android original. A instalação continua a exigir autorização do utilizador.
- Se for necessário autorizar «Instalar aplicações desta fonte», a SaúdePrática abre a definição correspondente e retoma a instalação depois da autorização.
- Falhas de download e de verificação passam a ser comunicadas ao utilizador, mantendo a APK em Downloads para diagnóstico.

## Compatibilidade

- Mantidos todos os módulos, alarmes, perfil cuidador, sincronização, medicação, nutrição e documentos da v1.9.88.
- Aplicação Android `com.mediagenda.app.stable`, assinada com o certificado original. Instalar **por cima**, sem desinstalar, para preservar os dados.
- A correção resolve o mecanismo de download futuro. Quem estiver na v1.9.87/v1.9.88 com o atualizador antigo a falhar deve instalar esta APK uma vez diretamente pelo browser do GitHub.

**Nota:** a compilação, integridade e assinatura foram verificadas, mas o comportamento do DownloadManager/PackageInstaller num equipamento Xiaomi/HyperOS real deverá ser testado após a instalação.
