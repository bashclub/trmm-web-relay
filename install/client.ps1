# SPDX-License-Identifier: GPL-3.0-or-later
# TRMM Web-Relay: Client installieren oder aktualisieren (Windows).
#
# Installiert bei Bedarf uv (bringt ein passendes Python mit), dann den
# Client als eigenständiges Werkzeug und legt das Startsymbol an
# (Desktop und Startmenü). Danach: Doppelklick auf „TRMM Web-Relay“.
#
# Aufruf: powershell -ExecutionPolicy Bypass -File client.ps1
# Quelle: Ordner dieses Repos (Standard) oder $env:WR_SOURCE, z. B.
#   git+https://git.example.com/msp/trmm-web-relay
# Voraussetzungen: OpenSSH-Client (in Windows 10/11 enthalten) und Brave, Chrome oder Edge.

$ErrorActionPreference = "Stop"
$source = if ($env:WR_SOURCE) { $env:WR_SOURCE } else { (Resolve-Path "$PSScriptRoot\..").Path }

if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
    throw "OpenSSH-Client fehlt: Einstellungen > System > Optionale Features > OpenSSH-Client"
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "==> uv installieren (https://astral.sh/uv)"
    powershell -ExecutionPolicy Bypass -NoProfile -Command "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}

Write-Host "==> TRMM Web-Relay installieren aus $source"
uv tool install --force "$source"
if ($LASTEXITCODE -ne 0) { throw "uv tool install fehlgeschlagen" }

$bin = Join-Path (uv tool dir --bin) "trmm-web-relay.exe"
Write-Host "==> Startsymbol anlegen"
& $bin desktop
Write-Host ""
Write-Host "Fertig. Start per Doppelklick auf „TRMM Web-Relay“ (Desktop bzw. Startmenü)."
