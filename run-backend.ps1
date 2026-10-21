$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\backend"
if (!(Test-Path ".env")) { Copy-Item ".env.example" ".env"; Write-Host "Created backend\.env. Edit DB credentials and ADMIN_PASSWORD, then run this script again."; exit 0 }
if (!(Test-Path ".venv")) { py -3.12 -m venv .venv }
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
& ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
