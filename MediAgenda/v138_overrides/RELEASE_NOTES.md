# SaúdePrática v1.9.118 — Ficha de medicação simplificada

- O ecrã da medicação começa pelo essencial: **nome, dose, fotografia real em miniatura (se existir), via de administração, tipo de toma, posologia, hora do aviso, opção sem alarme, suspensão e notas**.
- Nova **via de administração**: oral, sublingual, parentérica/injeção, tópica/cutânea, inalatória, retal, vaginal, ocular, otológica, nasal e outra. Ao selecionar **injeção**, pode especificar a via **subcutânea, intramuscular, intravenosa, intradérmica ou outra**. As fichas antigas ficam sem via definida até ser indicada, em vez de presumir uma.
- O resto passa a **cinco secções expansíveis**: Prescrição, Repetições, Informação, Bula/Folheto e Foto da embalagem.
- Os mesmos controlos continuam associados aos mesmos dados e ações: anexar imagens e PDF, pesquisar informação, selecionar datas, suspender e retomar.
- Formulário principal em **ecrã completo**, com Cancelar/Guardar sempre no rodapé. Também se aplica a dados obtidos por digitalização/OCR.
- Dados de via e injeção são guardados no JSON do medicamento, por perfil, e incluídos nos backups desse JSON.
- **Não foram modificados o motor de alarmes, ecrã bloqueado, ADIAR, TOMEI, notificações, identidade da aplicação, certificado nem imagens oficiais.**

## Testes de aceitação
- Editar e guardar um medicamento antigo sem perder fotografias, bula, horários ou receita.
- Escolher cada via, incluindo injeção subcutânea e intramuscular; reabrir e confirmar a escolha.
- Expandir/recolher os cinco grupos com letras grandes e teclado aberto.
- Confirmar Cancelar sem gravar e Guardar com gravação.
- Testar medicação de uma e várias tomas com ecrã bloqueado, incluindo 07:00, ADIAR e TOMEI.
- Confirmar exportação/importação do JSON e sincronização seletiva dos novos campos.

A compilação e os testes automáticos não substituem a validação nos telemóveis reais.
