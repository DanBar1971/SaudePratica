# SaúdePrática Windows 0.6.2 — interfaces limpos e importação Android JSON experimental

- Retirado campo de pesquisa dos módulos, sem função real.
- Cabeçalhos de Perfis, Medicação e Agenda com tipografia clara e linha de destaque subtil.
- Removidos painéis opacos exteriores de Perfis e do editor de Medicação para deixar mais fundo 16:9 visível.
- Agenda com listagem em cartões dos compromissos importados (ainda sem edição ou alertas no Windows).
- Nova ficha integral **Importar dados Android**: seleciona o perfil ativo, lê `medicacao.json` ou `agenda.json`, mostra pré-visualização, conta registos novos/repetidos, pede confirmação e guarda de modo aditivo com rollback.
- Sem substituição silenciosa; conserva campos adicionais desconhecidos do Android e identificadores de origem.
- ZIP Android: **só inspecionar** nomes e quantidades de ficheiros, sem extração, sem afirmar restauro total.
- Backups `.spbackup` do Windows permanecem independentes; **não são backups Android compatíveis**.
- Instalador ainda sem assinatura Authenticode verificada: o SmartScreen poderá apresentar «Editor desconhecido». Recomendado certificado comercial ou publicação Microsoft Store MSIX; não desativar SmartScreen.
- Os alarmes Android, APK, certificados e dados do telemóvel não foram modificados.

Instalar por cima da versão anterior. Recomenda-se exportar uma cópia `.spbackup` antes dos testes de importação.
