# SaúdePrática Android v1.9.125 — Fiabilidade da sincronização Nearby

Esta atualização reutiliza melhorias testadas na Remote PhotoBridge, mas **não altera os dados clínicos, a lógica de fusão de perfis, os medicamentos, as tomas ou os alarmes**.

- Em **Sincronização familiar**, barra de progresso com percentagem real dos bytes transferidos pelo Nearby. A barra fica em 99% enquanto o destinatário está a integrar o ficheiro e apenas atinge 100% depois de o processo de receção terminar.
- O telemóvel de origem deixa de anunciar antecipadamente que os dados foram sincronizados apenas porque a transmissão do ficheiro terminou. O destinatário envia confirmação curta **apenas depois de a fusão do perfil escolhido ter terminado com sucesso**. Os dois telemóveis devem estar atualizados para 1.9.125 para mostrar este estado final confirmado.
- Em **Modo da ligação Nearby**, escolha entre Padrão (comportamento anterior e valor inicial), Estável (tenta preservar o Wi-Fi do router) e Velocidade máxima (pode alterar temporariamente o Wi-Fi do router). A escolha só entra em vigor num novo emparelhamento.
- Botão **Repetir ligação** após falha, sem iniciar transferências automáticas nem dispensar a confirmação de segurança nos dois telemóveis.
- Retenção visual de dispositivos encontrados quando o Nearby comunica uma perda temporária durante a negociação em alguns Android/Xiaomi.
- Ecrã mantido ativo enquanto o utilizador executa a sincronização em primeiro plano. Não é criado nenhum serviço permanente, notificação intrusiva ou sincronização sem consentimento.

## Segurança e compatibilidade

Continua **um único perfil por operação e um único sentido**, com escolha do perfil, verificação visual dos códigos nos dois aparelhos e lógica de importação/identidade original. O destinatário tem de integrar o perfil antes de confirmar o envio. Continua recomendada uma cópia de segurança dos dois aparelhos antes de testar em dados clínicos reais.

**O sistema de dados Windows ↔ Android não foi alterado.** A versão Windows continua com o comportamento publicado anteriormente.

APK Android com a **mesma assinatura original** e identificador `com.mediagenda.app.stable`, atualizável por cima da versão anterior. O workflow publica a APK no GitHub Releases e atualiza a página oficial GitHub Pages somente após a validação da assinatura.
