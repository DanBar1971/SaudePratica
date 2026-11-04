# SaúdePrática Windows 0.8.17 — PIN com identidade visual original

**Instalador experimental Windows 10/11, 64 bits**. Atualização por cima da 0.8.16, sem desinstalar nem apagar o armazenamento.

## Interface da primeira utilização e do login
- Os dois ecrãs de PIN usam o **fundo oficial SaúdePrática**, adaptado proporcionalmente à janela, com motivos turquesa e sem distorção.
- Logótipo oficial, painel central maior e contraste elevado, tipografia e botões coerentes com o aspeto dos outros módulos.
- Lista de perfis mostra apenas o nome; códigos internos só são usados internamente para impedir misturas entre pessoas.
- Primeira abertura: escolher perfil predefinido, introduzir e confirmar PIN de 4 números.
- Depois: introduzir o PIN e abrir automaticamente o perfil predefinido. A escolha de outros perfis mantém-se disponível. As fichas e a pesquisa na rede não abrem antes de confirmar o PIN.

## Backups e restauro
- Novos ficheiros .spbackup usam **PIN de quatro números** (AES-256-GCM, chave derivada por PBKDF2-HMAC-SHA256).
- Campos numéricos maiores, com instrução específica de PIN; só é necessário repetir o PIN ao criar um backup.
- No restauro de ficheiros PIN recentes, usar apenas o PIN de 4 números.
- Para **backups antigos** protegidos com palavra-passe, a app reconhece o formato e pede a palavra-passe original. Não é tecnicamente possível abrir esses ficheiros com um PIN novo.
- O PIN de entrada do Windows é distinto do PIN do backup.
- Um PIN curto é mais cómodo, mas menos robusto face a tentativas offline: guarda os backups em local seguro e não partilhes ficheiros clínicos.

## Mantido da 0.8.16
- O peso manual Android, altura e número de pesagens importadas são mostrados no ecrã Atividade e Saúde sem substituir medições do Windows.
- Restauro automático por perfil, prevenção de duplicados e compatibilidade de backup Android 1.9.135.

## Qualidade
- Testes automatizados para formatos novos e antigos, PIN local, isolamento de perfis, documentos, alarmes e sincronização.
- Ensaio em Windows real de ambas as interfaces de PIN com a imagem de fundo carregada.
- Dados de teste sintéticos; não são enviados para o GitHub os ficheiros médicos originais.

Antes de atualizar, guarda uma cópia de segurança. A 0.8.17 é ainda experimental.
