# SaúdePrática Windows 0.8.9 — Hidratação, Atividade e Saúde, Ciclo Menstrual

Versão Windows 10/11 x64 experimental, baseada na 0.8.8, seguindo os números vermelhos 3, 4 e 5 do menu inicial.

## 3. Hidratação — funcional
- Registo manual de água por copo ou volume em ml, com hora e data, remoção individual e histórico diário.
- Objetivo diário **opcional** (0 = sem objetivo) e volume de copo configurável.
- Evolução dos últimos sete dias e progresso visual face ao objetivo escolhido pelo utilizador.
- Horários inicial/final e intervalo de avisos guardados para futura compatibilidade com o Android. **O Windows não emite alarmes de água nesta versão.**
- Não recomenda volumes de hidratação nem infere que a água foi bebida.

## 4. Atividade e Saúde — funcional em modo manual
- Registo diário por perfil: passos, distância, energia ativa, sono, ritmo cardíaco médio, peso e tensão arterial; notas opcionais.
- Editar ou apagar o registo de cada dia; histórico e evolução dos passos nos últimos sete dias.
- Valores não recolhidos são mostrados como "sem registo", nunca como zero ou medidos automaticamente.
- **Não lê diretamente Health Connect, relógios ou telemóveis** nesta versão Windows. O módulo Android continua a disponibilizar Health Connect conforme as permissões autorizadas; a sincronização de medições ainda não está desenvolvida.
- Não interpreta medições para fazer diagnósticos.

## 5. Ciclo Menstrual — funcional com registos manuais
- Calendário mensal, períodos com datas de início e fim, notas e histórico removível.
- Duração de ciclo escolhida entre 21–45 dias; estimativa do próximo início do período baseada no último início guardado.
- Esquemas de pílula opcionais: desligado, diário, 21+7 ou 24+4, hora e data de início configuráveis.
- Registo explícito "Tomei", com confirmação pelo utilizador, e possibilidade de anular uma confirmação anterior; nunca confirma automaticamente nem confirma datas futuras.
- **A estimativa do ciclo não prevê fertilidade, ovulação ou gravidez e não serve de método contracetivo.** O Windows ainda não emite alarmes da pílula.

## Dados e compatibilidade
- Os novos dados ficam dentro de cada perfil, protegidos pelo armazenamento Windows DPAPI, e entram no mesmo backup `.spbackup` da SaúdePrática.
- Não modifica os dados anteriores de medicação, agenda, consultas, documentos, tomas, Situação Clínica ou Despesas.
- A mudança de perfil repõe a seleção das datas e mostra apenas os dados daquele perfil.
- A versão Android oficial permanece inalterada. **Ainda não existe sincronização automática** de água, dados Health Connect, ciclo ou pílula entre Windows e Android.
- Os testes automáticos usam apenas perfis e medições sintéticos; nenhum dado pessoal é enviado ao GitHub.

## Próximos módulos segundo a numeração
6. Nutrição
7. Saúde Visual
8. Sintomas
9. Vacinas
10. Emergência
11. Farmácias
12. Lares e Apoios

**Instalação:** realizar um backup `.spbackup` e instalar por cima da 0.8.8, sem remover os dados locais. Instalador experimental ainda sem assinatura digital.
