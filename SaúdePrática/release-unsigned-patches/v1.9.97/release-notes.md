# SaúdePrática v1.9.97 — Gemini 503 e pontualidade dos alarmes

Atualização sobre a v1.9.96 (mesmo pacote Android e certificado original).

## Alarme: correção do diagnóstico
O utilizador confirmou o comportamento real:
- Agendamento de teste às **12:45**, disparou cerca das **12:46**;
- O aviso sonoro funcionou;
- Ao tocar em **TOMEI**, a aplicação **abriu corretamente as TOMAS** do perfil.

**Não modificámos a navegação TOMEI → TOMAS**, que está correta.

A SaúdePrática já utilizava `AlarmManager.setExactAndAllowWhileIdle()` quando o Android concedia acesso a alarmes exatos; quando a autorização faltava, caía em `setAndAllowWhileIdle()`, que pode atrasar. Nesta versão:
- **Opções → Segurança e notificações → Notificações** mostra se o Android autorizou alarmes exatos e apresenta um botão direto para conceder a permissão especial.
- A hora programada e a hora de entrega pelo Android do último alarme de medicação são registadas **sem nome de utente ou medicamento**.
- O diagnóstico em Notificações mostra o atraso em segundos do último evento recebido; adiamentos de 10 minutos não contaminam este cálculo.
- Requer confirmação real em Xiaomi/HyperOS, com as permissões de bateria e alarmes apropriadas.
- As limitações de agendamento do sistema Android não podem ser ignoradas pela app.

## Gemini: falhas HTTP 503 e ligação
O Google AI Studio mostrava HTTP **503 ServiceUnavailable**, por isso a chave não deve ser considerada inválida apenas por esse erro. Para chamadas Gemini REST acrescentámos:
- Até 3 tentativas limitadas para falhas temporárias, com intervalos progressivos;
- Uso do modelo estável **Gemini 3.8 Flash**, seguido do modelo estável alternativo **Gemini 3.6 Flash** quando o principal continua indisponível;
- Sem repetição automática de recusas permanentes de chave ou quota (4xx, incluindo 403 e 429);
- Mensagens que distinguem indisponibilidade temporária de chave recusada;
- Sem incluir a API key no código, logs ou GitHub. Permanece cifrada no Android Keystore.

**Configuração Gemini agora também em Opções → Segurança e notificações → Gemini · API Key e teste**. O novo acesso abre o diálogo já existente. Pode continuar a gerir a chave diretamente na Nutrição.

## Validação e limitações
- Mantida a assinatura original e ícone, splash e background oficiais.
- Preservadas as funcionalidades e dados das Fases A–E.
- Os testes automatizados não substituem um teste real num telemóvel Xiaomi.
- A utilização do Gemini pode ser sujeita a quotas e custos do projeto do utilizador. O modelo alternativo é igualmente servido pelo Google.
- Se o Google continuar a devolver 503, a app não consegue garantir o reconhecimento; o registo manual continua disponível.
- Recomenda-se backup completo antes de instalar.

## Referências oficiais
- https://ai.google.dev/gemini-api/docs/troubleshooting
- https://developer.android.com/about/versions/14/changes/schedule-exact-alarms
- https://ai.google.dev/gemini-api/docs/models
