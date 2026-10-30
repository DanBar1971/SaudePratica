# Política de atualizações Android, Windows e iOS

## Princípio
Uma alteração do núcleo de SaúdePrática é uma tarefa multi-cliente, mas cada
plataforma requer implementação, assinatura e testes próprios.

| Plataforma | Código atual | Instalação | Estado |
|---|---|---|---|
| Android | MediAgenda/ | APK original assinada | Em produção |
| Windows | windows/ | Futuro EXE/MSI | Não implementado |
| iPhone / iOS | ios/ | Futuro IPA/TestFlight | Planeado |
| Website | raiz do repositório | GitHub Pages | Publicado |

## Fluxo de uma mudança funcional
- Primeiro, classificar a alteração: interface exclusiva, dados partilhados,
  segurança/perfis, agendamentos, alarmes, documentos, sincronização ou serviços.
- Para dados partilhados, manter formatos com migrações de compatibilidade,
  exemplos JSON fictícios e testes de ida/volta.
- Quando o cliente Windows estiver implementado, uma mudança comum exige
  código + testes Windows no mesmo PR (ou fica identificada como pendente).
- Quando houver iOS, aplicar a mesma regra a iOS, com testes/macOS quando disponíveis.
- Não atualizar apenas os números de versão: publicar só binários reais testados.
- Para Android, confirmar package ID, certificado original, alarmes com
  ecrã bloqueado e download no GitHub Releases. Não apagar releases antigas.
- Todos os lançamentos usam o repositório SaudePratica; o antigo fica como
  arquivo e canal de transição até todas as instalações migrarem.

## Módulos prioritários para o Windows
Perfis, medicação, prescrições, documentos digitais, agenda, tomas, backups,
sincronização e painel do cuidador. O telefone continuará a receber os alarmes
de medicação, e o Windows terá notificações próprias quando for implementado.
