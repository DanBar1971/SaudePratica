# SaúdePrática Windows 0.8.12 — descoberta automática Android mDNS + UDP

**Acompanhamento do problema real:** o Windows 0.8.11 não encontrava a app Android auxiliar de ligação automaticamente, mesmo com os dispositivos na mesma rede Wi-Fi, mas o teste por IP e código de autorização funcionava.

## Diagnóstico do código
- No Windows, «Procurar novamente» chamava PhoneDiscovery.start(); este método regressava imediatamente quando o watcher Zeroconf já estava iniciado. O botão não gerava nova pesquisa.
- O Windows dependia apenas de mDNS/DNS-SD (`_saudepratica-sync._tcp.local.`). O router/AP, a firewall, redes convidadas, VPNs, interfaces Windows ou filtros multicast Android podem bloquear esses anúncios embora TCP por IP funcione.
- A app Android auxiliar anterior anunciava-se com NsdManager mas não adquiria uma WifiManager.MulticastLock; em alguns sistemas Android é necessária para receber multicast.

## Correção (Windows 0.8.12 + APK auxiliar Android 0.2)
- O botão «Procurar novamente» reinicia efetivamente a consulta mDNS e descarta resultados antigos.
- Em paralelo, o Windows envia **pedidos UDP broadcast** locais (`SP_DISCOVER_1:<nonce>`) na porta UDP 43838 a partir de cada interface IPv4 privada Wi-Fi/Ethernet válida. A pesquisa é limitada a algumas tentativas e não faz varrimento de toda a sub-rede.
- O novo APK auxiliar responde apenas enquanto o utilizador o tornou visível, com o mesmo nonce, a porta TCP temporária e a designação do telemóvel. Não transmite qualquer dado pessoal.
- A resposta só é apresentada no Windows após verificar por HTTP `/v1/status` que é de facto o protocolo `sp-pair-test-0` em modo `link-only`. Descobertas repetidas são deduplicadas por IP e porta.
- O Windows volta a tentar automaticamente a cada ~12 segundos enquanto estiver no ecrã Sincronização e não encontrar dispositivos; se o Android só ficar visível depois do Windows, deverá poder aparecer sem configurar IP.
- A pesquisa UDP continua possível mesmo quando o watcher mDNS falha; a ligação manual por IP e porta continua como alternativa.
- A aplicação Android auxiliar 0.2 usa a receção multicast enquanto está visível e liberta-a ao desligar. A permissão `CHANGE_WIFI_MULTICAST_STATE` é normal e não permite ler dados clínicos.

## Testes e segurança
- Novos testes de ponta-a-ponta sintéticos com servidor UDP Android fictício e endpoint HTTP, nonce errado/host público rejeitado, descoberta efetiva, rescan e identificação de interfaces.
- Código nunca lê medicação, perfis, fotos ou contactos para a rede. A autorização por código de 6 dígitos continua no Android.
- A comunicação de teste ainda **não tem autenticação/cifragem de transporte** e NÃO pode ser usada para transferir informação médica.
- Este teste **não substitui a app SaúdePrática oficial Android**: continua a ser uma APK auxiliar de emparelhamento.
- Android oficial 1.9.xxx, backups, perfis e releases normais preservados.
- Em redes que bloqueiam totalmente broadcast/multicast ou isolamento de clientes, a descoberta ainda pode falhar. O suporte por IP permanece disponível; não abrir portas do router.

## Como testar
1. No telemóvel instala `SaudePratica-Ligacao-Teste.apk` **0.2** (pode ser necessário remover a antiga aplicação auxiliar de teste se a assinatura DEBUG do GitHub for diferente; não remover a app SaúdePrática principal).
2. Instala a SaúdePrática Windows **0.8.12** por cima da anterior (backup `.spbackup` primeiro).
3. Abre a auxiliar Android → «Tornar visível» e, no Windows, Opções → Sincronização.
4. Deve surgir o telemóvel automaticamente sem introdução do IP; testa também «Procurar novamente».
5. «Pedir ligação» → confirma o mesmo código nos dois ecrãs → «Autorizar» no Android.
6. Repete com o Android a ficar visível **depois** de abrires o ecrã Windows para verificar a repetição automática.

Um sucesso da ligação prova apenas comunicação local e autorização; não sincroniza dados clínicos.
