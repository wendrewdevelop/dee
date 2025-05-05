#!/usr/bin/env bash
set -e

# 1. Verifica se o pipx está instalado
if ! command -v pipx &> /dev/null; then
  echo "➡️ pipx não encontrado. Instalando pipx..."
  python3 -m pip install --user pipx
  python3 -m pipx ensurepath
  export PATH="$HOME/.local/bin:$PATH"
fi

# 2. Define a versão do dee
REPO="wendrewdevelop/dee"
VERSION="${1:-v0.1.0}"
TARBALL_URL="https://github.com/${REPO}/archive/refs/tags/${VERSION}.tar.gz"

# 3. Instala o dee via pipx
echo "➡️ Instalando dee ${VERSION} via pipx..."
pipx install "$TARBALL_URL" --force

echo "✅ dee ${VERSION} instalado com sucesso!"
