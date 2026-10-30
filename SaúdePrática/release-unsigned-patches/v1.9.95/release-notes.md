# SaúdePrática v1.9.95 — Nutrição simplificada e Gemini corrigido

## Problemas identificados nos screenshots (v1.9.94)
- **Configurar Gemini** só aparecia após a escolha de uma fotografia, por baixo de muitos outros botões.
- Sem chave Gemini privada, a aplicação tentava um proxy central de IA que podia estar desativado; mensagens de erro demoravam a aparecer.
- Ao importar uma imagem, iniciava-se automaticamente o modelo offline, que só reconhecia **um prato**, abrindo avisos pouco úteis para refeições completas.
- A lista de ações era extensa e duplicada; o plano alimentar opcional tinha demasiados campos visíveis.

## Alterações reais na app Kotlin
- Interface **Nova refeição**: primeiro Fotografar / Escolher, depois rever a fotografia e **Analisar com Gemini** ou identificar ingredientes manualmente.
- Secção permanente **Inteligência artificial · Gemini**, com indicação de chave configurada ou por configurar e botão de configuração e teste visível mesmo sem fotografia.
- No diálogo de configuração, ligação direta a https://aistudio.google.com/apikey para criar uma chave API de autorização; chave cifrada localmente com Android Keystore, não incluída na APK nem no GitHub.
- Análise sem chave abre diálogo a explicar o que falta configurar. **Removida a tentativa silenciosa de encaminhar fotografias para o serviço remoto alternativo desativado**.
- Durante análise online, diálogo persistente de progresso até existir resposta ou erro; mensagens mais específicas para chave recusada, modelo indisponível e limite/quota.
- Modelo Gemini Flash estável atual: `gemini-3.8-flash`. A disponibilidade e os custos dependem do teu projeto Google AI Studio.
- Modo offline de um só prato fica **experimental e opcional**, apenas quando a pessoa pede; deixa de ser lançado automaticamente depois da fotografia.
- Ações alternativas reunidas: seleção manual de alimentos, scanner de códigos de barras e registo manual.
- Histórico mantém todos os dados por perfil, mas mostra apenas as **12 refeições mais recentes** na lista principal; os restantes registos não são eliminados.
- **Plano alimentar (opcional)**: ficha extensa substituída por cartão discreto e botão “Ver / editar plano alimentar”. Os campos e restrições já introduzidos ficam preservados.
- Preservados fotografia ligada a cada refeição, macros, edição de ingredientes, ecrãs e dados das Fases A–D, ícone oficial, splash e background.

## Privacidade e limitações
A análise necessita de Internet e uma chave Gemini configurada no próprio telemóvel; a fotografia escolhida será enviada ao Google **após confirmação explícita**. Só as fotografias selecionadas são enviadas; nome do perfil e registos clínicos não são enviados. O resultado de calorias/gramas é uma **estimativa**, e pode necessitar de correção. Consultas Gemini poderão ter custos ou limites conforme a conta Google. Nunca publiques a chave API num screenshot ou mensagem.

## Testes
Compilação CI e assinatura v2/v3 por certificado Android original verificadas. Falta confirmar num telemóvel Android/HyperOS real com chave pessoal e rede móvel ou Wi‑Fi, incluindo API auth key, consentimento, resposta multimodal e edição de alimentos.

Fonte de interface/padrão de correção: SnapCal (https://github.com/ghostwan/food-calories), usado como referência, sem copiar a aplicação completa.
