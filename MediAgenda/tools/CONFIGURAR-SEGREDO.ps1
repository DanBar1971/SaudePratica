# Configuração única da assinatura Android ORIGINAL no repositório principal.
# Executar num PC de confiança com GitHub CLI autenticado.
# O TXT privado de recuperação NUNCA é enviado para commits, issues ou logs.
param(
    [Parameter(Mandatory = $true)]
    [string]$FicheiroRecuperacao
)
$ErrorActionPreference = 'Stop'
$repo = 'DanBar1971/SaudePratica'
$secretName = 'SAUDEPRACTICA_SIGNING_RECOVERY_HEX'

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw 'GitHub CLI não encontrado. Instala https://cli.github.com/ e executa gh auth login.'
}
if (-not (Test-Path -LiteralPath $FicheiroRecuperacao -PathType Leaf)) {
    throw 'Não encontrei o TXT privado com o código de recuperação original.'
}

$txt = Get-Content -LiteralPath $FicheiroRecuperacao -Raw -Encoding UTF8
$matches = [regex]::Matches($txt, '(?m)^\s*([a-fA-F0-9]{64})\s*$')
if ($matches.Count -ne 1) {
    throw 'O TXT deve conter uma única linha com 64 caracteres hexadecimais do código original.'
}
$secret = $matches[0].Groups[1].Value
try {
    # Configura APENAS o repo principal, nunca o AndroidAppDev antigo.
    $secret | gh secret set $secretName --repo $repo
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao configurar o segredo no repositório atual.' }

    # A listagem contém só nomes e timestamps. NÃO lê nem revela o valor.
    $names = @(gh secret list --repo $repo --json name --jq '.[].name')
    if ($LASTEXITCODE -ne 0 -or $names -notcontains $secretName) {
        throw 'A configuração foi enviada mas não foi possível verificar o nome do segredo.'
    }
    Write-Host "Segredo de recuperação original configurado e nome verificado em $repo."
    Write-Host 'Não foi criada qualquer chave ou certificado novo.'
    Write-Host 'Agora testa Actions > SaudePratica Android Build + AutoRelease > Run workflow (main) numa versão ainda não lançada.'
}
finally {
    Remove-Variable secret,txt -ErrorAction SilentlyContinue
}
