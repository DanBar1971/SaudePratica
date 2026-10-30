# SaúdePrática v1.9.91 — Fase A: sincronização familiar segura

Atualização incremental da v1.9.90 (mesmo pacote e certificado Android original).

## Alterações
- Sincronização Nearby identifica cada perfil pelo par **dispositivo de origem + identificador original do perfil**, em vez de corresponder pelo nome.
- Preserva essa identidade no telemóvel recetor e nas transmissões seguintes para reduzir importações duplicadas.
- Duas pessoas com o mesmo nome permanecem perfis diferentes, sem misturar medicação, documentos e registos clínicos.
- Para fontes antigas, associa a identidade ao dispositivo emissor autenticado e ao respetivo ID.
- Continua a preservar dados e conflitos locais sem apagar nem unir automaticamente cópias antigas de perfis.
- Mantidos os alarmes, tomas, cuidador, agenda e restantes funcionalidades da v1.9.90.
- **Ícone, splash e background oficiais** restaurados e verificados na APK.

## Verificações
- Código reconstruído e compilado no GitHub Actions; verificações de identidade e branding passaram.
- APK assinada com o **certificado original**, pacote `com.mediagenda.app.stable`, versão `1.9.91`.
- Hashes SHA-256 da APK não assinada, patch e APK assinada validados antes de publicar.
- Continuam recomendados testes em dois telemóveis reais (Nearby bidirecional, perfis recebidos, alarme com ecrã bloqueado e HyperOS).

## Atenção
Não elimina perfis duplicados antigos nem funde dados médicos automaticamente. Antes de sincronizar, faça um backup em ambos os dispositivos.
