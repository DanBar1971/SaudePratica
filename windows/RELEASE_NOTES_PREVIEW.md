# SaúdePrática Desktop 0.3.0 — Windows experimental

## Identidade visual corrigida
- **Ícone oficial SaúdePrática** incorporado no executável, ícone dos atalhos, Menu Iniciar e desinstalador. Deixa de aparecer o logótipo genérico do Python.
- **Splash de arranque** com a imagem de abertura oficial fornecida, mostrado durante a inicialização.
- Aplicação empacotada em **modo pasta (onedir)** no instalador. Isto evita a extração temporária completa feita em cada arranque do antigo executável onefile.
- Botões arredondados, seletores escuros, painel inicial com fundo e ícone oficiais, melhor hierarquia e espaçamento.
- Mantém a ficha de medicação num único ecrã, sem janelas sequenciais para preencher.
- Instalação e desinstalação em português, ícones personalizados e opção de atalho no Ambiente de Trabalho.

## Instalação e preservação de dados
Instala a 0.3.0 **por cima da 0.2.0**, sem desinstalar. O diretório de dados Windows e o formato DPAPI **não foram alterados**; os perfis e medicamentos da experiência anterior continuam no mesmo local.

Se o Windows ainda mostrar o ícone antigo num atalho afixado à barra de tarefas, remove a afixação antiga e volta a afixar o novo atalho do menu Iniciar. O Windows pode manter uma cache de ícones.

## Limitações
A versão continua **experimental e sem assinatura digital de editor Windows**. Ainda não há sincronização bidirecional Android ↔ Windows nem restauro de backups Android. O Windows não substitui os alarmes de medicação do Android. Testa com dados fictícios.

O backup experimental .spbackup continua protegido por palavra-passe e compatível com as versões Windows anteriores. Não expor dados clínicos nem passwords no GitHub.
