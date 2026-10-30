# SaúdePrática v1.9.83 — Gemini na Nutrição e correções de alarmes

## Novidades
- **Nutrição:** reconhecimento de alimentos e estimativa de calorias por fotografia com Gemini Flash, após consentimento expresso. Separação de vários alimentos, edição de nomes, gramas e kcal antes de guardar. A análise online usa uma chave Gemini configurada uma única vez no telemóvel, cifrada com Android Keystore, ou o serviço central opcional; nunca incorpora segredos na APK. A chave não é sincronizada nem incluída em backups.
- **Nutrição:** botão **Eliminar refeição** agora visível diretamente em cada registo do histórico. Confirmação antes de apagar o registo e a fotografia associada ao mesmo perfil.
- **Alarme de medicação:** apresentação mais discreta da notificação quando a app já está aberta, para não tapar o ecrã do alarme.
- **Nome e dose:** medicamento e quantidade repostos no alarme, incluindo o resumo da notificação que mostra a fotografia da embalagem.
- **Adiamento de 10 minutos:** ao confirmar uma toma na notificação, em Tomas ou na ficha de medicação, o adiamento da ocorrência original é cancelado. Um aviso atrasado já confirmado não deve voltar a ser mostrado. Sem alteração dos alarmes de tomas futuras.

## Como instalar
**Atualiza por cima da versão anterior. NÃO desinstales a SaúdePrática.** A assinatura original e o package ID `com.mediagenda.app.stable` foram verificados contra a APK v1.9.82, para preservar os perfis e os dados locais. Recomenda-se backup antes de atualizar.

## Testes recomendados
1. Abre Nutrição, configura e testa a chave Gemini no telemóvel, fotografa uma refeição composta, confirma o envio da imagem e corrige ingredientes/porções.
2. Guarda uma refeição com foto, abre Histórico e experimenta **Eliminar refeição** (confirma a remoção após consentimento).
3. Aguarda um alarme real, confirma a presença do nome e da dose, toca **ADIAR 10 MIN**, depois confirma a toma em **Tomas** antes dos dez minutos. Não deve voltar a disparar esse alarme.
4. Verifica o ecrã do alarme aberto sem um aviso extra a tapar os controlos; confirma que Lares, Atalhos, fotografias, perfil e gráficos continuam presentes.

## Limitações
- O reconhecimento Gemini é uma estimativa visual sujeita a erro; revê todas as gramas e calorias. Exige Internet, uma chave Gemini válida/quota e consentimento explícito. Não foram enviadas chaves privadas para a APK/GitHub.
- A compilação e a assinatura Android foram verificadas. O funcionamento real em cada marca de telemóvel (incluindo HyperOS) necessita de teste prático; a apresentação do aviso também depende das permissões do sistema.
- A chave Gemini fornecida em mensagens anteriores foi exposta na conversa e não ficou pré-instalada na aplicação, por segurança. Recomenda-se a sua rotação antes da distribuição.
