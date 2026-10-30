# SaúdePrática — Serviço central de IA para refeições

## O que está preparado

A APK **v1.9.55** tem Nutrição → Diário de refeições → Fotografar → Analisar com IA. **Ninguém introduz chave API ou endereço de servidor na aplicação.** Todos usam o mesmo serviço central quando for ativado. As refeições continuam editáveis e guardadas por perfil.

Este ZIP contém um Cloudflare Worker com limites de segurança incorporados (máx. **5 análises por IP/dia** e **200 análises totais por dia UTC**). O limite total ajuda a controlar consumos, mas não substitui os limites de faturação da OpenAI. Não há autenticação forte dos utilizadores: não publicar em produção sem avaliar proteção contra abuso, controlo de gastos e política de privacidade. Imagens e respostas não são guardadas no servidor, mas a OpenAI processa o conteúdo enviado.

## Ativação única pelo responsável da SaúdePrática

**É impossível ativar uma API central só com uma chave se não houver um serviço alojado.** Os utilizadores não têm de fazer estes passos; apenas o responsável. A configuração da IA tem só **um segredo necessário: `OPENAI_API_KEY`**. A primeira publicação do servidor e a indicação do respetivo URL público são dois passos técnicos adicionais, feitos uma única vez.

1. Cria/inicia sessão numa conta Cloudflare: https://dash.cloudflare.com/ . Ativa Workers (pode começar no plano Free).
2. Num computador com Node.js, extrai este ZIP e faz duplo clique em `central-service/ATIVAR_SERVICO.bat` (a opção recomendada). O instalador verifica o `wrangler.jsonc`, instala ferramentas e, se ainda não houver autenticação, apresenta um código de acesso da Cloudflare. Abre https://dash.cloudflare.com/oauth2/device, introduz o código que surge na janela e confirma. Mantém o BAT aberto até à confirmação. Depois, o próprio BAT publica o serviço e pede a chave API. Como alternativa manual: `npm install`, `npx wrangler login --device --browser=false`, `npm run deploy` e `npm run secret`.
3. Na mesma pasta, executa `npm run secret` e cola a tua chave API da OpenAI quando o Wrangler a pedir. Esta chave **só existe no Worker, nunca na APK**.
4. O Wrangler apresenta um URL do género `https://saudepratica-refeicoes.<subdominio>.workers.dev`. Confirma em `<URL>/health` se indica `ready:true`.
5. Abre o ficheiro **`MediAgenda/cloud/meal-ai-config.json`** no GitHub `DanBar1971/AndroidAppDev`, altera `enabled` de `false` para `true`, e introduz `endpoint` como o URL completo `https://saudepratica-refeicoes.<subdominio>.workers.dev/analyze`. Faz commit. **Não coloques a chave API neste ficheiro!**
6. A partir desse momento, as APKs v1.9.55+ conseguem encontrar o servidor automaticamente pela configuração pública. Nenhuma atualização da APK é necessária para mudar o endereço central.

Se quiseres desligar a análise para todos, altera `enabled` para `false` no JSON (sem afetar o diário manual). Para cancelar pagamentos, revoga também a chave no painel da OpenAI. O ficheiro JSON é público e contém **apenas** o URL de serviço e o estado; não contém segredos.

## Custos / privacidade

- A chave da API é criada em https://platform.openai.com/api-keys e o uso é faturado em https://platform.openai.com/settings/organization/billing/overview . ChatGPT Plus não inclui os créditos da API.
- Ativa um orçamento e alertas de consumo no painel OpenAI. A Cloudflare Workers/Durable Objects pode ter custos conforme a utilização.
- A API recebe apenas a foto comprimida e uma instrução de análise. A SaúdePrática não transmite o nome do perfil ou outros dados de saúde com a foto.
- O IP é usado transitoriamente pelo Worker para limitar pedidos. Na Durable Object ficam apenas hashes diários com sal aleatório e contadores; não fotos.
- Mantém o consentimento explícito da app. Solicita testes de privacidade e segurança antes de disponibilizar a terceiros.

## Verificação antes de distribuir

`npm test` verifica o contador de pedidos. Faz um teste com um prato real, revê os resultados e confirma que a aplicação mostra uma mensagem amigável se o serviço estiver desligado.

## Resolução de erros: 23/10/2026

- **`CommaExpected` no ficheiro `wrangler.jsonc`**: a primeira versão do pacote tinha um `}` em falta na linha das `migrations`. Este ZIP está corrigido e o BAT valida o JSON antes da autenticação. Usa este ZIP em vez do anterior.
- **URL da autenticação abre e fecha / browser não consegue chegar a localhost**: o BAT corrigido utiliza o método *device*, que não depende de `localhost`. Abre https://dash.cloudflare.com/oauth2/device e introduz o código apresentado na janela; não feches o BAT enquanto aguardas. Os códigos expiram rapidamente; executa de novo para receber um novo.
- **Já tens sessão iniciada?** O BAT verifica com `wrangler whoami` e salta a autenticação se estiver tudo válido.
- **Nunca publiques a tua chave da OpenAI aqui no chat.** Coloca-a apenas na janela do Wrangler quando este executar `wrangler secret put OPENAI_API_KEY`.