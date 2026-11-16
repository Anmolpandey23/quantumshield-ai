# Windows PowerShell, from the repo root:  .\scripts\run_all_tests.ps1
$ErrorActionPreference = "Stop"
Write-Host "== integration"; python -m pytest -q
foreach ($d in "stage1_ai_threat_prediction","stage2_quantum_cryptography","stage3_self_healing","backend_dashboard") {
  Write-Host "== $d"; Push-Location $d; python -m pytest -q; Pop-Location
}
if (Test-Path frontend\node_modules) { Write-Host "== frontend"; Push-Location frontend; npm test --silent; Pop-Location } else { Write-Host "== frontend skipped (run: cd frontend; npm install)" }
Write-Host "ALL GREEN"
