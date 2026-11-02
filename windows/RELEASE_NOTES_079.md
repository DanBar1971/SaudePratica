# SaúdePrática Windows v0.7.9 — perfis, carregamento e arranque

- **Lista de perfis:** o minúsculo símbolo `›` em cada cartão foi substituído pelo botão `ABRIR ❯`, acompanhado por mais espaço lateral.
- **Carregamento real da ficha:** progress bar animada, mensagem «A carregar dados e fotografias do perfil...» e cursor de espera até terminar a leitura de anexos Android, sem bloquear o interface.
- **Indicador em todos os módulos:** o cursor de espera é mostrado durante a reconstrução do ecrã, com reposição depois do desenho.
- **Janela principal:** abre maximizada no Windows, respeitando o mesmo instalador e dados locais.
- **Arranque:** a janela principal fica oculta enquanto o splash PyInstaller oficial está visível; a janela final só aparece após fechar o splash, evitando sobreposição de dois ecrãs de arranque.
- Mantidas as fotografias originais, backups Windows/Android, estados da medicação e agente «SaúdePrática Avisos» independente sem splash.

**Segurança:** nunca é publicado qualquer ficheiro pessoal nem dados clínicos. Os testes usam perfis e anexos fictícios. Esta versão continua experimental e o instalador Windows não tem assinatura Authenticode.
