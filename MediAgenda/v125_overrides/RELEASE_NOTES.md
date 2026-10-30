# SaúdePrática v1.9.105 — Números clínicos e identidade visual

## Alterações
- Situação Clínica: registos individuais de números de observação e de processo, incluindo múltiplos números da mesma instituição, com adicionar, editar e eliminar individualmente.
- Dados antigos preservados: linhas existentes em `observations_by_unit` e o campo `observation_number` mantêm-se acessíveis; informação isolada por ID do perfil.
- Reposto o fundo oficial `saude_background` nos ecrãs Lares e Apoio e Calendário Mensal/Ciclo Menstrual.
- Apoiar o autor: substituição da cerveja por café ☕, preservando o destino PayPal.
- Ajuda atualizada sobre números clínicos e auditoria de ecrãs adicionais sem referência explícita ao fundo.

## Verificação
- Testes estáticos e compilação Android em GitHub Actions.
- Identificador Android inalterado: `com.mediagenda.app.stable`; versionCode **115**; versionName **1.9.105**.
- Imagens oficiais: ícone, fundo e splash preservados.
- Ainda é necessário testar em dispositivos Xiaomi/Android a edição de registos antigos, teclado nos diálogos e aparência dos fundos.

## Publicação
**Esta nota não significa que a APK assinada já esteja publicada.**
A publicação está concluída apenas quando `v1.9.105` for uma GitHub Release pública, com o asset assinado exato `SaudePratica.apk`, hash verificado, e a página https://danbar1971.github.io/SaudePratica/ encaminhar para esse ficheiro.

Nunca desinstalar a app existente para aplicar uma atualização assinada com a mesma chave; fazer primeiro backup dos dados.