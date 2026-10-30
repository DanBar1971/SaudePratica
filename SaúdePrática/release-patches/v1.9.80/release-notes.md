# 📱 SaúdePrática — v1.9.80

## 🏡 Lares e Apoio à Terceira Idade — residentes

- A **instituição e os contactos** passam a ser comuns dentro do módulo Lares: configuram-se **uma única vez**, sem repetir em cada perfil.
- Novo ecrã **Residentes do lar**, com **Associar / retirar residentes** para escolher explicitamente Camy, pais, avós ou outros perfis já existentes.
- Escolher **residente em acompanhamento** sem alterar o perfil principal da SaúdePrática.
- **Faturas, valores ADSE, valência ERPI/SAD/Centro de Dia, notas e documentos** permanecem separados pelo ID estável de cada residente.
- A app **não associa automaticamente o perfil ativo** à residência; só inclui os utentes selecionados.
- A informação institucional anterior é preservada e migrada com segurança para a ficha comum.

## 🔗 Atalhos Importantes

- Na gestão de links, botões **↑ Subir** e **↓ Descer** para alterar a ordem da lista.
- A ordenação é guardada localmente e preserva todos os links existentes, incluindo os personalizados.

## 🏠 Ecrã inicial

- Textos compactos para evitar descrições cortadas em telemóveis pequenos:
  - **Lares e Apoio à Terceira Idade:** “Lar, faturas e ADSE”
  - **Atalhos Importantes:** “Links úteis”

## 🎨 Gráficos originais restaurados

- **Fundo**, **ícone oficial** e **splash de abertura** recolocados a partir dos ficheiros fornecidos para o projeto.
- O ícone de lançamento Android utiliza a arte SaúdePrática em vez dos gráficos provisórios.
- O workflow de compilação passa a **bloquear a APK** se estas três imagens originais não estiverem presentes e incorporadas no ficheiro compilado.

### 🧪 Como testar

1. Atualizar por cima da versão anterior, **sem desinstalar** (preferencialmente com backup prévio).
2. Abrir **Atalhos Importantes → Gerir e adicionar atalhos**, reorganizar alguns com Subir/Descer e voltar para verificar a ordem.
3. No ecrã inicial, confirmar que as descrições curtas não ficam cortadas.
4. Abrir **Lares → Associar / retirar residentes** e selecionar **Camy** e, se necessário, outras pessoas do mesmo lar.
5. Usar **Escolher residente** e confirmar que as faturas e os documentos de Camy não aparecem como sendo do Daniel.
6. Abrir e fechar a app e confirmar o **ícone**, a **imagem de abertura** e o **fundo**.

**Importante:** a submissão à ADSE continua manual; esta versão não ativa automaticamente a sincronização familiar dos registos do lar nem envia emails sem confirmação.

A APK foi compilada, assinada com o certificado original (assinatura v2/v3), validada e preparada para atualização preservando os dados.

**SaúdePrática — Tudo num só lugar.**
