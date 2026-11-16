# Windows PowerShell, from the repo root:  .\scripts\dev_all.ps1
# Starts the backend in a new window, then the dashboard here. Close the backend window to stop it.
$ErrorActionPreference = "Stop"
if (-not (Test-Path frontend\.env)) { Copy-Item frontend\.env.example frontend\.env }
Start-Process powershell -ArgumentList "-NoExit","-Command","cd backend_dashboard; python -m uvicorn app.main:app --port 8000"
Set-Location frontend
if (-not (Test-Path node_modules)) { npm install }
Write-Host "Dashboard live mode needs VITE_USE_MOCK_DATA=false in frontend\.env"
npm run dev
