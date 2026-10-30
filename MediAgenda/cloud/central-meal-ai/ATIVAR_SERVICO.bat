@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
title SaudePratica - Ativar servico central de IA
cd /d "%~dp0"

echo ============================================================
echo  SAUDEPRATICA - SERVICO CENTRAL DE ANALISE DE REFEICOES
echo ============================================================
echo.
echo Configuracao unica. Os utilizadores NAO precisam de API KEY.
echo.
where npm >nul 2>&1
if errorlevel 1 (
 echo [ERRO] Instala Node.js LTS em https://nodejs.org/
 goto :error
)

echo [1/4] Preparar ferramentas Cloudflare...
call npm install
if errorlevel 1 goto :error

rem Catch invalid wrangler.jsonc syntax early, before launching browser.
node -e "JSON.parse(require('fs').readFileSync('wrangler.jsonc','utf8')); console.log('Configuracao Wrangler: OK')"
if errorlevel 1 goto :error

echo.
echo [2/4] Verificar acesso Cloudflare...
call npx wrangler whoami >nul 2>&1
if not errorlevel 1 goto :authenticated

echo.
echo NAO feches esta janela durante a autorizacao.
echo Abre no browser: https://dash.cloudflare.com/oauth2/device
echo O Wrangler vai mostrar um CODIGO nesta janela.
echo Introduz o codigo no site e confirma a autorizacao.
echo Se o navegador nao abrir sozinho, utiliza o endereco acima.
echo Se o codigo expirar, podes executar o BAT novamente.
echo.
call npx wrangler login --device --browser=false
if errorlevel 1 goto :auth_error

:authenticated
echo.
echo Conta Cloudflare autorizada. A verificar...
call npx wrangler whoami
if errorlevel 1 goto :auth_error

echo.
echo [3/4] Publicar o servico central...
call npx wrangler deploy
if errorlevel 1 goto :error

echo.
echo [4/4] Configurar chave OpenAI no servidor...
echo A chave fica SOMENTE na Cloudflare. Nunca na APK ou no GitHub.
echo Cola a tua OPENAI_API_KEY quando o Wrangler a pedir.
call npx wrangler secret put OPENAI_API_KEY
if errorlevel 1 goto :error

echo.
echo ============================================================
echo PUBLICACAO CONCLUIDA.
echo Usa o endereco *.workers.dev indicado acima e confirma /health.
echo No GitHub, atualiza MediAgenda/cloud/meal-ai-config.json:
echo    enabled = true
echo    endpoint = https://TEU-WORKER.workers.dev/analyze
echo NUNCA coloques a OPENAI_API_KEY no ficheiro publico.
echo ============================================================
pause
exit /b 0

:auth_error
echo.
echo [ERRO] Falhou a autorizacao da Cloudflare.
echo Executa novamente o BAT e introduz o codigo do novo login.
goto :error

:error
echo.
echo [ERRO] O processo nao terminou. Le as mensagens acima.
echo A janela vai ficar aberta para veres o erro.
pause
exit /b 1