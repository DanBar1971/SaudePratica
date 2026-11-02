# SaúdePrática Windows 0.7.4 — ficha de perfil como no Android

- **Fim do ecrã interminável de diagnóstico:** os índices de documentos, registos de tomas e JSON do backup deixam de ser mostrados na ficha pessoal. A informação original continua protegida no arquivo cifrado, sem perdas.
- **Perfis rápidos:** entrar em Perfis apresenta imediatamente a lista e deixa de inspecionar o ZIP completo; os dados históricos são recuperados em segundo plano apenas quando se abre um perfil específico e depois ficam em cache durante a sessão.
- **Nome do pai e da mãe:** reconhece também os campos Android `father_name` e `mother_name`, que estavam a surgir em registos técnicos, mas não no formulário.
- **Cartão de Cidadão:** o editor inclui número e validade, apresenta a frente e o verso **apenas se existirem fotografias reais desse perfil** no backup Android, e permite ampliá-las ao clicar. Nenhuma imagem é criada artificialmente.
- **Desenho da ficha:** fotografia no topo, dados de identificação e saúde por secções, contactos e notas, com os mesmos campos essenciais que o Android; não lista documentação, medicação ou registos de atividade fora dos módulos apropriados.
- Preserva os backups `.spbackup`, fotografias, medicamentos, agendamentos e respetivos alarmes Android. Não substitui nem remove nenhum dado só por visitar uma ficha.
- Mantém a correção do instalador para encerrar o agente Windows de lembretes durante a atualização e voltar a iniciá-lo.
- O Windows continua em desenvolvimento; não existe sincronização automática bidirecional. Antes de experimentar o restauro Windows → Android, fazer backup e testar primeiro com dados de ensaio.

O instalador foi compilado e testado no GitHub Actions com testes sintéticos, sem utilizar dados pessoais reais. Pode instalar-se por cima da 0.7.3.
