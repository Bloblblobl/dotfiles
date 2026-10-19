# Decisions

Record durable, non-obvious tradeoffs here; routine changes belong in commits.
Newest first.

## Keep tmux styling dependency-free

Use native tmux features rather than plugins or polling helpers. The Slate
status theme depends on tmux 3.4+ and a Nerd Font; WSL `clip.exe` bindings and
OSC 52 clipboard writes are deliberate portability/security tradeoffs.

## Make Windows setup explicit

A dry run must not change the machine. Configure the long-path registry policy
without a synthetic filesystem test or automatic reboot. Stop on native-command
failures; native Windows validation remains outstanding.

## Keep Git settings machine-local

Track an include of `~/.gitconfig.local`, not personal identity or credential
helpers. Clone this public repository anonymously; offer GitHub CLI login later.
GitHub CLI can fall back to plaintext token storage without a keyring.

## Preserve existing home files

Preflight symlink destinations and refuse to replace regular files or directories.
Reconciliation is manual; no implicit backups or deletions. This prioritizes
preserving user data over unattended installation.
