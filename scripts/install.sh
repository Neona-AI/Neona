#!/bin/bash
set -e

# Neona Installer
# Usage: curl -fsSL https://neona.app/install.sh | bash

REPO="fentz26/Neona"
BINARY_NAME="neona"
INSTALL_DIR="/usr/local/bin"
GO_BIN_DIR="$HOME/go/bin"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Installing Neona Control Plane...${NC}"

# Check for Go installation
if command -v go &> /dev/null; then
    echo -e "${GREEN}✓ Go detected. Installing via 'go install'...${NC}"
    
    # Install directly from main repo
    go install github.com/fentz26/neona/cmd/neona@latest
    
    # Ensure Go bin is in PATH
    if [[ ":$PATH:" != *":$GO_BIN_DIR:"* ]]; then
        echo -e "${BLUE}ℹ Adding $GO_BIN_DIR to PATH in ~/.bashrc${NC}"
        echo 'export PATH=$PATH:$HOME/go/bin' >> ~/.bashrc
        echo 'export PATH=$PATH:$HOME/go/bin' >> ~/.zshrc 2>/dev/null || true
        export PATH=$PATH:$HOME/go/bin
    fi

    echo -e "${GREEN}✅ Neona installed successfully!${NC}"
    echo -e "Run ${GREEN}neona${NC} to start."
    exit 0
fi

# Fallback: Download pre-built binary (Future implementation when releases exist)
echo -e "${RED}x Go not found.${NC}"
echo "For now, Neona requires Go to be installed."
echo "Please install Go from https://go.dev/dl/ and try again."
exit 1

# Future Release Download Logic (Commented out until releases are active)
# OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
# ARCH="$(uname -m)"
# if [ "$ARCH" == "x86_64" ]; then ARCH="amd64"; fi
# if [ "$ARCH" == "aarch64" ]; then ARCH="arm64"; fi
# URL="https://github.com/$REPO/releases/latest/download/neona_${OS}_${ARCH}.tar.gz"
# curl -fsSL "$URL" -o neona.tar.gz
# tar -xzf neona.tar.gz
# sudo mv neona $INSTALL_DIR/
# echo "Installed to $INSTALL_DIR/neona"
