# SaúdePrática Windows 0.6.9 — Filtros da Agenda

## Alterações
- **Agenda:** quatro seletores funcionais no topo, como no Android: **Todas | Pendentes | Realizadas | Canceladas**.
- O filtro aplica-se às marcações do perfil escolhido, sem alterar dados clínicos.
- Indicador de **marcações visíveis / total** e mensagem de lista vazia se o filtro não devolver resultados.
- Estados nos cartões: **PENDENTE, REALIZADA, CANCELADA**. A indicação de cancelamento tem prioridade; dados sem estado explícito seguem a regra Android de considerar realizada uma marcação após a respetiva data.
- A lista mantém próximos compromissos por ordem crescente e anteriores por ordem decrescente, com contraste claro/escuro da versão anterior.
- Layout responsivo, utilizando o cabeçalho e navegação horizontal já aprovados na aplicação Windows. Não introduz barra lateral nem controlos apenas ilustrativos.
- Dados Android e backups existentes preservados; não foram acrescentados alarmes nem sincronização bidirecional.
- Os testes automáticos usam exclusivamente registos fictícios para confirmar filtros, estados e preservação de dados.

## Notas
A versão Windows mantém-se experimental e sem assinatura digital reconhecida do editor. O Windows SmartScreen pode apresentar um aviso durante a instalação.
