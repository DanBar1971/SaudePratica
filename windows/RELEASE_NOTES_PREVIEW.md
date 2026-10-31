# SaúdePrática Windows 0.6.7 — Agenda, Medicação e Perfis Android

- **Agenda:** os cartões claros deixam de receber uma camada de composição de vidro que recortava a parte superior e deslocava os ícones. A dimensão de cada cartão adapta-se ao seu conteúdo.
- **Medicação:** alteração de estado, por exemplo Ativa para Suspensa, pode ser gravada sem preencher obrigatoriamente hora, tipo de toma, dose ou via. Textos de hora importados do Android deixam de bloquear a gravação; não são programados alarmes Windows.
- **Perfis:** campos de perfil recuperados de estruturas adicionais do ZIP familiar Android guardado com encriptação DPAPI; dados de identificação e saúde apresentados numa área de leitura, juntamente com miniaturas reais de ficheiros de identificação que estejam presentes no backup.
- **Integridade:** alterações e importações não inventam fotos, números ou datas, nem transferem informações clínicas para o GitHub. Perfil antigo sem ZIP original associado pode necessitar de reimportação por Backup.
- Mantém a exportação de ficheiros e backups encriptados .spbackup, e o aspeto da 0.6.6.
- O instalador é experimental e sem assinatura digital de editor reconhecido. O Windows não substitui os alarmes Android.
- Testes automáticos utilizam dados sintéticos. Criar backup encriptado antes de usar dados reais.
