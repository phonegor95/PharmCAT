#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd "${script_dir}/.." && pwd)"

cd "$repo_dir"

# install python packages
if [[ ! -d ~/.virtualenvs/PharmCAT ]]; then
  echo "Initializing venv"
  python3 -m venv ~/.virtualenvs/PharmCAT
else
  echo "venv already initialized"
fi

source ~/.virtualenvs/PharmCAT/bin/activate

echo "Installing required python packages"
python -m pip install -r preprocessor/requirements.txt
python -m pip install -r preprocessor/tests/requirements.txt
deactivate

# install samtools
if command -v lsb_release >/dev/null 2>&1; then
  distro="$(lsb_release -i -s)"
  if [[ "$distro" == "Ubuntu" ]]; then
    echo "Installing required libraries..."
    sudo apt install bzip2 zlib1g-dev libcurl4-openssl-dev libbz2-dev liblzma-dev libncurses-dev
  fi
fi

"${script_dir}/install_samtools.sh" "$HOME/.local"
