# SaúdePrática v1.9.112 — Dicas e Informações

- Novo módulo **Opções → Dicas e Informações**, com arquivo local persistente dos cartazes visualizados (sem recolha de dados pessoais no GitHub).
- Popups ocasionais a partir do catálogo JSON público em `SaudePratica/info_saude/informacoes.json`, sem atualizar a APK para adicionar mais dicas.
- Cartazes verticais ocupam quase toda a janela, **sem cabeçalho**, com botões Android reais `OK` e ação externa `Oferecer um cafezinho` quando existir URL HTTPS.
- Primeira mensagem: apoio voluntário à SaúdePrática, encaminhando para `https://buymeacoffee.com/danielbarr7`.
- Dicas e imagens guardadas para leitura offline após a primeira visualização, com seleção aleatória, controlo de repetição e escolha da frequência (desativado, diário, 3 dias ou 7 dias).
- Só tenta apresentar popups após o desbloqueio da app e quando a janela está ativa e o telefone não está bloqueado; não introduz alarmes nem notificações.
- Preserva o identificador Android `com.mediagenda.app.stable`, `versionCode=122`, `versionName=1.9.112`, o certificado original e as imagens oficiais da app.
- Cartaz criado sem nenhuma captura ou representação fictícia da interface Android da aplicação.

**Testes de aceitação em Android:** instalar por cima de 1.9.111, abrir com PIN, confirmar popup, usar link externo/OK, visitar Opções → Dicas e Informações, consultar histórico offline e alternar frequência. Garantir que nenhum popup interfere com a apresentação ou confirmação de alarmes de medicação.
