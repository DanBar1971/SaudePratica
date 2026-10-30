# SaúdePrática v1.9.109 — Nutrição: revisão segura de refeições e ementas

## Novo (sem alterar o Gemini)
- Mantido **exatamente o mesmo pedido, API, análise e correção Gemini** das versões anteriores. Nenhum modelo, token, prompt, imagem enviada, resposta ou tratamento de erros foi alterado.
- Na revisão antes de guardar, opção **«Comi tudo o que está na fotografia (incluindo acompanhamentos)»** e aviso para conferir sopa, arroz, batatas, salada, fruta e bebidas. Mantidos os comandos atuais para alterar quantidades e acrescentar/retirar alimentos. A indicação é opcional, não impede guardar.
- No detalhe de uma refeição guardada: **«Associar fotografia da ementa»**. A imagem é guardada **localmente no perfil**, independente da fotografia da refeição, e pode ser substituída.
- No detalhe da refeição: **«Comparar com calorias da ementa»** para introduzir um valor oficial de referência e descrever os pratos incluídos. Mostra diferença em kcal e percentagem. Pode apagar a referência sem alterar os valores da refeição.
- **Auditoria dos registos antigos**: quando a lista textual contém calorias por alimento mas a soma difere do total guardado, mostra aviso de inconsistência. Nunca altera automaticamente os valores antigos nem envia esses dados à IA.
- Ao eliminar uma refeição, remove também a sua eventual fotografia de ementa; resto do diário e fotos de refeições inalterados.

## Segurança e limites
- Os números oficiais da ementa representam porções padrão; a app recorda que os acompanhamentos podem já estar contabilizados, para evitar contagem dupla.
- A fotografia da ementa **não é enviada automaticamente ao Gemini** nem extraída por OCR; a introdução do valor de referência é opcional. Não há nova chamada à API nem custos de Gemini adicionais.
- Mantido `applicationId=com.mediagenda.app.stable`; versão `1.9.109`, código `119`; assinar com certificado Android original e publicar em GitHub Releases.
- Antes de atualizar, fazer backup dos dados; instalar por cima da versão existente, sem desinstalar.
