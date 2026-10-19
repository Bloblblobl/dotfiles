# dotfiles

Personal configuration and setup scripts for Windows and Ubuntu/WSL. macOS is
not yet supported.

## Layout

- `ubuntu_setup/symlink_fs/` mirrors paths under `$HOME` (Bash, Git,
  Starship, and the Pi maintenance skill).
- `ubuntu_setup/` contains the Ubuntu bootstrap scripts.
- `win_setup/` contains Windows setup and the winget package list.

## Setup

The existing Ubuntu bootstrap overwrites home files; inspect it and reconcile
local configuration before running it. Windows setup is `win_setup/setup.ps1`.

## Maintenance

See the [Pi maintenance skill](ubuntu_setup/symlink_fs/.pi/agent/skills/dotfiles/SKILL.md)
for the change workflow and [decisions](DECISIONS.md) for lasting tradeoffs.
