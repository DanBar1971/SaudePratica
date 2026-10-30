# SaúdePrática Desktop — Windows experimental

## O que existe nesta primeira base
- Janela inicial 1280×720, formato 16:9, redimensionável (mínimo 940×620).
- Interface escura/turquesa, inspirada na aplicação Android; usa os ficheiros
  oficiais disponíveis na raiz do repositório: assets/saude_background.png
  e assets/saude_icon.png (o splash está reservado para a futura abertura).
- Criação/seleção de perfis e registo local básico de medicamentos e doses.
- **Dados locais encriptados com Windows DPAPI, por utilizador Windows**.
- Backup com palavra-passe em ficheiro .spbackup (AES-256-GCM), importação
  validada e restauro conservador apenas de perfis novos.
- Código: windows/desktop.py, windows/secure_store.py,
  shared/python/saude_backup.py.

## O que NÃO está disponível ainda
- Sincronização entre telemóvel e Windows.
- Importação direta das cópias Android / Nearby v2 para Windows.
- Restauro de todas as categorias e anexos, ou interoperabilidade Android↔Windows.
- Avisos e alarmes Windows; o Android continua a ser o alarme principal.
- Editor completo de prescrições, agenda, documentos, fotografias, PIN e idiomas.
- Instalador **assinado digitalmente**; a primeira versão tem instalador com
  assistente e desinstalador, mas ainda não tem certificado de editor Windows.

## Instalar no Windows 10/11 x64

Descarregar o instalador oficial da release Windows no GitHub: 
https://github.com/DanBar1971/SaudePratica/releases

Abrir `SaudePratica-Setup.exe`. O assistente permite instalar sem conta de administrador,
cria atalho no menu Iniciar, oferece atalho no Ambiente de Trabalho e inclui
desinstalador em Definições → Aplicações. O instalador é **experimental e não assinado
digitalmente**. Não desativar a proteção geral do Windows e não guardar dados
clínicos reais enquanto o programa não estiver validado.

## Construir no Windows 10/11 x64
Instalar Python 3.12 e, na raiz do repositório:

    python -m pip install -r windows/requirements.txt
    python -m unittest discover -s shared/tests -v
    python windows/desktop.py

Criar executável experimental:

    pyinstaller --noconfirm --clean --onefile --windowed --name SaudePraticaDesktop --paths . --add-data "assets;assets" windows/desktop.py

O ficheiro fica em dist/SaudePraticaDesktop.exe. Não precisa de JDK/Android Studio.
O workflow GitHub Actions windows-build.yml executa os testes num runner
Windows e disponibiliza o EXE como artifact com retenção limitada.
O workflow cria também o instalador com Inno Setup 6 e publica a versão
`windows-v0.1.0-preview` em GitHub Releases. Ao atualizar o Windows, aumentar
o `WINDOWS_APP_VERSION` no workflow e publicar uma nova release.
**Não confundir a versão Windows experimental com uma versão estável.**

## Segurança
- Não importar backups reais antes de testar o restauro entre Android/Windows.
- Não publicar ficheiros .spbackup, PDFs clínicos ou dados privados no GitHub.
- Não partilhar palavras-passe de encriptação em chats/issues ou releases.
- A chave de assinatura Android não serve para assinar um EXE Windows.
- A versão Windows utiliza as imagens oficiais do repositório; os PNGs
  originais maiores enviados pelo utilizador podem substituir estes assets
  sem necessidade de refazer a interface.
