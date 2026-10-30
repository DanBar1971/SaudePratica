# SaúdePrática v1.9.108 — Agenda automática, atualização após login e apoio ao autor

## Agenda
- Marcações com data/hora passada passam automaticamente para **Realizadas**, sem exigir confirmações manuais nem mostrar «Por confirmar» apenas por serem antigas.
- A app guarda o estado `done` no ficheiro da agenda do perfil quando abre ou regressa à agenda; números de identificação e dados dos outros perfis ficam intocados.
- Se uma marcação for reagendada para uma data/hora futura, volta a ficar **Agendada**. O editor mantém as opções «Agendada» e «Cancelada», removendo a opção de confirmação manual.
- Marcações canceladas não ficam realizadas. Marcações recorrentes abertas não são concluídas prematuramente; registos sem hora só passam a realizados no dia seguinte. Atestados com validade usam a data de expiração.
- Filtros «Todas», «Pendentes», «Realizadas» e «Canceladas», cartões e Calendário Mensal refletem o mesmo estado.

## Atualização Android
- Consulta não identificada de versões oficiais do GitHub após desbloqueio/entrada no perfil, limitada a uma verificação inicial por sessão e com intervalo mínimo de 30 minutos.
- Continua a verificar automaticamente ao regressar à app, com cadência de 12 horas; falhas de rede não bloqueiam futuras tentativas.
- Quando existe uma release assinada mais recente, pergunta se o utilizador quer atualizar. Se escolher «Mais tarde», pode voltar a perguntar após 12 horas. A instalação exige sempre consentimento no Android.

## Situação Clínica
- Oculta «Número antigo (preservado)» do ecrã. O valor histórico não é apagado da ficha ou dos backups existentes.

## Apoiar o autor
- Corrige o diálogo que, no Xiaomi, só mostrava «Cancelar»: apresenta dois botões de ação claros e separados:
  1. **☕ Buy Me a Coffee** — https://buymeacoffee.com/danielbarr7
  2. **PayPal** — https://www.paypal.com/paypalme/djjindungo
- Ligações abertas no navegador externo; sem pagamentos automáticos nem valor fixado pela aplicação.
- Novos textos traduzidos em PT, EN, FR, DE e ES.

## Compatibilidade e proteção dos dados
- Mantém `com.mediagenda.app.stable`, certificado original, `versionCode=118`, `versionName=1.9.108`.
- Compilação e verificações estáticas em GitHub Actions. As interações em equipamento Xiaomi real devem ser confirmadas após instalar.
- **Faz backup dos perfis e instala por cima da versão anterior, sem desinstalar.**