# SaúdePrática Windows 0.8.1 — fichas compactas e OCR local

## Medicação e Agenda
- Fichas divididas em **formulário à esquerda** e **pré-visualização de PDF/fotografia à direita**.
- Campos compactos, com separadores por grupo. Medicação: Principal, Prescrição, Repetições, Informação clínica e Bula. Agenda: Marcação, Contactos, Notas e avisos.
- Os botões **Anexar** estão ao lado do documento de Prescrição/Bula. Para a Agenda, **Anexar** está ao lado do título Documento da marcação.
- Os campos técnicos originais do Android (por exemplo `recurrence`, `photo_uri`, `ocr_text`, identificadores) não aparecem na ficha, mantendo-se preservados no registo original para compatibilidade.
- OCR local de PDF/imagem: PDF com texto digital usa PyMuPDF; imagens e PDFs digitalizados usam motor RapidOCR/ONNX incluído no instalador, sem enviar documentos para servidores.
- **Reconhecer texto** mostra o resultado editável no painel direito. **Preencher campos** pede confirmação e só insere sugestões em campos vazios; nunca grava automaticamente ou substitui medicação já preenchida.
- Anexos protegidos pela conta Windows via DPAPI, separados por perfil, para medicação e agendamento. Apenas formatos PDF/JPEG/PNG/WebP, até 16 MB.
- Os alarmes Android, os agendamentos e prescrições originais importados, e o agente independente «SaúdePrática Avisos» mantêm-se.

## Testes e cautelas
- Testes de reconhecimento de texto num PDF sintético, OCR de imagem sintética, parsing de data/hora, protecção de anexos por perfil e interface gráfica real no Windows.
- O OCR pode interpretar mal textos médicos, nomes, horários e doses. É obrigatória a confirmação pelo utilizador antes de guardar.
- Instalação experimental, sem assinatura digital. Guardar `.spbackup` antes da atualização.
