#!/bin/bash

# Exit on error
set -e

GITHUB_USERNAME="Bloblblobl"
GITHUB_REPO="dotfiles"

# Prompt for clone destination path
read -p "Enter the directory where you want to clone the repository (default: ~/git/dotfiles): " clone_path
clone_path=${clone_path:-"$HOME/git/dotfiles"}

# Prompt for GitHub PAT (hidden input for security)
echo "GitHub PATs: https://github.com/settings/personal-access-tokens"
read -s -p "Enter a PAT for your account: " github_pat
echo

# Update and install git, python3
echo "Updating system and installing git and Python..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3 python3-pip

# Create the directory recursively if it doesn't exist
if [ ! -d "$clone_path" ]; then
  echo "Creating directory $clone_path..."
  mkdir -p "$clone_path"
fi

# Clone dotfiles repo and run master setup script
echo "Cloning dotfiles repository to $clone_path..."
git clone https://$GITHUB_USERNAME:$github_pat@github.com/$GITHUB_USERNAME/$GITHUB_REPO.git $clone_path
echo "Running master setup script..."
python3 $clone_path/master_setup.py
