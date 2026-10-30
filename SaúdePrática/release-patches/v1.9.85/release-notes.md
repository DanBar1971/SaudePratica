# SaúdePrática v1.9.85 — Alarmes conjuntos e atualização direta

## Medicação e Tomas
- **Mais de um medicamento no mesmo perfil e horário:** um único alarme apresenta a lista de nomes e doses, sem mostrar as fotografias das caixas.
- **Um único medicamento no horário:** mantém o alarme existente, com nome, dose e imagem da embalagem.
- Ao premir **TOMEI**, abre a área **Tomas** do perfil a que pertence o alarme. Em alarmes conjuntos, cada medicamento conserva o seu próprio registo pendente até à confirmação individual; não se assinalam todos automaticamente.
- **ADIAR 10 MIN:** conserva o grupo e os medicamentos ainda por confirmar. Confirmar parcialmente não cancela o adiamento dos restantes.

## Atualizações dentro da aplicação
- Quando está disponível uma nova Release no GitHub, a SaúdePrática pode descarregar a APK dentro da app, sem abrir o navegador.
- O download é verificado pelo SHA-256 fornecido pelo GitHub e pelo certificado de assinatura igual ao da APK instalada.
- Depois, abre o instalador do Android. A autorização e a confirmação de instalação pelo utilizador continuam obrigatórias; não há instalações silenciosas.

## Instalação e verificação
Instalar por cima da versão anterior **sem desinstalar**, para manter os dados. Recomenda-se backup prévio. A APK conserva a assinatura original e as três imagens oficiais da SaúdePrática.

Sugestões de teste: criar dois medicamentos com o mesmo horário e perfil; verificar lista e confirmação separada em Tomas; adiar por 10 minutos e confirmar apenas um; testar um medicamento isolado com fotografia. Confirmar também a descarga direta quando surgir uma versão posterior.

Compilação, certificado e reconstrução binária da APK validados. O comportamento no telemóvel Android/HyperOS necessita ainda de teste em condições reais.