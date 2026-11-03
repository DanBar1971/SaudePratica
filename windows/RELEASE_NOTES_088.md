# SaúdePrática Windows 0.8.8 — prioridades 1 e 2 concluídas

Pré-visualização Windows 10/11 x64. Versão de desenvolvimento a partir da 0.8.7, mantendo a app Android oficial intacta.

## 1. Situação Clínica
- Ficha para **registos manuais** de acompanhamento: título, data, tipo (Medicina do Trabalho, Consulta, Diagnóstico/Condição, Análises/Exames, Tratamento, Relatório e Outro), estado, profissional, unidade de saúde, próxima avaliação e notas.
- Listagem cronológica, edição e eliminação com confirmação.
- Seleção de documento já guardado no mesmo perfil; opção para consultar esse documento na área Documentos.
- Informação individual do perfil ativo, guardada localmente e protegida por Windows DPAPI.
- O módulo não emite diagnósticos, conselhos médicos nem valida automaticamente estados clínicos.

## 2. Despesas de Saúde
- Ficha para data, categoria, entidade, descrição, número de fatura, NIF, valor, reembolso, estado manual do e-Fatura e notas.
- Categorias e estados alinhados com o módulo Android, sem afirmar que já sincronizam.
- Cálculos em **cêntimos inteiros**, não em números de vírgula flutuante: total anual, reembolsado e valor por suportar.
- Lista por ano com setas para navegar, criar, editar e apagar registos.
- Possibilidade de associar um documento já guardado no mesmo perfil.
- Exportação CSV por ano, apenas com confirmação clara de que a cópia exportada não é cifrada e pode conter informação pessoal.
- Não determina elegibilidade fiscal; o estado do e-Fatura depende de confirmação manual do utilizador.

## Compatibilidade e segurança
- Os registos ficam em `profile["clinical_records"]` e `profile["health_expenses"]` dentro do armazenamento já cifrado (sem alterar o formato existente).
- O backup `.spbackup` da família/perfil inclui estes campos, preservando medicação, agenda, documentos, fotografias, tomas e dados Android originais.
- Mudar de perfil limpa a seleção dos novos módulos; uma tentativa de alterar registos do perfil errado é rejeitada também pela camada de persistência.
- A associação de documentos exige que o anexo pertença ao mesmo perfil.
- Não importa automaticamente o histórico de Situação Clínica ou de Despesas do Android. A compatibilidade e sincronização clínica entre as plataformas precisam de desenvolvimento e testes próprios.
- Nenhum registo real de utilizador é utilizado nos testes ou enviado para o GitHub.

## Próximas prioridades, mantendo a numeração do ecrã
3. Hidratação
4. Atividade e Saúde
5. Ciclo Menstrual
6. Nutrição
7. Saúde Visual
8. Sintomas
9. Vacinas
10. Emergência
11. Farmácias
12. Lares e Apoios

**Instalação:** efetuar um backup `.spbackup` e instalar sobre a versão anterior, sem desinstalar nem apagar os dados. O instalador é experimental e ainda não está assinado digitalmente.
