# SaúdePrática v1.9.113 — Cartaz fotográfico e botões integrados

- Substituído o cartaz vetorial por uma **imagem fotográfica vertical** com chávena de café sorridente, secretária e um telemóvel onde foi aplicada a captura verdadeira do ecrã inicial da SaúdePrática fornecida pelo autor.
- A imagem contém visualmente os dois botões **«Oferecer um cafezinho»** e **«OK»**.
- Os botões visuais agora têm **áreas Android clicáveis, acessíveis e sem duplicação no rodapé**; o primeiro abre Buy Me a Coffee externamente e o segundo fecha o popup.
- O JSON público tem `embedded_actions` e retângulos normalizados para permitir futuras imagens com botões embutidos.
- O histórico passa a utilizar os metadados mais recentes da imagem; o cache do antigo SVG é atualizado na primeira abertura com rede, sem apagar o histórico.
- Mantém-se a periodicidade configurável e a proteção de medicação, dados dos perfis, imagens oficiais, identidade Android `com.mediagenda.app.stable` e assinatura original.
- `versionCode=123` e `versionName=1.9.113`.
- Validar num telemóvel real a posição dos dois botões na imagem em diferentes resoluções e tamanhos de letra.