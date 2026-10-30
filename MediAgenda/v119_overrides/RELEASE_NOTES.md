# SaúdePrática v1.9.100 — Alarme de medicação

- **TOMEI** confirma imediatamente, dentro do próprio ecrã de alarme ou da notificação, sem abrir login nem Tomas. Com vários medicamentos à mesma hora, confirma cada medicamento como registo separado; o botão pressupõe que **todos os medicamentos listados** foram tomados.
- **ADIAR 10M** termina toque/vibração/ecrã, mantém as tomas pendentes e agenda nova tentativa 10 minutos mais tarde, sem novo aviso intermédio. Adiar não confirma toma.
- Após **60 segundos sem resposta**, termina o som e regista cada medicamento como **alarme sem resposta / toma por confirmar**, com contador imediato e acesso a Tomas. Isto **não prova** que a pessoa se esqueceu da medicação.
- Se o ecrã de alarme estiver visível e o telemóvel desbloqueado, abre diretamente Tomas ao terminar o tempo. Se o telemóvel ainda estiver bloqueado ou Android proibir abertura em segundo plano, deixa uma notificação privada que abre Tomas **após desbloqueio**, sem revelar informação clínica por cima do PIN.
- Corrigido falso estado de foreground: a aplicação já não suprime o pedido de ecrã inteiro quando o processo continua em memória mas a janela não está realmente à frente. Canal de alarme HIGH novo, pedido FSI sempre emitido.
- Mantidos os perfis, o histórico, as fotografias das caixas, as imagens oficiais (ícone, splash e fundo), a sincronização, a Nutrição e a identidade Android **com.mediagenda.app.stable**.

**Limitação do Android/HyperOS:** Android 14+ apresenta uma notificação destacada quando o dispositivo está desbloqueado e outra app está em primeiro plano, mesmo com FSI autorizado. O sistema não permite garantir abertura automática de ecrã inteiro em todas as circunstâncias. Ativar **Notificações**, **Alarmes exatos**, **Notificações em ecrã inteiro**, e no Xiaomi permitir atividade em segundo plano e sem restrições de bateria. Validar no telemóvel real.

**Testes recomendados:** dispositivo bloqueado/desbloqueado, aplicação aberta/fechada, toma única/grupo, dois TOMEI rápidos, adiamento por 10 minutos, 60 segundos sem interação, reboot com adiamento pendente, ausência de duplicados e verificação de que o PIN só surge quando alguém acede voluntariamente à app protegida.

**Segurança:** nenhuma chave de assinatura ou dados de utentes são publicados em texto simples; manter o certificado original para preservar a atualização sobre v1.9.99. Não desinstalar a versão existente.
