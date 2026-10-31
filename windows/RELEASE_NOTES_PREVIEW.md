# SaúdePrática Windows v0.6.6 — Perfis, Medicação e Agenda

## Correções pedidas para Windows
- **Perfis:** ação Eliminar em cada cartão, confirmação explícita, preservação dos outros perfis e anexos partilhados, recuperação de campos já existentes em backups Android antigos ou recentes, sem preencher dados inventados.
- **Seletor de perfil:** avatar e nome compactos e alinhados, sem espaço vazio antes da fotografia.
- **Medicação:** imagens autênticas ocupam o quadro fotográfico com fundo desfocado e original legível; estado Ativa verde, Suspensa vermelho; próxima data/hora prevista calculada apenas quando há regra de toma válida e sem criar alarmes Windows.
- **Agenda:** compromissos futuros ordenados por data/hora e visualmente destacados com cartões claros quase brancos; compromissos anteriores escurecidos e discretos. Datas inválidas não são anunciadas como compromissos futuros.
- **Navegação:** botões Importar JSON removidos dos ecrãs Medicação e Agenda. Importação/exportação mantém-se no módulo Backup/Importar e Exportar.
- **Rodapé:** apresenta a versão atual do aplicativo, sem número antigo.

## Dados, cópias e segurança
- Mantém importação familiar Android, fotografias, documentos e backups encriptados .spbackup introduzidos na v0.6.5.
- Nunca coloca informações clínicas, imagens reais ou dados de utilizadores no GitHub. Eliminar um perfil não apaga um ZIP original que contém outros membros da família.
- A data de toma apresentada é informativa; **não é um despertador Windows**. Se não existir uma recorrência inequívoca, a data fica por definir em vez de ser inventada.
- O instalador Windows continua experimental e sem certificado de assinatura de editor reconhecido; o aviso SmartScreen pode persistir.

## Validação
Testes automáticos com dados sintéticos: correspondência de campos Android, datas e recorrências, eliminação com rollback e documentos partilhados, regressão de interface, abertura do executável e instalação Inno Setup. Recomenda-se cópia de segurança antes de qualquer teste com dados reais.
