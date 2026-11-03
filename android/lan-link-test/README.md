# SaúdePrática — Ligação Wi-Fi experimental Windows ↔ Android

## O que é possível testar
1. No Android, instalar a aplicação auxiliar **SaúdePrática Ligação (Teste)**. É separada da app clínica instalada e **não substitui a versão 1.9.127**.
2. Ligar Android e Windows à mesma rede Wi-Fi. Abrir a aplicação auxiliar e tocar em «Tornar visível».
3. Abrir a SaúdePrática Windows **0.8.12**: deteta o Android por mDNS e pergunta se queres abrir a sincronização. Em «Mais módulos → Sincronização» podes também escolher o dispositivo manualmente.
4. Clicar em «Pedir ligação». Comparar os seis dígitos apresentados no Windows e no telemóvel; tocar **Autorizar** ou **Recusar** no Android.
5. O Windows mostra «Ligação aprovada» ou «Ligação recusada». Se o mDNS falhar, o Windows tenta automaticamente descoberta UDP pela rede local; a ligação por IP permanece uma alternativa. A descoberta UDP necessita da versão 0.2 deste APK auxiliar.

## Limites intencionais
- Este é apenas um **teste de ligação**, sem acesso aos dados da app SaúdePrática Android existente. Nenhum medicamento, perfil, documento, consulta ou fotografia é sincronizado.
- A comunicação do teste não utiliza TLS e não é adequada a dados clínicos. Na próxima fase, emparelhamento autenticado com canal cifrado, identidades estáveis, cópia de segurança e interface de conflitos serão obrigatórios antes de transmitir qualquer dado de saúde.
- Não abrir portas no router, não usar o serviço fora da rede local e desligar a aplicação auxiliar no fim do ensaio.
- A app auxiliar usa um identificador Android distinto (`pt.saudepratica.linktest`), é assinada com uma chave de teste própria e não consegue aceder aos dados privados da app original.
- A app Windows também não passa a agendar alarmes no Android. Backups existentes não são alterados.

Objetivo: testar deteção automática, pedido de ligação, código e autorização antes de ligar a sincronização real à aplicação Android principal.

## Atualização auxiliar 0.2 — descoberta automática mais robusta

- No Android, quando o utilizador toca «Tornar visível», o telemóvel anuncia-se por NSD/mDNS e responde a pedidos UDP locais de descoberta na porta 43838. A resposta contém apenas o código temporário de descoberta, a porta TCP local e a designação genérica do telemóvel. Não há acesso aos dados da app SaúdePrática clínica.
- O Android mantém temporariamente a receção multicast ativa enquanto o teste está visível (permissão normal CHANGE_WIFI_MULTICAST_STATE) e liberta-a ao desligar.
- Windows 0.8.12 volta a consultar mDNS ao tocar «Procurar novamente» e procura em paralelo por broadcast UDP na rede local (usando os IPs e máscaras das interfaces Wi-Fi/Ethernet). Verifica por HTTP apenas o protocolo de teste do dispositivo antes de o apresentar.
- O utilizador continua a confirmar o mesmo código de seis dígitos no ecrã do Android. A pesquisa por IP continua disponível.
- É necessário **instalar 0.8.12 Windows e 0.2 Android auxiliar** para testar a alternativa UDP. A app Android oficial mantém-se separada e não é modificada.
- Caso o router bloqueie a comunicação entre clientes, ou uma firewall impeça a descoberta UDP/mDNS, a ligação manual por IP pode continuar necessária. Não é um canal seguro para dados clínicos e não sincroniza informação médica.
