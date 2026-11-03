# SaúdePrática Windows 0.8.11 — recuperar SOS/Lares do Android e localizar farmácias de serviço

Continuação da versão Windows 0.8.10, com Android independente e sem alteração dos dados clínicos/financeiros já gravados.

## Recuperação do backup Android do perfil selecionado
- **SOS Emergência:** botão «Recuperar SOS do backup Android» na ficha. Lê a família de preferências `saudepratica_emergency_<source_id>` associada ao perfil Windows atual, que é a mesma usada pelo `PersonalHealthStore` Android. Só preenche os campos ainda vazios; não substitui edições já efetuadas no Windows.
- **Lares e Apoios:** botão «Recuperar instituição e faturas do Android». Lê `saudepratica_care_home_v1_<source_id>`, incluindo instituição, contactos, valência (ERPI/SAD/Centro de Dia), notas e mensalidades guardadas no campo `months`.
- Recupera estado manual de mensalidade, valor faturado, pago, reembolsado, referência ADSE e nome original do documento, quando existentes. A ligação automática ao PDF por `document_id` Android ainda não foi implementada; o nome e ID originais são preservados na ficha, e os documentos existentes continuam na área Documentos.
- A importação é **explícita**, repetível sem duplicar os IDs nem as mesmas mensalidades e não altera registos Windows já editados. Os dados ficam cifrados com Windows DPAPI e incluídos no backup `.spbackup`.
- A origem Android do perfil tem de estar ligada ao backup familiar **já protegido neste computador**. Se o ZIP for mais antigo que os dados do telemóvel, deve criar novo backup completo no Android e importá-lo no Windows.
- **Nutrição:** mantém o botão da 0.8.10 «Importar refeições e fotos do Android» (registos em `saudepratica_meal_diary/<source_id>`) e guarda os JPEGs reais por perfil, sem inventar refeições ou recalcular calorias. Esta versão não exige um novo upload se o ZIP já estiver armazenado e associado.
- Nenhuma destas recuperações envia informações pessoais à nuvem.

## Farmácias de serviço — pesquisa em Portugal
- A prioridade do módulo Farmácias passa a ser **consultar farmácias de serviço, não guardar apenas favoritos**.
- Botão «Encontrar perto de mim»: abre no navegador o serviço `https://www.farmaciasdeservico.info/`, que disponibiliza pesquisa por proximidade. A localização só é disponibilizada caso o utilizador autorize o site no navegador.
- Botão «Pesquisar por distrito/concelho»: abre `https://www.farmaciasdeservico.net/` para seleção manual de região e farmácias de turno.
- Ligação INFARMED e favoritos anteriores mantidos em secção secundária; não são feitas pesquisas ocultas, não se conserva a localização e a SaúdePrática não apresenta horários ou disponibilidade como verificados localmente.
- Os serviços são de terceiros e dependem de Internet. Confirmar sempre a escala e o atendimento com a farmácia antes de sair, especialmente fora de horas.

## Validação
- Testes com backups **sintéticos de duas pessoas**, verificando SOS e Lares por source ID, não contaminação entre perfis, estados/valores e nomes de faturas, repetição de importação sem duplicados, preservação dos dados Windows e rollback em falha de gravação.
- Ensaios GUI Python, EXE Windows, OCR e agente Avisos incluídos no workflow de release.
- Instalador Windows experimental, ainda sem assinatura. Fazer backup familiar `.spbackup` antes de instalar por cima da versão anterior.

## Limitações
- Nenhum dado real do perfil Daniel foi aberto no GitHub ou incluído nos testes. Só o próprio Windows, com o backup familiar associado, pode apresentar os valores efetivamente guardados.
- Sincronização clínica bidirecional Windows ↔ Android e importação automática de medições Health Connect continuam pendentes.
