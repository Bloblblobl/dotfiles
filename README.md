# dotfiles
Dotfiles and scripts to set up my environment across different systems.

## Windows
Assuming you have cloned this repo already, run the `setup.ps1` script from
the root of the repo as follows:
```
# Temporarily bypass the default execution policy which prevents running
# powershell scripts for the current powershell session.
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\win_setup\setup.ps1
```

This script will install the packages in `winget_packages.txt` (via
[`winget`](https://learn.microsoft.com/en-us/windows/package-manager/winget/),
surprisingly!) and set up WSL2 with the default distro (Ubuntu). Once Ubuntu
is installed, open a WSL shell with `wsl` and follow the instructions below to
get the Ubuntu environment set up.

## Ubuntu
First, run the following commands to download the bootstrap script from this
repo and run it:
```
sudo apt update && sudo apt install -y curl
curl -O https://raw.githubusercontent.com/YOUR_GITHUB_USERNAME/YOUR_DOTFILES_REPO/main/bootstrap.sh
chmod +x bootstrap.sh
./bootstrap.sh
```

The bootstrap script will update/install `git` and `python3`, clone the repo
(you will be prompted for a
[PAT](https://github.com/settings/personal-access-tokens)), and execute the
`bootstrap.py` script. This script will symlink the `symlink_fs/` directory
maintaining relative paths, using `$HOME` as the root directory. After that,
it will execute each script in `scripts/` one by one.

-

(TODO): Scripts to setup zsh, oh-my-zsh, starship.rs