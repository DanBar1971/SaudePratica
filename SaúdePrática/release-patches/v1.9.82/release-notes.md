# SaúdePrática 1.9.82 — Nutrição: Gemini preparado, refeições editáveis

## Novidades
- **Botão "Analisar refeição com Gemini (online)"** após fotografar ou escolher uma imagem.
- Pedido explícito de consentimento antes de enviar qualquer fotografia para a análise online.
- Apresentação dos **alimentos separadamente**; edição de nome, gramas e kcal de cada alimento, opção de acrescentar alimento e recálculo do total.
- Resultado ainda revisto no ecrã de confirmação antes de guardar. Porções/calorias são estimativas e não uma medição clínica.
- **Modo manual offline preservado**, incluindo seleção de vários alimentos e estimativa por tabelas nutricionais.
- **Histórico por perfil com fotografias**, possibilidade de associar fotografia a refeições antigas e **Eliminar refeição** com confirmação (incluindo remoção da fotografia), preservados da v1.9.81.
- Preservados os gráficos originais da SaúdePrática, os restantes módulos (incluindo Lares e Atalhos) e a assinatura Android anterior.

## Estado do Gemini online — importante
**O serviço central Gemini ainda NÃO está ativado.** Esta versão já prepara a ligação e a revisão dos alimentos, mas a análise real só estará disponível quando o responsável configurar um projeto/chave Gemini e um gateway HTTPS seguro. **Não é pedida conta nem chave a quem usa a app.** Enquanto não houver serviço, a app informa a indisponibilidade e continua a permitir o registo manual offline. Não foram inventados resultados ou calorias online.

O serviço opcional está no código `MediAgenda/cloud/central-meal-ai/gemini-worker.mjs` e as instruções de ativação em `GEMINI_SETUP_PT.md`. A chave **nunca** é colocada na APK nem no repositório.

## Instalação
Descarrega `SaudePratica.apk` desta Release e instala **por cima** da versão anterior, sem desinstalar, para manter os dados. Recomendado fazer backup antes da atualização.

## Testes sugeridos
1. Fotografar uma refeição, escolher modo manual e introduzir vários alimentos com gramas e kcal.
2. Abrir histórico, ver miniatura/fotografia; associar foto a refeição antiga; testar Eliminar com confirmação.
3. Premir análise Gemini para confirmar o consentimento e a mensagem de serviço ainda não ativado.
4. Verificar medicação, agendamentos, perfil, atalhos, Lares e os gráficos do arranque.

**APK compilada, assinatura v2/v3 original verificada e os 3 gráficos originais confirmados.**
