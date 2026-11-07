# SaúdePrática — IA Online com Cloudflare Workers AI

Este serviço é **opcional**. Nenhuma chave fica dentro da APK. Sem este serviço
configurado a aplicação continua com Ajuda tradicional, acesso nativo a Agenda
e Medicação e IA local (descarregamento voluntário).

## Instalação do serviço numa conta Cloudflare do responsável

1. Criar/iniciar sessão na Cloudflare e ativar Workers AI no plano Free.
2. Numa máquina de confiança, com Node.js instalado:
   ```bash
   cd SaudePratica-OnlineAI/cloudflare-worker
   npm install
   npm test
   npx wrangler login
   npx wrangler secret put SAUDE_AGENT_SHARED_TOKEN
   npm run deploy
   ```
3. Usar um código aleatório **longo e exclusivo** no segredo (mínimo 24 caracteres).
   **Não** o colocar no GitHub, Issues, mensagens, websites ou APKs.
4. Copiar o URL `https://...workers.dev/v1/ask` apresentado pelo deploy.
5. Na **SaúdePrática Android > Assistente > IA Online > Configurar**, introduzir
   o endereço HTTPS do Worker e o código secreto num dispositivo autorizado.
   Estes elementos são guardados localmente com Android Keystore.
6. Usar IA Online quando houver Internet. Desativar ou eliminar configuração
   no próprio dispositivo quando já não for necessária.

O Worker só recebe `{"question":"texto introduzido pelo utilizador"}`.
A app faz consultas aos seus próprios dados localmente e não envia
automáticamente nomes, perfis, medicamentos, contactos ou históricos clínicos.
O que o utilizador escrever na pergunta **é enviado à Cloudflare**. Não incluir
dados médicos pessoais identificáveis. Respostas não alteram registos.

A Cloudflare oferece uma quota gratuita diária de Workers AI, sujeita a limites;
não é utilização ilimitada nem há garantia de disponibilidade. Sem conta
Cloudflare e sem um Worker implementado, a IA Online **não estará operacional**.

### Segurança adicional recomendada para serviço público

O token impede acesso anónimo, mas um token compartilhado não equivale
a autenticação por conta/dispositivo. Antes de disponibilizar a terceiros,
implementar autenticação individual, rotação/revogação, rate limits no
Cloudflare WAF e limites de custo. Nunca colocar o segredo no código-fonte.
A rota `/health` revela só estado de configuração; não expõe valores.

### Testes

`npm test` cobre autenticação, entrada limitada, nenhum contexto clínico,
erros e resposta do modelo. O deploy real precisa de validação no Android.
