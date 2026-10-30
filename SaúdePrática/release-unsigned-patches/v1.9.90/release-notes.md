# SaúdePrática v1.9.90 — Acesso rápido ao perfil e SOS visível

## Melhorias na interface
- **Perfil no canto superior direito:** manter o dedo sobre a fotografia/nome durante **3 segundos** abre diretamente a ficha de edição do perfil ativo. Um toque rápido continua a permitir escolher o perfil.
- **SOS na página inicial:** ao tocar e manter pressionado, o cartão fica **amarelo**, com contagem decrescente visível de **4 segundos**.
- Foi reforçada a gestão do toque para que o scroll da página não cancele inadvertidamente a contagem. A ação de chamada é ativada quando completados os 4 segundos de pressão contínua.
- Se soltares antes dos 4 segundos, **não é feita a chamada**. Um toque curto continua a abrir a Ficha de Emergência.
- A chamada usa exclusivamente o contacto de emergência guardado **no perfil selecionado** e continua sujeita à permissão Android de chamadas; sem permissão, abre o marcador do telemóvel quando permitido.

## Compatibilidade e atualização
- Mantidas as funções da v1.9.89: download persistente no Android, APK acessível na pasta Downloads e validação de SHA-256/certificado antes da instalação.
- Mantidos dados, medicação, tomas, agenda, documentos, alarmes e sincronização familiar.
- APK `com.mediagenda.app.stable`, assinada com o **certificado original** (Android v2/v3). Não desinstalar versões anteriores; instalar por cima para preservar os dados.

## Testes no telemóvel
- Verificar toque rápido e pressão de 3 segundos no avatar do perfil.
- Verificar SOS amarelo, contagem, cancelamento ao soltar e abertura da Ficha de Emergência.
- Testar a atualização automática **a partir da v1.9.89** no Xiaomi/HyperOS e confirmar a autorização de instalação.
- A medição do toque inicia-se imediatamente, mas a abertura da app Telefone pode depender da permissão Android e da resposta do sistema.
