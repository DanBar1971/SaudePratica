# SaúdePrática v1.9.122 — Correção do tema Claro e Escuro em toda a interface Android

## Correções

- **Fichas de Medicação, Perfis e Agenda:** corrigida a causa de texto ilegível em tema Claro. A janela de edição em ecrã inteiro tinha um **fundo escuro fixo** que não respeitava o tema escolhido. O fundo usa agora o tema guardado, sem mudar quaisquer dados ou alarmes.
- **Campos dos formulários:** cor de fundo, texto, dicas e contornos coordenados com o tema Claro/Escuro, incluindo no editor de medicação Eliquis mostrado na captura.
- **Tema aplicado à aplicação:** configuração de Claro, Escuro ou Automático aplicada desde o início do processo Android para que os módulos secundários não herdem um tema incorreto do sistema.
- **Ajuda Inteligente:** removida a apresentação permanentemente escura; agora tem paletas legíveis para os dois temas.
- **Ajuda e Contacto:** texto, cartões e fundo passam a respeitar o tema escolhido.
- **Dicas e Informações:** cabeçalho e cartões deixam de usar exclusivamente o estilo claro sobre fundo escuro.
- **Calendário/Ciclo:** a apresentação segue a preferência da SaúdePrática em vez do modo do telemóvel.

## Auditoria

Foram inspecionados os 85 ficheiros Kotlin do APK recompilado da v1.9.121 para procurar ecrãs com cores fixas e preferências de tema inconsistentes. A versão v1.9.122 corrige os componentes comuns e os ecrãs com discrepâncias concretas identificadas. A análise estática e a compilação não demonstram, por si só, que cada estado visual foi testado em telemóvel.

## O que verificar no telemóvel

1. Opções → Aspeto e idioma → Claro; abrir ficha de Medicação da Regina, sobretudo Eliquis (nome, dose, posologia, hora, checkbox, suspensão, Cancelar/Guardar).
2. Editar e criar Medicação, Perfil, Consulta e outros formulários de ecrã inteiro. Verificar títulos, dicas, cores e teclado, sem guardar alterações involuntárias.
3. Abrir Ajuda Inteligente, Ajuda, Dicas e Informações, Calendário/Ciclo e outras áreas; tudo legível em Claro.
4. Mudar para Escuro e depois Automático, repetindo a comparação. Em Automático, confirmar ambos os modos do sistema Android.
5. Garantir que os alarmes em ecrã bloqueado, TOMEI, ADIAR, perfis e fotografias não sofreram regressões.

**Segurança:** não altera registos clínicos nem a lógica de alarme; preserva ID com.mediagenda.app.stable e exige a **assinatura original**. Instalar por cima da versão anterior; não desinstalar. O diário Diabetes continua local e fora do backup geral nesta fase.
