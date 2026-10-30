# SaúdePrática v1.9.117 — Hidratação em ecrã completo e letras grandes

- **Configurar hidratação** passa a ocupar a área útil do ecrã, em vez de uma janela flutuante.
- O rodapé **Cancelar** e **Ativar e guardar** deixa de ter altura fixa de 50 dp. Os botões crescem com o tamanho de letra definido no Android e permanecem lado a lado.
- O teclado passa a ajustar o ecrã do formulário, sem retirar os botões de confirmação da janela.
- Mantidos os horários, intervalos, volume por copo, objetivo diário e callbacks de guardar/cancelar.
- **Alarmes da medicação NÃO alterados.** A app já mede o intervalo real entre a hora agendada e a receção pelo Android em Mais → Opções → Segurança e notificações. Sem permissão para alarmes exatos, o Android usa um agendamento aproximado, que pode atrasar o aviso.

## Testes necessários em equipamentos reais
1. Na configuração de hidratação, testar letras normais e letras muito grandes, teclado aberto e fechado, com scroll até ao fim.
2. Confirmar que **Ativar e guardar** realmente guarda e que **Cancelar** não guarda.
3. Num Xiaomi, confirmar **Pontualidade dos alarmes** e **Diagnóstico do último alarme de medicação** após um alarme real (a app regista hora prevista e hora de entrega, não o atraso da confirmação TOMEI).
4. Confirmar o alarme com telemóvel bloqueado, grupos de medicamentos, ADIAR 10 MIN e TOMEI.

Não foram modificados os dados clínicos, a assinatura Android, a identidade da aplicação, os recursos gráficos ou a implementação dos alarmes. Compilação e testes automáticos não substituem a validação no telemóvel.
