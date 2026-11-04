# SaúdePrática Android 1.9.129 — Assistente IA local, com confirmação humana

- Assistente de conversa integrado no módulo Ajuda, ligado **apenas ao perfil selecionado**.
- Consulta de medicação e próximas marcações através dos registos reais da app, sem acesso cruzado a outros perfis.
- Preparação de rascunhos de consulta e medicação em linguagem natural: o utilizador **revê a ficha nativa** e só depois guarda.
- Gemini Nano opcional no próprio dispositivo (sem serviço cloud da SaúdePrática, sem API paga), quando o Android/AICore suportar. Instalação do modelo apenas com consentimento explícito. Sem suporte do modelo, permanece a assistência guiada local e a Ajuda clássica.
- Os alarmes de medicação e agendamento continuam no Android e **não dependem da IA**. Nenhuma alteração automatizada a doses, TOMEI, ADIAR, prescrições ou registos.
- Os dados clínicos não são enviados a um serviço de IA externo pela SaúdePrática.
- Versão `1.9.129`, código Android `139`, package original `com.mediagenda.app.stable`.
- **Atenção:** só publicar depois de compilação, testes de regressão, verificação da assinatura original e de compatibilidade de atualização no telemóvel. Testar inicialmente com dados fictícios e backup feito.

Este ficheiro contém notas de versão propostas; a criação deste código **não significa que a release esteja publicada**.
