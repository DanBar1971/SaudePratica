# SaúdePrática Desktop 0.6.1 — iconografia Android e fundo corrigido

## Correções de qualidade visual
- **Ícones dos módulos muito maiores (64 px), sem qualquer quadrado, fundo artificial ou moldura à volta.** Utiliza os mesmos símbolos emoji presentes nos cartões Android, renderizados com a fonte colorida Segoe UI Emoji do Windows.
- **Fundo recomposto em formato 16:9 a partir de `assets/saude_background.png` original de alta resolução**. Os motivos geométricos são mantidos na proporção correta e o centro fica sóbrio. Já não amplia a miniatura WebP fortemente comprimida da 0.6.0.
- Retiradas molduras duplicadas do painel de Perfis e de secções da ficha de Medicação; cartões mais limpos.
- A seleção do perfil, fotografias autênticas, medicação em cartões, temas e todos os módulos mantêm-se.

## Segurança e testes
- Sem alterações aos dados DPAPI, cópias `.spbackup`, alarmes ou versão Android.
- Executa testes da resolução efetiva do fundo, transparência dos ícones, integridade da interface, arranque do código e do EXE empacotado antes da publicação.
- A sincronização entre Android e Windows e os módulos marcados «Em breve» continuam pendentes.

Instala por cima da versão 0.6.0 **sem desinstalar**.
