# SaúdePrática v1.9.98 — revisão de refeições e gravação no diário

Atualização sobre a v1.9.97. Mantém o pacote Android `com.mediagenda.app.stable`, `versionCode=108` e o certificado original como condição obrigatória para publicar.

## Nutrição · Gemini
- Ecrã de revisão de refeições maior, com cartões por alimento e rótulos permanentes de quantidade (g) e calorias (kcal).
- Macronutrientes (proteínas, hidratos e gorduras) editáveis através de uma secção expansível.
- Adicionar ou retirar ingredientes e ver o total estimado de calorias atualizado.
- Botão fixo **«Guardar refeição no diário»**, independente da lista com deslocamento; guarda diretamente no perfil ativo, com fotografia e nutrientes.
- Último resultado Gemini bem-sucedido disponível para nova revisão sem nova chamada à API enquanto não for alterada a fotografia.
- Diagnósticos mais precisos para problemas de DNS, timeout e HTTP 503, sem apresentar indisponibilidade do Google como erro da chave.

## Continuidade e privacidade
- Não altera a navegação de **TOMEI → TOMAS**, agendamento dos alarmes nem perfis existentes.
- Mantém as Fases A–E, dados de medicação, documentos digitais e imagens oficiais (ícone, splash e background).
- Não distribui a chave API Gemini; a configuração local cifrada deverá manter-se numa atualização normal sem remoção dos dados.
- As falhas temporárias do fornecedor de IA não são consideradas resolvidas por esta atualização.

## Validação
- Compilação e verificações automáticas concluídas no commit da PR #44.
- A publicação exige APK assinada, assinatura válida e certificado idêntico ao da v1.9.97, `versionName=1.9.98` e `versionCode=108`.
- **Teste real recomendado em Xiaomi/HyperOS:** lista longa de ingredientes, teclado aberto com botão Guardar visível, guardar refeição e fotografia no perfil correto, consultar histórico e verificar os alarmes e TOMAS.
- Recomenda-se fazer backup da app antes da atualização.
