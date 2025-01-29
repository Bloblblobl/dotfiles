#!/usr/bin/env python3

import os
import subprocess
import sys
import argparse
from pathlib import Path

DOTFILES_DIR = Path(__file__).resolve().parents[1]
SYMLINK_DIR = DOTFILES_DIR / "ubuntu_setup" / "symlink_fs"
SCRIPTS_DIR = DOTFILES_DIR / "ubuntu_setup" / "scripts"


def shorten_path(path):
    """Replace home directory with '~' in printed paths."""
    home = str(Path.home())
    return str(path).replace(home, "~", 1) if str(path).startswith(home) else str(path)


def confirm_action(prompt):
    """Prompt user for confirmation with a default 'Yes' option."""
    while True:
        response = input(f"{prompt} (Y/n): ").strip().lower()
        if response in {"", "y", "yes"}:
            return True
        elif response in {"n", "no"}:
            return False
        else:
            print("❌ Invalid input. Please enter 'y' or 'n'.")


def create_symlinks(interactive, dry_run):
    """Symlink everything in symlink_fs/ to the home directory."""
    print("🔗 Creating symlinks...")

    if interactive and not confirm_action("Create all symlinks?"):
        print("⏩ Skipping symlink creation.")
        return

    home_dir = Path.home()

    for item in SYMLINK_DIR.glob("**/*"):
        if item.is_file():
            relative_path = item.relative_to(SYMLINK_DIR)
            target_path = home_dir / relative_path

            if not dry_run:
                target_path.parent.mkdir(parents=True, exist_ok=True)

                if target_path.exists() or target_path.is_symlink():
                    target_path.unlink()

                target_path.symlink_to(item)
            
            symbol = "⭕" if dry_run else "✅"
            print(f"  {symbol} Symlinked: {shorten_path(item)} -> {shorten_path(target_path)}")

    print("🎉 Symlinks created successfully!\n")


def run_scripts(interactive, verbose, exit_on_error, dry_run):
    """Run all setup scripts in scripts/ directory."""
    print("🚀 Running setup scripts...")

    for script in sorted(SCRIPTS_DIR.glob("*.py")):
        if interactive and not confirm_action(f"Run {script.name}?"):
            print(f"⏩ Skipping {script.name}")
            continue

        symbol = "⭕" if dry_run else "➡️"
        print(f"{symbol} Running {script.name}...")

        if dry_run:
            continue

        result = subprocess.run(
            [sys.executable, str(script)],
            text=True,
            capture_output=True
        )

        if verbose:
            output = result.stdout.strip()
            error_output = result.stderr.strip()
            if output:
                print(f"  📜 Output:\n    " + "\n    ".join(output.splitlines()))
            if error_output:
                print(f"  ⚠️ Error:\n    " + "\n    ".join(error_output.splitlines()))

        if result.returncode != 0:
            error_msg = f"❌ {script.name} failed with exit code {result.returncode}."
            if exit_on_error:
                print(error_msg + " Aborting.")
                sys.exit(1)
            else:
                print(error_msg + " Continuing...")

    print("🎉 All scripts executed successfully!\n")


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Bootstrap script for setting up dotfiles.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show script output.")
    parser.add_argument("-i", "--interactive", action="store_true", help="Prompt before performing actions.")
    parser.add_argument("-e", "--exit-on-error", action="store_true", help="Abort if any scripts error.")
    parser.add_argument("-d", "--dry-run", action="store_true", help="Simulate actions without making changes.")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.dry_run:
        print("⭕ Dry run mode: No changes will be made!\n")

    try:
        create_symlinks(args.interactive, args.dry_run)
        run_scripts(args.interactive, args.verbose, args.exit_on_error, args.dry_run)
        print("✅ Bootstrap process completed!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
