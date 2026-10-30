# SaúdePrática — sincronização bidirecional Windows ↔ Android (protocolo v3)

## Estado atual
Nearby v2 no Android é incremental, de sentido único e não é backup/restauro.
A versão experimental Windows não sincroniza; o ecrã identifica isto claramente.

## Funcionalidade a desenvolver
- Rede local Wi-Fi, sem Internet obrigatória; não usar o GitHub para dados clínicos.
- Emparelhamento com confirmação explícita em ambos os aparelhos, usando
  código de utilização única ou QR, e canal encriptado com autenticidade.
- Utilizador escolhe exatamente perfis e categorias antes da transferência.
- Ambos trocam identidades, IDs, versões e hashes; mostram diferenças e
  conflitos num resumo antes de gravar.
- Sem duplicação de tomas, medicamentos ou fotografias; não fazer fusão por
  simples coincidência de nome; só apagar com consentimento explícito.
- Cópia local de segurança antes de aplicar alterações; operações atómicas.
- Falha da rede não pode anunciar sucesso parcial como completo; permitir
  retomar transferências verificadas e comparar hashes.
- Testar Windows→Android e Android→Windows, uso simultâneo, conflitos,
  equipamentos desconhecidos, cancelamentos e desconexões.
- Alarme Android não é alterado pela sincronização do Windows.

## Entregas
1. Portabilidade do backup em ambas as plataformas.
2. Conversão dos modelos de dados com IDs preservados.
3. Pairing seguro v3 e sincronização bidirecional.
4. Interface de conflitos e testes reais em dois aparelhos.
5. Evolução posterior para iOS.
