# SaúdePrática Desktop 0.7.5 — perfis sem mistura de dados

Correções verificadas com dados de teste, após auditoria local de um backup do utilizador (nenhum dado privado foi publicado).

- **Perfil cuidador:** a identificação é recuperada de `saudepratica_caregiver_v1/caregiver_id` e aplicada apenas à pessoa com o mesmo identificador de origem Android. O interruptor é atualizado quando os dados chegam em segundo plano, sem eliminar edições em curso.
- **Fim da mistura de campos:** os valores do perfil são extraídos apenas de fontes de identificação autorizadas, nunca de ficheiros de medicação, Agenda, registos clínicos, documentos ou Emergência. O leitor já não procura `notes` recursivamente.
- **Notas de medicamentos:** uma nota de medicamento que apareça por engano como nota pessoal na base Windows não é reexportada no `profile.json`; continua preservada no registo original do medicamento.
- **Contactos SOS:** removidos do formulário Perfil Windows, seguindo a estrutura Android. Campos SOS legados ficam preservados em armazenamento protegido para não haver apagamentos ao guardar o perfil.
- Mantém o visual aprovado em 0.7.4: fotografias autênticas do Cartão de Cidadão, ficha com campos pessoais e leitura diferida do backup.
- Mantém a instalação por cima da versão anterior e o agente residente de avisos da Agenda.

**Limitação importante:** a importação Windows → Android continua em validação e ainda não deverá ser utilizada para substituir dados clínicos reais até existir correspondência e testes abrangentes de todos os campos, incluindo cuidador e CC.

Build Windows 0.7.5 compilada e ensaiada com 112 testes automatizados, GitHub Actions #41458179893. O backup usado na análise não foi incluído no código nem nos artefactos.
