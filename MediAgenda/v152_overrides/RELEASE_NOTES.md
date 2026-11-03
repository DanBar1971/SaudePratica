# SaúdePrática Android 1.9.132 — desenvolvimento (ainda sem APK oficial)

## Assistente IA
- Indicador animado e sempre visível enquanto a IA local, Gemini Nano ou IA Online prepara a resposta.
- Evita envios duplicados enquanto a resposta está em curso.
- Botões e atalhos com fundo translúcido escuro, contorno subtil e texto claro no modo escuro; correspondência com os cartões da aplicação.
- IA local previamente descarregada mantém-se; não exige novo download do modelo.

## Ligação Windows dentro da aplicação principal
- Entrada **Ligação Windows · Wi-Fi (teste)** em Backups e sincronização.
- Torna o telemóvel visível mDNS + UDP broadcast na mesma rede, compatível com Windows 0.8.12.
- Pedido de ligação com código de 6 dígitos e consentimento explícito no Android.
- **Este teste só confirma descoberta e autorização, não transfere dados clínicos.**
- A ligação não usa TLS; não deve ser utilizada para medicação, perfis, fotografias ou documentos enquanto não existir canal autenticado e cifrado.
- O ecrã é interno e não exportado; serviço de descoberta termina ao fechar a ficha.

## Segurança e entrega
- Identificador `com.mediagenda.app.stable`, versão 1.9.132, versionCode 142.
- Mantém o funcionamento dos alarmes, tomas, backups, autenticação e restantes módulos.
- Precisa de CI verde, assinatura com o **certificado original** e teste no equipamento real antes de publicar como atualização normal no GitHub Releases.
