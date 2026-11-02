# SaúdePrática Desktop 0.7.6 — medicação Android e Avisos sem splash

## Medicação
- **Estados Android recuperados corretamente:** o Windows interpreta a data `suspended_from` de um medicamento suspenso e distingue a hora de aviso `reminder_time` do tipo de toma (jejum, jantar, etc.).
- **Vista com contadores** de medicamentos suspensos, avisos ativos e horários guardados, incluindo horários de medicamentos suspensos (não contam como aviso ativo).
- Novo filtro **Com aviso**, badge com hora real da medicação e ficha com campo próprio para editar hora de aviso no formato HH:MM.
- Uma alteração explícita no Windows prevalece sobre os metadados históricos Android, sem modificar o ZIP original.
- **Importante:** a app Windows continua a **apresentar** os estados da medicação Android, mas não dispara os alarmes fortes dos medicamentos; estes continuam da responsabilidade do Android.

## SaúdePrática · Avisos
- A aplicação principal mantém um único splash; o agente de avisos passa a ter **executável separado, sem splash nem janela principal**, para impedir o segundo splash ao abrir a app.
- O agente apresenta o **ícone oficial** na área de notificações do Windows.
- Clicar com o botão direito no ícone mostra **Abrir SaúdePrática** e **Sair dos avisos**; sair termina só o agente de lembretes. Os avisos da Agenda param até voltar a abrir a aplicação ou iniciar uma sessão Windows.
- O instalador atualiza a versão anterior por cima e encerra de forma segura o processo residente, voltando a iniciar o agente no fim.

## Validação
- **117 testes automáticos** concluídos; testes no ambiente Windows confirmaram abertura da app e arranque/encerramento do agente, incluindo a ação de sair e o sinal usado pelo instalador.
- Build verificada: [GitHub Actions #41466219222](https://github.com/DanBar1971/SaudePratica/actions/runs/41466219222).
- Dados e backups existentes permanecem em armazenamento privado; nenhum dado real de pacientes foi publicado.
- A transferência de alterações clínicas Windows → Android continua sujeita à validação de interoperabilidade antes de ser usada em perfis reais.
