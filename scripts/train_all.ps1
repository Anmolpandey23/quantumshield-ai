# Windows:  .\scripts\train_all.ps1            (synthetic)   or   .\scripts\train_all.ps1 cicids D:\datasets\CIC-IDS2017
param([string]$Src = "synthetic", [string]$Dir = "")
$ErrorActionPreference = "Stop"
Push-Location stage1_ai_threat_prediction
if ($Src -eq "cicids") { python -m stage1.train --data cicids --data-dir $Dir } else { python -m stage1.train --data synthetic }
Pop-Location
Push-Location stage3_self_healing; python -m stage3.train; python -m stage3.evaluate; Pop-Location
