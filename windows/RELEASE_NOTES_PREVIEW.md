# SaúdePrática Windows 0.7.0 — Ficha editável dos agendamentos

## Agenda: alterações funcionais
- **Abrir ficha** em cada cartão. Também é possível abrir a ficha ao clicar no título ou na zona do cartão.
- **Formulário em ecrã completo**, não numa janela flutuante, com título, data, hora, atividade, tipo, especialidade, unidade de saúde, local/sala, departamento, médico/profissional, médico prescritor, recurso, referência, telefone, email, descrição e notas.
- **Campos adicionais importados do Android** visíveis e editáveis, mantendo tipos originais (números, booleanos e estruturas JSON). Identificadores internos, chaves de importação e cópia original Android permanecem protegidos contra alterações.
- **Estado editável:** Pendente, Realizada ou Cancelada. Permite cancelar uma marcação localmente e voltar a reativá-la, sem a apagar.
- **Adicionar** uma marcação nova na Agenda, incluindo campos não obrigatórios.
- **Guardar/Cancelar** no ecrã da ficha; o botão Cancelar sai sem gravar. O cancelamento da marcação é escolhido no campo Estado.
- **Filtros da Agenda** Todas, Pendentes, Realizadas, Canceladas refletem imediatamente os novos estados e preservam a contagem de marcações.
- Gravação atómica no armazenamento protegido DPAPI com reposição dos dados anteriores em caso de falha de disco.
- **Importante:** mudar o estado para Cancelada na SaúdePrática **não cancela a consulta no hospital**; o utilizador continua a ter de contactar a unidade de saúde.
- Continuam sem implementação a sincronização automática bidirecional e os alarmes Windows. A importação e exportação manual por backup mantêm-se.
- Testes automáticos sintéticos de alterações de campos, persistência, cancelamento e reativação, isolamento de perfis, dados originais do Android e rollback.

## Instalação
Instalador experimental Windows 10/11, sem certificado de assinatura de editor reconhecido. O aviso SmartScreen pode continuar a aparecer. Recomenda-se criar um backup .spbackup antes de atualizar.
