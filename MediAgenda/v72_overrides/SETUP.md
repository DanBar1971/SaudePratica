# SaúdePrática – Análise fotográfica de refeições (IA opcional)

A APK inclui o diário de refeições, a câmara, importação, pré-visualização, edição de porções e macros e arquivo privado por perfil. **O reconhecimento online necessita de um serviço de IA configurado:** nenhum acesso à OpenAI está incluído na APK.

## Serviço Cloudflare Worker de exemplo

1. Cria um Cloudflare Worker e substitui o código pelo ficheiro `meal-ai-worker.js`.
2. Nas definições do Worker adiciona os *secrets* `OPENAI_API_KEY` (chave de um projeto API próprio, só no servidor) e `APP_TOKEN` (token aleatório com pelo menos 24 caracteres). Opcionalmente define `OPENAI_MODEL` para um modelo com visão, por exemplo `gpt-4o-mini`.
3. Publica o Worker e copia o endereço HTTPS terminando em `/analyze`, por exemplo `https://meu-worker.meu-dominio.workers.dev/analyze`.
4. Em SaúdePrática → Nutrição → Fotografar e analisar → Configurar IA, introduz o endereço HTTPS e o `APP_TOKEN`. **Não introduzir a chave da OpenAI nesta opção.**
5. Faz uma fotografia; a app **pede consentimento antes de a enviar**. Revê alimentos, porções, calorias e nutrientes antes de guardar.

### Custos e privacidade

- As chamadas à API de visão são faturadas no projeto API configurado. Não estão incluídas numa assinatura ChatGPT.
- Apenas a fotografia redimensionada segue para o servidor configurado e o serviço de IA; nome e dados clínicos do perfil não são enviados.
- O Worker demonstrativo não guarda fotografias, mas é necessário cumprir a política de privacidade aplicável e evitar registos de payloads no fornecedor.
- Não colocar `OPENAI_API_KEY` nem o conteúdo dos segredos em GitHub, APK, screenshots ou repositórios públicos.
- O token para o Worker é guardado encriptado no Android Keystore; se fizeres backup/restauro do telemóvel pode ser necessário introduzi-lo outra vez.
- A IA fornece **estimativas**. As medidas de porção, adição de azeite, molhos e alergénios não podem ser confirmadas por uma fotografia.
- Em caso de restrições nutricionais clínicas ou alergias, seguir recomendações do profissional e o rótulo original do produto.

### Contrato HTTP

`POST <endpoint HTTPS /analyze>` com `Authorization: Bearer <APP_TOKEN>` e corpo JSON com `image_mime`, `image_base64`, `language`. Resposta JSON: `foods` [{`name`,`grams`,`kcal`}], `total_kcal`, `protein_g`, `carbs_g`, `fat_g`, `uncertainty_note`.

O ficheiro é um exemplo técnico a testar antes de ser usado em produção; protege o endereço com tokens fortes, limites de pedidos, controlo de custos e observação de erros. A ligação online não é funcional até que o Worker esteja publicado e configurado.