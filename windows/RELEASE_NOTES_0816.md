# SaúdePrática Windows 0.8.16 — PIN de entrada e backup numérico, peso manual Android visível

**Experimental Windows 10/11, 64 bits.** Atualização por cima da 0.8.15, sem apagar perfis ou documentos.

## Entrada com PIN e perfil predefinido
- No primeiro arranque: escolher o perfil predefinido (quando já existirem perfis), criar e confirmar um PIN de quatro números.
- Nos arranques seguintes: pedir o PIN antes de apresentar as fichas, entrar no perfil predefinido e continuar a permitir mudar de perfil no canto superior direito.
- Nas Opções: alterar o PIN (com PIN atual) ou escolher outro perfil predefinido.
- O verificador do PIN permanece cifrado no armazenamento local DPAPI; não é incluído nos backups portáteis. Há bloqueio temporário após tentativas incorretas.
- O PIN de entrada protege a interface, não substitui a segurança da conta Windows ou a encriptação do disco.

## Backups com quatro números
- Criar novos `.spbackup` protegidos com PIN de exatamente 4 algarismos. A interface usa dois campos de confirmação, sem teclados de palavras-passe.
- Nova estrutura cifrada AES-256-GCM, com chave derivada por PBKDF2-HMAC-SHA256 a 1 200 000 iterações e salt aleatório. Os dados continuam privados; não são publicados.
- A mesma estrutura está preparada para Android 1.9.135; essa atualização Android deve ser instalada antes de esperar novos backups PIN entre os dois sistemas.
- Os backups `.spbackup` antigos, com palavra-passe longa, **continuam a abrir**. O Windows reconhece automaticamente o formato e só pede a palavra-passe antiga quando necessário.
- Um PIN de quatro dígitos tem apenas 10 000 combinações; guarda o ficheiro em armazenamento privado e protegido, pois a derivação de chave não elimina o risco de ataques offline.

## Peso manual Android — confirmação com backup familiar real
- Foi analisado localmente o backup familiar entregue em 04/11/2026. Contém **8 pesagens manuais do perfil Daniel**, de 27/10 a 04/11, com última pesagem **104,2 kg** e altura **188 cm**.
- A estrutura `saudepratica_body_<id>` no ZIP Android original tem oito registos válidos, e a identidade corresponde à fonte do perfil. Não foi alterado o backup nem enviado ao GitHub.
- O ecrã Atividade e Saúde passa a destacar no painel direito o último peso, a altura e a quantidade de registos do Android. Os campos de edição no Windows permanecem vazios até introdução explícita para não criar medições duplicadas.
- O painel esquerdo mantém o histórico completo e passa a apresentar diagnóstico quando um backup de outro perfil não contém pesagens ou as medições são inválidas.
- Reprocessamento local idempotente dos ZIPs Android guardados; não sobrescreve medições anteriores.

## Nota
Os testes de CI são sintéticos. Não é necessário gerar outro backup para os oito pesos verificados. Faz uma cópia de segurança antes de atualizar e verifica o ecrã com os teus dados reais. A app não executa medições clínicas nem substitui recomendações médicas.