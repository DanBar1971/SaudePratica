# SaúdePrática Windows v0.7.8 — carregamento e fotografias da medicação

- A seta do seletor de perfis tornou-se mais visível.
- Enquanto o ecrã é reconstruído (incluindo mudança de perfil, abertura de medicação e fotografia), o Windows apresenta o cursor de espera.
- O catálogo e a ficha da medicação recuperam fotografias originais dos anexos encriptados do backup Android quando a miniatura estava em falta.
- Imagens encriptadas são lidas apenas do perfil associado à medicação, com cache separada por perfil.
- A ficha mostra informações clínicas complementares presentes no registo Android (prescrição, suspensão, repetições, etc.) em **consulta**, sem inventar valores nem substituir o original.
- Sem alterações à lógica de alarmes Android ou do agente de Avisos Windows.

**Nota:** nem todos os tipos de informação complementar têm edição Windows completa. A importação é conservadora e mantém o registo Android original. Confirma sempre os alertas efetivos no Android.

**Segurança:** testes de CI apenas com registos sintéticos. O instalador experimental não possui assinatura Authenticode.
