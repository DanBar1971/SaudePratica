# SaúdePrática — Regra obrigatória de notas de versão

A cada nova versão da SaúdePrática, entregar **sempre**, juntamente com o APK assinado e o ZIP opcional, um texto pronto a copiar e partilhar com as pessoas que testam a aplicação.

## Regra permanente de entrega ao utilizador

**Obrigatório para todas as próximas versões, sem ser preciso voltar a pedir:**
- Na mesma resposta onde é enviada a ligação da **APK instalável**, incluir também um **texto de divulgação completo, pronto a copiar e a reenviar**, em português de Portugal.
- O texto deve trazer a versão, lista objetiva das **novidades** e **correções**, forma de instalar/atualizar sem perder dados, e — quando relevante — uma indicação breve de como testar.
- Escrever o texto **no corpo da resposta**, não apenas dentro de um TXT/ZIP; criar também um ficheiro de notas opcional para anexar à APK.
- Não anunciar melhorias que não foram implementadas ou validadas; distinguir compilação e testes reais.
- Se o lançamento estiver bloqueado (APK não compilada/assinada), explicar o estado e **não escrever uma mensagem a apresentá-la como disponível**.

## O que cada entrega deve incluir

1. **Versão exata** e, se fizer sentido, data da atualização.
2. **O que mudou**: novas funcionalidades e erros corrigidos, em linguagem simples.
3. **Como testar**: passos curtos para confirmar a principal alteração.
4. **Instalação**: atualizar por cima da versão anterior, sem desinstalar, para preservar os dados (desde que a assinatura e o package ID tenham sido verificados).
5. **Limitações conhecidas**: distinguir o que compilou do que foi efetivamente testado num telemóvel.
6. **Download**: ligação ao APK assinado e ao ZIP apenas quando os ficheiros exatos tiverem sido gerados e confirmados no ambiente atual.

Tom: português de Portugal, claro, objetivo, simpático. Formato: mensagem curta pronta para WhatsApp, email ou grupo de testers. Evitar termos técnicos que os testers não precisam de conhecer.

Não declarar uma correção como validada no telemóvel apenas porque o código compilou. Não prometer que uma funcionalidade funciona sem testes reais. Nunca sugerir desinstalar a aplicação para instalar uma atualização normal.

## Mensagem de exemplo — v1.9.39

**📱 SaúdePrática — Versão 1.9.39**

**Novidade:** a fotografia da caixa de medicamentos passa a usar uma câmara integrada na SaúdePrática, em vez da câmara externa do telemóvel. Foi concebida para corrigir o problema de fotografar, carregar no visto e não surgir nenhuma pergunta.

**Como testar:** Medicação → Adicionar → Fotografar caixa. Fotografar uma embalagem e confirmar se aparece a opção de analisar com ML Kit, guardar a imagem sem análise ou repetir a fotografia.

**Instalação:** atualizar por cima da versão anterior, sem desinstalar, para manter os dados.

**Nota:** esta versão compilou e foi assinada, mas a nova câmara ainda precisa de ser validada nos Xiaomi dos testers.

📎 **APK:** anexar o ficheiro do lançamento correspondente.

## Regra obrigatória de Ajuda atualizada

Em **todas as novas versões** que acrescentem, retirem, alterem, movam ou renomeiem módulos e funcionalidades, atualizar também **Mais → Ajuda** (guia ilustrado e instruções relevantes), em todos os idiomas suportados. Confirmar que não ficam nomes de módulos ou caminhos antigos. Este requisito deve ser verificado juntamente com a compilação e referido no texto de atualização entregue com a APK.
