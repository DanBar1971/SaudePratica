# SaúdePrática v1.9.104 — Correção urgente de perfis e botões tapados

- **Escolher perfil:** Corrigida sobreposição causada pela combinação `MaterialCardView`/`FrameLayout`. Reaparecem nome, foto e indicadores de cada perfil; é possível tocar no próprio perfil para entrar.
- **Associar alarmes a este telemóvel:** Continua disponível, mas numa linha inferior independente, que não cobre a fotografia nem intercepta a seleção.
- **Criar novo perfil:** Botões **Anterior** e **Seguinte/Criar perfil** sempre acima da barra de navegação do Android, incluindo HyperOS 3 e Android 16.
- A janela passa a respeitar `WindowInsetsCompat.Type.systemBars()` e `Type.ime()`. O formulário continua a permitir scroll, mesmo com teclado visível.
- Mantidos os dados, perfis, alarmes, TOMAS por utente, medicação, Nutrição, imagens oficiais, identificador e certificado original.

**Verificação necessária em dispositivo:** Selecionar cada familiar na página de escolha; associar alarmes; abrir **Novo perfil**, avançar com o teclado aberto, testar as teclas de navegação Android de três botões e o gesto inferior. Não é necessário desinstalar a aplicação; efetuar backup antes da atualização.
