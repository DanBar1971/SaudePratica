# SaúdePrática v1.9.114 — Sincronização por perfil (correção de segurança)

- Escolher explicitamente o perfil no telemóvel de origem (ENVIAR) e no destino (RECEBER).
- Transferir apenas um perfil por operação, sem trocar automaticamente dados de toda a família.
- Protocolo Nearby v2: impede combinação com versões antigas que exportavam todos os perfis.
- Proibir a criação automática de perfis «recebido de…» e o envio de duplicados históricos.
- Recusar fusão com nome curto divergente, nome clínico completo divergente, ou associação remota já atribuída a outra pessoa.
- Fusão aditiva de medicação, agenda e registos, com identificação semântica de repetidos; consultas com identificadores reutilizados e conteúdo diferente preservam ambos os eventos.
- Os registos diferentes ou incertos permanecem preservados como conflitos; nunca são automaticamente apagados.
- Lista de perfis com nome curto; ocultação do nome legal completo; botão pequeno «FICHA» em vez de «Alarmes deste telemóvel».
- Mantidos dados existentes, perfis de cuidador, alarmes e navegação; NÃO é feita qualquer eliminação automática dos perfis importados anteriormente.

**Importante:** Antes da primeira sincronização, criar backups completos em ambos os equipamentos. Duplicados criados por versões anteriores exigem revisão individual; a migração nunca elimina nem mistura dados clínicos automaticamente. A utilização em equipamentos reais exige validação de duas vias por operações separadas.

Identidade Android `com.mediagenda.app.stable` e certificado de assinatura original preservados.
