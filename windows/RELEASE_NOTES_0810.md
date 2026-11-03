# SaúdePrática Windows 0.8.10 — Módulos 6 a 12

Nova versão experimental Windows 10/11 x64, a partir da 0.8.9. Os módulos agora têm fichas reais e dados protegidos por perfil. A app Android não foi alterada.

## 6. Nutrição e fotografias originais
- Diário privado de refeições: data, hora, tipo, alimentos/porções, energia, proteínas, hidratos, gorduras, notas, fotografia opcional.
- Fotografias guardadas como anexos cifrados DPAPI; pré-visualização sem descarregar para a Internet.
- **Importar refeições e fotos do Android**: lê apenas `saudepratica_meal_diary/<source_id>/meals.json` e os JPEGs com IDs correspondentes, do backup Android original **já guardado** no Windows e ligado ao perfil ativo. Os outros perfis não são lidos para esse destino; importação por ID estável e não duplica registos.
- O backup completo Android inclui a pasta `saudepratica_meal_diary`, desde que os registos existam no momento da cópia. Se um ZIP anterior não contiver refeições recentes, é necessário criar novo backup no Android e importá-lo.
- A versão Windows **não volta a analisar as fotografias com IA nem inventa valores nutricionais**; apresenta os números originalmente guardados ou introduzidos manualmente.
- Sem sincronização automática bidirecional da Nutrição com Android nesta versão.

## 7. Saúde Visual
- Fichas de exame/receita com data, profissional, esfera/cilindro/eixo/adição de cada olho, distância pupilar, observações e documento protegido do perfil.
- Transcrição de receitas existentes, não um teste de visão nem prescrição automática.

## 8. Sintomas
- Diário individual com descrição, intensidade validada 0–10, tipo (sintoma / possível efeito secundário), data, evolução, notas e documento opcional.
- Não classifica gravidade nem sugere tratamentos. Sintomas alarmantes ou preocupantes requerem assistência clínica.

## 9. Vacinas
- Histórico de vacinação com nome, data da dose, próxima data opcional, lote, unidade, notas e comprovativo; criação/edição/remoção.
- A ficha não valida o Programa Nacional de Vacinação nem decide necessidade de doses.

## 10. Emergência
- Ficha por perfil com contacto principal, telefone, segundo contacto, alergias, doenças crónicas, informações médicas, grupo sanguíneo se confirmado e notas.
- Botão para abrir marcador telefónico apenas depois de confirmação explícita. 112 identificado como número nacional de emergência em Portugal, mas o Windows requer um marcador configurado. Não são efetuadas chamadas nem enviados SMS/WhatsApp automaticamente.
- Não cria informações médicas a partir de campos de outro perfil.

## 11. Farmácias
- Favoritos pessoais com nome, morada, localidade, telefone, website validado e observações.
- Atalhos informativos SNS 24 e Infarmed e botão Ligar com confirmação.
- **Sem geolocalização, pesquisa em tempo real, horários de serviço ou disponibilidade garantida**; confirmar diretamente com a farmácia.

## 12. Lares e Apoios
- Três áreas: Instituições/Contactos (ERPI, SAD, Centro de Dia), Faturas/ADSE e Apoios.
- Dados da instituição, morada, contactos, admissão, responsável e contrato associado aos Documentos.
- Faturas com mês/data, instituição, estado manual, valor faturado/pago/reembolsado, referência e comprovativo.
- Apoios ADSE/Segurança Social/complementos com estado **introduzido manualmente**, referência e documento. Links para portais oficiais externos.
- A app não faz submissões, calcula elegibilidade nem promete reembolsos. O acompanhamento mensal continua a depender do utilizador e das entidades responsáveis.

## Dados, testes e continuidade
- Os seis grupos de registos e a ficha de Emergência ficam **estritamente no perfil ativo** no arquivo local Windows DPAPI.
- O backup `.spbackup` inclui todos estes dados e as fotografias novas/importadas, sem substituir medicação, tomas, agenda ou outros dados.
- O backup de um único perfil é bloqueado quando depende de um ZIP Android familiar; usar **Backup Família** para garantir que não inclui dados de terceiros inadvertidamente.
- Testes automáticos com perfis e fotos sintéticos, fronteiras de privacidade, importação idempotente do ZIP Android, backup e ensaios da interface/EXE Windows.
- A sincronização automática Android ↔ Windows destes sete módulos continua por desenvolver.
- Continuam pendentes melhorias anteriores de sincronização clínica e importação Health Connect/Hidratação, já identificadas no projeto.

**Antes de instalar:** guardar backup familiar `.spbackup`; instalar por cima da 0.8.9. O instalador é experimental e não está assinado digitalmente.
