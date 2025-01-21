# dotfiles
Dotfiles and scripts to set up my environment across different systems.

## Windows
Run the `setup.ps1` script as follows:
```
# Temporarily bypass the default execution policy which prevents running
# powershell scripts for the current powershell session.
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup.ps1
```

This script will install the packages in `win_packages.txt` (via [`winget`](https://learn.microsoft.com/en-us/windows/package-manager/winget/))
and set up WSL2 with the default distro (Ubuntu).

