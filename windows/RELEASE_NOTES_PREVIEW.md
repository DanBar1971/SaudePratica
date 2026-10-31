# SaúdePrática Windows v0.6.5 — Importação e Exportação Familiar Completa

## Importar de Android para Windows

- **Backup → Importar toda a família Android** e, no módulo Importar / Exportar, selecionar um ZIP completo exportado pelo Android.
- Validação integral do ZIP familiar: manifesto, SHA-256 de cada ficheiro, limites de dimensão e proteção contra caminhos/entradas perigosas.
- Pré-visualização de **todos os perfis Android** com nome, número de medicamentos, marcações e anexos. Não altera os dados sem confirmação.
- O Windows cria automaticamente os perfis que faltam e reconhece os previamente associados à mesma identidade Android; não mistura nomes iguais nem substitui silenciosamente registos já existentes.
- Importação de medicação, agenda, fotografias e documentos que o Windows já suporta, em única operação com rollback por falha de gravação. Os dados de outros módulos ficam no ZIP original.
- Guarda uma cópia **integral, byte-a-byte**, do ZIP de origem com proteção Windows DPAPI: perfis, definições Android, fotos, documentos, análises, medições e quaisquer categorias extra permanecem recuperáveis mesmo sem ecrã Windows correspondente.

## Exportar

- **Backup encriptado .spbackup:** um só ficheiro para todos os perfis Windows, campos de perfil, medicação, agenda, fotografias, documentos, preferências e ZIPs Android originais importados; AES-256-GCM e palavra-passe.
- **Restauro .spbackup** noutra conta Windows: preserva os perfis e os anexos, com confirmação. É aditivo e bloqueia IDs já presentes, para não perder nem sobrepor dados.
- **Reexportar ZIP Android original:** recupera os bytes exatos do ficheiro importado, com aviso de privacidade porque o ZIP é não encriptado.
- Importação/exportação JSON individual permanece disponível.

## Limitações e segurança

- A cópia integral preserva **todos os ficheiros existentes no ZIP Android**, mas ainda não torna todos os módulos Android editáveis no Windows. Sem sincronização automática bidirecional; alterações feitas no Windows **não são incorporadas automaticamente** no ZIP original devolvido.
- A aplicação Windows **não substitui alarmes do Android**, nem importa dados já não presentes no ZIP.
- A portabilidade .spbackup só funciona no Windows neste momento; importar diretamente .spbackup no Android ainda não está implementado.
- Não enviar backups, documentos, imagens nem perfis clínicos ao GitHub. ZIP original reexportado é sensível; preferir .spbackup cifrado.
- Instalador ainda é **experimental e sem certificado de editor Windows** (o aviso SmartScreen pode continuar).

## Testes

Suite sintética Windows: importação de vários perfis, associações, anexos encriptados, ficheiro original imutável, exportação .spbackup, restauro noutra conta, reimportação sem duplicação e rollback. Os testes CI e o arranque gráfico de compilação não substituem testes manuais com cópias de segurança reais.
