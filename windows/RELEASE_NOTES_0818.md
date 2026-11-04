# SaúdePrática Windows 0.8.18 — Processos hospitalares do Android

Instalador experimental Windows, atualizável por cima da versão 0.8.17. Preserva a configuração Windows, o PIN de 4 dígitos e a seleção de perfil predefinido.

## Situação Clínica

- Nova área «Processos hospitalares do Android», por perfil, usando o **backup familiar Android 1.9.136+** que o Windows importou/restaurou.
- Abre uma janela de consulta com um processo por botão e apresenta: **A minha equipa**, nome/especialidade/email/telefone, **taxas moderadoras** separadas por Consultas, Exames e Análises, estados Pago/Por pagar/Isento/Anulado e total por pagar, **declarações de transporte** e **imagem de identificação**.
- Os dados são **de consulta no Windows**, não editáveis. Para alterar, usar Android e restaurar um backup atualizado.
- Só lê o arquivo Android original validado por checksums e associado ao perfil Windows atual. Não tenta inferir o paciente por nome nem mistura dados de outros perfis. Fotografias mantidas nos anexos cifrados com DPAPI.
- Não comunica com sistemas do IPO Lisboa / SNS e não efetua pagamentos ou pedidos.

## Limites

- O Windows apenas mostrará estes dados quando o backup restaurado incluir os ficheiros originais do Android 1.9.136 ou posterior. Uma restauração antiga precisa de um backup novo.
- A sincronização direta por Wi-Fi de dados clínicos continua pendente; a ligação descoberta/pareamento não transfere registos.
- Os estados de pagamento/transportes são os registados manualmente no telemóvel, não informação oficial em tempo real.
- Instalar como atualização por cima da 0.8.17 e testar com um backup não identificado antes de carregar dados clínicos reais. A aplicação Windows continua experimental.
