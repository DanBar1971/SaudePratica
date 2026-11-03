# SaúdePrática Windows v0.8.3 — visual uniforme e editor de medicação

## Estilo aprovado aplicado
- Navegação superior, botões Guardar/Cancelar e botões de voltar ao menu agora partilham o mesmo estilo arredondado com borda e cores coerentes em modo claro/escuro.
- Os botões de voltar a Medicação, Agenda e Perfis seguem a mesma apresentação; módulos secundários apresentam **Voltar ao menu**.
- Os cartões de perfis, formulários da Agenda, Medicação, ecrãs de Backup/Restauro e as caixas de diálogo reutilizam os componentes gráficos comuns. Os separadores clínicos foram aumentados e têm maior destaque visual.
- A interface conserva o fundo original e os logótipos, sem alterar os dados de perfis.

## Medicação
- **Hora de aviso (HH:MM)** agora tem setas para aumentar/diminuir em intervalos de 5 minutos, com validação e passagem de 23:55 para 00:00. Continua editável por teclado.
- **Condição da toma** é uma combobox editável: opções jejum, refeições, ao deitar, etc., ou texto personalizado. Não volta a criar uma segunda hora.
- Na secção **Repetições**, Frequência, Número de repetições e Tipo de repetição passam a comboboxes editáveis. Os valores originais Android que não estejam na lista mantêm-se editáveis sem serem substituídos.
- **Fotografia da embalagem** aumentada, com pré-visualização usando exclusivamente a fotografia real do registo; botões Anexar/Remover dispostos ao lado.
- Mantém intactos dados de prescrição, anexos, suspensão, OCR local, alarmes e valores originais Android. A aplicação Windows continua sem agendar alarmes no telemóvel.

## Testes
- Validação do incremento de 5 min e mudança de dia, das opções editáveis, compatibilidade de campos Android e regressões anteriores.
- Ensaios do EXE Windows com uma fotografia sintética, edição real de um medicamento fictício, gravação de hora/condição, abertura da Agenda, Perfis, Documentos, Backup, Importação e mudança claro/escuro.
- Mantida proteção por perfil e backup `.spbackup`. Recomenda-se cópia antes da atualização.

Instalador experimental para Windows 10/11 x64, sem assinatura Authenticode. Verificar doses e horários na fonte Android; as alterações feitas no Windows não sincronizam automaticamente com o telemóvel.
