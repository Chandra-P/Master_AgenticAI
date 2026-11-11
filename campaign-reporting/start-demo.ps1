$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$demoPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $demoPython)) {
    throw 'Project environment is missing. Follow README.md setup instructions.'
}
$env:DEMO_MODE = '1'
$env:ENABLE_OPENAI = '0'
$env:LANGSMITH_TRACING = 'false'
& $demoPython -m streamlit run ui/app.py --server.address=127.0.0.1 --server.port=8510 --server.headless=true --browser.gatherUsageStats=false
