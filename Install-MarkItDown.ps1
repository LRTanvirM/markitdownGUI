<#
  MarkItDown installer — no third-party tooling required.
  Installs to %LOCALAPPDATA%\Programs\MarkItDown, adds Start Menu + Desktop
  shortcuts, and registers an entry in "Apps & features" (per-user, no admin).

    Install:    powershell -ExecutionPolicy Bypass -File Install-MarkItDown.ps1
    Uninstall:  ... Install-MarkItDown.ps1 -Uninstall
#>
param([switch]$Uninstall)
$ErrorActionPreference = 'Stop'

$Version    = '1.0'
$ExeName    = 'MarkItDownGUI.exe'
$InstallDir = Join-Path $env:LOCALAPPDATA 'Programs\MarkItDown'
$ExePath    = Join-Path $InstallDir $ExeName
$StartLnk   = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\MarkItDown.lnk'
$DeskLnk    = Join-Path ([Environment]::GetFolderPath('Desktop')) 'MarkItDown.lnk'
$RegKey     = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\MarkItDown'

function New-Shortcut($lnk, $target) {
    $ws = New-Object -ComObject WScript.Shell
    $s = $ws.CreateShortcut($lnk)
    $s.TargetPath = $target
    $s.WorkingDirectory = Split-Path $target
    $s.IconLocation = "$target,0"
    $s.Description = 'Convert files to Markdown'
    $s.Save()
}

if ($Uninstall) {
    Remove-Item $StartLnk, $DeskLnk -Force -ErrorAction SilentlyContinue
    Remove-Item $RegKey -Recurse -Force -ErrorAction SilentlyContinue
    if (Test-Path $InstallDir) { Remove-Item $InstallDir -Recurse -Force -ErrorAction SilentlyContinue }
    Write-Host 'MarkItDown uninstalled.'
    return
}

# Find the exe: next to this script, or in .\dist (running from the repo).
$src = @((Join-Path $PSScriptRoot $ExeName), (Join-Path $PSScriptRoot "dist\$ExeName")) |
    Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $src) { throw "Could not find $ExeName next to this script or in .\dist. Build it first (build.bat)." }

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Copy-Item $src $ExePath -Force
Copy-Item $PSCommandPath (Join-Path $InstallDir 'Install-MarkItDown.ps1') -Force  # so uninstall works later
New-Shortcut $StartLnk $ExePath
New-Shortcut $DeskLnk  $ExePath

$sizeKB = [int]((Get-Item $ExePath).Length / 1KB)
New-Item -Path $RegKey -Force | Out-Null
Set-ItemProperty $RegKey DisplayName     'MarkItDown'
Set-ItemProperty $RegKey DisplayVersion  $Version
Set-ItemProperty $RegKey Publisher       'MarkItDown GUI'
Set-ItemProperty $RegKey DisplayIcon     $ExePath
Set-ItemProperty $RegKey InstallLocation $InstallDir
Set-ItemProperty $RegKey EstimatedSize   $sizeKB -Type DWord
Set-ItemProperty $RegKey NoModify        1 -Type DWord
Set-ItemProperty $RegKey NoRepair        1 -Type DWord
Set-ItemProperty $RegKey UninstallString "powershell -ExecutionPolicy Bypass -File `"$InstallDir\Install-MarkItDown.ps1`" -Uninstall"

Write-Host "MarkItDown $Version installed to $InstallDir"
Write-Host 'Shortcuts added to the Start Menu and Desktop.'
