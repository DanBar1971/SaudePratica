# SaúdePrática Android v1.9.121 — Correção visual e Atalhos

## Correções

- **Diabetes:** passa a seguir o mesmo ambiente gráfico de **Atividade e Saúde**: fundo oficial escuro com arte da app, cabeçalho com SaúdePrática e identificação do perfil, cartões escuros com contornos discretos, verde-água e botões arredondados. Em tema claro usa cores claras coerentes; respeita o modo de visualização escolhido.
- **Atalhos Importantes, no menu principal:** agora é um ecrã de consulta e abertura apenas. Um toque num cartão abre a aplicação instalada ou o website. Sem três pontos, botões para adicionar, editar, apagar ou ordenar.
- **Mais → Opções → Atalhos Importantes:** mantém o gestor de Apps e Websites com opções de adicionar, pesquisar aplicações instaladas, alterar, remover e mover atalhos; identificado com modo próprio.
- **Atalhos existentes:** preservados. Sem alteração de identificação do Android nem das preferências anteriores.
- **Barras de estado/navegação:** respeitam os espaços de segurança da câmara e barra de navegação, ao contrário da primeira versão do novo ecrã.

## Testes recomendados no telemóvel

1. Tema Escuro → Início → Diabetes: compara com Atividade e Saúde. Tema Claro e Automático também.
2. Início → Atalhos: abrir SNS 24 e IPO Lisboa; **não** mostrar edição nem botões `+`.
3. Mais → Opções → Atalhos Importantes: gerir apps/websites; as alterações aparecem no Início sem eliminar atalhos anteriores.
4. Abrir e fechar, rodar ecrã, verificar status bar, barra inferior e zonas de toque.
5. Confirmar que registos e histórico Diabetes da v1.9.120 continuam disponíveis e separados por perfil.
6. Confirmar alarmes, alarmes em ecrã bloqueado e outras funcionalidades sem regressões.

## Limitações

MVP Diabetes permanece offline, com dados locais **ainda fora do backup total e sincronização**. Não depende de medições por câmara e não calcula insulina. Não é substituto de sensor médico ou orientação profissional. A compilação e testes estáticos não substituem testes reais no aparelho. Preservar assinatura original e pacote `com.mediagenda.app.stable`.
