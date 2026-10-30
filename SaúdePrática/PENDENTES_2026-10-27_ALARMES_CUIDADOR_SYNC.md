# SaúdePrática — alarmes, cuidador e sincronização (27-10-2026)

**Origem:** relato do utilizador e captura de ecrã, após as versões v1.9.85/v1.9.86. Pendentes de implementação, compilação, teste e Release. Nunca apresentar como resolvidos apenas por haver código em GitHub.

## 1. Alarme à frente de tudo, com ecrã bloqueado

- Mesmo com SaúdePrática encerrada ou no background, a Activity do alarme deve surgir sobre o ecrã bloqueado e apresentar o(s) medicamento(s) e opções «ADIAR 10 MIN»/«TOMEI».
- Atualmente ouve-se o alarme, mas surge login/PIN da app e o ecrã do alarme fica por detrás.
- Preservar proteção dos restantes módulos: mostrar alarme sem PIN, exigir autenticação se necessário ao entrar na parte clínica.
- Validar permissões de full-screen intents (Android 14+/HyperOS), notification channel HIGH, TURN_SCREEN_ON/SHOW_WHEN_LOCKED, gestão da bateria e permissões especiais específicas do equipamento. Sem prometer contornar limitações do SO.
- Testar app fechada, ecrã desligado, bloqueio ativo, e app aberta em segundo plano.

## 2. Alarmes agrupados por perfil e hora

- Cada grupo de várias medicações com hora coincidente apresenta lista com **nome e dose de cada um**, não fotografias.
- Preservar fotografia, nome e dose no alarme de um único medicamento.
- Ao premir **ADIAR 10 MIN**, criar/atualizar uma toma **pendente individual por medicamento**, não uma confirmação; reagendar grupo completo e evitar registos repetidos.
- Ao premir **TOMEI**, abrir diretamente TOMAS **do mesmo profileId** do alarme e mostrar todas as tomas individualmente, aguardando confirmação uma a uma.
- Não marcar todos os medicamentos tomados automaticamente; cada confirmação deve ser explícita.

## 3. Poder retirar a hora/alarmes de uma medicação

- Na edição de Medicação, oferecer «Sem alarme / Retirar horário» para limpar a hora previamente selecionada sem apagar o medicamento.
- Cancelar/reagendar PendingIntents antigos; não gerar notificações novas de medicação sem hora; manter histórico de tomas.

## 4. Perfil cuidador e associação deste telemóvel

- A app contém quatro perfis e o utilizador atual é cuidador.
- Criar seleção persistente de «Perfil associado a este telemóvel», por ID estável e independente do perfil ativo que se esteja a consultar.
- Só medicação do perfil associado ao dispositivo deve originar alarme de ecrã completo/voz/som.
- Para medicação e agenda de outros perfis, mostrar **notificação normal** na hora marcada, com nome de utente e evento, sem alarme intrusivo.
- Guardar lembretes/tomas pendentes no ID do perfil de origem, mantendo separação de dados médicos.

## 5. «Regina (recebido de ...)» duplicada

No ecrã «Tomas», mesmo medicamento Eliquis, mesma data/hora 27-10-2026 07:00:
- «Regina»
- «Regina (recebido de 6c2c59)»
- «Regina (recebido de 6e96a4)»

Estas entradas sugerem perfis clonados na sincronização. Auditar a importação/mescla (ID estável do utente, ID original dos registos e identificação do dispositivo). Evitar que receber novamente o mesmo perfil crie clones e triplique lembretes. Tornar a receção idempotente. Para duplicados legados, oferecer diagnóstico e associação segura, com backup e confirmação; **nunca apagar nem unir automaticamente perfis e dados clínicos sem correspondência comprovada**. Verificar também troca indevida dos nomes dos pais nas sincronizações.

## Critérios de conclusão

- Regressões testadas para medicação única, grupo, adiar, confirmar, bloqueio/alarme, PIN, perfis cuidador, agenda e sincronização bidirecional.
- Atualizar `versionCode`/`versionName`, documentar changelog.
- Compilar, verificar APK, assinar com certificado original, publicar GitHub Release contendo `SaudePratica.apk`, confirmar tag Latest e ligação funcional.
- Se qualquer etapa falhar, informar exatamente o que ficou pendente e não declarar versão concluída.

## Estado de implementação (27-10-2026)

- **Código preparado (sem validação de compilação nem APK confirmada):** patches `MediAgenda/v107_overrides/DeviceAlarmRouting.kt` e `apply_v107.py`. Workflow atualizado para **v1.9.88**.
- Foram preparados: seleção do utente associado ao telemóvel, notificação normal dos outros perfis, actividade do alarme em tarefa independente, registo individual de pendências ao tocar «TOMEI» em grupo, opção «Sem alarme» no editor, e ocultação na lista do cuidador apenas das entradas recebidas com mesma pessoa/nome de origem, medicamento e instante que o perfil principal.
- **Ainda pendente de teste real:** permissão de ecrã completo e comportamento HyperOS com PIN/lockscreen, alarmes nos dias seguintes após retirar horário, agrupamento/snooze, fluxos do cuidador, sintomas de clonagem na sincronização, e validação do APK assinado.
- **A fusão/associação permanente das cópias «Regina (recebido de...)» NÃO foi implementada**, para não misturar identidades e dados clínicos indevidamente. Os perfis e registos não foram eliminados. Deduplicação introduzida é só visual e só para avisos coincidentes com o perfil principal.
- **Release pública v1.9.88 não confirmada**: Git tag v1.9.88 ainda não estava acessível no último teste. Verificar Actions e publicação final antes de informar conclusão.

## Publicação verificada 27-10-2026
- [Release v1.9.88](https://github.com/DanBar1971/AndroidAppDev/releases/tag/v1.9.88): disponível com o ficheiro `SaudePratica.apk` (153237558 bytes), SHA-256 `e17b1476d376d0b8bb746c70fde9e6f88759b74bba18eafb8ba6ec4d7fea6de9`.
- [Workflow de publicação](https://github.com/DanBar1971/AndroidAppDev/actions/runs/40470790809): sucesso. APK reconstruída e verificada; certificado Android comparado com a v1.9.87; download Latest conferido byte a byte.
- **Continuam pendentes testes funcionais no telemóvel** e a associação definitiva de perfis duplicados por sincronização. Não fundir nem eliminar automaticamente dados clínicos.
