# SaúdePrática — estado atual e continuidade entre chats

**Atualizado:** 2026-11-02 (Europe/Lisbon).

Este ficheiro é a fonte de continuidade técnica do projeto: consultar antes de pedir novamente ao utilizador código, ficheiros ou chaves já existentes. Nunca guardar segredos, dados clínicos reais nem códigos de recuperação no GitHub.

## Repositórios

- Principal: https://github.com/DanBar1971/SaudePratica
- Histórico legado: https://github.com/DanBar1971/AndroidAppDev
- Website: https://danbar1971.github.io/SaudePratica/
- Releases oficiais (Android e Windows): https://github.com/DanBar1971/SaudePratica/releases

## Versões publicadas

| Plataforma | Versão | Estado | Download |
| --- | --- | --- | --- |
| Android | **1.9.127** | **Última versão oficial normal**, APK com certificado original | https://github.com/DanBar1971/SaudePratica/releases/latest/download/SaudePratica.apk |
| Android | **1.9.125** | Versão anterior | https://github.com/DanBar1971/SaudePratica/releases/download/v1.9.125/SaudePratica.apk |
| Windows | **0.7.3** | Versão Windows em desenvolvimento, instalador EXE | https://github.com/DanBar1971/SaudePratica/releases/download/windows-v0.7.3-preview/SaudePratica-Setup.exe |

- Android release normal: https://github.com/DanBar1971/SaudePratica/releases/tag/v1.9.127
- A antiga `v1.9.127-preview` existe apenas como artefacto histórico; **não é o download oficial atual**.
- Windows 0.7.3 com mais campos de perfil Android, barra de progresso por etapas e atualização sem bloqueio do agente de Agenda. Testado em [GitHub Actions](https://github.com/DanBar1971/SaudePratica/actions/runs/41440065581) e publicado em [Releases](https://github.com/DanBar1971/SaudePratica/releases/tag/windows-v0.7.3-preview).\n- Windows preview: https://github.com/DanBar1971/SaudePratica/releases/tag/windows-v0.7.3-preview
- iOS ainda não está disponível; planeado para fase futura.
- Página oficial atualizada para Windows 0.7.2 e Android 1.9.127 normal. `releases/latest` devolve agora `v1.9.127`; a aplicação Android pode procurar e instalar a atualização normalmente.

## Builds e segurança validados

- Android 1.9.127: CI de compilação e testes com emulador passou: https://github.com/DanBar1971/SaudePratica/actions/runs/41425615910
- Windows 0.7.2: CI de instalador/testes passou: https://github.com/DanBar1971/SaudePratica/actions/runs/41423597783
- Publicação Android 1.9.127 **normal** (APK e assinatura já validadas): https://github.com/DanBar1971/SaudePratica/actions/runs/41435596638
- Validação original da APK assinada e verificação de SHA-256 e Android v2/v3: https://github.com/DanBar1971/SaudePratica/actions/runs/41433392342
- Publicação Windows: https://github.com/DanBar1971/SaudePratica/actions/runs/41432821559
- GitHub Pages: https://github.com/DanBar1971/SaudePratica/actions/runs/41433870392
- APK Android 1.9.127: SHA-256 `aaf211b5ca48fa0701ce2199f662ffd30efa5678fded203a073e999550701edb`; assinatura original com certificado SHA-256 `7f67082f5e0de76986a0078d5f998e65467c8468f4d09b0caf8e4b332cc60e6a`; `com.mediagenda.app.stable`, versionCode `137`.
- Windows 0.7.2 EXE: SHA-256 `9f2f81a74b8c0dcd973bf247649138ec0d97c1990d010112559161585bb552be`.
- A reconstrução da assinatura utiliza um **delta binário público sem chave privada** em `MediAgenda/release-verified/v1.9.127/signed.patch.zst.b64` no ramo de pré-visualização.

## Código e ramos

- PR de integração experimental ainda não fundido: https://github.com/DanBar1971/SaudePratica/pull/41 (ramo `fix/portable-backup-unificado-20261102`).
- Ramo associado às releases experimentais, preservando os conteúdos clínicos e com ficheiros de workflows compatíveis com `main`: `release/windows-072-android-127-preview`.
- O código fonte de Windows 0.7.2 e Android 1.9.127 encontra-se no ramo de pré-visualização; **não considerar o código de `main` automaticamente equivalente às duas pré-releases** até a integração ser revista e concluída.
- Android 1.9.127 é a release normal mais recente, por decisão do utilizador. O módulo de restauro Android ↔ Windows continua a precisar de testes reais; a numeração 2.0 fica reservada até o utilizador dar por concluído o desenvolvimento.

## Causa do erro 403 e resolução confirmada

Em 2026-11-02, a publicação Windows 0.7.2 por `gh release create` falhou com `HTTP 403: Resource not accessible by integration`, mesmo com `permissions: contents: write`.

O problema foi o `--target` apontar para um commit no ramo experimental que modificava ficheiros `.github/workflows/*` relativamente ao ramo principal; a API Releases do GitHub exige autorização de alteração de workflows nessas condições, que `GITHUB_TOKEN` não fornece. Não assumir automaticamente que `Workflow permissions` está definido incorretamente.

**Solução que funcionou:** criar um ramo de publicação com **o mesmo código experimental** e **workflows iguais aos de `main`**, e usar esse ramo no `--target` do `gh release create`. Resultado: ambas as publicações Android/Windows bem-sucedidas. A documentação oficial é https://docs.github.com/en/rest/releases/releases.

## Regras de publicação futura

1. Testar a compilação Android e Windows e a integridade do instalador/APK.
2. **Não trocar nunca o certificado Android original**; confirmar nome do pacote, versionCode, SHA-256 e assinatura.
3. Publicar `SaudePratica.apk` e `SaudePratica-Setup.exe` com versões/tags próprias; não confundir builds experimentais e estáveis.
4. Atualizar obrigatoriamente https://danbar1971.github.io/SaudePratica/ e confirmar que o workflow Pages passou.
5. **Regra fixa:** todas as versões Android durante o desenvolvimento são releases normais **v1.9.xxx**, nunca `-preview` nem prerelease; a versão **2.0** só será publicada quando o utilizador declarar a aplicação concluída. Todas têm de ser encontradas pela app via `releases/latest`.
6. Não exigir novamente ficheiros/chaves se já constam das fontes autorizadas, e nunca incluir credenciais no repositório, em logs ou em releases.
7. Preservar os alarmes Android e a identidade gráfica real; não usar dados reais nos testes.

## Validação pendente

- A publicação como release normal não dispensa verificações reais do restauro. Testes reais do ficheiro `.spbackup` de Família/Perfil Android ↔ Windows, incluindo fotos, documentos, agendamentos, medicação, restauro e prevenção de duplicações.
- Validar sincronização manual bidirecional e comportamento em dados de teste; **não afirmar que existe sincronização automática**.
- Revisar PR #41 e integrar apenas após testes e revisão de regressões.
- Confirmar instalação e atualização Windows sem obrigar a desinstalação, mantendo a nota de que o EXE ainda não tem assinatura de editor.
