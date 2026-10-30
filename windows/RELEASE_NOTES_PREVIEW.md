# SaúdePrática Desktop 0.5.0 — Cartões visuais (experimental)

## Novo ambiente
- Menu principal redesenhado como **catálogo de cartões compactos**, com ícones maiores e coloridos, inspirado na organização da referência de cinema e na app SaúdePrática Android.
- Todos os módulos conhecidos do Android apresentados no painel, com pesquisa. Funcionalidades não desenvolvidas no Windows são claramente identificadas como **Em breve**, sem falsa gestão clínica.
- **Medicação em galeria de cartões**: fotografia verdadeira da embalagem, nome, dose, horário e estado (ativa, suspensa, sem alarme).
- Pesquisa de medicamentos e filtros Todos / Ativos / Suspensos / Sem alarme. Clicar no cartão abre a ficha integrada.
- Importação de fotografia da embalagem a partir de um ficheiro real do utilizador, comprimida e guardada no armazenamento local encriptado. Nada é enviado para a Internet.
- Perfis com fotografia real, nome e indicação de cuidador.
- Controlo dos tamanhos: botões, inputs, cabeçalhos e margens compactados para mais conteúdo visível.

## Tema claro e escuro
- Paletas explícitas em cada campo, botão, etiqueta, caixa de texto e seletor, melhorando o contraste em modo claro.
- Testes de contraste e testes de arranque do **executável Windows**, cobrindo Início, Perfis, catálogo, edição de medicação e Aspeto em Claro/Escuro/Sistema.

## Preservação e limites
- Instala por cima da 0.4.1 sem desinstalar. Não muda o caminho de dados DPAPI nem a estrutura dos backups .spbackup.
- Backups Windows continuam encriptados por palavra-passe e incluem fotografias de perfis e medicamentos.
- **A versão Windows não sincroniza com Android e não emite os alarmes do telemóvel.**
- Agenda, Tomas, Nutrição, Situação Clínica e outros módulos ainda não são funcionais no Windows.
- Instalador experimental sem assinatura digital de editor Windows. Testar com dados fictícios.

Site oficial: https://danbar1971.github.io/SaudePratica/
