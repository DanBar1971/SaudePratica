# SaúdePrática — assinatura original e publicação Android

## Situação comprovada em 03/11/2026

- Repositório **atual**: `DanBar1971/SaudePratica` (branch `main`).
- O certificado original SHA-256 é `7f67082f5e0de76986a0078d5f998e65467c8468f4d09b0caf8e4b332cc60e6a`.
- A cópia encriptada da chave original está no repositório em `SaúdePrática/release-unsigned-patches/v1.9.98/MediAgenda-CHAVE-PRIVADA-ENCRIPTADA.aesgcm.b64`.
- O código privado para desencriptar está num **ficheiro TXT separado** (`SaudePratica_Codigo_Recuperacao_28-10-2026.txt`). Nunca o colocar no repositório, Issues, Releases, prints ou logs.
- A APK Android normal v1.9.127 foi publicada com o certificado original através de um fluxo de publicação alternativo, verificando a assinatura.
- No run `41306720632` de 01/11/2026, o workflow principal compilou, mas registou expressamente que **não havia segredo** no repositório e ignorou os passos de assinatura. Isto é uma observação histórica, não uma leitura atual de GitHub Secrets.
- O script antigo `CONFIGURAR-SEGREDO.ps1` apontava incorretamente para `DanBar1971/AndroidAppDev` após a migração do repositório. Esta revisão corrige o destino.

## Verificação sem revelar segredos

No repositório atual: **Settings → Secrets and variables → Actions → Repository secrets**.
Confirmar apenas o **nome** `SAUDEPRACTICA_SIGNING_RECOVERY_HEX`. O valor não é legível pelo GitHub depois de guardado.

Alternativa com GitHub CLI autenticado:

```powershell
gh secret list --repo DanBar1971/SaudePratica
```

Esta listagem **não prova que o valor seja correto**. A validação efetiva acontece na assinatura de uma nova APK, com verificação do certificado original. Nunca gerar ou substituir por uma chave nova.

## Reconfiguração única — apenas se o segredo faltar

Num computador de confiança com o TXT de recuperação original (separado do ZIP encriptado), executar:

```powershell
gh auth login
.\MediAgenda\tools\CONFIGURAR-SEGREDO.ps1 -FicheiroRecuperacao 'C:\CAMINHO\SaudePratica_Codigo_Recuperacao_28-10-2026.txt'
```

O script atua **apenas** no repositório principal `DanBar1971/SaudePratica`, valida o formato do código e confirma apenas o **nome** do segredo. O conteúdo não é apresentado, publicado nem enviado para este chat.

## Compilação e publicação

1. Alterar e testar o código Android, aumentando `versionCode` e `versionName` para uma versão nova da família `1.9.xxx`. Não publicar apenas alterações de documentação.
2. Executar o workflow existente `.github/workflows/saudepratica-android.yml` (**SaudePratica Android Build + AutoRelease**) na branch `main`, depois das verificações e revisão do código. **Não usar `master`**, nem o repositório antigo.
3. O workflow aplica os overrides, verifica gráficos e identidade, compila a APK, recupera a chave privada temporariamente com `SAUDEPRACTICA_SIGNING_RECOVERY_HEX` e executa `MediAgenda/tools/sign_release.py`.
4. A assinatura falha caso a recuperação ou o SHA-256 do certificado não corresponda ao original. Confirmar assinaturas Android v2/v3, package `com.mediagenda.app.stable`, `versionCode` crescente e testes em dispositivo real.
5. Só depois publicar a APK normal `SaudePratica.apk` em GitHub Releases e atualizar/verificar a página oficial `https://danbar1971.github.io/SaudePratica/`.

### Cuidados
- Pull requests não têm acesso à chave de assinatura e **não devem publicar APKs assinadas**.
- Uma execução `success` da compilação não basta: verificar se os passos **Sign release** e **Publish signed APK** foram efetivamente executados, não `skipped`.
- A existência de uma APK antiga assinada ou um ZIP encriptado **não comprova que o segredo CI esteja configurado**.
- Nenhuma chave privada, palavra-passe, código de recuperação ou dados de pacientes pode ser incluído em GitHub.
- Não deixar uma release Windows substituir `releases/latest` da Android.
