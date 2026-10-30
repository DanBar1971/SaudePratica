# SaúdePrática — continuidade de “Alterações 1” (28/10/2026)

## Implementado e já publicado
- **v1.9.101:** cartões de medicação, faixa SUSPENSA, imagem alternativa sem caixa, bula PDF e Agenda compacta.
- **v1.9.102:** criação guiada de perfis, fotografia maior, pré-visualização do Cartão de Cidadão e transferência dos identificadores médicos para Situação Clínica.
- **v1.9.103:** galeria privada de fotografias de refeições e resumo de macronutrientes guardados.
- **v1.9.104:** correção do seletor de perfil e dos botões tapados pela barra de navegação Android.

## Código em revisão — v1.9.105, PR #53
- Situação Clínica: vários números de observação/processo, inclusive da mesma instituição, com ações individuais de adicionar, editar e eliminar.
- Preservar `observations_by_unit`, `observation_number` e `patientId` sem migração destrutiva ou mistura entre perfis.
- Apoiar o autor: café ☕ em vez de cerveja; manter link PayPal.
- Fundo original em Lares e Apoio + Calendário Mensal/Ciclo Menstrual.
- Guia Ajuda atualizado com gestão de números clínicos.
- **Não considerar publicado até existir APK assinada com certificado original e release verificada.**

## Questões ainda a verificar por testes Android reais
- Tradução integral dos módulos e botões em PT/EN/FR/DE/ES; entradas introduzidas pelas pessoas não são traduzidas automaticamente.
- Auditoria visual automática v1.9.105: o código sinalizou `DocumentOrientationActivity`, `HealthPermissionsRationaleActivity`, `MedicationBoxCameraActivity`, `ProfileWizardActivity`, `SmartHelpActivity`, `SplashActivity` e `SupportHelpActivity` sem referência direta a `saude_background`. **É preciso confirmar visualmente** os quatro ecrãs de perfil/ajuda/permissões: podem não ter o fundo. Os ecrãs de câmara, visualizador de documentos e splash devem manter a apresentação própria e não receber o fundo indiscriminadamente.
- Alarme em ecrã bloqueado, confirmação individual de vários medicamentos, adiamento, PIN e associação dos alarmes ao perfil correto.
- Atualização por download e abertura do instalador do Android em Xiaomi/HyperOS; testar sem desinstalar.
- Reconhecimento real de refeições, correção manual e conservação das fotografias.

## Regra de publicação e website
Depois de **cada** release, verificar o asset `SaudePratica.apk` em https://github.com/DanBar1971/AndroidAppDev/releases/latest e a página https://danbar1971.github.io/SaudePratica/ (repositório `DanBar1971/SaudePratica`).

O site deve apontar dinamicamente para a última APK **assinada** e, em caso de indisponibilidade da API, usar `releases/latest/download/SaudePratica.apk` sem mostrar uma versão antiga fixada.

Nunca publicar APK não assinada como atualização instalável.