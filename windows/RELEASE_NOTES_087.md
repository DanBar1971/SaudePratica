# SaúdePrática Windows 0.8.7 — Calendário e Documentos lado a lado, Opções e Links

Atualização experimental Windows 10/11 x64, a partir da versão 0.8.6.

## Calendário
- Vista em dois painéis: esquerda com calendário mensal compacto, direita com as marcações do dia escolhido.
- Dias com marcações destacados com cores e contadores; hoje e dia selecionado distinguem-se.
- Horário, título, local e estado em linhas compactas; scroll apenas na lista da direita.
- Edição de qualquer agendamento através do botão Abrir; usa exclusivamente o perfil ativo.

## Documentos
- Lista de PDF/imagens do perfil à esquerda; pré-visualização da página à direita.
- Botão Abrir para visualização ampliada numa janela própria, com navegação entre páginas PDF.
- Botão Imprimir para a impressora predefinida do Windows, após confirmação explícita.
- Botão Guardar como para exportação intencional de ficheiros desencriptados.
- PDFs e imagens são desencriptados apenas em memória para pré-visualização e envio à impressora; sem criar ficheiros temporários em claro. A fila de impressão Windows poderá manter dados conforme as regras do sistema.
- Seleção de documento reposta ao mudar de perfil; arquivo DPAPI e backups anteriores mantidos.

## Menu e Opções
- Dicas e Informações, Backup e Restauro e Sincronização acessíveis por **Opções**, não pela grelha principal.
- SNS 24 e IPO Lisboa retirados da grelha principal e criados como atalhos Web na secção **Atalhos Importantes**:
  - https://www.sns24.gov.pt/pt/inicio
  - https://www.ipolisboa.min-saude.pt
- Em Opções, gestor de atalhos para criar, editar, remover e alterar ordem (↑ e ↓).
- Lista de links preservada no armazenamento local protegido por DPAPI e incluída nos backups completos.
- URLs limitados a http:// e https://; bloqueados esquemas inseguros e credenciais embutidas.

## Preservação
- Os dados clínicos e os horários originais não são alterados pelo novo desenho.
- Tomas, Medicação, Agenda, fotografia, OCR, backup, Avisos e emparelhamento LAN existentes mantidos.
- Ainda não há sincronização clínica automática entre Windows e Android nem alarmes de medicação Windows.
- Antes de atualizar, fazer backup da família .spbackup; executar o instalador por cima da versão anterior sem apagar dados.
- Instalador experimental ainda sem assinatura digital de editor.
