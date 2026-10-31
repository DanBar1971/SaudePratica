# SaúdePrática Desktop — Windows experimental

## O que existe nesta primeira base
- Janela inicial 1370×790, redimensionável, navegação horizontal compacta, menu de cartões de módulos inspirado no Android e galeria de medicação com fotografias autênticas.
- Interface escura/turquesa, inspirada na aplicação Android; usa os ficheiros
  oficiais disponíveis na raiz do repositório: assets/saude_background.png
  e assets/saude_icon.png. O splash original surge durante o arranque.
- Gestão completa dos campos do perfil, fotografia, cuidador, seleção permanente do perfil ativo e editor de medicação num único formulário. Aspeto escuro/claro/sistema e cinco idiomas na interface base.
- **Dados locais encriptados com Windows DPAPI, por utilizador Windows**.
- Backup com palavra-passe em ficheiro .spbackup (AES-256-GCM), importação
  validada e restauro conservador apenas de perfis novos.
- Código: windows/desktop_v04.py, windows/secure_store.py,
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

**Descarregar diretamente o instalador Windows:**

[**SaudePratica-Setup.exe — Windows 10/11 (64 bits), versão experimental 0.6.3**](https://github.com/DanBar1971/SaudePratica/releases/download/windows-v0.6.3-preview/SaudePratica-Setup.exe)

**Consultar a release Windows específica:**
https://github.com/DanBar1971/SaudePratica/releases/tag/windows-v0.6.3-preview

Não utilizar a página genérica de Releases como botão de instalação: ela mistura as versões Android e Windows. A página oficial https://danbar1971.github.io/SaudePratica/ apresenta um botão Windows que procura a release mais recente e conserva uma ligação direta funcional caso a API GitHub não esteja disponível.

Abrir `SaudePratica-Setup.exe`. O assistente permite instalar sem conta de administrador,
cria atalho no menu Iniciar, oferece atalho no Ambiente de Trabalho e inclui
desinstalador em Definições → Aplicações. O instalador é **experimental e não assinado
digitalmente**. Não desativar a proteção geral do Windows e não guardar dados
clínicos reais enquanto o programa não estiver validado.

## Construir no Windows 10/11 x64
Instalar Python 3.12 e, na raiz do repositório:

    python -m pip install -r windows/requirements.txt
    python -m unittest discover -s shared/tests -v
    python windows/desktop_v04.py

Criar executável experimental (mais rápido a iniciar e com ícone/splash oficiais):

    python windows/tools/build_brand_assets.py
    pyinstaller --noconfirm --clean --onedir --windowed --name SaudePraticaDesktop --icon dist/saude_icon.ico --splash dist/saude_splash_windows.png --paths . --collect-all customtkinter --add-data "assets;assets" --add-data "dist/saude_icon.ico;assets" windows/desktop_v04.py

O programa fica em dist/SaudePraticaDesktop/SaudePraticaDesktop.exe, acompanhado das suas bibliotecas. O instalador inclui toda a pasta. Não precisa de JDK/Android Studio.
O workflow GitHub Actions windows-build.yml executa os testes num runner
Windows e disponibiliza o EXE como artifact com retenção limitada.
O workflow cria também o instalador com Inno Setup 6 e publica a versão
`windows-v0.6.3-preview` em GitHub Releases. Ao atualizar o Windows, aumentar
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

## Diagnóstico e prevenção de falhas de arranque

O pipeline executa `python windows/tools/smoke_windows.py --script` e `python windows/tools/smoke_windows.py --exe`. O instalador só é publicado se a interface conseguir abrir e desenhar o primeiro ecrã. Os testes usam dados fictícios isolados, nunca dados clínicos do utilizador.

Caso haja falha, a aplicação fecha o splash e regista um relatório em `%LOCALAPPDATA%\\SaudePraticaDesktop\\startup_error.log` na conta Windows; não é necessário partilhar perfis nem cópias DPAPI para diagnóstico.

O splash `assets/saude_splash.png` agora aparece inteiro, sem qualquer recorte ou texto inventado, limitado proporcionalmente a 720 px de altura.

## Nova galeria de medicação v0.5

Cartões em grelha com foto da embalagem quando existe, nome, dose, horário e estado. A fotografia pode ser anexada na ficha de edição, ficando guardada na conta Windows com DPAPI e incluída no backup encriptado. Sem imagem, é mostrado apenas um símbolo de medicação, não uma embalagem inventada. Pesquisa e filtros são locais. O tema claro usa uma paleta explícita e é validado pelos testes.

Todos os módulos Android são apresentados na grelha, mas os que ainda não têm implementação Windows mostram **Em breve**.

## Novo fundo e perfis (v0.6)

A arte 16:9 aprovada é incorporada no pacote de instalação sem pedidos à internet. A grelha dos módulos é desenhada num canvas com ícones a cores e fundo próprio, evitando os blocos da 0.5. Nos outros módulos, o mesmo fundo aparece atrás dos formulários. O seletor de perfil na barra superior mostra fotografias reais (se existirem) em miniaturas redondas e permite trocar de perfil ou abrir a ficha. Não cria pessoas, fotos ou dados clínicos fictícios em produção.

## Correção gráfica 0.6.3

A imagem de fundo é gerada a partir do PNG original Android (`assets/saude_background.png`, 941×1672), em composição panorâmica com **proporção preservada**, em vez de ampliar um WebP minúsculo. Os ícones exibem os mesmos símbolos Android em 64 px com transparência verdadeira (sem quadrados artificiais); Windows Segoe UI Emoji assegura cores. Removidas as molduras exteriores redundantes no painel de Perfis e simplificada a ficha de Medicação.


## Importação e exportação manual Android ↔ Windows (v0.6.3 experimental)

1. Selecionar **perfil Windows de destino** no canto superior direito.
2. Abrir **Backup → Importar JSON / ZIP Android**.
3. Para um JSON do perfil: importar `medicacao.json` ou `agenda.json`. Os campos Android reais (`medication`, `activity`, `department`) são reconhecidos, e marcações com IDs Android repetidos distinguem-se pela identidade do evento.
4. Para ZIP familiar Android: selecionar `SaudePratica-backup-*.zip`, **selecionar explicitamente perfil Android de origem**, preparar e conferir pré-visualização de medicação, agenda e anexos, e confirmar. Repetir para os restantes perfis, sempre com o destino correto.
5. Fotografias e documentos importados são guardados cifrados por ficheiro com Windows DPAPI. Em **Documentos** pode importar manualmente PDF/fotografias, ver a lista e exportar um ficheiro escolhido para pasta Windows.
6. Em Importar/Exportar há exportação de Medicação ou Agenda JSON por perfil (não encriptada: exige confirmação). Em Backup, o `.spbackup` encriptado inclui também fotografias/documentos e é restaurável no Windows.

**Atenção:** antes de qualquer teste com dados reais, fazer um backup `.spbackup`. Os dados do Android não são alterados. Nunca transferir ZIP ou ficheiros com informação clínica para o repositório público. O restauro ZIP Android é aditivo e **por perfil**, não é uma sincronização automática nem substitui a gestão de alarmes Android. Campos de outros módulos e compatibilidade de restauro `.spbackup` diretamente no Android ainda estão em desenvolvimento. Não deixar exportações JSON sem proteção em pastas partilhadas.
