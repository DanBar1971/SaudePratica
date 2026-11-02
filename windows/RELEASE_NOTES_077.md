# SaúdePrática Windows 0.7.7 — menu «Sair dos avisos» corrigido

## Ícone na área de notificação do Windows

- Corrigido o **botão direito** no ícone «SaúdePrática · Avisos», que na 0.7.6 não mostrava qualquer menu.
- O menu contém **«Abrir SaúdePrática»** e **«Sair dos avisos»**. Escolher Sair encerra apenas o agente residente da Agenda; a aplicação principal e os dados não são alterados.
- A seleção do menu é agora obtida diretamente através do comando escolhido no menu Win32. O separador do menu usa um formato compatível com diferentes versões do pywin32.
- Mantém o ícone oficial, o agente independente **sem splash**, um único splash na aplicação principal e atualização por cima da versão anterior.
- Se encerrares os Avisos, os lembretes Windows da Agenda param até abrires novamente a aplicação ou iniciares uma nova sessão.

## Funcionalidades preservadas

- Mantêm-se as correções para os **medicamentos suspensos e avisos importados do Android**, incluindo a hora das 07:00, filtros «Com aviso» e estados suspensos.
- O Windows **ainda não dispara os alarmes fortes da medicação**: continuam no Android.
- Os backups encriptados e as fichas existentes não são modificados apenas por instalar esta versão.

## Validação

- 120 testes Windows e 5 testes partilhados concluídos.
- Teste nativo Windows acionou efetivamente o botão direito, verificou que apareceu um popup visível e clicou em «Sair dos avisos» com o rato, confirmando o encerramento do processo. Também testou o reinício e o sinal de encerramento do instalador.
- Instalação compilada com sucesso no [GitHub Actions #41470168223](https://github.com/DanBar1971/SaudePratica/actions/runs/41470168223).
- Nenhum dado pessoal ou clínico real foi incluído nos testes.
