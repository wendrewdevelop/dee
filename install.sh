#!/usr/bin/env bash
set -e

# 1. Definições
REPO="wendrewdevelop/dee"
TARBALL="deevcs.tar.gz"
if [ -z "$VERSION" ]; then
  VERSION=$(curl -sL "https://api.github.com/repos/${REPO}/releases/latest" \
             | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
fi
URL="https://github.com/${REPO}/releases/download/${VERSION}/${TARBALL}"

# 2. Download e extração
tmpdir=$(mktemp -d)
curl -sL "$URL" -o "$tmpdir/$TARBALL"
tar -xzf "$tmpdir/$TARBALL" -C "$tmpdir"

# 3. Instalação
install -Dm755 "$tmpdir/dee" /usr/local/bin/dee

echo "dee v${VERSION} instalado com sucesso em /usr/local/bin/dee"
