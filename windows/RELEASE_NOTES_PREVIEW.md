# SaúdePrática Desktop 0.6.0 — ambiente gráfico aprovado (experimental)

## Novidades da interface
- Fundo em ecrã inteiro em formato 16:9 a partir da imagem abstrata azul-petróleo aprovada, com o mesmo tema nos módulos, perfis, medicação e opções.
- **Corrigido o banner defeituoso «Olá»**: texto desenhado diretamente sobre o fundo, sem rectângulos indesejados nem imagem esticada por uma etiqueta.
- Menu principal em grelha compacta de 25 módulos, com ícones efetivamente coloridos renderizados como imagens (não emojis brancos do Windows/Tkinter).
- Cartões clicáveis com destaque quando o rato passa e pesquisa de módulos.
- Seletor de perfis renovado na barra superior, com fotografias reais circulares e menu que permite escolher o perfil ativo, visualizar o cuidador e abrir a gestão de perfis.
- Fotografias dos perfis também circulares na lista de perfis. Não são inventadas fotografias nem enviados dados clínicos.
- Mantidas as cores e botões compactos; temas claro e escuro preservados.
- Medicação continua em cartões com fotos reais e edição integrada no ecrã.

## Segurança e limitações
- Instalar por cima da 0.5.0, sem desinstalar. Dados locais e backups .spbackup mantêm a encriptação DPAPI/AES e a compatibilidade de armazenamento.
- **A app Windows ainda não sincroniza com Android e não substitui alarmes no Android.**
- Módulos em desenvolvimento continuam marcados como tal. É uma versão visual experimental.

## Testes e instalador
- Verificações automáticas ao arranque da aplicação Python e do EXE PyInstaller Windows, com ecrãs e temas.
- Instalador Inno Setup Windows 10/11 (64 bits), release própria que não altera a APK Android.
