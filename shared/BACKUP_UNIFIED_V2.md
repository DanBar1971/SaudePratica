# SaúdePrática — contrato de backup unificado v2

Estado: em testes na PR #41. Não publicar como restauro seguro até passar testes reais Android↔Windows.

## Só duas escolhas públicas

- Backup / Restaurar Família: um único ficheiro .spbackup cifrado com todos os perfis.
- Backup / Restaurar Perfil: um único ficheiro .spbackup cifrado com só a pessoa escolhida; nenhum dado de outros membros.
- Os importadores ZIP/JSON antigos ficam apenas para migração interna e não como opções principais.

## Requisitos obrigatórios

1. Mesmo formato .spbackup no Android, Windows e futuro macOS. AES-256-GCM, verificação SHA-256 de ficheiros e autenticação de cabeçalho.
2. Exportar ficheiros reais de medicação, agenda, fotografias e documentos; não criar ficheiros vazios para disfarçar dados em falta.
3. Conservar cada perfil pelo identificador estável, evitando repetir pessoas com o mesmo ID ou nome. Qualquer correspondência por nome exige confirmação explícita.
4. Restaurar em modo Pré-visualizar → Confirmar substituição → Cópia de segurança cifrada automática → Aplicar atomicamente → Verificar.
5. Não tocar nos perfis não escolhidos. Não mudar PIN, credenciais, associação ao telemóvel nem funcionamento dos alarmes.
6. Fotografias, documentos e imagens dos medicamentos são binários com hash e perfil associado, não somente referências locais.
7. O backup Perfil não pode conter um ZIP original que inclua outros familiares. Em caso de dúvida deve recusar a operação.
8. As alterações feitas no Windows têm de ser mapeadas, comparadas e validadas no Android. Restaurar um ZIP antigo não é sincronização.
9. Todos os módulos Android devem entrar no arquivo: medicação/tomas, agenda, hidratação, nutrição, Diabetes, documentos e módulos futuros, mesmo se ainda não editáveis no Windows.

## Testes de aceitação

- Criar quatro perfis fictícios com medicação, marcações, imagens e documentos.
- Exportar e restaurar Família Android → Windows → Android e Perfil em ambos os sentidos; comparar contagens, conteúdo e hashes.
- Restaurar 3 vezes: não aumentar número de perfis, medicamentos, agenda ou anexos.
- Simular ZIP truncado, fotos em falta, palavra-passe errada, conflito e falha de disco: nenhum dado existente é modificado.
- Validar ecrãs reais com seleção de perfil, contagens e diferenças antes de importar.
- Comparar o serviço e alarmes Android antes/depois para garantir ausência de regressões.

Não marcar a versão como segura ou atualizar downloads oficiais só porque compilou.