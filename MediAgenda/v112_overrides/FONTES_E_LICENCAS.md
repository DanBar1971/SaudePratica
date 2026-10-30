# SaúdePrática Fase C — fontes, código e atribuições

## O que foi realmente integrado
O código Kotlin em `MealBarcodeService.kt`, `MealNutritionHistory.kt`, a rotina
`MealGeminiDirect.correct()` e os novos controlos em `MealAiActivity.kt`
fazem parte da compilação da app. Não são exemplos, mockups nem apenas ideias.

- **SnapCal**: https://github.com/ghostwan/food-calories — padrões da correção
  multimodal Gemini, leitura nutricional por barcode e organização histórica.
  O repositório descreve a licença como MIT no README. As implementações foram
  escritas especificamente para a SaúdePrática, e não transplantadas em bloco.
  Verificar/licenciar separadamente qualquer futura cópia literal de ficheiros.
- **Open Food Facts**: https://world.openfoodfacts.org/ e
  https://openfoodfacts.github.io/documentation/docs/Product-Opener/v3/products/get-api-v3-product-code/
  — consulta de dados públicos de produtos por código EAN/UPC através de API v3.
  Base de dados sob **ODbL 1.0**: dados de colaboradores Open Food Facts.
  O código tem User-Agent identificável e faz uma consulta apenas do código,
  sem nomes de utentes nem dados clínicos.
- **Google ML Kit / Google Code Scanner**:
  https://developers.google.com/ml-kit/vision/barcode-scanning/android
  — SDK já presente nas dependências, reaproveitado na Nutrição.
- **Código e fotos originais da SaúdePrática**: diário privado por perfil,
  fotografias persistidas, e editor de refeições preexistente preservados.

## Limites, segurança e UX
Uma fotografia não permite estimar com precisão gramagens, molhos, óleo,
ingredientes invisíveis ou alergénios. Resultados por IA são sugestões:
a app exige a confirmação de alimentos e kcal antes de guardar. Valores por
100 g de produtos embalados são escalados pelos gramas efetivamente consumidos.
Os valores são informativos, nunca uma prescrição clínica.

O serviço Gemini usa a chave BYO guardada com Android Keystore, não uma chave
incluída no APK. A opção de correção volta a enviar **a mesma fotografia**
apenas após consentimento. A consulta Open Food Facts envia somente o barcode.

A fotografia da refeição é preservada como JPEG privado associado ao registo
existente do perfil (com redimensionamento para controlar o tamanho); não se
promete conservar os bytes originais não comprimidos da câmara.

Os valores de 7 e 30 dias são médias **do que foi registado**, não do consumo
alimentar efetivo; dias sem registo não significam ausência de refeições.

## Compatibilidade
Manter package `com.mediagenda.app.stable`, certificado de assinatura e
ícone, splash e background oficiais. Evitar migração destrutiva da base de dados.
