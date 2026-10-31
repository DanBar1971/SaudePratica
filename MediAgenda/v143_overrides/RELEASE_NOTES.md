# SaúdePrática Android v1.9.123 — Compatibilidade de backup Windows (Fase 1)

## Novidades

- **Backup familiar Android mais completo:** passa a incluir a pasta **Diabetes** e outros diretórios persistentes do tipo saudepratica_ que respeitem a lista de segurança. Não exporta PIN, palavras-passe, tokens nem pastas temporárias.
- **Exportar backup para Windows:** nova opção em Backup, cria ficheiro `.spbackup` compatível com o formato encriptado da SaúdePrática Windows 0.6.5 (AES-256-GCM, PBKDF2-HMAC-SHA256 600 000 iterações e autenticação do cabeçalho). Inclui os perfis, representações de medicação e agenda editáveis no Windows e o ZIP Android **original completo**, preservado para categorias ainda não suportadas no Windows.
- **Inspecionar backup Windows:** a aplicação Android consegue abrir e autenticar um `.spbackup` com palavra-passe, verificar hashes de TODOS os ficheiros, localizar cópias Android originais e, após aviso muito explícito, restaurar uma cópia original.
- **Nunca confundir restauro com sincronização:** recuperar um ZIP original de dentro do backup Windows **não importa** alterações posteriores feitas no Windows. Por isso o Android só permite recuperação explícita e **substitutiva** com confirmação. Não há fusão automática de medicação, agenda, tomas ou documentação.
- Exportação ZIP Android normal continua disponível. Identidade Android, alarme e dados existentes permanecem inalterados até o utilizador confirmar a substituição.

## Limites conhecidos

- A exportação `.spbackup` está limitada a 220 MB de ZIP Android para permanecer compatível com Windows 0.6.5. A exportação ZIP familiar Android normal mantém o limite anterior de 850 MB.
- O Windows 0.6.5 restaura um `.spbackup` por adição de **perfis novos**; não substitui IDs que já existam. Em instalações Windows já com os mesmos perfis, utilizar a importação familiar do ZIP Android normal.
- Alterações editadas no Windows ainda não regressam automaticamente ao Android. A sincronização bidirecional requer implementação do protocolo v3, deteção de alterações e resolução de conflitos.
- O formato é interoperável ao nível do contrato e da compilação, mas precisa de ensaio real Android → Windows e Windows → Android com dados fictícios, backups e fotografias.
- Os documentos e informações clínicas podem conter dados sensíveis; não enviar cópias reais para GitHub nem correio desprotegido.

## Testes de aceitação

1. Exportar backup familiar Android, confirmar que inclui `diabetes_v1` se houver registos.
2. Exportar `.spbackup` com 10+ caracteres, abrir no Windows 0.6.5 e confirmar todos os perfis, medicamento, agenda e arquivo original.
3. Restaurar `.spbackup` num Windows vazio e reexportar o ZIP Android original (hash idêntico).
4. Abrir o `.spbackup` no Android, testar palavra-passe errada, ficheiro adulterado e cancelamentos; o Android não deve alterar dados na pré-visualização.
5. Antes de qualquer restauro, verificar que o aviso de **substituição de todos os dados** é explícito. Não usar esta via para sincronizar edições Windows.
6. Verificar alarmes em ecrã bloqueado, PIN e imagens originais.

Documentação técnica: `shared/PORTABLE_BACKUP_V1.md` e `shared/SYNC_V3_DESIGN.md`.
