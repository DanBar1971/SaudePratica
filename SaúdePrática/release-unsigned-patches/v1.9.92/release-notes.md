# SaúdePrática v1.9.92 — Fase B: Medicação crítica

Atualização incremental sobre v1.9.91. Mesmo identificador Android e assinatura original.

## Melhorias
- Recuperação de alarmes agendados após reiniciar o telemóvel, atualizar a aplicação, alterar data/fuso horário ou recuperar a permissão de alarmes exatos.
- Recuperação dos adiamentos de 10 minutos com referência à data/hora original da toma. Um adiamento não significa medicação tomada.
- Os grupos de medicamentos da mesma pessoa e da mesma hora preservam a identidade de cada medicamento quando a agenda é reconstruída.
- Quando expira um alarme agrupado, o evento ignorado é assinalado por cada medicamento ainda não confirmado, sem registar falsamente tomas efetuadas.
- Os registos de tomas continuam individuais por **perfil + medicamento + horário original**.
- Botões de grupo encaminham para **TOMAS** do perfil associado ao alarme, para confirmar medicamentos um a um.
- Foi mantido o alarme individual com nome, dose e fotografia da embalagem.
- Tratamento de falhas de autorização de alarmes exatos sem deixar cair o agendamento silenciosamente.
- Compatível com as medidas de proteção de perfis da Fase A (v1.9.91).

## Recursos visuais e compatibilidade
As três imagens oficiais **saude_icon.png**, **saude_splash.png** e **saude_background.png** foram preservadas e verificadas. Package `com.mediagenda.app.stable` e certificado de assinatura original.

## Nota importante
Esta versão foi compilada e verificada automaticamente. É necessário verificar num telemóvel real, especialmente Xiaomi/HyperOS, as permissões de ecrã completo e alarmes exatos. Nenhum Android permite contornar arbitrariamente essas permissões. Antes de sincronizar vários dispositivos, faça backup dos dados clínicos.
