# Dicas e Informações — SaúdePrática

Catálogo público de cartazes informativos e de mensagens de apoio voluntário. O APK lê o catálogo em `https://danbar1971.github.io/SaudePratica/info_saude/informacoes.json`.

## Estrutura
- `informacoes.json`: versão, frequência sugerida e itens ativos.
- `imagens/info_001.png`: cartaz fotográfico 9:16 com captura autêntica da interface e dois botões desenhados, ativados na app por áreas clicáveis acessíveis.

## Adicionar uma dica
1. Guardar uma imagem vertical 9:16 em `imagens/` (SVG, PNG, JPG ou WebP conforme leitor implementado).
2. Adicionar no catálogo um `id` único e estável, `title`, `image` relativo, `enabled` e, opcionalmente, `action_url` HTTPS.
3. Validar JSON e URLs antes de publicar. Imagens e JSON são públicos: **nunca publicar dados de utentes, fotos de medicamentos pessoais nem documentos clínicos**.
4. O histórico de visualização pertence apenas ao telemóvel (SharedPreferences); o GitHub não recolhe identificadores de perfis nem estatísticas do utilizador.

## Regras
- A imagem ocupa a maioria da janela; não há cabeçalho adicional. Para os cartazes normais, os botões Android reais ficam debaixo da imagem. Se `embedded_actions=true`, a imagem desenha os botões e a app cria áreas clicáveis transparentes sobre eles (sem duplicações).
- OK fecha; Saber mais/Oferecer cafezinho abre URL HTTPS verificado externamente, sem recolher pagamento na app.
- Mostrar, quando apropriado, na app aberta e desbloqueada; nunca sobre alarmes, PIN, marcações ou tomas.
- Apresentar aleatoriamente sem repetições próximas; manter histórico local, mesmo offline, de itens já mostrados.
- A mensagem de apoio é voluntária, pouco frequente e não condiciona qualquer função.
