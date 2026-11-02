# SaúdePrática Windows v0.8.0 — ficha de medicação completa

### Medicação
- Substituídos os quatro blocos «Em desenvolvimento» por editores funcionais para **Prescrição**, **Repetições e posologia**, **Informação clínica** e **Bula**.
- Prescrição: data, profissional prescritor, referência da receita, início e fim e documento associado.
- Repetições: frequência, intervalo em horas, repetições, tipo, duração e posologia.
- Informação: princípio ativo, tipo de medicação, quantidade, stock, instruções, código de barras, período da suspensão.
- Bula: notas/referência e associação segura de PDF ou fotografia da bula. Documentos e imagens ficam protegidos localmente por DPAPI e associados exclusivamente ao perfil selecionado. O botão «Guardar cópia» permite abrir depois o documento exportado pelo utilizador.
- Mantidos o editor anterior (nome, dose, via, hora, tipo de toma, alarme, suspensão, notas e fotografia), a compatibilidade com antigos backups, as imagens existentes e o ficheiro original Android imutável.
- Valores Android complexos/estruturados continuam no registo original, sem serem substituídos por texto vazio. A app Windows não programa alarmes de medicação.

### Arranque e agente Avisos
- Removido o caminho de compatibilidade pelo qual o agente Avisos podia executar o EXE principal com outro splash.
- O instalador pára também o agente antigo do tipo `--reminder-agent` durante a atualização, além do agente autónomo atual.
- O executável autónomo SaúdePrática Avisos continua a ser compilado **sem splash**; apenas o EXE principal contém o splash oficial.

**Experimental:** guardar backup `.spbackup` antes da atualização. Os testes automatizados usam exclusivamente dados sintéticos e o instalador não está assinado digitalmente.
