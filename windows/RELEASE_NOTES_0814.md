# SaúdePrática Windows 0.8.14 — Restauro automático e fichas completas

Versão experimental Windows 10/11 (x64). Correção de continuidade da 0.8.13.

## Corrigido
- **Sem botões obrigatórios por módulo:** ao iniciar uma instalação que já tinha um ZIP Android original guardado no Windows, a aplicação converte automaticamente os dados disponíveis em Nutrição, Hidratação, Sintomas, Tomas, SOS e Lares/Apoios. A migração é executada uma vez para cada combinação de backup/perfil; não duplica registos existentes. A associação aos perfis Android é explícita e nunca baseada em nomes semelhantes.
- **Restauro familiar ZIP Android:** as categorias compatíveis são também importadas no momento de importar a família, com fotografias guardadas sob DPAPI e preservação dos ZIPs originais.
- **Nutrição:** cada refeição importada apresenta a miniatura da fotografia autêntica à esquerda do cartão, quando existe e pode ser lida; a fotografia completa continua na ficha.
- **SOS Emergência:** os campos originais aparecem automaticamente após importação/restauro, preservando edições já efetuadas no Windows.
- **Hidratação:** usa o total diário e data originais efetivamente guardados pelo Android; o histórico antigo que nunca constou do backup não pode ser inventado.
- **Sintomas e Tomas:** importação automática dos registos Android suportados, com as tomas confirmadas associadas ao medicamento correto e sem duplicados.
- **Lares e Apoios:** no perfil do cuidador, consulta direta e resumida da instituição, número de faturas e última mensalidade dos residentes que estejam explicitamente associados pelo backup. As fichas de cada residente continuam separadas.
- Os botões de recuperação por módulo foram retirados, ficando a ferramenta de recuperação técnica apenas em Opções → Backup e Restauro.

## Segurança e compatibilidade
- Antes da migração inicial é conservada cópia do ficheiro local *ainda cifrado por DPAPI* na pasta `%LOCALAPPDATA%\\SaudePraticaDesktop\\restores`. Não há upload de dados pessoais.
- Todas as alterações aos registos são aditivas e idempotentes; os ZIPs originais e os dados Windows editados são preservados.
- `.spbackup` continua encriptado com palavra-passe. A importação de conteúdos existentes é local e não implica sincronização com telemóveis.
- Este Windows ainda não executa alarmes clínicos do Android nem recebe automaticamente dados novos sem um novo backup/sincronização válida.
- O formato de backup Android antigo pode conter apenas o último total diário de água; dias antigos ausentes não são recuperáveis deste ZIP.

## Verificação automatizada
- Testes unitários com perfis e fotografias sintéticos para importação, arranque com arquivo já guardado, segurança, associações cuidador/residente e repetição sem duplicados.
- Pipeline Windows verifica sintaxe, testes, abertura de interface, empacotamento PyInstaller, OCR, agente Avisos e instalador Inno Setup antes da publicação.

## Instalação
Fazer backup familiar de segurança. Instalar a 0.8.14 por cima da versão Windows anterior. Na primeira abertura, a migração dos backups Android locais existentes é automática. Se ainda faltar algum módulo, confirmar que o backup original desse perfil continha os respetivos registos. A opção de recuperação manual global continua em Backup e Restauro para diagnósticos.

**Importante:** versão experimental sem assinatura digital de editor Windows. Não desativar proteções do sistema para a executar.
