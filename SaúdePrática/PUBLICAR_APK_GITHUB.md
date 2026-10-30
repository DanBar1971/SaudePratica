# Publicar APK da SaúdePrática no GitHub Releases

Sim: o GitHub permite alojar ficheiros `.apk` através de **Releases**. O GitHub Actions também consegue automatizar a publicação depois de ter os segredos de assinatura configurados.

## Publicação manual segura

1. Compila e valida a nova versão Android.
2. Assina a APK com a **mesma chave de assinatura** usada nas versões anteriores; sem essa chave não é possível atualizar a app instalada, preservando os dados.
3. Abre https://github.com/DanBar1971/AndroidAppDev/releases e seleciona **Draft a new release**.
4. Cria uma tag com o formato `v1.9.75` (usar a versão real), escreve as novidades, e anexa **apenas a APK assinada**. Não publiques a keystore, passwords, backups, dados médicos nem documentos pessoais.
5. Para manter um endereço de download constante, chama ao ficheiro anexo **`SaudePratica.apk`**, qualquer que seja a versão.
6. Publica como release normal (não pre-release), se estiver validada e pronta para os utilizadores.

## Ligações para partilhar

Página da versão mais recente:

https://github.com/DanBar1971/AndroidAppDev/releases/latest

**Download direto da APK mais recente**, quando existir uma release publicada contendo `SaudePratica.apk`:

https://github.com/DanBar1971/AndroidAppDev/releases/latest/download/SaudePratica.apk

**Importante:** estas ligações só funcionam para descarregar uma APK depois de a release correspondente ter sido publicada. GitHub Actions → Artifacts não é equivalente a Releases (artefactos expiram e podem requerer autenticação).

Se o repositório for privado, o destinatário precisa de acesso autorizado ao GitHub.

## Futuras atualizações automáticas

- Configurar segredos privados no GitHub Actions para a keystore, a password e o alias de assinatura.
- Usar os gráficos originais no build de produção, validando-os antes de publicar.
- Publicar com GitHub Actions / GitHub CLI `gh release create` e asset `SaudePratica.apk`.
- Nunca publicar APKs não assinadas como ficheiros prontos a instalar.
- Manter o identificador Android e a assinatura para permitir instalar por cima sem perder dados.

**Atenção:** alterar o nome do projeto/aplicação não obriga a alterar o package ID do Android. A pasta técnica `MediAgenda` mantém-se para o build.

## Atualização automática na aplicação (desde 1.9.76)

A aplicação consulta, no máximo uma vez de 12 em 12 horas, a API pública GitHub Releases `/repos/DanBar1971/AndroidAppDev/releases/latest` sem transmitir qualquer dado de saúde. Na área **Opções → Ajuda e informações → Verificar atualizações**, o utilizador pode iniciar a mesma consulta manualmente.

- A Release deve ser pública, não estar marcada como pré-lançamento e usar a tag `v1.9.76` (ou versão posterior em formato `vMAJOR.MINOR.PATCH`).
- O ficheiro APK assinado deve chamar-se **exatamente `SaudePratica.apk`**.
- Se a versão publicada for mais recente do que a instalada, surge uma proposta de download com ação explícita. A aplicação abre o browser e o Android confirma a instalação.
- Não instalar silenciosamente, não permitir downgrade, não solicitar credenciais ou dados médicos durante a verificação.
- Enquanto não existir uma Release pública, a API devolve 404 e a app explica o motivo.

**Primeira Release:** a versão v1.9.76 já foi publicada manualmente. A v1.9.77 foi publicada automaticamente no GitHub Actions em 26/10/2026 com verificação integral de SHA-256.

## Processo oficial: publicação automática após a APK estar assinada

**Preferência de manutenção do projeto:** cada atualização da SaúdePrática deve ser compilada, assinada, validada e **publicada numa Release pública do GitHub**, sem pedir ao utilizador que volte a anexar manualmente a APK. Confirmar também que `releases/latest` aponta para a nova versão e que o asset se chama sempre `SaudePratica.apk`.

Workflow: [Publicar SaúdePrática APK assinado](../.github/workflows/saudepratica-publish-release.yml).

1. Produzir uma APK assinada com o certificado original e validar assinaturas v2/v3, package ID, versionCode, versionName e imagens.
2. Se a chave de assinatura só estiver disponível no ambiente privado, criar um delta binário **entre a APK assinada já publicada e a APK assinada nova**, usando `zstd --patch-from=SaudePratica-anterior.apk -7 nova.apk -o delta.zst`. O delta não contém a keystore. Guardar em pedaços de texto Base64 `delta.part00.b64` etc. no diretório `SaúdePrática/release-patches/vX.Y.Z/`.
3. Preparar `release-notes.md` e um `manifest.json` com a tag, a tag de base e os hashes SHA-256 da APK anterior, do delta e da APK nova.
4. Guardar **`manifest.json` por último**. Um push desse ficheiro para `master` inicia automaticamente o workflow, que descarrega a APK anterior publicada, reconstrói a APK nova, verifica os três hashes e a assinatura Android e publica a Release `vX.Y.Z` com o asset `SaudePratica.apk`.
5. Verificar via GitHub Releases API que a versão é `Latest`, não está em draft/prerelease e que o SHA-256 do asset corresponde à APK previamente validada. O workflow recusa substituir uma Release existente.

A alternativa preferencial para o futuro, se os segredos de assinatura vierem a ser configurados no GitHub, é construir e assinar diretamente dentro do GitHub Actions. Até lá, o método de delta mantém o certificado **privado** e permite publicação totalmente automatizada depois de preparada a APK assinada.

**Não guardar passwords, keystores, dados de saúde ou fotografias pessoais no repositório público.**
