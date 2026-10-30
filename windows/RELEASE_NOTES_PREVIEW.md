# SaúdePrática Desktop 0.4.0 — Fase 1 (experimental)

## Interface redesenhada
- Navegação horizontal moderna em vez do antigo menu lateral.
- Ecrã inicial com cartões dos módulos, fundo e ícone oficiais.
- Botões e campos coerentes nos modos claro e escuro.
- Seletor permanente do perfil ativo no cabeçalho, guardado entre sessões.

## Perfis e medicação
- Ficha do perfil em ecrã principal: nome, nascimento, telemóvel, email, NISS, unidade de saúde, morada, localidade, código postal, contactos SOS, cuidador, notas e fotografia.
- Criar/editar perfis sem perder a medicação ou outras informações preexistentes.
- Editar medicação dentro da janela, mantendo nome, dose, via, tipo de injeção/toma, hora, indicação, notas, suspensão e ausência de alarme.
- Dados locais existentes de 0.1 a 0.3 mantêm-se no mesmo ficheiro DPAPI.

## Opções e backup
- Tema escuro, claro ou automático conforme o Windows.
- Idiomas: PT, EN, FR, DE, ES (interface base); a tradução clínica continuará a evoluir.
- Backups .spbackup protegidos por palavra-passe incluem todos os campos do perfil, inclusive fotografia, sem alterar a encriptação anterior.
- Restauro continua conservador e apenas adiciona perfis com IDs novos.

## O que falta
- A aplicação **ainda não é funcionalmente equivalente à Android**: Agenda, Documentos, Nutrição, Hidratação, Lares, integração e outras áreas são apresentados como módulos futuros.
- Ainda não sincroniza Android ↔ Windows. Não importa backups atuais Android.
- Não substitui os alarmes do telemóvel.
- Instalador Windows ainda não tem assinatura digital de editor.

**Instala por cima da 0.3.0, sem desinstalar.** Testar com dados fictícios.
