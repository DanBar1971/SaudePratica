# SaúdePrática v1.9.88 — Alarmes, perfil do telemóvel e Tomas

## Alterações
- Preparado o alarme de medicação numa tarefa Android independente do ecrã principal e do PIN, com intenção de aparecer à frente do ecrã bloqueado. A autorização de alarmes em ecrã completo do Android 14+/HyperOS continua necessária.
- Adicionada na ficha do perfil a opção **Este perfil pertence a este telemóvel**. Um perfil pode ser cuidador sem ser o utilizador dos alarmes fortes deste aparelho.
- Medicação de familiares associada a outros perfis: notificação discreta com nome e dose, em vez de abrir alarme forte.
- Medicação agrupada à mesma hora: lista de medicamentos sem fotografias, registos de toma por medicamento, e revisão individual no módulo TOMAS. A opção ADIAR 10 MIN não confirma automaticamente medicamentos.
- Adicionada **Sem alarme · retirar horários deste medicamento** para limpar horas previamente selecionadas, sem apagar medicamento nem histórico.
- Na vista de cuidador, os cartões recebidos de perfis sincronizados podem ser ocultados quando duplicam visualmente um aviso local de mesma pessoa, medicação e hora. Os dados clínicos originais **não são apagados nem fundidos**.
- Mantido o atualizador Android com PackageInstaller.Session da v1.9.87.

## Segurança e compatibilidade
- APK assinada localmente com a keystore original e verificada com esquemas Android v2 e v3. O GitHub apenas reconstrói o ficheiro a partir de uma APK **não assinada** verificada e de um delta binário assinado, sem ter acesso à chave privada.
- Package Android `com.mediagenda.app.stable`, com versionCode superior ao anterior.
- Instalar diretamente por cima da aplicação instalada: **não desinstalar** para preservar os perfis, fotos e registos.

## Testes ainda recomendados no telemóvel
- Confirmar o comportamento do alarme à frente do ecrã de bloqueio no equipamento real, incluindo permissões HyperOS.
- Validar agenda e medicação entre os quatro perfis e o perfil deste telemóvel.
- Rever a associação dos clones sincronizados da Regina sem apagar dados clínicos importantes.

Esta Release contém o APK gerado e assinado; testes comportamentais em diferentes fabricantes Android permanecem necessários.
