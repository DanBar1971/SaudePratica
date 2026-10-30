# SaúdePrática v1.9.120 — fase experimental Diabetes e Atalhos (Android)

## Funcionalidades introduzidas
- **Diabetes (primeiro módulo offline)**: diário de glicemia por perfil e HbA1c laboratorial, seleção de mg/dL/mmol/L, data, contexto, notas, gráfico de 30 dias, histórico e exportação CSV por partilha Android.
- **Atalhos Importantes · Apps e Web**: nova área com separação explícita entre aplicações instaladas e websites. Seletor pesquisável de aplicações lançáveis, ordenação, edição e eliminação de atalhos. Presets SNS 24 e IPO Lisboa com os package IDs oficiais. Não apaga os atalhos legados existentes.
- **Menu Início**: troca de SNS 24 e IPO Lisboa por um cartão Diabetes; as aplicações passam a ser acessíveis via novos Atalhos em Mais.
- **Página oficial**: Mais → Página oficial da SaúdePrática; abrir ou partilhar https://danbar1971.github.io/SaudePratica/ .
- **Ajuda**: secções em PT/EN/FR/DE/ES para Diabetes e Atalhos.
- **Ajuda Inteligente**: perguntas e respostas offline sobre Diabetes, Atalhos e Nutrição. Não envia dados clínicos.

## Limitações e cuidados
- **Não são medidos valores pela câmara ou pelo ecrã**. A aplicação não substitui aparelhos médicos, os alertas clínicos oficiais ou o plano de emergência.
- Sem recomendações automáticas de insulina, sem alertas médicos autónomos.
- **Diabetes MVP é local**: os registos nesta fase **não estão integrados com o backup familiar nem com Nearby Sync**. Exportar CSV separadamente antes de mudar/desinstalar de telemóvel. Não desinstalar a SaúdePrática atual para testar.
- CSV é partilhado como texto para evitar providers inseguros; geração de PDF e integração com Health Connect/PortFIR ainda não concluídas.
- Acessibilidade/Modo Sénior **ainda não foi movido** para Aspeto e Idioma; o antigo fluxo de Atalhos pode continuar acessível.
- A integração nativa PortFIR, Open Food Facts e os sensores/medidores será uma fase posterior e depende de revisão de fontes, licenças e fiabilidade.

## Validação necessária
- Compilar no CI e testar num Android real, especialmente Xiaomi/MIUI: instalação por cima da versão anterior assinada; menu e navegação; seletor de apps e execução SNS 24/IPO; websites; manter backups históricos; inclusão/edição/eliminação de glicemias; valores com vírgula; unidades; data; exportação; isolamentos entre perfis; modo sénior; funcionamento dos alarmes e do ecrã bloqueado.
- **Não publicar esta fase como release estável antes de passar a compilação, os testes de regressão e os testes básicos de dados do módulo.**
- Preservar `com.mediagenda.app.stable` e a assinatura original. Não utilizar outro certificado.
