# SaúdePrática — backup portável encriptado v1 (.spbackup)

**Estado:** implementação Python para Windows; a versão Desktop 0.6.5 exporta
e restaura perfis, anexos e cópias byte-a-byte de backups Android importados.
Android e iOS ainda NÃO importam/exportam este `.spbackup`. O Nearby Android
v2 NÃO é um backup integral.

## Segurança e contrato comum
1. Nenhum dado clínico enviado para GitHub. O arquivo pode ser copiado por
   USB, pasta partilhada ou transferência local aprovada.
2. Palavra-passe criada pelo utilizador; sem ela não há restauro. Nunca registar
   credenciais, pacientes ou anexos em logs.
3. Restaurar exige pré-visualização e confirmação; nunca substituir silenciosamente.
   A primeira base Windows apenas adiciona perfis novos, sem substituir IDs.
4. Preservar IDs únicos, categorias, anexos e campos futuros; antes de usar
   dados reais entre sistemas, passar testes de interoperabilidade Android↔Windows.

## Formato binário
- Prefixo UTF-8: SAUDEPRATICA-BACKUP-V1 + newline.
- 4 bytes big endian com comprimento do cabeçalho JSON.
- Cabeçalho: kind=saudepratica-encrypted-v1,
  kdf=PBKDF2-HMAC-SHA256, iterations=600000, salt_b64 (16 bytes),
  cipher=AES-256-GCM e nonce_b64 (12 bytes).
- AES-256-GCM encripta o ZIP; AAD é o prefixo completo e o cabeçalho,
  incluindo os quatro bytes de comprimento.
- ZIP desencriptado: manifest.json e entradas data/<path>.
- Manifesto: kind=saudepratica-portable-v1, created_at, file_count e files
  com path, size e sha256.
- Paths previstos: profiles/<UUID>/profile.json,
  profiles/<UUID>/medicacao.json, profiles/<UUID>/agenda.json,
  profiles/<UUID>/attachments.json, profiles/<UUID>/android_archives.json,
  profiles/<UUID>/windows_state.json, attachments/<id>/<nome>.
  Os ZIPs Android originais são guardados como anexos com hash; esses ficheiros
  podem ter até 240 MB, mantendo o limite global do backup em 512 MB.
- Rejeitar caminhos absolutos, '..', ficheiros extra, ficheiros duplicados,
  zip-bombs e hashes incorretos. Não extrair ZIP sem validação.
- Código Python de referência: shared/python/saude_backup.py.
- Testes sintéticos: shared/tests/test_portable_backup.py.

## Integrações pendentes
Criar versão Kotlin Android e Swift iOS conforme estas regras, com teste
de ida e volta REAL, documentos, imagens, histórico de tomas e dados completos.
O Windows importa a família completa, mas as categorias Android sem interface
Windows ficam conservadas apenas no arquivo original. A compatibilidade de
edição/sincronização transversal NÃO está concluída.
