# SaúdePrática 1.9.102 — auditoria dos alarmes e isolamento por perfil

## Causa confirmada no código (não é um teste em dispositivo)
- `SaudePraticaApplication.onActivityResumed()` chamava `AppPinActivity` também sobre `MedicationAlarmActivity`. Um alarme com o ecrã bloqueado podia apresentar um PIN da própria app, mesmo sendo um alarme independente.
- O serviço confundia a importância do processo `IMPORTANCE_FOREGROUND` (devido ao serviço de som/voz) com uma **janela visível**, tentando abrir o ecrã indevidamente.
- Havia `FLAG_DISMISS_KEYGUARD` na Activity do alarme, flag obsoleta que não é necessária para mostrar o ecrã sobre o bloqueio.
- `IntakeBadgeManager`, `MainActivity` e `HealthRecordsActivity` misturavam contadores/listas de familiares no perfil do cuidador.
- `DeviceAlarmRouting` associava implicitamente a identidade do cuidador ao dono dos alarmes neste telemóvel. O papel de cuidador não equivale a paciente local.
- `NotificationReceiver` criava uma notificação adicional por familiar. Agora deixa o registo no perfil correto, sem mostrar o alarme/notificação desse familiar neste aparelho.

## Invariantes de comportamento
1. O alarme legítimo toca e mostra **ADIAR 10M** + **TOMEI** sem abrir a página de PIN da SaúdePrática.
2. Com PIN do sistema, não se tenta contornar o bloqueio do dispositivo para abrir a app; apenas a Activity de alarme usa `setShowWhenLocked` e `setTurnScreenOn`.
3. **ADIAR 10M** silencia e fecha, sem confirmar medicação; reagenda na identidade (perfil, medicamento, horário original).
4. **TOMEI** confirma só os medicamentos desse evento/perfil, nunca abre MainActivity e deve ser idempotente.
5. Sem interação, o alarme termina após 60 s, as doses ficam por confirmar no perfil correto, com acesso protegido por PIN aos dados clínicos.
6. Um cuidador pode consultar contadores individuais na **escolha de perfil**, mas a página Tomas e o contador do módulo mostram exclusivamente o perfil selecionado.
7. A associação de alarmes é explícita por telemóvel, independente do papel cuidador; seleciona **📱 Associar alarmes a este telemóvel** na escolha de perfil.
8. Imagens e a opção **💊 NÃO TEM CAIXA · Só lamelas/blisters** ficam disponíveis na ficha de medicação.

## Testes manuais obrigatórios no Xiaomi/HyperOS
- Ecrã ligado e desbloqueado; ecrã bloqueado com PIN; ecrã apagado; app em primeiro plano, em segundo plano e encerrada; reinício do telefone.
- Com e sem permissão de ecrã inteiro. Confirmar se o Xiaomi mostra ecrã completo ou aviso destacado (comportamento controlado pelo OS).
- Testar dois medicamentos às 07:00: um único ecrã, duas confirmações individuais; verificar que o aviso de outro perfil não aparece.
- Carregar **ADIAR 10M** duas vezes e confirmar que não surge PIN, que o som pára, e que nenhum registo é dado como tomado.
- Carregar **TOMEI** sem desbloquear o PIN da SaúdePrática: verificar registo correto e que não abre o login.
- Deixar tocar 60 segundos, verificar tomas por confirmar sem marcar automaticamente como “não tomou”.
- Alternar entre perfil cuidador, paciente local e familiar: os contadores do módulo Tomas não somam outros perfis.
- Confirmar teste de notificação, permissões de `Notificações em ecrã inteiro`, `Alarmes e lembretes`, execução em segundo plano e ausência de restrições de bateria.

## Limite do Android (não é um bug que a app possa superar)
No Android 14+, uma Full-Screen Intent **com permissão** abre automaticamente no ecrã bloqueado ou apagado. Quando o telemóvel está desbloqueado, o sistema pode mostrar um banner destacado (heads-up) em vez de abrir a Activity. Com a permissão negada, pode não abrir sequer sobre o bloqueio; é necessário ativar `Notificações em ecrã inteiro` nas permissões especiais. A app não deve contornar o PIN do telemóvel por código.

**Sem garantia de teste real:** os gates automáticos verificam invariantes de código e compilação, não a política concreta do Xiaomi.
