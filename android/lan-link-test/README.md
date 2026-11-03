# SaúdePrática — Ligação Wi-Fi experimental Windows ↔ Android

## O que é possível testar
1. No Android, instalar a aplicação auxiliar **SaúdePrática Ligação (Teste)**. É separada da app clínica instalada e **não substitui a versão 1.9.127**.
2. Ligar Android e Windows à mesma rede Wi-Fi. Abrir a aplicação auxiliar e tocar em «Tornar visível».
3. Abrir a SaúdePrática Windows **0.8.4**: deteta o Android por mDNS e pergunta se queres abrir a sincronização. Em «Mais módulos → Sincronização» podes também escolher o dispositivo manualmente.
4. Clicar em «Pedir ligação». Comparar os seis dígitos apresentados no Windows e no telemóvel; tocar **Autorizar** ou **Recusar** no Android.
5. O Windows mostra «Ligação aprovada» ou «Ligação recusada». Em routers que bloqueiam mDNS, é possível introduzir IP e porta exibidos no Android.

## Limites intencionais
- Este é apenas um **teste de ligação**, sem acesso aos dados da app SaúdePrática Android existente. Nenhum medicamento, perfil, documento, consulta ou fotografia é sincronizado.
- A comunicação do teste não utiliza TLS e não é adequada a dados clínicos. Na próxima fase, emparelhamento autenticado com canal cifrado, identidades estáveis, cópia de segurança e interface de conflitos serão obrigatórios antes de transmitir qualquer dado de saúde.
- Não abrir portas no router, não usar o serviço fora da rede local e desligar a aplicação auxiliar no fim do ensaio.
- A app auxiliar usa um identificador Android distinto (`pt.saudepratica.linktest`), é assinada com uma chave de teste própria e não consegue aceder aos dados privados da app original.
- A app Windows também não passa a agendar alarmes no Android. Backups existentes não são alterados.

Objetivo: testar deteção automática, pedido de ligação, código e autorização antes de ligar a sincronização real à aplicação Android principal.
