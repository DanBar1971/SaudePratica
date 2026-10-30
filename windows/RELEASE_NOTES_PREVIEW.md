# SaúdePrática Desktop 0.1.0 — Windows experimental

Primeiro **instalador para Windows 10/11 (64 bits)**, com assistente de instalação em português, atalho no menu Iniciar, opção de atalho no Ambiente de Trabalho, atualização por cima da versão anterior e desinstalador nas Definições do Windows.

## O que já está incluído
- Janela redimensionável com dimensão inicial 1280 × 720 (16:9), ícone e fundo SaúdePrática originais.
- Perfis e registo inicial de medicação guardados localmente, protegidos com Windows DPAPI.
- Exportação e restauro conservador de perfis novos num backup experimental `.spbackup` encriptado.
- Testes automatizados em Windows e verificação SHA-256 do instalador.

## Limitações e segurança
**Versão experimental, sem assinatura digital de editor Windows.** O Windows SmartScreen pode avisar que o editor é desconhecido. Confirma sempre a origem oficial no GitHub; não desatives globalmente a proteção do Windows.

Esta versão **ainda não sincroniza** com o Android, não importa diretamente o backup Android, não abrange todos os módulos clínicos e **não substitui os alarmes de medicação do telemóvel**. Testar inicialmente com dados fictícios.

**A desinstalação não apaga automaticamente os dados locais de saúde**, para evitar perdas acidentais. A gestão segura de eliminação de dados será adicionada posteriormente.

## Atualizações
As versões Windows usam tags `windows-vX.Y.Z-preview`; as versões Android mantêm `v1.9.X`. Esta release experimental não altera o identificador `releases/latest` usado pelas APKs Android.

Website oficial: https://danbar1971.github.io/SaudePratica/
