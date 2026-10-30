# SaúdePrática Desktop 0.2.0 — Windows experimental

## Melhorias de interface
- Ecrã inicial redesenhado, com identidade oficial, ícone, contadores e informações úteis.
- Nova ficha de medicação dentro da janela principal, sem sequência de caixas popup para cada campo.
- Editar medicação já registada ou criar nova, com campos acessíveis e scroll, e rodapé com Guardar/Cancelar.
- Nome, dose, via de administração, tipo de injeção, tipo de toma, hora, indicação, sem alarme, suspensão e notas.
- Criar perfil diretamente no ecrã Perfis, sem janela popup.
- Mantém todos os dados locais criados na 0.1.0: localização e formato de armazenamento Windows inalterados.
- Compatibilidade com o backup experimental .spbackup da versão anterior e preservação de campos já guardados.

## Instalação
Instalador português para Windows 10 e 11 (x64). Instala por cima da versão experimental anterior, com atalho e desinstalador, sem apagar dados locais.

## Limitações e segurança
A versão **ainda é experimental e não tem assinatura digital Windows**. Pode surgir um aviso de editor desconhecido; confirmar sempre a origem oficial antes de executar.
Não sincroniza com Android, não importa backups Android, não substitui alarmes do telemóvel, nem fornece gestão clínica completa. Testar com dados fictícios.
O backup .spbackup é encriptado (AES-256-GCM) e protegido por palavra-passe; Android/iOS ainda não o conseguem restaurar.
Nenhum dado clínico real deve ser enviado para o GitHub.
