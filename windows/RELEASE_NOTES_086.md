# SaúdePrática Windows 0.8.6 — Calendário redesenhado

Pré-visualização Windows 10/11 (64 bits), evoluindo da 0.8.5. O Android oficial não foi alterado.

## Calendário
- Nova vista mensal de aspeto semelhante a um calendário tradicional: dias organizados em células altas, número do dia em destaque e marcações dentro da própria célula.
- Dias com uma ou mais marcações ficam coloridos, com contador de marcações e breve descrição da primeira. Mesmo dias fora do mês são distinguíveis quando têm compromissos.
- Dia selecionado em turquesa; dia de hoje com contorno próprio. Ambos os destaques coexistem com o número de marcações.
- Legenda de cores, cabeçalho do mês melhor organizado e navegação anterior/seguinte ou Hoje.
- Lista por baixo do calendário com data por extenso, hora, título, local, estado (Pendente/Realizada/Cancelada) e acesso à ficha.
- Estado vazio apresentado como um cartão discreto; menos espaço desperdiçado.
- Conteúdo integral deslocável para funcionar em ecrãs menores e com letras maiores; cores específicas para tema claro e escuro.
- Sempre **somente o perfil ativo**. Os dados originais, marcadores de estado, horas e identidade das marcações mantêm-se inalterados.

## Mantido da 0.8.5
- Tomas com histórico e confirmação explícita, separadas por perfil.
- Agenda e edição em ecrã completo, backups encriptados e documentos por perfil.
- Descoberta da APK auxiliar Android pela rede local e convite de ligação (sem sincronização clínica automática).
- Agente autónomo dos avisos de consultas e documentos/OCR local; instalação por cima da anterior.

## Validações e limites
- Testes de perfil, colorização, tema claro/escuro, marcas visuais, datas e estados; ensaios da aplicação Python e EXE empacotado em Windows.
- Não existem alarmes de medicação Windows; registo de tomas Android ainda não é sincronizado automaticamente.
- Instalador experimental sem assinatura digital. Fazer backup .spbackup antes da atualização e testar com dados fictícios sempre que possível.
