#!/usr/bin/env python3
"""Ubuntu/WSL configuration installer. No credentials belong in the repository."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

DOTFILES_DIR = Path(__file__).resolve().parents[1]
SYMLINK_DIR = DOTFILES_DIR / "ubuntu_setup/symlink_fs"
SCRIPTS_DIR = DOTFILES_DIR / "ubuntu_setup/scripts"


def confirm(prompt):
    return input(f"{prompt} [y/N]: ").strip().lower() in {"y", "yes"}


def link_state(source, target):
    if target.is_symlink():
        return "unchanged" if target.resolve() == source.resolve() else "replace link"
    if os.path.lexists(target):
        raise RuntimeError(f"Refusing to replace real file/directory: {target}; reconcile it first")
    return "create link"


def create_symlinks(dry_run=False):
    # Preflight every destination before making any changes.
    plan = []
    for source in sorted(SYMLINK_DIR.rglob("*")):
        if not source.is_file():
            continue
        target = Path.home() / source.relative_to(SYMLINK_DIR)
        for parent in target.parents:
            if os.path.lexists(parent) and not parent.is_dir():
                raise RuntimeError(f"Parent is not a directory: {parent}")
        plan.append((source, target, link_state(source, target)))
    for source, target, action in plan:
        print(f"{action}: {target}")
        if dry_run or action == "unchanged":
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink():
            target.unlink()
        target.symlink_to(source)


def configure_github(dry_run=False):
    if dry_run:
        print("Would offer GitHub CLI installation/login and local credential configuration")
        return
    if not confirm("Set up GitHub CLI for private repositories and pushing?"):
        return
    if not shutil.which("gh"):
        if not shutil.which("apt-get"):
            raise RuntimeError("Automatic gh installation currently requires Ubuntu/WSL apt-get")
        subprocess.run(["sudo", "apt-get", "update"], check=True)
        subprocess.run(["sudo", "apt-get", "install", "-y", "gh"], check=True)
    gh = shutil.which("gh")
    status = subprocess.run([gh, "auth", "status", "--hostname", "github.com"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if status.returncode:
        print("GitHub CLI may fall back to plaintext token storage if no keyring is available.")
        if not confirm("Proceed with interactive login knowing this storage limitation?"):
            return
        subprocess.run([gh, "auth", "login", "--hostname", "github.com",
                        "--git-protocol", "https", "--web", "--skip-ssh-key"], check=True)
    local = Path.home() / ".gitconfig.local"
    if local.is_symlink():
        raise RuntimeError("Refusing to write credentials configuration through a local-file symlink")
    local.touch(mode=0o600, exist_ok=True)
    local.chmod(0o600)
    # Explicitly target the local file, never `gh auth setup-git` or --global.
    import shlex
    for host in ("github.com", "gist.github.com"):
        key = f"credential.https://{host}.helper"
        subprocess.run(["git", "config", "--file", str(local), "--replace-all", key, ""], check=True)
        subprocess.run(["git", "config", "--file", str(local), "--add", key,
                        f"!{shlex.quote(gh)} auth git-credential"], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-d", "--dry-run", action="store_true")
    parser.add_argument("--skip-github", action="store_true")
    args = parser.parse_args()
    create_symlinks(args.dry_run)
    if not args.skip_github:
        configure_github(args.dry_run)
    for script in sorted(SCRIPTS_DIR.glob("*.py")):
        print(f"Setup script: {script.name}")
        if not args.dry_run and confirm(f"Run {script.name}?"):
            subprocess.run([sys.executable, str(script)], check=True)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError, EOFError) as error:
        print(f"Bootstrap failed: {error}", file=sys.stderr)
        sys.exit(1)
