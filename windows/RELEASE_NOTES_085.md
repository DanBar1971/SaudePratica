# SaúdePrática Windows 0.8.5 — Tomas e Calendário

Pré-visualização Windows 10/11 x64, desenvolvida a partir da 0.8.4. Não altera o APK oficial Android.

## Novidades
- **Calendário mensal:** navegar mês a mês, voltar a Hoje e selecionar um dia. O número de marcações aparece em cada dia; abaixo fica a lista cronológica de todas as marcações desse dia, com hora, local e estado.
- **Abrir marcação:** qualquer marcação com identificador abre a ficha existente da Agenda, onde continuam disponíveis edição, cancelamento e avisos.
- **Tomas:** listagens Todas / Por confirmar / Confirmadas por dia, estado dos horários realmente programados, e registo manual **apenas após confirmação explícita**.
- **Atrasada por confirmar** significa exclusivamente que passaram 15 minutos da hora prevista sem confirmação local. Não representa uma dose clinicamente omitida ou um alarme disparado.
- **Perfil isolado:** Calendário, Tomas, medicação e agendamentos usam sempre o identificador do perfil ativo. Não há agregação silenciosa de dados de outras pessoas.
- Os registos de toma Windows ficam cifrados no armazenamento local, são preservados pelo formato de backup encriptado .spbackup e podem ser apagados individualmente mediante confirmação.
- Reutilizados os controlos e botões existentes, o fundo e a identidade visual da aplicação; mantidas as funcionalidades da 0.8.4, incluindo a descoberta Wi-Fi LAN para pedido de ligação ao Android.

## Limitações e cuidados
- O Windows **não cria alarmes de medicação** nesta versão e não confirma tomas automaticamente.
- A lista de tomas previstas só é projetada quando existe uma regra fiável de repetição diária, semanal ou datas explicitamente agendadas. Medicamentos SOS, sem alarme ou suspensos não geram automaticamente tomas pendentes.
- O histórico de tomas confirmado **no Android não é importado automaticamente** como tomas Windows; a ligação LAN da 0.8.4 ainda não transfere dados clínicos. É necessário desenvolver e testar a reconciliação bidirecional antes de a ativar.
- Nunca criar dados fictícios com significado clínico. Os testes usam apenas perfis/medicamentos de demonstração.
- O instalador não tem assinatura digital de editor; o aviso SmartScreen pode aparecer. Não desativar a proteção geral do Windows.
- Fazer backup da Família .spbackup antes de atualizar, e validar dados no computador de testes. A atualização deve usar o instalador normal sem apagar dados anteriores.

## Verificações de build
- Testes Python de calendário, fronteira de perfis, horários genuínos, duplicados e backup.
- GUI smoke real em Windows com ecrãs Tomas e Calendário, perfis sintéticos separados.
- Verificação adicional do executável empacotado, OCR e agente Avisos.
- SHA-256 do instalador publicado com a release.
