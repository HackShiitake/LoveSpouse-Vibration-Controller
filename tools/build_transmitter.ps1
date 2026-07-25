<#
Builds the standalone BLE transmitter executable used by the Minecraft mod.

Output: dist/lovespouse-ble.exe  (a single, self-contained Windows executable
that needs no Python install). The mod launches this in --headless mode and
talks to it over the local HTTP API.

Usage:
    pip install pyinstaller winsdk
    ./tools/build_transmitter.ps1
#>
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    python -m PyInstaller `
        --noconfirm --clean --onefile `
        --name lovespouse-ble `
        --paths src `
        --collect-submodules winsdk `
        --exclude-module tkinter `
        --exclude-module _tkinter `
        main.py
    Write-Host "Built: $root\dist\lovespouse-ble.exe"
}
finally {
    Pop-Location
}
