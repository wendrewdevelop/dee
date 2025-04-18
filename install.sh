#!/usr/bin/env bash
set -e

# 1. Configurações
REPO="wendrewdevelop/dee"
# Se VERSION não for informado via parâmetro, busca a última release
if [ -z "$1" ]; then
  VERSION=$(curl -sL "https://api.github.com/repos/${REPO}/releases/latest" \
    | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
else
  VERSION="$1"
fi

# URL do tarball gerado pelo GitHub
TARBALL="${VERSION}.tar.gz"
URL="https://github.com/${REPO}/archive/refs/tags/${TARBALL}"

# 2. Download e extração
echo "➡️ Baixando ${URL}..."
tmpdir=$(mktemp -d)
curl -sL "$URL" -o "$tmpdir/$TARBALL"
echo "➡️ Extraindo em ${tmpdir}..."
tar -xzf "$tmpdir/$TARBALL" -C "$tmpdir"     # 

# 3. Instalação global (via pip) — requer Python e pip instalados
echo "➡️ Instalando o pacote Python..."
cd "$tmpdir"/dee-"${VERSION#v}"*            # adapta conforme o diretório gerado
pip3 install --upgrade .                     # :contentReference[oaicite:3]{index=3}

echo "✅ dee ${VERSION} instalado com sucesso!"
