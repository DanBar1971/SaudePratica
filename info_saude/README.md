# Dicas e Informações — SaúdePrática

Catálogo público de cartazes informativos e de mensagens de apoio voluntário. O APK lê o catálogo em `https://danbar1971.github.io/SaudePratica/info_saude/informacoes.json`.

## Estrutura
- `informacoes.json`: versão, frequência sugerida e itens ativos.
- `imagens/info_001.svg`: cartaz 9:16 de apoio à app, sem simulações de ecrãs Android.

## Adicionar uma dica
1. Guardar uma imagem vertical 9:16 em `imagens/` (SVG, PNG, JPG ou WebP conforme leitor implementado).
2. Adicionar no catálogo um `id` único e estável, `title`, `image` relativo, `enabled` e, opcionalmente, `action_url` HTTPS.
3. Validar JSON e URLs antes de publicar. Imagens e JSON são públicos: **nunca publicar dados de utentes, fotos de medicamentos pessoais nem documentos clínicos**.
4. O histórico de visualização pertence apenas ao telemóvel (SharedPreferences); o GitHub não recolhe identificadores de perfis nem estatísticas do utilizador.

## Regras
- A imagem ocupa a maioria da janela; não há cabeçalho adicional. Os botões Android reais ficam debaixo da imagem.
- OK fecha; Saber mais/Oferecer cafezinho abre URL HTTPS verificado externamente, sem recolher pagamento na app.
- Mostrar, quando apropriado, na app aberta e desbloqueada; nunca sobre alarmes, PIN, marcações ou tomas.
- Apresentar aleatoriamente sem repetições próximas; manter histórico local, mesmo offline, de itens já mostrados.
- A mensagem de apoio é voluntária, pouco frequente e não condiciona qualquer função.
