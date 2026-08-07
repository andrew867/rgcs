# RGCS Windows frozen build: PyInstaller via the existing desktop spec
# (tools/packaging/rgcs_desktop.spec — one spec, reused), then smoke
# check + SHA-256 checksums + release manifest.
$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
Set-Location $Root

if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    python -m venv .venv
}
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[desktop,packaging]"

pyinstaller tools\packaging\rgcs_desktop.spec --noconfirm `
    --distpath release\windows --workpath build\pyinstaller-windows

$exe = "release\windows\rgcs-workbench\rgcs-workbench.exe"
if (!(Test-Path $exe)) {
    throw "Missing $exe"
}

$env:QT_QPA_PLATFORM = "offscreen"
& $exe --smoke-check
if ($LASTEXITCODE -ne 0) {
    throw "Frozen smoke check failed ($LASTEXITCODE)"
}

Get-FileHash $exe -Algorithm SHA256 |
    Format-List |
    Out-File release\windows\rgcs-workbench\SHA256SUMS.txt

python tools\packaging\release_manifest.py `
    --platform windows `
    --build-command "tools/packaging/windows/build_windows.ps1" `
    --smoke-command "rgcs-workbench.exe --smoke-check" `
    --smoke-status passed `
    --artifact $exe `
    --out release\windows\release_manifest.json

Write-Host "Windows build complete: $exe"
