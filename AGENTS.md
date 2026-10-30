# SaúdePrática — regras de continuidade do desenvolvimento

Repositório oficial: https://github.com/DanBar1971/SaudePratica
Repositório antigo/arquivo: https://github.com/DanBar1971/AndroidAppDev

## Projeto único, várias plataformas
- Android: fonte atual em MediAgenda/ e compilação em .github/workflows/saudepratica-android.yml.
- Windows: versão experimental com instalador Inno Setup em windows/; releases `windows-vX.Y.Z-preview`; ainda sem sincronização bidirecional e sem assinatura digital Windows.
- iPhone: desenvolvimento futuro em ios/ (sem build iOS publicado).
- shared/: contratos de dados e APIs comuns (a estruturar à medida que novos clientes forem criados).
- website e cartazes públicos: raiz / info_saude.

## Obrigatório em qualquer alteração
1. Identificar o impacto por plataforma: Android, Windows, iOS, modelo/sincronização e website.
2. Atualizar o código de todas as plataformas já suportadas pela funcionalidade afetada.
3. Testar compilações e regressões em cada plataforma afetada. Não afirmar que uma versão Windows foi atualizada quando ainda não existe.
4. Registar no changelog o que mudou e o estado de cada plataforma; não publicar uma versão simultânea sem binários válidos.
5. Preservar o identificador Android com.mediagenda.app.stable e a assinatura CERT_SHA256 já verificada. Nunca criar chave alternativa para atualização de utilizadores existentes.
6. Não alterar a lógica dos alarmes (ecrã bloqueado, agrupamento, TOMEI, ADIAR) sem testes específicos.
7. Publicar APK Android assinada no GitHub Releases. Para Windows, publicar `SaudePratica-Setup.exe` em release própria, não apenas como artifact. Nunca deixar uma release Windows substituir `releases/latest` Android. Atualizar sempre a página web Android/Windows/iOS e testar os dois downloads.
8. Nunca colocar segredos, dados clínicos pessoais ou keystores privados neste repositório público.

## Migração
- O código Android foi importado da versão v1.9.118 do repositório antigo.
- As releases históricas v1.9.76–v1.9.118 foram copiadas sem recompilar, com verificação de anexos.
- A versão Android de transição v1.9.119 passa a apontar para este repositório.
- Antes de publicar versões futuras aqui, configurar secret SAUDEPRACTICA_SIGNING_RECOVERY_HEX (mesmo certificado original), se ainda não estiver disponível.
- Manter a origem acessível até os utilizadores conseguirem atualizar para o canal novo.
