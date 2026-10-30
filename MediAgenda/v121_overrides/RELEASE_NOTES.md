# SaúdePrática v1.9.102 — Alarmes sem PIN, perfis separados e criação guiada

- Novo perfil guiado em quatro etapas: nome e fotografia, Cartão de Cidadão opcional com OCR e escolha de guardar ou não fotografias, associação do perfil a este telemóvel e papel de cuidador, revisão e contactos.
- Só confirma a criação no último passo. Fotografias intermédias ficam em cache privada e são eliminadas se a criação for cancelada.
- Perfil reorganizado com fotografia grande ao abrir, miniaturas clicáveis do CC, largura e altura ampliadas e separação de dados pessoais, identificação, morada e contactos.
- Números de observação e processos saem da ficha pessoal para a Situação Clínica; as chaves legadas permanecem e os valores existentes são preservados.
- Mantidos identificadores de perfil, código do pacote Android, notificações e certificados de assinatura existentes.
- As traduções globais da aplicação, o design completo da Nutrição e outras partes do pedido **não** estão incluídos nesta versão.
- É necessário testar OCR, autorizações de câmara, armazenamento de fotos, criação de perfil de cuidador, dados já existentes e atualização sem desinstalar num telemóvel físico.

## Alarme de medicação: correções prioritárias
- **Ecrã de alarme excluído do PIN da SaúdePrática**. Os únicos botões são **ADIAR 10M** e **TOMEI**; não é necessário fazer login na app para os utilizar. O acesso aos dados clínicos continua protegido.
- O alarme usa a visibilidade de uma Activity realmente autenticada, não a importância de um processo que tenha um serviço de áudio em primeiro plano.
- Retirada a flag obsoleta `FLAG_DISMISS_KEYGUARD`. Mantém `setShowWhenLocked(true)` e `setTurnScreenOn(true)`, respeitando a segurança do Android/HyperOS.
- **Tomas separadas por perfil**: a ficha Tomas do cuidador já não agrega nem permite apagar os registos dos familiares. Os contadores de tomas atrasadas e de próximas marcações aparecem individualmente em **Escolher perfil**.
- **📱 Associar alarmes a este telemóvel** permite definir explicitamente qual o perfil que deve tocar neste equipamento. O papel cuidador não o associa automaticamente como paciente local.
- Os medicamentos de familiares continuam registados no próprio perfil, mas deixam de criar uma segunda notificação desse familiar neste telemóvel.
- Na ficha da medicação, nova caixa de seleção visível **NÃO TEM CAIXA · Só lamelas/blisters**; usa a imagem de comprimidos, distinguindo-a da imagem de embalagem sem fotografia.
- Mantidos os botões de adiamento de 10 minutos e confirmação de dose sem abrir a app; os alarmes sem interação ficam por confirmar após 60 segundos.

## Limitações e testes obrigatórios
- O Android 14+/HyperOS pode mostrar uma notificação destacada, em vez da janela inteira, quando o telemóvel está desbloqueado. **A aplicação não pode obrigar o sistema a contornar esta regra.**
- Para o ecrã bloqueado, verificar a autorização especial **Notificações em ecrã inteiro** para SaúdePrática, notificações, alarmes exatos, e restrições de bateria. Um PIN do próprio telemóvel não deve ser desativado.
- Compilação e verificações estáticas de PIN, identidade dos alarmes e registos por perfil foram executadas; **o comportamento real do Xiaomi ainda exige teste com o ecrã bloqueado e desbloqueado**, medicação única, grupos, adiamento e 60 s sem resposta.
- Consultar `MediAgenda/v122_overrides/ALARM_AUDIT.md` para a matriz de ensaios e as causas dos erros anteriores.
