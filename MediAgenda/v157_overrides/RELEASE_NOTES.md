# SaúdePrática Android 1.9.137 — Equipa compacta e calendário visível

- Situação Clínica: cada hospital/processo tem **um único botão**. Ações de editar e eliminar processo e módulos de equipa, taxas, imagem de identificação e declarações de transporte ficam no respetivo ecrã.
- A minha equipa: lista compacta pesquisável por nome, especialidade, telefone ou email. Ações de editar e eliminar são ícones discretos à direita; telefone e email são texto clicável. Remove os grandes botões repetidos e o símbolo de email isolado.
- Corrige a disposição no topo/rodapé do ecrã de processo hospitalar para respeitar barras do sistema e aparelhos Xiaomi.
- Google Calendário: a antiga lista invisível é substituída por um seletor real, com Próximas e Histórico. Permite escolher um registo e abrir o formulário do calendário do telemóvel. **Não há sincronização automática nem duplicação programática de eventos:** o utilizador tem de guardar o evento explicitamente no calendário selecionado no dispositivo. Não pede permissões de calendário.
- Dados já existentes dos 44 contactos, taxas, documentos e transportes não são eliminados nem convertidos nesta atualização. O mesmo JSON de processo continua guardado em pasta específica do perfil e incluído no backup familiar Android.
- Alarmes TOMEI/ADIAR e restantes serviços de medicação não são alterados.
- Atenção: o Windows 0.8.17 preserva o backup original, mas não apresenta automaticamente os novos dados nos ecrãs. Essa visualização requer versão Windows adaptada.
