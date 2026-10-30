# SaúdePrática — publicação automática no GitHub

A compilação usa o workflow `.github/workflows/mediagenda-v1969.yml` e, no mesmo job,
assina a APK de release **com o certificado Android original**, publica a versão
em GitHub Releases e aciona o workflow do GitHub Pages.

## Configuração única (obrigatória)

1. No PC de confiança, guardar fora do repositório o ficheiro de recuperação
   `SaudePratica_Codigo_Recuperacao_28-10-2026.txt` e o backup encriptado.
2. Instalar [GitHub CLI](https://cli.github.com/) e autenticar com `gh auth login`.
3. Executar num PowerShell do Windows:
   `./CONFIGURAR-SEGREDO.ps1 -FicheiroRecuperacao "C:\CAMINHO\SaudePratica_Codigo_Recuperacao_28-10-2026.txt"`
   Isto cria `SAUDEPRACTICA_SIGNING_RECOVERY_HEX` em **Settings → Secrets and variables → Actions**.
   **Nunca colocar o código de recuperação num commit, issue, log ou mensagem pública.**
4. Em **Actions → SaudePratica Android Build → Run workflow (master)**, acionar
   uma execução depois de configurar o Secret. A versão Android ainda não
   publicada é lançada automaticamente.

## Versões futuras

1. Aplicar os patches de código no repositório e aumentar `versionCode` e
   `versionName` na alteração correspondente.
2. O workflow compila e verifica todos os testes da app.
3. Se o resultado for válido, recupera o JKS original em memória/ficheiro
   temporário, assina a APK e compara o certificado SHA-256 fixo conhecido.
4. Publica `SaudePratica.apk`, ZIP com código-fonte e SHA256SUMS na nova tag.
5. Desencadeia a atualização do GitHub Pages; o site aponta para `releases/latest`.

Se o Secret faltar ou estiver incorreto, a publicação falha **sem criar uma APK
com chave nova**. Repor o Secret e executar novamente o workflow.

## Segurança

- Não são usados segredos em builds `pull_request`.
- Chave privada e palavra-passe nunca são registadas nem publicadas como artifact.
- A tag existente nunca é substituída automaticamente.
- O package Android permanece `com.mediagenda.app.stable`.
- Os perfis clínicos dos utilizadores não são enviados ao GitHub.