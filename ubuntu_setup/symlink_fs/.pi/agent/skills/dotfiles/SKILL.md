---
name: dotfiles
description: "Maintain this dotfiles repository through focused changes, safe setup, verification, and reviewable commits."
---

# Maintain dotfiles

The repository is the source of truth. `ubuntu_setup/symlink_fs/` mirrors paths
under `$HOME`; `ubuntu_setup/bootstrap.py` creates their symlinks. Windows setup
lives in `win_setup/`. Work in the repository, not through the installed links.

## Rules

- Do not overwrite existing regular files or directories in `$HOME`. Investigate
  conflicts and reconcile them explicitly.
- Never add credentials, secrets, private keys, personal identity, or
  machine-specific paths to tracked files. Ignore rules are not a security guarantee.
- Keep changes focused and commits independently reviewable. Do not stage
  unrelated work.
- Do not claim platform support or validation that has not been tested.

## Workflow

1. Read the relevant configuration and its existing documentation before editing.
2. Make the smallest coherent change. Explain non-obvious settings in nearby
   comments; avoid narrating obvious code.
3. Update `README.md` only when setup, usage, or discoverability changes. Add a
   `DECISIONS.md` entry only for a durable, non-obvious tradeoff. Keep deferred
   work separate from setup instructions.
4. Run relevant checks. For bootstrap changes, start with
   `python3 -m unittest discover -s tests -v` and
   `bash -n ubuntu_setup/bootstrap.sh`. Disclose untested platforms or flows.
5. Stage explicit paths, inspect the entire staged diff, review for secrets,
   then commit with an imperative summary that describes the outcome.

## Before committing

```sh
git status --short
# Stage only the intended files, for example:
git add -- README.md ubuntu_setup/symlink_fs/.tmux.conf
git diff --cached --check
git diff --cached --name-only
git -c core.pager=cat diff --cached
```

Inspect both filenames **and content** for credentials, tokens, email addresses,
private hostnames/URLs, and absolute personal paths. Do not assume an ignored
file cannot be force-added or that a regex catches every secret. Confirm the
staged change contains only the intended work before committing.

Commit subjects should be concise and imperative. Use a short body only to
explain important motivation or a surprising tradeoff, not to repeat the diff.
