# SaúdePrática Android v1.9.130 — IA local leve opcional

Preparado para equipamentos Android compatíveis com CPU arm64, incluindo a classe do Redmi Note 13 Pro. Continua a existir a opção Gemini Nano quando suportada pelo Android.

- **Perguntas e respostas offline** com Qwen3 0.6B (GGUF Q4_K_S, ~383 MB), licenciado Apache 2.0.
- **Escolha explícita em dois passos**: primeiro confirmar o download (idealmente Wi‑Fi) e depois instalar/ativar o modelo na aplicação. A APK não contém nem instala automaticamente os 383 MB.
- Verificação SHA-256 contra uma versão fixa e auditável do GGUF antes da ativação; armazenamento privado e opção de remoção.
- Motor nativo CPU baseado em llama.cpp, compilado e distribuído com a APK; o modelo fica no telemóvel. Nenhuma pergunta é enviada para servidores da app.
- Ajuda nativa de medicação e agenda sem alterações; rascunhos só são guardados mediante confirmação, com separação por perfil.
- Ecrã com imagem de fundo oficial da SaúdePrática, botões mais coesos e correção de espaço para teclado e barra de navegação.
- Se o motor não estiver instalado ou for incompatível, a app continua a funcionar sem IA.
- *Limitação inicial*: o modelo é muito pequeno, pode ser lento e pode falhar em perguntas complexas. Não substitui profissionais de saúde.
- Não alterar alarmes, horas, estados de toma, dados de medicação ou clínica sem validação adicional.

**Versão normal 1.9.xxx**, não pré-release. Só publicar após compilação Android, testes de regressão e assinatura verificada com o certificado original.
