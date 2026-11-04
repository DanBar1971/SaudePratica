# Agente IA SaúdePrática — base de autorização (não lançada)

Código experimental **isolado**, preparado para o futuro adaptador de agente Android. Não altera a aplicação publicada, os alarmes ou os dados de pacientes.

## Estado
- ✅ Camada pura de autorização: perfil desbloqueado, ativo e autorizado.
- ✅ Comandos tipados: consultas e preparação de rascunhos de Agenda/Medicação.
- ✅ Negação explícita de escritas clínicas e ações como TOMEI/ADIAR.
- ✅ Oito verificações Kotlin executadas localmente com `kotlinc`.
- ⛔ Ainda sem modelo local, ecrã de chat, integração com DataRepository, testes de dispositivo, pipeline de assinatura ou APK.
- ⛔ Não tratar este código como integração funcional ou como versão 1.9.xxx.

## Próxima integração
1. Adicionar backend local Google ADK Kotlin + LiteRT-LM **apenas quando validado em dispositivos reais**. Modelo descarregável por decisão explícita do utilizador, com consentimento para consumo de espaço e energia; modo ajuda offline alternativo nos aparelhos incompatíveis.
2. Adaptar `SmartHelpActivity` para interface de conversa com a ajuda clássica disponível.
3. Expor ferramentas **somente** por gateway nativo. Sempre que o modelo propuser uma chamada, reconstruir `AgentSession` do estado seguro atual da app e aplicar `AgentAuthorization.check` imediatamente antes da execução.
4. Leitura só de dados do perfil selecionado; controlar permissões do cuidador na camada de dados, nunca apenas no prompt do modelo.
5. Para criar/alterar agendamentos ou medicação, chamar os editores atuais em **rascunho**, e guardar apenas após revisão e confirmação humana na ficha nativa. A IA não altera posologias, doses, alarmes ou estados clínicos automaticamente.
6. Alarme e aviso de consulta independentes do LLM; preservação integral de `NotificationScheduler`/TOMEI/ADIAR.
7. Testar regressões, custo de armazenamento, compatibilidade Android, atualização sobre 1.9.127 e assinar apenas com certificado original.

O protocolo e critérios de aceitação estão em [issue #51](https://github.com/DanBar1971/SaudePratica/issues/51).

### Executar teste puro de autorização

```bash
kotlinc MediAgenda/agent-foundation/AgentAuthorization.kt MediAgenda/agent-foundation/AgentAuthorizationTest.kt -include-runtime -d /tmp/sp-agent-test.jar
java -jar /tmp/sp-agent-test.jar
```

Esta base foi mantida **fora do build da app**, deliberadamente, até haver implementação do motor local e testes de integração. Não publicar uma APK que apenas mude o nome da Ajuda para 'Agente IA'.
