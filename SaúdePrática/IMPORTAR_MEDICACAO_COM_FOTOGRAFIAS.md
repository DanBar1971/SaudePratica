# SaúdePrática — Importação de medicação com fotografias (v1.9.84)

## Objetivo
Importar um único ficheiro `medicacao.json` que contenha medicamentos e fotografias, sem necessitar de copiar manualmente imagens para o armazenamento privado do Android.

## Formato JSON compatível
- Campos obrigatórios legados: `settings`, `medications`, `last_notified`.
- Campo opcional `embedded_medication_images`: objeto indexado pelo nome simples do ficheiro (`.png`, `.jpg`, `.jpeg`). Cada imagem possui `mime_type`, `sha256` e `data_base64`.
- Cada medicamento pode incluir `embedded_image_names`, lista das fotografias que lhe pertencem.
- O importador confere tipo, assinatura PNG/JPEG, SHA-256 e dimensões. Guarda as imagens unicamente em `filesDir/medication_photos` e converte as referências em caminhos locais.
- Os nomes locais incluem o ID do perfil e um identificador por conteúdo para evitar colisões. O ficheiro JSON privado do perfil é atualizado apenas após processar os anexos.
- Depois da importação, as imagens são mostradas com o mecanismo `MedicationPhotoLoader` existente, incluindo nos alarmes quando disponível.
- JSON antigos continuam a poder ser importados sem qualquer alteração de formato.

## Procedimento no telemóvel
1. Fazer primeiro **Backup completo** da SaúdePrática.
2. Selecionar explicitamente o **perfil correto** na aplicação.
3. Em **Opções → Backup → Importar JSON**, escolher o ficheiro portátil que contém as imagens incorporadas.
4. Confirmar o total de medicamentos e a mensagem de importação, com o número de fotografias.
5. Abrir as fichas e verificar as fotografias; confirmar as doses, horários e repetições antes de ativar avisos.

**Atenção:** importar um JSON de medicação pode substituir a lista atual do perfil selecionado. Não importa ficheiros para todos os perfis; o importador atua apenas sobre o perfil ativo.

## Privacidade
A funcionalidade é inteiramente local. Não envia fotografias nem prescrições para a Internet ou GitHub. Os ficheiros de pessoas concretas são gerados localmente e não são incluídos no repositório.
