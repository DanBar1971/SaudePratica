# One-time setup. Run on a trusted PC with GitHub CLI authenticated.
# No private signing material is committed to GitHub.
param(
    [Parameter(Mandatory = $true)]
    [string]$FicheiroRecuperacao
)
$ErrorActionPreference = 'Stop'
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw 'GitHub CLI não encontrado. Instala-o em https://cli.github.com/ e faz gh auth login.'
}
if (-not (Test-Path -LiteralPath $FicheiroRecuperacao)) {
    throw 'Não encontrei o TXT privado com a chave de recuperação.'
}
$txt = Get-Content -LiteralPath $FicheiroRecuperacao -Raw
$matches = [regex]::Matches($txt, '(?m)^\s*([a-fA-F0-9]{64})\s*$')
if ($matches.Count -ne 1) { throw 'O TXT não contém uma única chave de recuperação de 64 caracteres.' }
$secret = $matches[0].Groups[1].Value
try {
    $secret | gh secret set SAUDEPRACTICA_SIGNING_RECOVERY_HEX --repo DanBar1971/AndroidAppDev
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao configurar o segredo no GitHub.' }
    Write-Host 'Segredo de assinatura instalado. Nunca o coloques no repositório.'
    Write-Host 'Abre GitHub → Actions → SaúdePrática Android Build → Run workflow (master).'
} finally {
    Remove-Variable secret -ErrorAction SilentlyContinue
}