# SaúdePrática Android 1.9.133 — regresso à Ajuda tradicional

### O que muda
- Sai do Android o Assistente generativo com IA local leve (Qwen), Gemini Nano e IA Online privada.
- Volta o acesso direto à **Ajuda tradicional**, com respostas sobre funcionalidades da SaúdePrática.
- A versão 1.9.133 deixa de incluir o motor nativo Qwen, o download de 383 MB e a configuração de IA online do Assistente.
- Na primeira abertura após atualizar, remove automaticamente do armazenamento privado o modelo Qwen descarregado nas versões anteriores e as preferências exclusivas da IA Online do Assistente. **Não apaga dados clínicos, fotografias nem backups.**
- A funcionalidade de **Nutrição** e a sua configuração Gemini, quando usada, não são alteradas por esta atualização.

### Prioridade: sincronização
- Mantém a sincronização familiar Nearby entre telemóveis Android.
- Mantém «Backups e sincronização → Ligação Windows · Wi-Fi (teste)» na própria aplicação Android, compatível com o Windows 0.8.12 (descoberta mDNS/UDP, autorização de seis dígitos).
- **A ligação Windows ainda só emparelha os dispositivos; não sincroniza registos de saúde.** A transferência bidirecional encriptada entre Android e Windows continua pendente.
- Mantém backup/restauro familiar ou por perfil em formato `.spbackup`.

### Instalação
- Atualização normal 1.9.133, identificador `com.mediagenda.app.stable`, versionCode 143.
- Instala por cima da SaúdePrática existente, com o certificado original, **sem desinstalar** e após backup preventivo.
- Ao abrir a nova app, a limpeza do Qwen (~383 MB) é automática, assíncrona e limitada ao diretório `ia-local`.
- Testar a Ajuda, os alarmes, a sincronização Nearby, a descoberta Windows e a preservação das fichas num telemóvel real.
