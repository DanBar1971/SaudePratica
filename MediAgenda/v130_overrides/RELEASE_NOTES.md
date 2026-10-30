# SaúdePrática v1.9.110 — Correção transversal de botões e diálogos
- Auditoria aos diálogos Material utilizados em **22 ecrãs** da aplicação (cerca de 190 chamadas).
- Barra de ações de cada diálogo com **botões lado a lado**, preservando as ações existentes e os listeners; para textos longos, até duas linhas, tamanho de letra adaptativo e descrição completa de acessibilidade.
- Diálogos longos limitados à altura disponível do telemóvel, evitando que os botões do rodapé fiquem tapados pelas barras do sistema.
- **Nutrição:** o diálogo do histórico mantém «Associar foto», «Eliminar refeição» e «Fechar» e beneficia do novo rodapé global.
- **Perfil:** mantém «Eliminar», «Cancelar» e «Guardar» numa única linha; o formulário ocupa menos altura, disponibilizando mais espaço para o rodapé.
- Sem alterações ao Gemini (incluindo prompts, modelos, APIs, cálculos e persistência), à medicação e alarmes, nem às funções de criação/edição de registos.
- Compatibilidade: applicationId `com.mediagenda.app.stable`, versionCode `120`, versionName `1.9.110`, certificado Android original.
- **Verificação funcional recomendada no Xiaomi:** abrir diálogo longo de Nutrição e deslocar até ao fim, guardar perfil com teclado aberto, verificar «Eliminar / Cancelar / Guardar» e usar o tamanho de letra ampliado.
- Instalar por cima da versão anterior, sem desinstalar; fazer backup preventivo.
