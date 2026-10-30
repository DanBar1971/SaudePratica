# SaúdePrática v1.9.115 — Eliminar perfil apenas com PIN

- Retirada a obrigação de escrever o nome completo do perfil para o apagar.
- Eliminar um perfil exige sempre o PIN da SaúdePrática, mesmo em telemóveis onde o PIN não estava ativado (nesse caso, a app impede a eliminação até o ativar).
- O formulário apresenta claramente o perfil escolhido e um identificador curto para distinguir perfis com nomes iguais.
- O botão de eliminação continua associado ao **ID imutável** do perfil escolhido, nunca ao nome.
- Conservado o aviso de perda definitiva de dados, o botão Cancelar e a proteção de tentativas do PIN.
- Nenhum perfil é eliminado durante a atualização. A eliminação de perfis criados por sincronizações antigas é manual, após fazer backup.

Mantidos a assinatura Android original, o package `com.mediagenda.app.stable`, os alarmes e os restantes módulos.
