# Run in PowerShell; elevation is required for registry and WSL changes.
param(
    [Alias("d")][switch]$dryRun,
    [Alias("v")][switch]$verbose
)
$ErrorActionPreference = 'Stop'

function Invoke-CheckedNative {
    param([string]$Command, [string[]]$Arguments)
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Command failed with exit code $LASTEXITCODE"
    }
}

$regPath = 'HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem'
if ($dryRun) {
    Write-Host '[DRY RUN] Would ensure LongPathsEnabled; a reboot may be required.'
} else {
    $principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Rerun in an elevated PowerShell session.'
    }
    $flag = (Get-ItemProperty $regPath -Name LongPathsEnabled -ErrorAction SilentlyContinue).LongPathsEnabled
    if ($flag -ne 1) {
        $answer = Read-Host 'Enable long paths? Reboot and rerun setup afterward. [y/N]'
        if ($answer -notmatch '^[Yy]$') { throw 'Long-path configuration declined.' }
        New-ItemProperty -Path $regPath -Name LongPathsEnabled -PropertyType DWord -Value 1 -Force | Out-Null
        Write-Host 'Long paths enabled. Reboot manually and rerun setup. No automatic restart.'
        exit 0
    }
}
# The registry flag is configuration, not proof that every application supports long paths.
$packagesFile = Join-Path $PSScriptRoot 'winget_packages.txt'
$packages = Get-Content $packagesFile | ForEach-Object {
    ($_ -split '#', 2)[0].Trim()
} | Where-Object { $_ -ne '' }

if (-not $dryRun -and -not (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw 'winget is missing. Install/update App Installer before rerunning.'
}
foreach ($package in $packages) {
    if ($package -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$') {
        throw "Invalid package ID: $package"
    }
    $installArgs = @('install', '--id', $package, '--source', 'winget', '-e',
        '--accept-source-agreements', '--accept-package-agreements', '--disable-interactivity')
    if ($dryRun -or $verbose) { Write-Host "winget $($installArgs -join ' ')" }
    if (-not $dryRun) {
        Invoke-CheckedNative -Command 'winget' -Arguments $installArgs
    }
}

if ($dryRun) {
    Write-Host '[DRY RUN] Would install WSL if needed and set default version 2.'
} else {
    Invoke-CheckedNative -Command 'wsl' -Arguments @('--install', '--no-launch')
    Invoke-CheckedNative -Command 'wsl' -Arguments @('--set-default-version', '2')
    Write-Host 'WSL setup requested. A reboot may be required. Open Ubuntu and run its bootstrap next.'
}
Write-Host 'Setup complete.'
