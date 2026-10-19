#!/usr/bin/env bash
# Minimal Ubuntu/WSL entry point: prerequisites, anonymous clone, Python handoff.
set -euo pipefail
dry_run=false
python_args=()
for arg in "$@"; do
  case "$arg" in
    --dry-run|-d) dry_run=true ;;
    *) python_args+=("$arg") ;;
  esac
done
if [[ $(uname -s) != Linux ]] || ! command -v apt-get >/dev/null; then
  echo 'This entry point currently supports Ubuntu/WSL with apt-get only.' >&2
  exit 1
fi
read -r -p "Clone destination [$HOME/git/dotfiles]: " clone_path
clone_path=${clone_path:-"$HOME/git/dotfiles"}
if [[ $clone_path == '~/'* ]]; then
  clone_path="$HOME/${clone_path#\~/}"
fi
parent=$(dirname "$clone_path")
if $dry_run; then
  echo 'Ubuntu bootstrap (dry run)'
  export GIT_OPTIONAL_LOCKS=0 GIT_NO_LAZY_FETCH=1
  ready=true
  for package in git python3 ca-certificates; do
    if command -v dpkg-query >/dev/null &&
       [[ $(dpkg-query -W -f='${Status}' "$package" 2>/dev/null) == 'install ok installed' ]] &&
       { [[ $package == ca-certificates ]] || command -v "$package" >/dev/null; }; then
      printf '[OK] %s installed\n' "$package"
    else
      printf '[PENDING] %s must be installed and available\n' "$package"
      ready=false
    fi
  done
  directory=$parent
  while :; do
    if [[ -d "$directory" ]]; then
      printf '[OK] %s exists\n' "$directory"
      break
    elif [[ -e "$directory" || -L "$directory" ]]; then
      printf '[BLOCKED] %s is not a usable directory\n' "$directory"
      ready=false
      break
    fi
    printf '[PENDING] %s does not exist\n' "$directory"
    ready=false
    directory=$(dirname "$directory")
  done
  if [[ -L "$clone_path" && ! -e "$clone_path" ]]; then
    printf '[BLOCKED] Destination is a dangling symlink: %s\n' "$clone_path"
    ready=false
  elif [[ -e "$clone_path" || -L "$clone_path" ]]; then
    # Require this checkout's root, HEAD, origin, and Python files.
    if command -v git >/dev/null && [[ -d "$clone_path" ]] &&
       [[ $(git -C "$clone_path" rev-parse --show-toplevel 2>/dev/null) == "$(cd "$clone_path" && pwd -P)" ]] &&
       git -C "$clone_path" rev-parse --verify 'HEAD^{commit}' >/dev/null 2>&1 &&
       git -C "$clone_path" cat-file -e HEAD:ubuntu_setup/bootstrap.py 2>/dev/null &&
       [[ -f "$clone_path/ubuntu_setup/bootstrap.py" && -d "$clone_path/ubuntu_setup/symlink_fs" ]]; then
      origin=$(git -C "$clone_path" remote get-url origin 2>/dev/null || true)
      case "$origin" in
        https://github.com/Bloblblobl/dotfiles|https://github.com/Bloblblobl/dotfiles.git|git@github.com:Bloblblobl/dotfiles|git@github.com:Bloblblobl/dotfiles.git)
          echo '[OK] Repository checkout verified' ;;
        *) echo '[BLOCKED] Checkout origin is not Bloblblobl/dotfiles'; ready=false ;;
      esac
    else
      printf '[BLOCKED] Not a usable dotfiles checkout: %s\n' "$clone_path"
      ready=false
    fi
  else
    printf '[PENDING] Repository not cloned at %s\n' "$clone_path"
    ready=false
  fi
  if ! $ready; then
    echo 'Python dry-run skipped: shell prerequisites incomplete.'
    exit 0
  fi
  echo 'Running Python bootstrap dry-run...'
  exec python3 "$clone_path/ubuntu_setup/bootstrap.py" --dry-run "${python_args[@]}"
fi
if [[ -e "$clone_path" || -L "$clone_path" ]]; then
  echo "Destination already exists: $clone_path. Run its Python bootstrap directly." >&2
  exit 1
fi
sudo apt-get update
sudo apt-get install -y git python3 ca-certificates
mkdir -p "$parent"
git clone https://github.com/Bloblblobl/dotfiles.git "$clone_path"
exec python3 "$clone_path/ubuntu_setup/bootstrap.py" "${python_args[@]}"
