# SaúdePrática Android v1.9.124 — Diagnóstico de permissões de alarmes (Redmi/MIUI)

## Objetivo

Quando o som da medicação toca, mas a ficha TOMEI/ADIAR não surge no ecrã bloqueado, a causa pode estar nas permissões Android ou nas permissões específicas do fabricante. Não devemos alterar o código de alarmes que já está a funcionar noutros telemóveis.

## O que foi acrescentado

Novo acesso **Opções → Segurança e notificações → Permissões e alarmes do telemóvel**.

- Mostra estado real das notificações, incluindo permissão Android 13+.
- Mostra se **Ecrã completo** está autorizado em Android 14+, com acesso ao ecrã especial do sistema.
- Mostra se os **alarmes exatos** estão autorizados em Android 12+, com ligação às definições correspondentes.
- Inspeciona a prioridade do canal existente **ALARMES DE MEDICAÇÃO — ecrã completo**, permitindo abrir as definições específicas desse canal.
- Mostra o estado de otimização padrão de bateria e abre as definições Android. Em Redmi/MIUI pode existir otimização adicional do fabricante.
- Guia Redmi/MIUI/HyperOS: verificar **Mostrar no ecrã bloqueado**, **Abrir novas janelas em segundo plano**, **Mostrar janelas pop-up**, **Início automático** e **Bateria → Sem restrições**.
- O estado é atualizado ao voltar das definições do Android.
- Instruções em Ajuda nos cinco idiomas.

## Proteção dos alarmes existentes

**Nenhuma alteração** no agendador, serviço, receiver, ecrã do alarme, sons, vibração, canal, tempos, perfil associado ao telemóvel, TOMEI ou ADIAR. O build guarda/verifica as assinaturas SHA-256 do código dos módulos existentes durante a aplicação da alteração. Não solicita permissões perigosas nem modifica a configuração do dispositivo sem toque do utilizador.

## Testes a realizar

1. No Redmi onde o alarme já funciona: confirmar que a v1.9.124 não muda som, ecrã bloqueado, TOMEI, ADIAR ou duração.
2. No Redmi mais antigo: abrir o novo diagnóstico, corrigir permissões relevantes no Android/MIUI e regressar; os estados devem atualizar.
3. Utilizar **Opções → Segurança e notificações → Notificações → Testar alarme de medicação** com o ecrã bloqueado. O teste existente não deve registar uma toma.
4. Verificar também se as notificações de app são autorizadas e o canal não está silenciado.
5. Atenção: as rotas Xiaomi variam com MIUI/HyperOS. Os atalhos universais levam às definições da aplicação; algumas permissões especiais Xiaomi têm de ser ativadas manualmente.

A alteração é apenas diagnóstica e de navegação; não garante que todas as versões MIUI autorizem ecrãs completos em segundo plano.
