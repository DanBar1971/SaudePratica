# SaúdePrática Desktop 0.4.1 — correção crítica do arranque

## Correções
- O instalador só é publicado se a interface **abrir e desenhar o primeiro ecrã** num ensaio Windows, tanto a partir do código como do executável compilado.
- Se falhar a inicialização, o splash fecha e é criado um diagnóstico privado em `%LOCALAPPDATA%\SaudePraticaDesktop\startup_error.log`. É apresentado um aviso em vez de ocultar a falha.
- **Splash oficial completo, sem cortes, sem texto extra, sem duplicar logótipos e sem alterar a composição.** Apenas redimensionado proporcionalmente.
- Mantidos o ícone Windows e os dados locais DPAPI e o formato de backup `.spbackup`, sem migração destrutiva.

## Utilização
Instalar por cima da 0.4.0 sem desinstalar. Se a 0.4.0 bloqueava no splash, terminar a aplicação no Gestor de Tarefas antes de instalar.

**Versão experimental.** A sincronização Android/Windows e os restantes módulos clínicos ainda estão em desenvolvimento. A versão Windows não substitui alarmes Android.
