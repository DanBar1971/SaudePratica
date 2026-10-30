# SaúdePrática v1.9.93 — Fase C: Nutrição

Nova fase integrada na app Android existente, com código Kotlin real adaptado de padrões SnapCal e API Open Food Facts (não apenas sugestões).

## Funcionalidades
- Gemini multimodal em PT-PT: fotografia analisada e ingredientes visualizados separadamente; **Corrigir com IA** reanalisa a mesma fotografia com uma indicação textual da pessoa.
- Revisão individual de gramas, calorias, proteínas, hidratos e gorduras; recálculo dos totais apenas após confirmação do utilizador.
- Código EAN/UPC pela câmara via Google Code Scanner, com introdução manual alternativa.
- Consulta do produto por **Open Food Facts API v3** e cálculo proporcional a gramas consumidas a partir dos valores por 100 g. Atribuição e termos ODbL 1.0.
- Histórico nutricional privado por perfil, com resumos dos últimos **7 e 30 dias**, respetivas calorias e macronutrientes guardados.
- Reaproveitamento do diário privado com **fotografia associada**, pré-visualização, associação posterior e eliminação.
- Origem do resultado (Gemini, Open Food Facts ou manual) e código de barras associados ao registo.
- Sem dependências Android novas. Ícone, splash e background oficiais preservados.

## Limitações e privacidade
As estimativas visuais de refeições completas e porções podem estar erradas. Óleo, molhos e ingredientes não visíveis não são mensuráveis por fotografia; alergénios não são garantidos. A fotografia associada é guardada em JPEG otimizado, **não preserva necessariamente o ficheiro original sem compressão**. A correção por IA exige chave Gemini configurada e consentimento. Sem chave, há sempre edição manual. A consulta Open Food Facts envia apenas o código EAN/UPC, não informações de saúde.
Faltam testes reais em Xiaomi/HyperOS de câmara, serviços Google, ligação Gemini e produtos portugueses.

## Referências
- SnapCal: https://github.com/ghostwan/food-calories (MIT declarada no README; adaptação, sem transplante integral).
- Open Food Facts: https://world.openfoodfacts.org/ (dados ODbL 1.0).
- API OFF: https://openfoodfacts.github.io/documentation/docs/Product-Opener/v3/products/get-api-v3-product-code/
- Implementação/licenças: `MediAgenda/v112_overrides/FONTES_E_LICENCAS.md`.

## Compatibilidade
Mantidos `com.mediagenda.app.stable`, assinatura Android original, perfis, medicação, alarmes, backups existentes, direitos de dados e recursos gráficos originais. Recomenda-se fazer backup antes de atualizar.
