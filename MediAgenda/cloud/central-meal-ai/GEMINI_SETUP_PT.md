# SaúdePrática — Gemini online central (preparado na v1.9.82)

**Estado em 26-10-2026:** App e código do serviço central preparados. **A análise Gemini real fica desativada** até existir um endpoint público seguro com chave API Gemini. O módulo manual offline, a seleção e edição de alimentos, o histórico com fotografias e a eliminação de registos continuam a funcionar sem serviço online.

## Experiência para o utilizador
1. Fotografar ou escolher uma imagem no diário de Nutrição.
2. Premir **Analisar refeição com Gemini (online)**.
3. Aceitar explicitamente o envio apenas daquela imagem; nomes de perfis e registos médicos não são enviados.
4. Rever a lista de vários alimentos, alterar os **gramas e kcal de cada um**, adicionar alimentos em falta e confirmar o total antes de guardar.
5. Abrir a refeição no histórico para ver a fotografia, ou **Eliminar**, com confirmação. O diário permanece associado ao perfil.
6. Quando não houver Internet, serviço, quota gratuita ou consentimento: registo e cálculo **manual offline** continuam disponíveis.

## Porque não há zero configuração externa
A API Gemini exige um projeto Google e chave para autenticação. Não é tecnicamente possível oferecer chamadas API Gemini gratuitas, anónimas, sem credenciais nem configuração de um serviço. **Nenhum utilizador da app terá de se inscrever em Gemini ou introduzir tokens.** O responsável pela app terá de criar/configurar a conta Google e o serviço de uma única vez; não foi encontrado um projeto/endpoint Gemini ativo neste repositório e, por isso, não inventar credenciais.

Documentação Google:
- https://aistudio.google.com/docs/get-started
- https://ai.google.dev/gemini-api/docs/pricing
- https://ai.google.dev/gemini-api/docs/rate-limits
- https://firebase.google.com/docs/ai-logic

## Backend sem segredos no Android

Um Cloudflare Worker opcional está em `MediAgenda/cloud/central-meal-ai/gemini-worker.mjs`. O segredo `GEMINI_API_KEY` fica exclusivamente no Cloudflare e nunca numa APK ou GitHub. Os limites são controlados por Durable Object: até 5 análises por IP/dia e 200 no total, sujeito às quotas adicionais da Google. O Worker não persiste fotografias ou respostas, mas transmite a fotografia ao Google, e o nível gratuito pode implicar uso de dados para melhoria do serviço. Isto deve ser explicado na Política de Privacidade antes da ativação.

Para ativar, o responsável terá de:
1. Criar projeto/chave na Google AI Studio. Pode começar pelo *free tier* sem pagamento, respeitando os limites atuais.
2. Criar conta Cloudflare Workers (plano Free é potencialmente suficiente; confirmar quotas antes de ativar).
3. Na pasta `MediAgenda/cloud/central-meal-ai/`: `npm install`, `npx wrangler login`, `npx wrangler deploy --config wrangler-gemini.jsonc`.
4. Inserir segredo sem o colocar em ficheiros ou comandos públicos: `npx wrangler secret put GEMINI_API_KEY --config wrangler-gemini.jsonc` (a CLI solicita a chave em entrada privada).
5. Testar `https://saudepratica-gemini.<conta>.workers.dev/health` até devolver `ready:true`; testar resposta a fotografia não sensível.
6. Alterar **apenas** o ficheiro público `MediAgenda/cloud/meal-ai-config.json` para `{"provider":"gemini","enabled":true,"endpoint":"https://saudepratica-gemini.<conta>.workers.dev/analyze"}`.
7. Nunca deixar a chave visível na configuração pública, nos logs de GitHub, APK ou parâmetros URL. Não ativar com backend público sem mitigação adicional de abuso e validação legal/privacidade.

Para suspender o serviço, definir `enabled:false` no JSON e revogar o segredo no backend se necessário. A app passa automaticamente a explicar a indisponibilidade, sem afetar o diário offline.

**Não confundir a presença do botão Gemini na v1.9.82 com a ativação efetiva do serviço.**

## Regras de qualidade e segurança
- Não sugerir que o modelo Google AIY offline de prato único consegue reconhecer todos os itens de uma refeição composta.
- Não fabricar resultados, fotos, calorias ou valores de macro. A estimativa Gemini só deve aparecer após uma resposta real.
- Nunca pedir login Google ou API key a cada utilizador da app.
- O envio de fotografia exige confirmação individual, com aviso de transferência a um terceiro.
- Estimativas só depois de revisão; kcal por ingrediente são editáveis, cálculo total revisto, macros não recalculadas ficam sinalizadas.
- Fazer backup antes de atualizar e verificar que a assinatura Android, o package e os 3 assets gráficos originais são preservados.
