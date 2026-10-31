# SaúdePrática Windows v0.6.4 — ZIP Android completo (por perfil) e interface de vidro

- **Aspeto:** os grandes painéis de formulários passaram a receber uma textura composta diretamente do fundo 16:9 e um véu suave. Não há transparência nativa dos controlos Tkinter; o efeito visual simula vidro e mantém os campos legíveis.
- **Agenda:** corrigidos os títulos reais Android em `activity`/`department` e identificadores reutilizados; registos distintos são preservados, duplicados exatos são ignorados.
- **Medicação:** compatibilidade com `medication`, `reminder_time`, `suspended_from` e outros campos Android, preservando dados originais.
- **Importar ZIP Android:** escolher ficheiro de backup completo, escolher *perfil de origem Android*, selecionar previamente o *perfil Windows de destino*, visualizar quantidades e confirmar. Verificação integral do manifesto e dos hashes. Nenhum perfil é criado/substituído automaticamente.
- **Fotografias/documentos:** ativos importados por perfil e protegidos em ficheiros DPAPI na conta Windows. As fotografias dos medicamentos são mostradas quando encontradas no ZIP. O avatar do perfil pode ser recuperado caso ainda não exista no Windows. O módulo Documentos permite exportação manual para uma pasta escolhida e anexação manual de PDF/fotografias.
- **Exportações:** Medicação/Agenda JSON por perfil (texto não encriptado: mostrar aviso). O backup `.spbackup` Windows encripta perfis, medicação, agenda e documentos importados. O restauro `.spbackup` dos anexos inclui hashes SHA-256.
- **Validação reforçada 0.6.4:** anexos DPAPI existentes são desencriptados e verificados antes de reutilização em restauro; reimportações de ZIP recusam fotografias/documentos antigos danificados sem alterar as fichas. O restauro recusa também caminhos de perfis inconsistentes. Novos testes automáticos com dados fictícios.
- **Segurança:** a importação é aditiva, com rollback em falha de gravação. Recusa conflitos com dados previamente importados. Nunca utiliza dados clínicos reais na CI. Não substituir alarmes nem medicação Android por versões experimentais.
- **Limite importante:** importação ZIP é **por perfil**; selecionar os perfis Android um a um para evitar misturas de membros da família. Os documentos fora do índice ou associações externas poderão precisar de verificação manual. A exportação JSON não é ainda um restauro automático compatível Android; validar antes de utilizar dados reais no outro sentido.
- **SmartScreen:** instalador permanece sem assinatura de editor reconhecida, pode aparecer aviso.
- **Website:** mostrar Windows experimental 0.6.4, download Setup direto, Android inalterado, iOS futuro.

**Testes:** verificações sintéticas de JSON, identificadores duplicados, ZIP com verificação do manifesto, anexos, segurança contra caminhos inseguros, backup encriptado e restaurar no Windows.
