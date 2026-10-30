# SaúdePrática v1.9.87 — Corrigida a atualização direta no Android/HyperOS

## Correção principal
- Corrigida a falha **“Ocorreu um problema ao analisar o pacote”** ao atualizar através do botão **Atualizar agora**.
- Em vez de abrir uma APK através de um URI privado da SaúdePrática (FileProvider + ACTION_VIEW), a aplicação utiliza uma sessão oficial **Android PackageInstaller**, entregando os bytes da APK já descarregada e verificada diretamente ao instalador do sistema.
- Continua a comparar a soma **SHA-256** da Release pública e o certificado Android da APK com a aplicação instalada, recusando ficheiros adulterados ou com assinatura diferente.
- A instalação continua a exigir **confirmação explícita do utilizador** e, quando aplicável, autorização para instalar desta fonte. Não há atualização silenciosa.
- Se o Android recusar a sessão, apresenta um erro e uma opção de abrir o GitHub para instalação manual.

## Compatibilidade
- Mantidos dados, perfis, medicação, tomas, fotografias, sincronização, Nutrição, alarmes individuais/grupais, ecrã de bloqueio e outros módulos da v1.9.86.
- APK assinada com o mesmo certificado da v1.9.86. **Não desinstalar** a versão anterior; instalar por cima para preservar os dados.

## Importante para quem tem a v1.9.85 ou v1.9.86
O atualizador existente nessas versões pode falhar. **Esta v1.9.87 deve ser instalada uma vez manualmente** a partir da APK desta Release. Depois disso, o novo método será utilizado ao procurar versões futuras.

O fluxo de compilação, assinatura (v2/v3), comparação de certificado e reconstrução binária foram validados. O comportamento do instalador no dispositivo Xiaomi/HyperOS ainda deve ser confirmado numa atualização posterior.
