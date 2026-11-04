# SaúdePrática Desktop — Windows experimental

## O que existe nesta primeira base
- Janela inicial 1370×790, redimensionável, navegação horizontal compacta, menu de cartões de módulos inspirado no Android e galeria de medicação com fotografias autênticas.
- Interface escura/turquesa, inspirada na aplicação Android; usa os ficheiros
  oficiais disponíveis na raiz do repositório: assets/saude_background.png
  e assets/saude_icon.png. O splash original aparece só no arranque da janela principal. O agente autónomo de Avisos não tem splash.
- Gestão completa dos campos do perfil, fotografia, cuidador, seleção permanente do perfil ativo e editor de medicação num único formulário. Aspeto escuro/claro/sistema e cinco idiomas na interface base.
- **Dados locais encriptados com Windows DPAPI, por utilizador Windows**.
- Backup com palavra-passe em ficheiro .spbackup (AES-256-GCM), importação
  validada e restauro conservador apenas de perfis novos.
- Código: windows/desktop_v04.py, windows/secure_store.py,
  shared/python/saude_backup.py.

## O que NÃO está disponível ainda
- Sincronização entre telemóvel e Windows.
- Sincronização automática em tempo real com o Android (o ZIP completo já pode ser importado manualmente).
- Edição Windows de todas as categorias Android; os dados ainda não suportados são preservados no ZIP original cifrado, sem integração visual.
- Sincronização automática de avisos Windows–Android; avisos locais da Agenda já disponíveis no Windows.
- Editor completo de prescrições, agenda, documentos, fotografias, PIN e idiomas.
- Instalador **assinado digitalmente**; a primeira versão tem instalador com
  assistente e desinstalador, mas ainda não tem certificado de editor Windows.

## Instalar no Windows 10/11 x64

**Descarregar diretamente o instalador Windows:**

[**SaudePratica-Setup.exe — Windows 10/11 (64 bits), versão experimental 0.8.19**](https://github.com/DanBar1971/SaudePratica/releases/download/windows-v0.8.19-preview/SaudePratica-Setup.exe)

**Consultar a release Windows específica:**
https://github.com/DanBar1971/SaudePratica/releases/tag/windows-v0.8.19-preview

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
O workflow de compilação cria o instalador com Inno Setup 6. A versão experimental
`windows-v0.8.0-preview` foi publicada com base no código testado no ramo
`release/windows-080-medication-complete-nosplash-20261102`, através do workflow
`publish-windows-075-approved.yml`. O código do `main` será integrado após validação.
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

## Importação familiar e exportação completa (Windows 0.6.6)

- Abrir **Backup → Importar toda a família Android**. Em Importar / Exportar escolher **Importar ZIP familiar completo** mesmo sem ter selecionado um perfil Windows.
- Depois da validação e da pré-visualização, clicar **Confirmar importação familiar**: cria os perfis em falta, acrescenta medicação, agenda e anexos por pessoa sem substituir registos existentes.
- O programa guarda uma **cópia original integral do ZIP Android**, protegida com DPAPI na conta Windows. Os dados que ainda não têm módulo Windows ficam conservados nesse ZIP.
- **Backup → Exportar** cria um único ficheiro `.spbackup` **encriptado com palavra-passe** contendo perfis, medicação, agenda, documentos, fotografias, preferências e ZIPs Android completos importados. **Restaurar** recupera esses dados noutro Windows sem sobrescrever perfis existentes.
- **Reexportar ZIP Android original** recupera exatamente os mesmos bytes do ficheiro recebido. **Esse ZIP original não está encriptado pelo programa**; apenas o `.spbackup` é protegido por palavra-passe.
- Não existe ainda sincronização bidirecional ou restauro de `.spbackup` no Android. Alterações Windows não modificam o ZIP Android original.
- Fazer um backup e confirmar a associação dos perfis antes de trabalhar com dados clínicos reais.

## Perfis, Medicação e Agenda na 0.6.6

- Perfis antigos podem ser eliminados na lista após confirmação explícita. A operação preserva os outros perfis, impede a perda de anexos compartilhados e mantém os ZIP Android originais encriptados. Recomenda-se criar um backup .spbackup antes da eliminação.
- Os campos originais Android disponíveis em nomes snake_case/camelCase são recuperados para fichas Windows vazias; nenhum dado pessoal fictício é preenchido.
- Seletor de perfil no topo compacto e alinhado com a fotografia autêntica.
- Cartões de Medicação mostram as fotografias originais com preenchimento visual, sem deformação nem substituição de embalagens. Estados Ativa em verde e Suspensa em vermelho. Data da próxima toma prevista apenas quando existe regra real de calendário; Windows não cria alarmes.
- Agenda separa por data real os compromissos futuros (cartões quase brancos) dos anteriores (cartões discretos). Botões de importação JSON retirados da Medicação e Agenda: continuam apenas em Backup/Importar-Exportar.
- A construção e os testes automáticos usam dados sintéticos. Validar visualmente com backup encriptado antes de trabalhar com dados reais.

## Windows 0.6.8: Agenda e recuperação dos perfis

Agenda com cartões futuros sem composição de vidro por cima, evitando recortes. Na Medicação, guardar apenas a mudança de estado não exige criar uma hora nem um tipo de toma. Os perfis importados podem consultar dados adicionais do backup Android cifrado (incluindo documentos de identificação e fotos do CC presentes no arquivo) numa área de leitura. Não se criam valores ou fotografias fictícias. Para perfis sem ZIP original associado, importar o backup familiar no módulo Backup. Fazer um .spbackup antes de testar com dados reais.

## Versão 0.6.8 — Medicação

Cartões com fundo completo e altura automática; botão Sem alarme amarelo; novo filtro Sem definição, distinto de Sem alarme intencional. Preservação dos dados e do backup familiar.

## Windows 0.6.9 — Filtros da Agenda

A Agenda apresenta os quatro filtros funcionais no topo: **Todas | Pendentes | Realizadas | Canceladas**. São vistas dos dados importados; não alteram as marcações nem criam alarmes. O estado explícito Cancelada tem prioridade, o estado explícito Realizada é respeitado e os compromissos de data já passada são apresentados como realizados se não tiverem indicação de cancelamento, de acordo com o comportamento Android. Mostra também o número de marcações visíveis e totais.

## Windows 0.7.0 — Edição de Agenda e cancelamento

É possível abrir qualquer marcação, editar os seus campos em ecrã completo, alterar o estado entre Pendente, Realizada e Cancelada, guardar com preservação dos metadados originais Android, e adicionar novas marcações. Também são editáveis os campos adicionais presentes no registo, mantendo os respetivos tipos. Identificadores e payloads de proveniência são protegidos. Cancelar aqui é local e **não contacta o hospital**. Criar um backup cifrado antes de testar.

## Windows 0.7.1 — Avisos de Agenda

A ficha permite selecionar avisos **1 dia, 2 horas, 1 hora, 30 minutos antes e na hora da consulta**, usando os mesmos valores numéricos `reminders_minutes` do Android. Um processo auxiliar do Windows, iniciado automaticamente com a sessão, apresenta avisos locais mesmo com a janela principal fechada. É necessário que a conta esteja iniciada, o PC ligado/acordado e as notificações permitidas. Intervalos adicionais antigos continuam preservados. O Android continua com os avisos que já tinha configurados; **não existe sincronização automática** e modificar a configuração no Windows não a altera no telemóvel. Os alarmes da medicação continuam apenas no Android.

## Windows 0.8.0 — carregamento e medicação Android

O seletor de perfis apresenta uma seta mais visível. O cursor de espera surge enquanto os módulos carregam. Fotografias existentes como anexos encriptados do backup Android podem ser recuperadas nos cartões e fichas da medicação, respeitando sempre o perfil selecionado. Informação adicional de prescrição, repetição ou suspensão surge apenas para consulta quando foi recebida do Android; não são criados valores fictícios nem alarmes Windows. O instalador inclui o agente de Avisos sem splash.

## Windows 0.8.0 — seletor de perfis e arranque maximizado

Nos cartões de perfil, o minúsculo símbolo › foi substituído por «ABRIR ❯» e a coluna da lista foi alargada. Durante o carregamento assíncrono das fotografias Android surge uma barra de progresso indeterminada, mensagem de espera e cursor de carregamento até a leitura terminar. A janela principal fica inicialmente oculta durante o splash oficial, e é revelada maximizada quando o splash fecha. O agente Avisos mantém-se sem splash. A instalação é uma atualização sobre a versão anterior e preserva os dados Windows.

## Windows 0.8.0 — Medicação e Avisos

As secções anteriormente indicadas «Em desenvolvimento» foram substituídas por campos editáveis e persistentes: Prescrição, Repetições e posologia, Informação clínica e Bula. Os PDF e fotografias de bula e prescrição são associados a cada medicamento e protegidos por perfil; o original Android é mantido sem alterações. A app Windows continua a não agendar alarmes de medicação. O agente Avisos utiliza apenas o seu executável sem splash e o instalador encerra instâncias antigas em segundo plano.

## Windows 0.8.1 — formulários compactos com OCR local

A Medicação e a Agenda apresentam um formulário à esquerda com separadores compactos e um painel de documento à direita. PDF digital: extração de texto local; PDF digitalizado e fotografia: RapidOCR com modelos ONNX incluídos no EXE. Os documentos são encriptados localmente por perfil; o preenchimento sugerido só atua em campos vazios e após aprovação. Na Agenda, campos técnicos de importação Android como `photo_uri`, `ocr_text` e `recurrence` deixaram de aparecer no formulário. O registo Android original é preservado e não existe sincronização automática. O instalador está publicado em `windows-v0.8.1-preview` com origem no ramo `release/windows-081-dualpane-ocr-20261103`.

## Windows 0.8.2 — hora única do aviso de medicação

A ficha da medicação usa **Hora de aviso (HH:MM)** como única entrada de horas e passa a mostrar **Condição da toma** (jejum, ao almoço, etc.) separadamente. A hora gravada é a mesma mostrada no cartão e na previsão da próxima toma. Quando uma edição antiga deixou horas contraditórias (como aviso 07:00 e hora auxiliar 08:00), a ficha oferece **Usar hora anterior 08:00**, uma escolha explícita. Os campos Android originais permanecem preservados e as alterações Windows **não alteram os alarmes reais Android** sem sincronização.

Instalador: https://github.com/DanBar1971/SaudePratica/releases/download/windows-v0.8.19-preview/SaudePratica-Setup.exe

## Windows 0.8.3 — interface gráfica uniforme

O aspeto dos botões, separadores, navegação, campos e botões de voltar foi harmonizado com o desenho aprovado para a Medicação. A ficha da Medicação mantém o campo único de hora de aviso e acrescenta setas de 5 minutos, condições de toma editáveis com sugestões, dropdowns nas repetições e uma pré-visualização maior da fotografia real do medicamento. A Agenda usa os mesmos separadores, campos e botões; Perfis, Backup, Documentos e módulos secundários partilham o mesmo estilo de navegação, com «Voltar ao menu» quando aplicável. Mantêm-se os documentos e OCR locais e as salvaguardas dos dados Android. Alterações Windows não sincronizam os alarmes reais Android. Instalar por cima da versão anterior após criar backup `.spbackup`.

## Windows 0.8.4 — descoberta e autorização do Android via Wi-Fi

O Windows procura automaticamente a aplicação auxiliar Android pela rede Wi-Fi local, usando mDNS/DNS-SD. Quando encontra um telemóvel, sugere abrir «Mais módulos → Sincronização» e pedir ligação. O Android tem de mostrar o mesmo código de seis dígitos e o utilizador toca Autorizar ou Recusar. Para redes que bloqueiam o mDNS, existe introdução manual do IP e porta exibidos no Android.

O teste necessita da APK independente [SaúdePrática Ligação (Teste)](https://github.com/DanBar1971/SaudePratica/releases/download/android-lan-link-v0.1-preview/SaudePratica-Ligacao-Teste.apk), pacote `pt.saudepratica.linktest`. Esta app de ensaio não substitui a SaúdePrática Android oficial e não lê ou transfere qualquer dado clínico. O canal de teste não é encriptado, portanto **não está autorizado a transportar dados de saúde**. A futura sincronização real exigirá TLS/autenticação mútua, backup, diff de registos e resolução de conflitos antes de qualquer aplicação.

No fim do teste, desliga a aplicação auxiliar no Android; não abrir portas no router. Para atualizar o Windows, efetuar backup `.spbackup` antes de instalar por cima.

## Windows 0.8.5 — Tomas e Calendário

Os novos módulos mostram dados exclusivamente do perfil ativo. Calendário oferece uma grelha mensal com número de agendamentos por dia e uma lista cronológica de consultas/marcações abaixo; é possível abrir a respetiva ficha. Tomas apresenta histórico diário, horários previstos apenas quando existe uma regra real, filtros e registo de toma confirmado manualmente, sem fabricar doses tomadas ou omitidas. Os registos Windows são encriptados e seguem no backup .spbackup. Não existem alarmes de medicação Windows nem sincronização automática do histórico Android. A release independente 0.8.5 foi compilada e validada com smoke tests reais do EXE e dados fictícios.

## Windows 0.8.6 — Calendário mais visual

Agora o Calendário mostra células mensais mais altas com dias de marcações coloridos, o número de consultas, o título real da primeira marcação, hoje assinalado por contorno e dia selecionado em turquesa. Por baixo, uma lista cronológica apresenta hora, título, local, estado e entrada direta para a ficha. A vista usa exclusivamente os agendamentos do perfil selecionado e adapta cores ao tema claro/escuro. Os novos desenhos foram verificados no Windows com testes automáticos e arranque real do EXE. Mantêm-se as Tomas, o armazenamento DPAPI e os backups .spbackup existentes.

## Windows 0.8.7 — dois painéis e Opções reorganizadas

Calendário: esquerda com grelha mensal colorida compacta, direita com lista de consultas do dia e abertura da ficha; consulta sempre o perfil ativo. Documentos: lista à esquerda e visualizador PDF/JPG/PNG/WebP à direita, botão Abrir para ampliação, Imprimir com confirmação da impressora predefinida e Guardar como para exportação intencional. A pré-visualização e a impressão não criam ficheiros temporários clínicos em claro; a fila Windows pode manter cópias conforme o sistema. Dicas e Informações, Backup e Sincronização ficaram sob Opções; SNS 24 e IPO Lisboa tornaram-se links Web em Atalhos Importantes. O gestor em Opções permite criar, editar, remover e ordenar links com setas, guardados por Windows DPAPI e preservados no backup completo. A sincronização clínica Android ↔ Windows continua em desenvolvimento. Ver nota windows/RELEASE_NOTES_087.md no ramo da release.

## Windows 0.8.8 — Situação Clínica e Despesas de Saúde

A partir da ordem de prioridades numeradas no ecrã principal, os pontos 1 (Situação Clínica) e 2 (Despesas de Saúde) são agora funcionais. Ambos gravam, editam e removem registos individuais por perfil e podem associar documentos já protegidos no mesmo perfil. Situação Clínica inclui acompanhamento e medicina do trabalho, unidade, profissional, estado e próxima avaliação. Despesas inclui faturas, categorias, valores em cêntimos, reembolsos, e-Fatura com estado manual, totais anuais e exportação CSV expressamente não cifrada. Os dados ficam protegidos pelo armazenamento Windows DPAPI e incluídos no backup .spbackup. A aplicação não gera diagnósticos nem garante elegibilidade fiscal. Os módulos clínicos e financeiros da app Android ainda não sincronizam automaticamente com os registos Windows. Próxima prioridade: 3 Hidratação, seguida das restantes da lista numerada.

## Windows 0.8.9 — Hidratação, Atividade e Saúde e Ciclo Menstrual

Seguindo a numeração de desenvolvimento no ecrã de módulos, os pontos 3, 4 e 5 estão agora funcionais. Hidratação permite registos por volume e data, objetivo diário opcional e gráfico semanal; os horários de avisos ficam guardados mas o Windows ainda não dispara alarmes de água. Atividade e Saúde permite introduzir manualmente passos, distância, calorias, sono, frequência cardíaca, peso e tensão arterial com histórico e gráfico semanal; não existe leitura automática do Health Connect do Android. Ciclo Menstrual inclui calendário, períodos, estimativa aproximada do próximo início, esquemas 21+7/24+4/diário e confirmação manual de pílula, mas sem alarmes no Windows e sem interpretação de fertilidade. Tudo fica associado ao perfil ativo no armazenamento DPAPI e integra o backup .spbackup. Continua pendente a sincronização automática dos três módulos com a app Android. Próximas prioridades: 6 Nutrição, 7 Saúde Visual, 8 Sintomas, 9 Vacinas, 10 Emergência, 11 Farmácias, 12 Lares e Apoios.

## Windows 0.8.10 — módulos 6 a 12

Nutrição com diário e fotografia protegida DPAPI; botão de importação idempotente das refeições e fotografias do **backup familiar Android original já guardado** e ligado ao perfil ativo, sem interpretar fotos por IA. Saúde Visual guarda graduação e receitas, Sintomas regista intensidade e evolução, Vacinas guarda doses e comprovativos, Emergência apresenta contactos e informações essenciais com abertura de marcador apenas após confirmação, Farmácias permite guardar favoritos e links externos sem prometer horários, e Lares e Apoios permite registar instituições, faturas, referências e apoios com estados manuais. Todos os dados ficam isolados por perfil e protegidos pelo backup .spbackup. Os serviços clínicos, fiscais, farmácias de serviço e elegibilidade para apoios não são verificados automaticamente. A sincronização bidirecional com os dados Android ainda está por implementar. Consultar RELEASE_NOTES_0810.md no ramo da versão Windows.

## Windows 0.8.11 — recuperar SOS e Lares do backup Android e Farmácias de Serviço

Abre o perfil pretendido e usa **«Recuperar SOS do backup Android»** em Emergência ou **«Recuperar instituição e faturas do Android»** em Lares e Apoios. A importação apenas consulta a origem Android associada a esse perfil, dentro do backup familiar original cifrado que já está no Windows. Preenche só campos SOS vazios e acrescenta instituições/faturas ainda inexistentes, sem substituir edições Windows. O nome e ID originais do documento Android são preservados, mas o botão de abrir a fatura pelo ID Android ainda não foi associado ao visualizador Documentos. Nutrição mantém importação explícita dos pratos/fotos reais Android. Farmácias oferece agora botões **«Encontrar perto de mim»** (site de proximidade que pode pedir permissão de localização no navegador) e **«Pesquisar por distrito/concelho»** (portal nacional). Sem GPS oculto, sem horários/turnos fictícios nem garantia de farmácia aberta. Consultar notas da release 0.8.11 no GitHub.

## Windows 0.8.12 — descobrir o telemóvel automaticamente com mDNS e UDP

Corrigido o botão **Procurar novamente**, que antes não iniciava uma nova pesquisa quando o watcher mDNS já estava ativo. O Windows agora reinicia a pesquisa mDNS e emite pedidos UDP broadcast limitados na rede local a partir das interfaces privadas disponíveis. O telemóvel responde à pesquisa apenas se a nova aplicação auxiliar de teste **Android 0.2** estiver visível, e o Windows verifica o serviço encontrado antes de mostrar o botão Pedir ligação. Existe repetição automática da pesquisa no ecrã de Sincronização enquanto não aparecem equipamentos. Ligação manual por IP preservada. Instalar APK auxiliar [0.2](https://github.com/DanBar1971/SaudePratica/releases/download/android-lan-link-v0.2-preview/SaudePratica-Ligacao-Teste.apk); este teste não envia dados clínicos e não substitui a SaúdePrática Android oficial. Se a antiga APK auxiliar de teste 0.1 tiver assinatura debug diferente, remover apenas essa auxiliar antes de instalar 0.2. Não abrir portas no router nem desativar firewall. Ver notas de versão `windows/RELEASE_NOTES_0812.md` do ramo Windows.

## Windows 0.8.13 — recuperar os dados reais do backup Android

Corrigido restauro de `.spbackup` com fontes Android preservadas mas módulos Windows vazios. O restauro completo preenche automaticamente Nutrição com refeições e fotografias originais, Hidratação com último total diário e objetivos, Sintomas e medições manuais, Tomas confirmadas com associação exata aos medicamentos, Emergência SOS e Lares/Apoios. A relação de cuidador e residente vem do próprio backup Android, sem misturar fichas: o cuidador pode entrar na ficha do residente associado. Novidade: em **Opções → Backup e Restauro**, botão **«Recuperar dados Android dos backups já guardados»** para instalações já restauradas. Faz primeiro cópia de segurança, importa apenas o que falta e mostra contagens. Atualização instalada por cima da versão anterior, sem alterar Android principal. Ver `windows/RELEASE_NOTES_0813.md` no ramo da release.

## Windows 0.8.14 — restauro automático e cuidador

Esta versão migra sem cliques os ZIPs Android já existentes em instalações Windows anteriores e incorpora os módulos na importação familiar; apresenta fotografias em miniatura na Nutrição e os valores de Lares/Apoios para residentes ligados ao cuidador. Preserva registos existentes, cria cópia de segurança DPAPI local e evita duplicações. Ver notas completas em [release Windows 0.8.14](https://github.com/DanBar1971/SaudePratica/releases/tag/windows-v0.8.19-preview).

## Windows 0.8.15 — dados Health Connect Android 1.9.134

A nova versão importa do ZIP original dentro do .spbackup familiar os registos Health Connect que a SaúdePrática Android 1.9.134 guardou localmente após atualizar Atividade e Saúde: passos, distância, energia, sono, pulso, sinais vitais e peso Health Connect. Também mostra o histórico de peso manual do Android, separado do Health Connect e das medições Windows. Os dados são associados estritamente ao perfil, os gráficos cobrem os últimos sete dias e as importações repetidas não criam duplicados. É necessário criar **novo backup Android depois de atualizar as medições**. O PC não tem ligação direta a sensores nem sincronização clínica automática. Ver [release Windows 0.8.15](https://github.com/DanBar1971/SaudePratica/releases/tag/windows-v0.8.19-preview).

## Windows 0.8.16

PIN de entrada com quatro números, escolha do perfil predefinido, criação de backups protegidos por PIN e compatibilidade com backups antigos. Atividade e Saúde destaca o último peso manual Android, a altura e o número de pesagens, mantendo o histórico separado de novas medições Windows. O backup familiar real de 04/11/2026 foi analisado localmente e contém oito pesagens válidas do perfil Daniel; nenhum dado privado foi publicado no GitHub.

## Windows 0.8.17 — ecrãs PIN com identidade visual SaúdePrática

A configuração inicial e a entrada com PIN de quatro números usam agora o wallpaper Android original adaptado ao Windows, o logótipo oficial, painéis e botões maiores e uma lista de perfis sem identificadores técnicos. O perfil predefinido continua a ser escolhido na primeira utilização. Em Backups, os campos de PIN de criação e restauro ficam maiores; novos .spbackup usam apenas PIN de quatro dígitos, e os ficheiros antigos são restaurados com a sua palavra-passe original. O teste de interface Windows verifica as duas páginas e o carregamento real da imagem de fundo. [Release 0.8.17](https://github.com/DanBar1971/SaudePratica/releases/tag/windows-v0.8.19-preview).

## Windows 0.8.18 — processos hospitalares por perfil

O módulo Situação Clínica permite consultar os ficheiros do processo hospitalar guardados no backup familiar Android 1.9.136 ou posterior: profissionais, contactos, taxas moderadoras Consultas/Exames/Análises, estado de pagamento, declarações de transporte e imagem de identificação. Cada ficheiro é lido do ZIP Android original validado e privado, associado ao perfil Windows selecionado. Este ecrã é **só de consulta**, não comunica com a app IPO Lisboa, não efetua pagamentos nem envia pedidos de transporte. A sincronização clínica automática por Wi-Fi continua pendente.


## Windows 0.8.19 — Hotfix do restauro com PIN numérico

Corrigido o restauro de backups familiares e por perfil protegidos por PIN de **4 dígitos**: o Windows deixou de exigir uma palavra-passe com dez caracteres na fase de criação da cópia de segurança automática. O novo backup de segurança permanece encriptado e os perfis atuais continuam preservados até à confirmação do restauro. A aplicação continua a aceitar backups antigos protegidos por palavra-passe e mantém a visualização hospitalar da 0.8.18. Instalação direta por cima da versão anterior. [Descarregar o instalador 0.8.19](https://github.com/DanBar1971/SaudePratica/releases/download/windows-v0.8.19-preview/SaudePratica-Setup.exe).
