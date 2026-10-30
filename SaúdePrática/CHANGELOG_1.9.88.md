# SaúdePrática v1.9.88 — notas de implementação (aguarda validação)

**Estado de publicação:** APK compilada, assinada com o certificado original, verificada e publicada na [Release pública v1.9.88](https://github.com/DanBar1971/AndroidAppDev/releases/tag/v1.9.88) em 27-10-2026. **Testes no Android real continuam necessários.**

- **Alarme no ecrã bloqueado:** separada a tarefa visual do alarme da tarefa da aplicação/PIN. Android 14+/HyperOS continua a exigir autorização de ecrã completo e pode aplicar limitações.
- **Perfil associado ao telemóvel:** seleção explícita por ID estável dentro da ficha de perfil. O perfil cuidador é usado como preferência de compatibilidade quando não há escolha explícita.
- **Outros perfis:** passam a receber notificação normal, não ecrã completo/alarme forte, mantendo o registo pendente no perfil correto.
- **Tomas agrupadas:** confirmações individuais; ao premir TOMEI num grupo cria/garante cada pendência antes de abrir o módulo TOMAS. ADIAR 10m mantém regras introduzidas na v1.9.86.
- **Desativar horário:** caixa de seleção «Sem alarme · retirar horários deste medicamento» na edição. Mantém medicamento e histórico.
- **Sincronização:** os cartões de tomas pendentes recebidos são ocultados **apenas na vista de cuidador** quando têm o mesmo nome-base, medicamento e hora que o perfil principal. Nenhum perfil ou registo é apagado nem fundido. Continua pendente o emparelhamento consciente dos IDs remotos que originam nomes «recebido de …».
- **Atualizador de APK:** mantém correção PackageInstaller.Session da v1.9.87, com confirmação do Android.

## Conclusão obrigatória antes de anunciar «versão pronta»
Compilação Gradle release bem-sucedida; APK assinada com certificado histórico; verificações de integridade; testes de alarme e sincronização; Release v1.9.88 publicada com asset exato `SaudePratica.apk`; link `releases/latest/download/SaudePratica.apk` verificado byte-a-byte no workflow.

Documentação detalhada: [pendentes e critérios de teste](PENDENTES_2026-10-27_ALARMES_CUIDADOR_SYNC.md).
