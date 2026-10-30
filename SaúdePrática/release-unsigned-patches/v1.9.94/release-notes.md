# SaúdePrática v1.9.94 — Fase D: Documentos Digitais e Agenda

Esta atualização mantém o APK Android original e o mesmo certificado de assinatura.

## O que muda
- **Importação universal PDF/IMG**: PDFs, JPEG, PNG, WEBP, HEIC e HEIF recebidos para OCR de medicação ou agenda passam a ser guardados como **originais** nos Documentos Digitais do perfil correto, antes de qualquer reconhecimento.
- Os ficheiros enviados ao módulo de **Análises Clínicas** e **Saúde Ocupacional** também são arquivados nos Documentos Digitais do respetivo perfil, incluindo **imagens**, não apenas PDFs.
- **Anti-duplicados SHA-256** por perfil e formato: importar duas vezes o mesmo PDF ou imagem não cria duas cópias, mesmo que o nome mude.
- **Partilhar vários documentos para a SaúdePrática**: PDF/imagens enviados em conjunto por outros programas Android; até 20 documentos por partilha, com seleção do perfil quando existem vários.
- Mantido o visualizador interno Android PdfRenderer, visualizador de imagens, OCR local ML Kit e opção de rotação sem modificar o PDF original.
- **Agenda/consulta**: escolha distrito, concelho ou GPS (com autorização), e agora **pesquisa local por nome** de hospital, USF ou localidade sem exigir Internet.
- Unidades introduzidas manualmente podem ficar memorizadas no catálogo local do telemóvel para utilizações futuras (sem associar dados clínicos ao catálogo).
- Inclui Hospital de Vila Franca de Xira, IPO Lisboa e as restantes unidades já registadas; quando não encontra uma unidade, mantém acesso ao **diretório nacional da ERS** e introdução manual.
- Mantidos alarmes, TOMAS, Nutrição Gemini, sincronização familiar e identidade dos perfis das Fases A/B/C.
- **Ícone, splash e background oficiais** preservados e validados dentro da APK.

## Fontes e licença
Não foi transplantado código do **meuse24/PDF_Scanner**: o projeto não apresenta uma licença explícita de reutilização. O código desta fase foi desenvolvido especificamente em Kotlin sobre componentes e bibliotecas Android já existentes na SaúdePrática (Storage Access Framework, PdfRenderer e ML Kit). O fluxo de agenda foi inspirado em abordagens do projeto Simple Android (MIT) sem copiar a sua base clínica.

## Limitações e testes
- O catálogo offline é uma lista inicial e não o registo nacional completo. A ligação oficial ERS pode exigir Internet.
- Os ficheiros originais são preservados em armazenamento privado da aplicação; como tal, não devem ser eliminados os dados da app durante uma atualização.
- Os limites atuais de tamanho (50 MB por documento) mantêm-se.
- Validar em telemóvel real Android/HyperOS: PDF de várias páginas, JPEG, HEIC, OCR, share múltiplo, pesquisa por município e instalação por cima da versão anterior.
- Antes de sincronizar dispositivos, recomenda-se um backup completo em ambos.

