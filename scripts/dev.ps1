$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Python = "C:\Users\thond\AppData\Local\Programs\Python\Python312\python.exe"
$NodeRoot = Get-ChildItem "C:\Users\thond\Documents\Codex\tools\node" -Directory |
  Where-Object { $_.Name -like "node-*-win-x64" } |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1

if (-not (Test-Path $Python)) {
  throw "Python was not found at $Python"
}

if (-not $NodeRoot) {
  throw "Node.js portable install was not found under C:\Users\thond\Documents\Codex\tools\node"
}

$env:Path = "$($NodeRoot.FullName);C:\Users\thond\Documents\Codex\tools\git\cmd;C:\Users\thond\Documents\Codex\tools\gh\bin;$env:Path"

Write-Host "Starting ShiftMemory backend and frontend..."
Write-Host "Backend:  http://127.0.0.1:8000"
Write-Host "Frontend: http://127.0.0.1:5173"

$Backend = Start-Process powershell.exe -PassThru -WindowStyle Normal -ArgumentList @(
  "-NoExit",
  "-Command",
  "cd '$Root\apps\backend'; .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
)

$Frontend = Start-Process powershell.exe -PassThru -WindowStyle Normal -ArgumentList @(
  "-NoExit",
  "-Command",
  "cd '$Root\apps\frontend'; npm run dev"
)

Write-Host "Backend PID:  $($Backend.Id)"
Write-Host "Frontend PID: $($Frontend.Id)"
