# SaúdePrática Android 1.9.127 — Backup unificado (teste de interoperabilidade)

Estado: nova funcionalidade em ensaio. Manter cópias independentes dos dados.

## Alterações
- Apenas dois tipos de backup: Família (.spbackup) e Perfil (.spbackup); uma opção de restauro.
- Perfil isolado sem ZIP familiar escondido; inclui medicação, agenda, fotos, documentos, preferências do próprio perfil e diário Diabetes identificado por hash do ID.
- Antes de exportar, mostra quantidades de medicamentos e consultas e recusa ficheiros clínicos em falta. Reabre e autentica o .spbackup após exportar.
- Restaura campos editados no Windows em medicação, agenda, fotografia e perfil, após pré-visualização, confirmação e backup de segurança com rollback.
- Recupera outros ficheiros persistentes de saúde para perfis novos a partir de arquivos originais autenticados, sem importar PIN, token ou configurações de alarmes.
- Motor de alarmes, serviço, TOMEI e ADIAR não foram modificados.

## Limitações
- Transferência MANUAL, não é sincronização automática.
- Categorias globais sem associação inequívoca ao perfil não são restauradas automaticamente; é necessária avaliação de compatibilidade antes de qualquer restauro.
- ZIP original até 220 MB e arquivo portátil até 512 MB.
- Testes automáticos e compilação não substituem ensaio em dispositivos Android reais.
- Nunca apagar a instalação existente nem confiar no único backup antes de validar as imagens e registos.

## Ensaios finais
- Android Família/Perfil → Windows → editar medicação, agenda e fotos → Windows .spbackup → Android, com dados fictícios.
- Repetir restauro 3 vezes, confirmar IDs, fotos, documentos, Diabetes e alarmes em ecrã bloqueado.
- Testar anexos em falta, corrupção, palavra-passe errada e conflitos entre perfis.

Implementação e testes: PR #41 e shared/BACKUP_UNIFIED_V2.md.