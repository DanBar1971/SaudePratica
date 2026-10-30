# SaúdePrática v1.9.96 — Fase E: Saúde e Bem-estar + descoberta da Fase D

## Saúde, Health Connect e Mi Fitness
- Mantidos passos, distância, sono e calorias, com gráficos de 7 dias.
- Acrescentadas permissões granulares e consultas de registos nativos **SpO₂**, peso, frequência cardíaca em repouso, tensão arterial, frequência respiratória e temperatura corporal, disponíveis no Android 14+.
- Adicionados gráficos semanais de frequência cardíaca e peso. O utilizador escolhe o indicador para evitar ecrãs sobrecarregados.
- Cada indicador mostra «sem registos» se a fonte não disponibiliza dados e «sem permissão» quando aplicável. Nunca apresenta um zero inventado como medição.
- Dados Health Connect só são mostrados no perfil explicitamente associado ao telemóvel. Não são copiados para backups, nuvem ou perfis de familiares.
- **Mi Fitness / Xiaomi:** a partilha pode abranger passos, atividade, sono, calorias e batimentos em exercício, mas pode **não incluir SpO₂**. A SaúdePrática não consegue extrair dados que a Xiaomi não tenha enviado ao Health Connect. Consulta dados e permissões na origem.

## Peso, altura e IMC
- Registo de peso manual por perfil, com histórico e gráfico simples dos últimos dez registos.
- Altura lida automaticamente da ficha do perfil, quando disponível; pode ser corrigida no módulo. Dados anteriores preservados.
- IMC para adultos, com categorias de referência neutras, sem diagnóstico médico, rótulos depreciativos nem imposições de peso ideal.
- Peso manual guardado privadamente na SaúdePrática; não escreve automaticamente para Health Connect.

## Hidratação
- Barra de progresso da ingestão de água e do objetivo diário configurado.
- Botão **Acrescentar água / Reagendar**: permite aumentar o objetivo no mesmo dia em 250, 500, 750, 1000 ou 1500 ml, mantendo todos os copos já registados.
- Ao aumentar o objetivo, reativa notificações ainda dentro do horário de avisos, sem alterar alertas de medicação ou a agenda.
- Mantidos botão «Copo tomado» nas notificações, proteção de registos duplicados e felicitação por objetivo alcançado.
- A aplicação não decide quanto beber. Se houver restrição hídrica por doença ou indicação médica, prevalecem as orientações do profissional.

## Onde encontrar as melhorias da Fase D
- Menu principal **Agenda**: agora aparecem cartões **Pesquisar unidades de saúde** e **Importar guia PDF ou fotografia**.
- O catálogo pode ser consultado por nome, distrito, concelho e GPS opcional. Uma unidade encontrada pode ser associada à criação/edição da marcação.
- Menu principal **Documentos**: originais PDF e imagem por perfil, sem duplicados por hash; importar normalmente ou através da partilha de outras aplicações.
- Análises, medicação e saúde ocupacional continuam a arquivar originais automaticamente como na v1.9.94.

## Código-fonte e licenças
- Implementação Kotlin Android nativa sobre a aplicação original, inspirada na **Android Health Samples** (Apache-2.0). O projeto **OpenVitals** (AGPL-3.0) forneceu ideias de visualização; não foram incorporados ficheiros licenciados em AGPL na SaúdePrática.
- Foi mantido `com.mediagenda.app.stable`, as versões anteriores A–D, a assinatura original e as imagens oficiais (`saude_icon.png`, `saude_splash.png`, `saude_background.png`).

## Testes e limitações
- A validação automatizada verifica reconstrução Kotlin, invariantes A–E, recursos gráficos, versão, certificado e hash SHA-256; a utilização real de Health Connect e de notificações Xiaomi/HyperOS precisa de confirmação num telemóvel.
- Os valores SpO₂ do relógio apenas aparecerão se a fonte os escrever no Health Connect e a SaúdePrática tiver permissão.
- O histórico lido de outras aplicações está normalmente limitado aos 30 dias anteriores à autorização inicial, salvo permissão adicional de histórico.
- Recomenda-se fazer um backup antes da atualização.
