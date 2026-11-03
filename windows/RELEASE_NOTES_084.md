# SaúdePrática Windows 0.8.4 — descoberta automática do Android (teste)

## Novo ecrã Sincronização
- Ao abrir a SaúdePrática Windows, inicia-se pesquisa **mDNS/DNS-SD** na rede local por serviços `_saudepratica-sync._tcp.local.`.
- Ao encontrar a aplicação auxiliar Android **SaúdePrática Ligação (Teste)**, o Windows apresenta um convite: «Telemóvel encontrado. Queres abrir a sincronização?».
- Em **Mais módulos → Sincronização**, a lista mostra os equipamentos disponíveis, com botão **Pedir ligação**.
- O Windows apresenta um **código de seis dígitos**; o telemóvel mostra o mesmo código e pede aprovação explícita («Autorizar» / «Recusar»).
- Se o router bloquear a descoberta automática, existe **Ligar por IP**: utilizar o IPv4 e a porta mostrados no ecrã do telemóvel.
- Os pedidos são iniciados manualmente, os resultados são confirmados no Windows e a interface não fica bloqueada durante a espera.
- Mantém todo o grafismo e módulos Windows 0.8.3: Medicação, Agenda, Perfis, OCR, fotos, Backup e Avisos.

## Segurança e estado REAL
Esta primeira versão **NÃO SINCRONIZA qualquer dado**. Nunca lê/envia perfis, medicação, receitas, agendas, fotos ou documentos. O protocolo de demonstração é HTTP em rede local sem TLS e **não pode ser usado para dados clínicos**. O primeiro passo é verificar apenas a descoberta, a conexão e a autorização presencial.

O Android oficial **1.9.127 permanece inalterado**. Para este teste é necessária uma APK auxiliar separada chamada «SaúdePrática Ligação (Teste)», com identificador próprio, disponível na Release `android-lan-link-v0.1-preview`. Não desinstalar a SaúdePrática Android original.

A sincronização bidirecional de dados virá numa fase posterior com autenticação mútua, cifragem, identificação estável, comparação e confirmação de conflitos, backup de segurança e testes completos. Não fazer encaminhamento de portas no router nem usar fora da rede local. A ligação experimental apenas funciona enquanto as duas aplicações de teste estiverem ativas.

Antes de atualizar o Windows, guardar um backup `.spbackup`.
