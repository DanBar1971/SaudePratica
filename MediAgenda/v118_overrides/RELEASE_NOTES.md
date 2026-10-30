# SaúdePrática v1.9.99 — Nutrição: alternativas Gemini e mensagens de quota

Correção do módulo **Refeições** após os erros HTTP 429 e HTTP 503 reportados em 27/10/2026.

- A app tenta primeiro o Gemini **3.5 Flash-Lite**, seguido de **3.1 Flash-Lite** e **2.5 Flash-Lite** (quando autorizado pelo projeto Google). Todos são modelos oficiais multimodais para analisar fotografias; deixam de ser feitas tentativas repetidas no 3.8 Flash sobrecarregado.
- **429 (limite/quota):** a app informa que não significa necessariamente que a chave API seja inválida. As quotas são do projeto Google e, em alguns casos, são específicas do modelo. É preciso consultar o [Google AI Studio](https://aistudio.google.com/rate-limit); a app não altera limites nem faz cobranças.
- **503 (indisponibilidade):** tenta os modelos alternativos sem repetir indefinidamente a mesma chamada. Se o serviço continuar indisponível, mantém a fotografia e permite **modo manual**.
- O teste de chave é feito com os mesmos modelos da análise e distingue falta de quota de falha de autenticação.
- O resultado continua sujeito a revisão de alimentos, porções e calorias. Todos os valores são estimativas visuais.

**Preservados:** identificador Android `com.mediagenda.app.stable`, certificação MediAgenda original, icon/splash/background, perfis, medicação, alarmes, TOMEI → TOMAS, documentos digitais e histórico de refeições.

**Testes:** verificações estáticas das fases A–E, validação do módulo nutricional e compilação Android CI. A compatibilidade de assinatura pode ser verificada com `apksigner`; a confirmação de funcionamento real da IA, da quota e dos alarmes exige ensaio no telemóvel com a chave e o projeto Google do utilizador.

**Importante:** nenhuma alteração à aplicação consegue resolver uma quota de API igual a zero ou a ausência de acesso a todos os modelos; nesses casos, pode ser necessário corrigir o projeto Google AI Studio ou o plano de utilização. Nenhuma chave API Google está incluída no APK ou neste repositório.
