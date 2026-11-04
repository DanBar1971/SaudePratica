# SaúdePrática Android 1.9.136 — Fichas por processo hospitalar e calendário

## Situação Clínica · unidade / processo

Cada número de processo já existente passa a ter acesso a uma **ficha própria**, com:
- **A minha equipa**: adicionar, editar, eliminar, ligar e escrever email aos contactos; importar manualmente ficheiro JSON da equipa; remoção de duplicados por nome+especialidade.
- **Taxas moderadoras**: Consultas, Exames e Análises, montante por linha, pago/por pagar/isento/anulado, histórico e total em dívida manual.
- **Identificação**: fotografia ou captura do cartão do hospital, guardada no armazenamento privado da SaúdePrática, sem usar a app do hospital.
- **Transporte**: pedidos e declarações, estado manual (por pedir, pedido enviado, a aguardar, declaração emitida, concluído, cancelado), data, referência e notas.

**A app não acede, importa, reproduz pedidos ou consulta a app IPO Lisboa.**
Todos os dados são manuais, locais e associados apenas ao perfil, à unidade hospitalar e ao número de processo. **Não há integração oficial com o hospital**, nem consulta automática de valores em dívida ou envio de pedidos de transporte. A lista de profissionais nas capturas do utilizador não integra o repositório nem o APK: importar o ficheiro de teste localmente, após instalar, evita publicar dados de pacientes.

## Agenda

A opção **Adicionar consulta ao calendário do telemóvel** permite escolher uma marcação futura e abrir o editor do calendário Android com os dados preenchidos, para confirmação explícita. Não pede permissões de leitura/escrita do calendário, não cria eventos silenciosamente e não inventa hora quando a marcação só tem data. Não existe ainda sincronização automática bidirecional nem atualização de eventos se a marcação for alterada na SaúdePrática.

## Backup e sincronização

Registos estruturados e imagem local em \`saudepratica_workplace/<perfil>/\`, pasta já permitida no backup familiar e na sincronização Nearby por perfil. Não se alteram o formato de backup PIN-v2, a restauração, a identidade dos perfis ou os alarmes TOMEI/ADIAR.

Android exclusivamente nesta versão; a aplicação Windows mantém as funções atuais. O ficheiro só pode ser publicado como APK normal se houver build e assinatura do **certificado original** verificados. Sem teste no telemóvel não se afirmará que a UX está validada em MIUI.
