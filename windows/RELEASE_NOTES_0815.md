# SaúdePrática Windows 0.8.15 — Atividade e Saúde com histórico Android 1.9.134

Instalador experimental Windows 10/11 (64 bits), sucessor da 0.8.14.

## Novo — ler os dados Health Connect já guardados pelo Android
- Compatibilidade com o novo formato `saudepratica_health_connect/<perfil>/daily.json` produzido pela SaúdePrática Android **1.9.134** quando se abre/atualiza Atividade e Saúde.
- O restauro do backup familiar encriptado **.spbackup** (ou do ZIP Android original) importa as leituras automaticamente, associando-as ao identificador estável do perfil.
- Resumo do dia: passos, distância, calorias ativas e totais, duração do sono e frequência cardíaca, apenas quando presentes no backup.
- Evolução dos últimos sete dias com seleção de Passos, Distância, Energia ativa, Sono, Pulso ou Peso, sem representar dados ausentes como zero.
- Sinais vitais, quando presentes: SpO₂, frequência cardíaca em repouso, tensão arterial, frequência respiratória, temperatura e peso partilhado pelo Health Connect.
- O histórico de peso e altura **manuais da app Android** (`saudepratica_body_<perfil>`) também é recuperado e mostrado em painel independente, sem modificar o peso manual já registado no Windows.
- A data de captura é apresentada para distinguir claramente valores guardados no backup de dados em tempo real.
- Nas instalações Windows já existentes, o carregamento da 0.8.15 reprocessa automaticamente os ZIPs originais guardados, preservando o restauro anterior, as edições manuais e os dados de outros módulos. Um mesmo backup não duplica leituras; capturas mais recentes atualizam o valor do respetivo dia.

## Como obter dados
1. Atualizar a aplicação no telemóvel para Android **1.9.134**.
2. Em **Atividade e Saúde**, no perfil correto, abrir/tocar **Atualizar dados** para guardar as medições autorizadas do Health Connect.
3. Em **Backups e sincronização**, criar um **novo** backup familiar `.spbackup` (ou ZIP Android original).
4. Restaurar o novo backup na SaúdePrática Windows 0.8.15. Ao abrir Atividade e Saúde aparecem os dias e as medições efetivamente incluídos no ficheiro.

Os ficheiros antigos não contêm automaticamente as leituras Health Connect que o Android ainda não guardava. O backup original tem de ser criado **depois** de atualizar os dados na Android 1.9.134.

## Segurança
- Os dados Health Connect permanecem locais e encriptados pelo armazenamento Windows (DPAPI); não há acesso direto do PC à Health Connect, nem ligação clínica bidirecional.
- O importador valida a identidade da fonte Android, os carimbos de data, o formato e os intervalos dos números; apenas admite valores observados e guardados. Não mistura perfis.
- As medições manuais Windows e Android não são substituídas nem falsamente atribuídas à Health Connect.
- O backup .spbackup continua protegido com palavra-passe. Antes da primeira migração, o Windows cria uma cópia de segurança do seu armazenamento DPAPI original.
- Os alarmes, sincronização Nearby e outros módulos continuam sem alteração.
- Testes automatizados utilizam apenas registos e perfis fictícios; o backup clínico real não é carregado no GitHub.

**Ainda não é sincronização automática em tempo real:** o PC lê somente o backup escolhido pelo utilizador. Validar no equipamento real após instalação.
