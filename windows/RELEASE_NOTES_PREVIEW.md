# SaúdePrática Windows 0.7.2 — Backup familiar e individual (.spbackup)

- Uma interface de backup com Família ou Perfil, ambos encriptados com palavra-passe.
- Restauro explícito de perfis existentes sem duplicar, com ID confirmado e backup de segurança cifrado antes da substituição.
- Exportação de fotos de perfis e caixas de medicação e documentos com SHA-256 verificado.
- Backup individual protege outros familiares, bloqueando ZIP original partilhado.
- Testes sintéticos de Android para Windows, edição e reexportação dos campos atualizados.
- A compatibilidade clínica requer ainda testes reais Android ↔ Windows.
- Não existe sincronização automática em tempo real. O instalador Windows continua experimental e sem assinatura de editor.

---
# SaúdePrática Windows 0.7.1 — Avisos de consultas

- A ficha dos agendamentos substitui o campo técnico reminders_minutes por cinco opções: **1 dia antes, 2 horas antes, 1 hora antes, 30 minutos antes, na hora da consulta**.
- São conservados os intervalos importados do Android que não constem destas opções. Ambos usam minutos: 1440 corresponde a um dia e 120 a duas horas.
- **Novo agente Windows:** verifica as consultas em segundo plano e apresenta avisos locais do Windows mesmo depois de fechares a janela principal. É iniciado automaticamente ao entrar na sessão Windows, na conta atual e sem privilégios de administrador.
- As notificações mostram apenas a data/hora, sem revelar dados clínicos ou nomes dos pacientes no ecrã bloqueado. Os avisos já enviados são controlados por identificadores anonimizados.
- Alterar a data, cancelar ou realizar uma consulta adapta os avisos futuros.
- Não é necessária Internet para os avisos Windows, mas o computador precisa de estar ligado, acordado e com a sessão iniciada. O modo Não incomodar ou as definições de notificações podem impedir a apresentação; após suspensão existe uma breve margem de recuperação.
- **O Android continua a emitir os avisos que já tem configurados.** Ainda não há sincronização automática Windows–Android. Alterações feitas na ficha Windows **não são enviadas automaticamente** ao Android; até existir sincronização, configurar os mesmos avisos no telemóvel.
- Os alarmes de medicação do Android não foram alterados e ainda não existem alarmes de medicação Windows.
- Sem exportação de informação clínica para serviços externos. Foram adicionados testes automáticos de cálculo, segurança, configuração e prevenção de duplicações.
- Instalação experimental e ainda sem certificado de editor reconhecido no Windows.
