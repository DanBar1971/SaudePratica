# SaúdePrática Desktop 0.7.3 — Perfis completos e atualização sem bloquear o instalador

- **Ficha de perfil ampliada**: nome curto e completo, data de nascimento, sexo/género, altura, nacionalidade, naturalidade, filiação, NIF, SNS, NISS, ADSE, unidade de saúde, morada, contacto, cuidador e fotografia.
- **Restauro Android → Windows**: extração dos campos privados do próprio perfil a partir das preferências do ZIP Android original, que já se encontra no backup cifrado. Corrige campos que ficavam vazios mesmo quando o perfil tinha nome e fotografia.
- Valores não conhecidos permanecem intactos no ZIP de origem; não são preenchidos com dados fictícios.
- **Backup e restauro Windows**: janela com barra de percentagem por fases *efetivamente concluídas* (não é uma velocidade nem uma percentagem de bytes); processamento sem bloquear o ecrã principal; confirmação de perfis afetados e cópia de segurança cifrada antes de substituir dados.
- **Atualização por cima da anterior**: o agente de lembretes da Agenda fecha ao receber pedido de atualização do instalador e é reiniciado após instalação. A instalação desde a antiga 0.7.2 também tenta encerrar *apenas* o processo residente correspondente, sem terminar à força a janela de edição.
- Mantêm-se os dados em `%LOCALAPPDATA%\SaudePraticaDesktop` e o mesmo AppId Inno Setup. O Windows pode pedir o encerramento de uma janela principal que esteja aberta.
- Esta versão continua a ser uma versão Windows em desenvolvimento, ainda sem assinatura de editor Windows. Não existe sincronização automática Android–Windows.
- **Antes de voltar a importar o backup editado para Android**: confirmar os campos nos quatro perfis no Windows, editar apenas dados de teste, fazer backup Família e Perfil e verificar a pré-visualização do restauro Android.
