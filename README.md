# dotfiles

Personal configuration and setup scripts for Windows and Ubuntu/WSL. macOS is
not yet supported.

## Layout

- `ubuntu_setup/symlink_fs/` mirrors paths under `$HOME` (Bash, Git, tmux,
  Starship, and the Pi maintenance skill).
- `ubuntu_setup/bootstrap.sh` and `bootstrap.py` install Ubuntu/WSL prerequisites
  and link the configuration.
- `win_setup/` contains Windows setup and the winget package list.

## Ubuntu / WSL

Download and inspect the bootstrap script before running it:

```sh
sudo apt-get update && sudo apt-get install -y curl
curl -fsSLo bootstrap.sh https://raw.githubusercontent.com/Bloblblobl/dotfiles/master/ubuntu_setup/bootstrap.sh
# Inspect bootstrap.sh, then run:
bash bootstrap.sh --dry-run
bash bootstrap.sh
```

The shell dry-run checks installed dependencies, directories, and repository
state without changing them. It reports pending or blocked steps and runs the
Python dry-run only when ready. Live mode installs prerequisites, clones the
public repository over HTTPS, and runs Python. GitHub authentication is optional.
To preview or resume Python independently from the clone (default: `~/git/dotfiles`):

```sh
cd ~/git/dotfiles
python3 ubuntu_setup/bootstrap.py --dry-run
python3 ubuntu_setup/bootstrap.py
```

Replace the `cd` path if you chose another clone destination. The Python stage
preserves existing regular files and directories: it refuses conflicting paths
rather than overwriting or backing them up. Fresh Ubuntu installations usually
have a `~/.bashrc` to reconcile manually before setup can finish. Existing
symlinks to other targets may be replaced.

The Python stage can offer GitHub CLI installation and interactive login. Decline
or use `--skip-github` to skip it. If no secure keyring is available, GitHub CLI
may store its token in plaintext.

### Local Git settings

The tracked `~/.gitconfig` includes `~/.gitconfig.local` for machine-specific
identity and credential helpers. Configure your identity in that untracked file:

```sh
git config --file ~/.gitconfig.local user.name 'Your Name'
git config --file ~/.gitconfig.local user.email 'you@example.com'
chmod 600 ~/.gitconfig.local
```

Do not run `gh auth setup-git` without checking its target: it may modify the
tracked `~/.gitconfig`. The bootstrap explicitly configures helpers in the local
file when GitHub setup is selected.

## Windows

From a PowerShell session in the repository:

```powershell
.\win_setup\setup.ps1 -dryRun
# Run PowerShell as administrator for the actual setup:
.\win_setup\setup.ps1
```

The script configures the Windows long-path policy, installs the listed winget
packages, and requests WSL 2. If it changes the long-path policy, reboot
manually and rerun it. After WSL setup, open Ubuntu and run the Ubuntu bootstrap.
Winget must already be available. Native Windows runtime validation is pending.

## tmux

The Slate theme uses built-in tmux features, requires tmux 3.4+ and a Nerd
Font, and was tested with Windows Terminal/WSL. Copy-mode bindings use WSL's
`clip.exe` and may mishandle non-ASCII text. OSC 52 also permits applications
inside panes to write to the system clipboard. Reload with
`tmux source-file ~/.tmux.conf` or `Ctrl-a`, then `r`.

## Maintenance and verification

See the [Pi maintenance skill](ubuntu_setup/symlink_fs/.pi/agent/skills/dotfiles/SKILL.md)
for the change workflow and [decisions](DECISIONS.md) for lasting tradeoffs.
Outstanding work is in [TODOs](TODOS.md).

```sh
python3 -m unittest discover -s tests -v
bash -n ubuntu_setup/bootstrap.sh
```
