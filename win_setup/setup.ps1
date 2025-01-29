# Set up params
param(
    [Alias("d")][switch]$dryRun,
    [Alias("v")][switch]$verbose
)

if ($dryRun) {
    Write-Host "Dry run mode. No operations will be performed." -ForegroundColor Red
}

Write-Host "Setting up Windows environment..." -ForegroundColor Yellow

# Step 1: Install packages
Write-Host "1. Installing Windows packages..." -ForegroundColor Yellow

# Read the package names, ignoring comments and empty lines
$packagesFile = ".\win_setup\winget_packages.txt"
$packageNames = Get-Content $packagesFile | Where-Object { 
    $_.Trim() -ne '' -and $_.Trim() -notmatch '^\s*#' 
}

foreach ($packageName in $packageNames) {
    Write-Host "  Installing" -NoNewline
    Write-Host " $packageName" -ForegroundColor Blue

    $wingetCommand = "winget install --id $packageName --source winget -e --accept-source-agreements --accept-package-agreements"

    # Print out the command being run in verbose mode
    if ($verbose) {
        Write-Host "    $wingetCommand" -ForegroundColor DarkGray
    } 

    if ($dryRun) {
        continue
    }

    # Run the command
    try {
        Invoke-Expression $wingetCommand
        Write-Host "  $packageName installation completed."
    } catch {
        Write-Host "  Failed to install $packageName. Skipping..."
    }
}

Write-Host "Packages installation complete!" -ForegroundColor Green

# Step 2: Enable WSL
Write-Host "Enabling WSL feature..." -ForegroundColor Yellow

wsl --install
wsl --set-default-version 2

Write-Host "WSL enabled!" -ForegroundColor Green