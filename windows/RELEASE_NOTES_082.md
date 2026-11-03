# SaúdePrática Windows 0.8.2 — hora única da medicação

- **Correção do problema de horários duplicados:** nas versões anteriores, era possível mudar a hora de toma em `time` (ex.: 08:00), mas o catálogo usava `reminder_time` (07:00) para mostrar «Aviso 07:00».
- Agora só existe **Hora de aviso (HH:MM)** para introduzir horários. A outra entrada é **Condição da toma**, destinada a indicações como «jejum», «ao almoço» ou «após as refeições», nunca a outra hora.
- Ao guardar, a hora escolhida é validada e sincronizada nos campos locais de horário; os cartões e a previsão de próxima toma usam esse mesmo valor.
- Se um medicamento antigo contiver duas horas diferentes, aparece **Usar hora anterior 08:00** (ou a hora realmente guardada), para o utilizador optar conscientemente. A app não muda automaticamente um horário clínico.
- A gravação recusa duas horas contraditórias, mantendo o perfil, dose, suspensão, documentos e dados originais Android intactos.
- Os testes de regressão simulam a sequência 07:00/08:00, guardam a correção, reabrem a base de dados e verificam a hora no cartão e na próxima toma.

**Importante:** os avisos de medicação são produzidos pelo Android. Alterar a ficha **Windows não modifica os alarmes no Android**, pois a sincronização automática ainda não existe. Confirma e altera separadamente a hora no telemóvel quando necessário.

O restante ambiente 0.8.1 mantém-se: fichas compactas, OCR local de PDF e imagens, documentos por perfil e agente de Avisos independente sem splash. Instalação experimental; guarda um `.spbackup` antes de atualizar.
