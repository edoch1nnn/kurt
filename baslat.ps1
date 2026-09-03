$ErrorActionPreference = 'Stop'

Write-Host ''
Write-Host '=== KURT ===' -ForegroundColor Magenta
Write-Host 'tespit boslugu analizcisi' -ForegroundColor DarkMagenta
Write-Host ''

if (-not (Test-Path '.env')) {
    Copy-Item '.env.example' '.env'
    Write-Host '.env olusturuldu. varsayilan olarak yerel sqlite kullaniliyor.' -ForegroundColor Yellow
}

python -m pip install -r requirements.txt
python main.py
