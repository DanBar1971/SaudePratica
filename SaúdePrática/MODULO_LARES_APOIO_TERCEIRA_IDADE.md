# SaúdePrática — Módulo «Lares e Apoio à Terceira Idade»
Data da pesquisa: 2026-10-26
Estado: requisitos documentados; NÃO implementado na APK.

## Objetivo
Acompanhamento por familiares de pessoas em ERPI (residência), SAD (apoio domiciliário) ou Centro de Dia. Focar o trabalho mensal da fatura do lar para ADSE, sem duplicar as fichas de medicação, a agenda ou os Documentos Digitais da SaúdePrática.

## UX e navegação
- Entrada «🏡 Lares e Apoio à Terceira Idade» no início, com visibilidade configurável em Opções > Aspeto e idioma > Módulos.
- Ecrã inicial do módulo com instituição ligada ao **perfil ativo** (nunca partilhar automaticamente com outro perfil), valência, atalho Ligar, próximo compromisso, fatura do mês e ações pendentes.
- Separadores: Resumo; Instituição/Contactos; Faturas e ADSE; Apoios; Agenda/Visitas; Documentos; Cuidados e Notas.
- Modo de edição por cuidador autorizado, sem assumir poder de representação legal; ecrãs compatíveis com acessibilidade/sénior.
- Todas as operações com ficheiros e avisos exigem consentimento da pessoa que usa o dispositivo.

## Instituição e valência
Campos: instituição_id, nome, tipo entidade, valência (ERPI/SAD/Centro de Dia), morada, GPS opcional, telefone geral, telefone móvel, email, website, contactos personalizados, horários de visitas, contrato, observações, data de admissão e representante/contacto familiar.
- Permitir várias instituições no catálogo e associar cada perfil a instituição + valência.
- Evitar gravar dados desnecessários de utentes no catálogo institucional partilhável.
- Catálogo inicial **exemplo APATI**, editável e removível; NÃO impor APATI a outros utilizadores.

### APATI predefinida
Associação Promotora de Apoio à Terceira Idade (IPSS), Rua Palha Blanco 83, 2600-669 Castanheira do Ribatejo.
Website: https://apaticastanheira.pt/
Telefone geral: +351 263 290 281; móvel geral +351 912 181 696;
Secretaria: secretaria@apaticastanheira.pt
Diretora Técnica: Dra. Odete Santos +351 912 181 695 (09h–17h);
Encarregada: Rosa Gomes +351 913 391 973 (09h–17h).
Fontes: https://apaticastanheira.pt/contactos/ ; https://apaticastanheira.pt/servicos/
Valências: ERPI https://apaticastanheira.pt/valencias/erpi/ ; SAD https://apaticastanheira.pt/valencias/servico-de-apoio-domiciliario/ ; Centro de Dia https://apaticastanheira.pt/valencias/centro-de-dia/
ERPI: alojamento, refeições, higiene e roupa, enfermagem, medicina, fisioterapia, acompanhamento psicossocial, atividades.
SAD: refeições, higiene pessoal e serviços complementares conforme contratualização.
Centro de Dia: transporte, refeições, acompanhamento e atividades.
**Horário de visitas da ERPI 14h30–18h30** no regulamento publicado, com exceções; CONFIRMAR disponibilidade e versão atual junto do lar.

## Fluxo mensal «Fatura do lar → ADSE Direta»
Cada registo mensal tem:
- month YYYY-MM (mês a que a fatura respeita), perfil_id, instituicao_id, estado;
- valor mensal contratado; valor faturado; extras discriminados; valor pago; data/pagamento e comprovativo opcional;
- pedido_fatura_em; fatura_recebida_em; fatura_id, tipo fiscal, NIF do beneficiário, ficheiro PDF/JPEG/PNG associado ao perfil;
- entregue_adse_em; referência do processo opcional; comprovativo de submissão; estado de análise; valor_reembolsado; data_reembolso; observações;
- estados: POR_PEDIR → PEDIDA → RECEBIDA → SUBMETIDA → EM_ANALISE → REEMBOLSADA, com ramos «Pendente de correção» e «Não elegível/Não submetida». PAGA é atributo separado de RECEBIDA.
- Cada mudança de estado é manual, confirmada pelo utilizador; nenhum estado de aceitação ou reembolso é inferido a partir de uma partilha ou abertura do portal.
- Uma fatura / uma comparticipação por mês, conforme ADSE; impedir duplicação acidental com alerta, mas permitir substituição de ficheiro corrigido mantendo histórico.

Ações:
1. «Pedir fatura»: abrir email/partilha para a secretaria com texto pré-preenchido, EXIGINDO confirmação manual antes do envio; oferecer pedido de envio automático pela instituição em cada mês.
2. «Recebi fatura»: anexar por seletor de ficheiros ou câmara, abrir visualizador interno e inserir na biblioteca Documentos Digitais do mesmo perfil com categoria Lar/Faturas.
3. «Abrir ADSE Direta»: Intent ACTION_VIEW https://adsedireta.adse.pt/ no navegador predefinido; sem recolher senhas nem fazer upload supostamente automático.
4. «Marcar como submetida» com data/referência e PDF/screenshot comprovativo.
5. «Marcar como reembolsada» com valor/data e totais por ano.
6. Lembretes configuráveis para pedir a fatura, apresentar na ADSE e verificar pendentes, com ações «feito» e «adiar». Desativar ao avançar o estado. Nunca reutilizar canais de alarme de medicação.

### Regras ADSE e documentos
- Apoio específico em Lares e Apoio Domiciliário, sujeito à elegibilidade/autorização e situação de dependência: https://www2.adse.pt/sou-beneficiario/reembolsos/lares-e-apoio-domiciliario/
- Documentação de candidatura pode incluir pedido de apoio, avaliação clínica, relatório médico/formulário de situação clínica, IRS ou dispensa e comprovativo CGA/CNP de complemento por dependência, além de elementos da instituição; apresentar checklist **condicional**, não como requisitos universais imutáveis.
- Folheto oficial 2026: https://www.adse.pt/wp-content/uploads/2026/01/ADSE_flyer_Lares_2026.pdf
- Regras 2026 de ERPI: escalões de capitação até 736 € → 9,48 €/dia; até 1104 € → 7,98 €/dia; até 1472 € → 6,98 €/dia; teto de 80% da fatura. São **referência sujeita a confirmação**, NÃO autorização nem promessa de reembolso.
- 2026: botão «Adicionar» para documento novo; «Substituir» para correção; em https://www.adse.pt/noticias/noticias/adse-direta-lares-apoio-domiciliario/ .
- Informação ADSE de reembolso e comprovativos: https://www2.adse.pt/sou-beneficiario/reembolsos/como-pedir-o-reembolso/
- **Não enviar documentos por email à ADSE** como se isso formalizasse um pedido; submissão exclusivamente nos canais reconhecidos.
- Modelos oficiais/formulários e manual: https://www.adse.pt/sou-beneficiario/documentos-uteis/
- Integrar atalhos sem duplicar «Atalhos Importantes» do v1.9.78.

## Apoios (guia informativo, sem declaração de elegibilidade)
- ADSE — lares e apoio domiciliário: documentação, estado de pedido e atalho;
- Segurança Social — respostas sociais ERPI, SAD, Centro de Dia e regime de comparticipação da IPSS: https://www.gov.pt/guias/apoio-a-familia/apoio-social-para-idosos
- Complemento por dependência (necessidade de ajuda de terceiros, ver condições): https://www.gov.pt/servicos/obter-informacoes-sobre-o-complemento-por-dependencia
- Complemento Solidário para Idosos (meios económicos/condições): https://www.gov.pt/pt/servicos/pedir-o-complemento-solidario-para-idosos
- Informar que diferentes apoios podem interagir; não somar comparticipações sem verificação legal.
- É possível link para simulador oficial ADSE; calculadora eventual deve identificar o ano/tabela e não recolher dados fiscais desnecessários.

## Agenda, visitas, ausências
- Visitas familiares com pessoa, data/hora, anotações; exportação para Agenda/Agendamentos já existente.
- Consultas, exames, saídas acompanhadas e transporte: referência aos módulos de saúde/agendamentos, não duplicar registos.
- Ausências e internamentos com datas, entidade avisada, comprovativos de alta e lembretes.
- Regulamento ERPI publicado da APATI menciona 10% de redução para ausências >=15 dias consecutivos e 50% em internamento hospitalar com comprovativo de alta; informar que a regra deve ser reconfirmada com a instituição, nunca calcular redução de forma automática sem validação.
- Fonte: https://apaticastanheira.pt/wp-content/uploads/2022/12/Regulamento-Interno-erpi.pdf

## Cuidados, notas e documentação
- Lista de itens a levar à instituição (roupa, produtos de higiene, óculos, equipamento, etc.), pedido do lar e data de entrega.
- Notas de visitas, comunicação com equipa e lista de perguntas para consulta.
- Plano individual de cuidados, contrato, regulamento, recibos, faturas, atestados e comprovativos; todos os documentos no «Documentos Digitais» do perfil.
- Quando a instituição disponibilizar ementas e atividades, permitir introdução manual ou anexo; NÃO inventar API/feed da APATI.
- Contactos, documentação, apoios e compromissos devem funcionar offline; links funcionam quando há internet.

## Segurança / sincronização
- Namespace por profile_id estável, verificando identidade do perfil e associação instituição→residente antes de importar sync.
- Merge por IDs estáveis + timestamps e tombstones; não misturar dados de pai/mãe/filhos quando há nomes iguais.
- PDF/faturas contêm dados financeiros e pessoais, exigir permissões existentes; evitar logs, texto de notificações com NIF, telemetria.
- Compartilhamento da documentação com familiar só após consentimento; respeitar export/backup/restauro existentes; credenciais ADSE nunca guardadas.
- Guardar referências content URI de forma persistente ou copiar para armazenamento interno protegido; evitar links temporários que deixem PDFs inacessíveis.
- A ligação ao módulo de medicação limita-se a dados de leitura com consentimento; não assumir que o lar administrou uma dose sem confirmação.

## Critérios de aceitação / testes
1. Perfil A tem ERPI e fatura mensal; Perfil B não vê nem recebe estes dados após sincronização.
2. Pedir fatura gera rascunho editável para email; sem envio automático e sem presunção de envio.
3. Anexar PDF cria entrada em Documentos Digitais no perfil correto, abrindo no visualizador interno.
4. O registo do mês mantém histórico e comprovativo mesmo quando a fatura é corrigida.
5. Submissão nunca marcada automaticamente; o link ADSE abre no browser e não pede senha na SaúdePrática.
6. Lembretes de fatura não alteram alarmes de medicação, água ou consultas.
7. Importar/restaurar e sincronizar não duplicam o mês nem trocam utentes.
8. Funciona com outros lares e qualquer das 3 valências, sem obrigatoriedade de APATI ou ADSE.
9. Acesso grande e legível, botão «Voltar», dark/light, 5 idiomas, módulo ocultável e versão documentada.
10. Build/assinatura APK devem manter package com.mediagenda.app.stable e certificado oficial; nunca publicar nova release sem compilação/teste e asset SaudePratica.apk verificados.

## Sequência recomendada de implementação
Fase 1 — catálogo de instituição/contacts, associação perfil, faturas + workflow manual, documentos, atalhos, lembretes separados.
Fase 2 — apoios/checklists, agenda/visitas, ausências, inventário e relatórios anuais.
Fase 3 — sincronização reforçada, modelos de instituições, lembretes inteligentes e integrações apenas com APIs oficiais/consentimento.
