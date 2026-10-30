# SaúdePrática v1.9.84 — Fotografias de medicamentos na importação JSON

## Novidade: importar medicamentos com fotografias num único ficheiro
- A importação JSON de Medicação aceita agora, além do formato antigo, fotografias PNG/JPEG codificadas em Base64 no campo opcional `embedded_medication_images`, referenciadas por `embedded_image_names` em cada medicamento.
- As fotografias são **extraídas automaticamente e guardadas no armazenamento privado** da SaúdePrática, associadas às fichas do **perfil atualmente selecionado**. Podem ser vistas na ficha, na lista e nos avisos de medicação, quando aplicável.
- Cada fotografia é validada por assinatura de ficheiro, SHA-256, dimensões e limites de tamanho antes de ser aceite. Não são enviados dados para a Internet.
- Os JSON antigos continuam a ser importados como antes. O processo não cria novos horários nem altera doses ou datas de medicação por conta própria.

## Instalação
Instalar `SaudePratica.apk` **por cima da versão anterior**, sem desinstalar, mantendo a assinatura Android e os dados locais. Fazer previamente **Backup completo** de cada perfil.

## Como importar
1. Abrir o perfil correto em SaúdePrática.
2. Abrir Opções → Backup → Importar JSON (ou a opção equivalente).
3. Escolher um ficheiro JSON preparado com imagens incorporadas.
4. Verificar a confirmação da importação, abrir as fichas e confirmar medicamentos, quantidades, horários e fotografias.

**Nota:** uma importação de `medicacao.json` substitui a lista de medicação do perfil selecionado. Confirmar o perfil e fazer backup antes de importar. Nunca importar um ficheiro de outro familiar num perfil diferente.

## Validação
O pacote Android é compilado com Android SDK, verifica os três elementos gráficos originais e exige assinatura válida v2/v3 com o mesmo certificado das versões anteriores. A integração em diferentes marcas e versões de Android requer confirmação no dispositivo.