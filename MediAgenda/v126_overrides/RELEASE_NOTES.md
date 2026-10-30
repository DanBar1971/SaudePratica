# SaúdePrática v1.9.106 — Continuação de «Alterações 1»

## Alterações incluídas nesta versão
- **Agenda:** atalhos superiores compactos, filtros «Todas», «Pendentes», «Realizadas» e «Canceladas». Foi acrescentado ao modelo de dados o estado explícito `cancelled`, guardado e reaberto em JSON. Marcações canceladas não geram avisos; as realizadas continuam a exigir confirmação manual, sem serem confundidas com marcações antigas. Cartões com estados, cores, prioridade visual para hoje e menor opacidade para realizadas/canceladas.
- **Medicação:** cartões existentes com foto da caixa, faixa «SUSPENSA», botão «Tomei» e informação de última toma. Novos indicadores visuais para suspensão, SOS, hora prevista ultrapassada e toma já registada nesse dia. Ordenação por nome, próxima toma, categoria e estado. Não altera a lógica dos alarmes de múltiplas tomas.
- **Situação Clínica:** retirado o comando «Editar número antigo (opcional)»; campo histórico original mantido intocado, visível apenas como legado. Na criação/edição de números individuais, é possível escolher instituição pela sequência Distrito → Concelho → Unidade usando o mesmo catálogo offline da Agenda, com entrada manual alternativa. Continua a aceitar múltiplos números por unidade e a manter os dados separados por ID de perfil.
- **Perfis:** assistente de criação dividido em **seis passos**: identidade, documento/CC, tipo de perfil, contactos, dados clínicos e conclusão. Campos adicionais de morada, contacto de emergência, unidade preferencial e notas clínicas guardados nas preferências do perfil, sem sobrescrever os já existentes. Ficha de edição com resumo de identidade e unidade; fotografias grandes e miniaturas do CC da versão anterior mantidas.
- **Nutrição:** histórico com identificação Gemini/manual e apresentação dos alimentos em minicartões no detalhe, conservando fotografia, kcal, macros, revisão Gemini, edição manual e persistência do diário por perfil.
- **Tema claro:** utiliza o fundo original SaúdePrática com sobreposição clara na página principal, Situação Clínica, criação de perfil e Nutrição; não depende de imagens externas.
- **Idiomas:** ampliação do catálogo PT/EN/FR/DE/ES para os novos controlos, correção das traduções de «Oferecer um café via PayPal». Os textos introduzidos pelo utilizador não são traduzidos automaticamente.
- **Compatibilidade:** mantidos `applicationId=com.mediagenda.app.stable`, ficheiros de dados por perfil e assinatura original Android; incremento para `versionCode=116` e `versionName=1.9.106`.

## Ainda pendente de «Alterações 1»
- Internacionalização **integral** de todos os textos estáticos e dinâmicos em todos os módulos: o catálogo foi alargado, mas não está completamente migrado para recursos de idioma.
- Reorganização integral do editor de perfil em cinco cartões separados (o formulário anterior ainda inclui campos extensos).
- Aperfeiçoamento adicional dos cartões e da edição dos alimentos de refeições antigas com todas as quantidades estruturadas.
- Validação visual em dispositivo Xiaomi real, especialmente modo claro, filtros da Agenda e assistente de seis passos.

## Segurança e instalação
- Fazer primeiro backup dos perfis na aplicação.
- Instalar a APK assinada por cima da versão anterior, **sem desinstalar**.
- A APK só é considerada publicada após verificação do `SaudePratica.apk` em GitHub Releases com o **mesmo certificado da v1.9.105**.
- Não incluir chaves privadas de assinatura, palavras-passe, segredos de recuperação ou dados clínicos no GitHub.
