# SaúdePrática Windows 0.8.13 — restauro completo dos módulos Android

Versão de correção fundamentada num backup familiar **real fornecido exclusivamente em privado pelo utilizador** (4 perfis; contém ZIP Android original cifrado). Nenhum byte do ficheiro real, nome de contacto, imagem pessoal, registo médico ou palavra-passe é publicado no repositório, nos testes ou nos logs do GitHub.

## Problema confirmado
A aplicação Windows restaurava os perfis, medicação, agenda, anexos e o ZIP Android original preservado, mas mantinha vazias as estruturas Windows de Nutrição, Hidratação, Sintomas, Tomas, SOS e Lares. As fichas recentes tinham importação manual por módulo, mas o restauro `.spbackup` não a executava. Além disso, os backups antigos `profile.json` podiam conter apenas identidade, provocando perda de módulos Windows que tivessem sido adicionados depois. A interface de Tomas projetava tomas por confirmar mesmo quando os eventos Android já existiam, porque não eram convertidos para os identificadores de medicação Windows.

## Alterações
- O restauro familiar `.spbackup` **converte automaticamente** os módulos do ZIP Android original associado a cada perfil. A operação só substitui perfis após pré-visualização, confirmação e cópia de segurança local encriptada; preserva módulos Windows já existentes que não estão no backup antigo.
- Botão **«Recuperar dados Android dos backups já guardados»** em Opções → Backup e Restauro. Útil para instalações onde os quatro perfis já tinham sido restaurados antes desta correção. Cria cópia de segurança encriptada antes da migração, não substitui outros campos, aplica alteração atomicamente e apresenta contagem de registos efetivamente novos.
- **Nutrição**: recupera cada refeição e foto JPEG original do diário do perfil, sem recálculos de calorias. Armazena as fotos na área DPAPI associada ao perfil e suporta reimportação sem duplicados.
- **Hidratação**: recupera o objetivo, volume configurado do copo e o **último total diário realmente guardado pelo Android**. Não inventa datas/hora de cada copo nem histórico anterior indisponível. A ficha permite visualizar o último dia que tem dados, mesmo quando hoje ainda não há consumos.
- **Sintomas**: converte registos `kind=symptoms` de `saudepratica_health/<perfil>/records.json`, preservando descrição, tipo, intensidade, data e notas.
- **Tomas**: converte apenas confirmações reais `kind=intakes` e ignora tombstones `deleted_intakes` correspondentes. Relaciona o `fields.medication_id` nativo com `medications[].android_source_id` no Windows, converte os milissegundos UNIX em hora local e guarda `confirmed_at` / `scheduled_at` para que as tomadas apareçam confirmadas, nunca como alarmes simulados. A reconversão não duplica eventos ou confirmações manuais.
- **Atividade e Saúde**: registos manuais originais `kind=measurements` passam a aparecer numa secção separada, sem se confundirem com medições Health Connect (que não estão contidas nesse ZIP).
- **Emergência/SOS**: carrega os contactos e outros campos realmente preenchidos nas preferências Android, sem substituir edições Windows.
- **Lares/Apoios**: carrega os dados do residente a partir do perfil Android correspondente. O backup identifica o cuidador e a lista explícita de residentes na configuração familiar; no perfil do cuidador, aparecem botões para abrir a ficha do residente associado. Os registos continuam a pertencer ao perfil do residente, sem copiar dados para perfis não relacionados. Estados e faturas só aparecem se estiverem realmente presentes no backup.
- A importação não modifica a app Android estável nem transmite dados pela rede. Todos os dados permanecem no Windows local e no backup cifrado.

## Limitações
- O backup Android original só guardava, no módulo de Hidratação antigo, o último dia e o total de ml; copos anteriores não podem ser reconstruídos.
- Os dados históricos completos do Health Connect não fazem parte deste backup; continuam a exigir exportação autorizada no Android.
- A sincronização automática clínica Windows ↔ Android continua pendente: a ligação Wi-Fi atual apenas testa descoberta e autorização.
- O restauro de um perfil que contém backups familiares originais tem limitações de privacidade; usar Backup Família para conservar todos os originais com segurança.

## Verificação
- Testes locais do conteúdo do ficheiro privado: 4 perfis e um ZIP Android original válido; diário com fotografias, preferências de hidratação, registos de sintomas, confirmações de tomas e associação familiar cuidador/residente presentes.
- Testes públicos **exclusivamente sintéticos**: 2 perfis fictícios, backup `.spbackup` encriptado com ZIP Android verificado, repetição sem duplicados, proteção das edições Windows, datas e identificação de medicamentos, isolamento do cuidador e do residente, recuperação manual posterior, rollback em falha de gravação.
- CI executa testes de código, abertura da interface, EXE PyInstaller, OCR, agente Avisos e instalador Inno Setup.

**Instalação**: fazer backup familiar, instalar por cima da 0.8.12, abrir Opções → Backup e Restauro e usar «Recuperar dados Android dos backups já guardados» para aproveitar o backup já restaurado, sem repetir a substituição dos perfis.
