#!/usr/bin/env bash
set -e

REPO="wendrewdevelop/dee"
VERSION="${1:-v0.1.17}"
TARBALL_URL="https://github.com/${REPO}/archive/refs/tags/${VERSION}.tar.gz"
TMPDIR=$(mktemp -d)
VENV_NAME="dee-env"

# 1) Garante pipx
if ! command -v pipx &> /dev/null; then
  echo "➡️ pipx não encontrado. Instalando pipx..."
  python3 -m pip install --user pipx
  python3 -m pipx ensurepath
  export PATH="$HOME/.local/bin:$PATH"
fi

# 2) Baixa e descompacta
echo "➡️ Baixando dee ${VERSION}..."
curl -sL "${TARBALL_URL}" | tar xz -C "${TMPDIR}"

# 3) Entra na pasta do pacote
cd "${TMPDIR}/dee-${VERSION#v}"

# 4) Tenta instalar como CLI via pipx (incluindo apps das deps)
echo "➡️ Tentando instalar dee como CLI via pipx (com --include-deps)..."
if pipx install . --force --include-deps; then
  echo "✅ dee instalado com success! Apps das dependências também estão disponíveis."
  exit 0
else
  echo "⚠️ Nenhum entry_point do dee detectado. Instalando como biblioteca num venv..."
  # 5) Cria venv e instala via pip
  python3 -m venv "${HOME}/.virtualenvs/${VENV_NAME}"
  source "${HOME}/.virtualenvs/${VENV_NAME}/bin/activate"
  pip install --upgrade pip setuptools
  pip install .
  echo "✅ dee instalado no venv '${VENV_NAME}'. Para usar, execute:"
  echo "   source \"\${HOME}/.virtualenvs/${VENV_NAME}/bin/activate\""
fi

# 6) Limpeza
cd -
rm -rf "${TMPDIR}"
