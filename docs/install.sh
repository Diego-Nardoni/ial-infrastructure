#!/bin/bash
# IAL (Infrastructure as Language) - Instalação Automática
# Similar ao padrão Amazon Q

set -e

echo "🚀 Instalando IAL (Infrastructure as Language)..."

# Detectar arquitetura
ARCH=$(uname -m)
case $ARCH in
    x86_64) ARCH="amd64" ;;
    aarch64) ARCH="arm64" ;;
    *) echo "❌ Arquitetura não suportada: $ARCH"; exit 1 ;;
esac

# URLs de download (ajustar conforme seu repositório)
GITHUB_REPO="SEU_USUARIO/ial"
PACKAGE_NAME="ialctl_${ARCH}.deb"
DOWNLOAD_URL="https://github.com/${GITHUB_REPO}/releases/latest/download/${PACKAGE_NAME}"

echo "📦 Baixando IAL para ${ARCH}..."
wget -O "/tmp/${PACKAGE_NAME}" "${DOWNLOAD_URL}"

echo "🔧 Instalando pacote..."
sudo dpkg -i "/tmp/${PACKAGE_NAME}"

echo "🔄 Resolvendo dependências..."
sudo apt-get update
sudo apt-get install -f -y

echo "🧹 Limpando arquivos temporários..."
rm "/tmp/${PACKAGE_NAME}"

echo "✅ IAL instalado com sucesso!"
echo ""
echo "Para começar a usar:"
echo "  ialctl --help"
echo "  ialctl"
echo ""
echo "Para configurar AWS (opcional):"
echo "  aws configure"
