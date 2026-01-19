#!/usr/bin/env sh
set -eu

# Neona Installer (production-grade, POSIX-sh compatible)
# Usage: curl -fsSL https://cli.neona.app/install.sh | bash
#
# Environment Variables:
#   NEONA_VERSION          Pin specific version (default: latest from API)
#   NEONA_INSTALL_DIR      Install directory (default: $HOME/.local/bin)
#   NEONA_REQUIRE_VERIFY   Set to 1 to fail if checksum missing (default: 0)
#   NEONA_SKIP_VERIFY      Set to 1 to skip checksum verification (default: 0)
#   NEONA_NO_COMPLETIONS   Set to 1 to skip shell completions (default: 0)
#   NEONA_MODIFY_SHELL     Set to 1 to auto-add PATH to shell rc (default: 0)

REPO="Neona-AI/Neona"
GO_MODULE="github.com/fentz26/neona"
BINARY_NAME="neona"
INSTALL_DIR="${NEONA_INSTALL_DIR:-$HOME/.local/bin}"
REQUIRE_VERIFY="${NEONA_REQUIRE_VERIFY:-0}"
SKIP_VERIFY="${NEONA_SKIP_VERIFY:-0}"
NO_COMPLETIONS="${NEONA_NO_COMPLETIONS:-0}"
MODIFY_SHELL="${NEONA_MODIFY_SHELL:-0}"

# Colors (ANSI, works in most terminals)
BANNER_COLOR='\033[38;2;189;224;254m'
NC='\033[0m'

# Logging (plain text prefixes, output to stderr)
log_info()    { printf '[INFO] %s\n' "$*" >&2; }
log_success() { printf '[SUCCESS] %s\n' "$*" >&2; }
log_warning() { printf '[WARNING] %s\n' "$*" >&2; }
log_error()   { printf '[FAILED] %s\n' "$*" >&2; }

have() { command -v "$1" >/dev/null 2>&1; }

# Downloader abstraction (curl preferred, wget fallback)
download() {
  url="$1"
  out="${2:-}"
  if have curl; then
    if [ -n "$out" ]; then
      curl -fsSL -H "Accept: application/octet-stream" -o "$out" "$url"
    else
      curl -fsSL -H "Accept: application/vnd.github+json" "$url"
    fi
  elif have wget; then
    if [ -n "$out" ]; then
      wget -q -O "$out" "$url"
    else
      wget -q -O - "$url"
    fi
  else
    log_error "Neither curl nor wget is installed."
    return 1
  fi
}

# Safe temp directory
mktemp_dir() {
  d="$(mktemp -d 2>/dev/null || mktemp -d -t 'neona-install' 2>/dev/null || true)"
  if [ -z "$d" ] || [ ! -d "$d" ]; then
    log_error "Failed to create temp directory."
    return 1
  fi
  printf '%s' "$d"
}

# ASCII Banner
show_banner() {
  printf '\n'
  printf '%b' "${BANNER_COLOR}"
  cat << 'EOF'
 __ _  ____  __   __ _   __  
(  ( \(  __)/  \ (  ( \ / _\ 
/    / ) _)(  O )/    //    \
\_)__)(____)\__/ \_)__)\_/\_/
EOF
  printf '%b\n\n' "${NC}"
}

# Platform detection
detect_platform() {
  os="$(uname -s 2>/dev/null | tr '[:upper:]' '[:lower:]')"
  arch="$(uname -m 2>/dev/null)"

  case "$os" in
    linux)  OS="linux" ;;
    darwin) OS="darwin" ;;
    mingw*|msys*|cygwin*) log_error "Windows shell not supported. Use WSL."; exit 1 ;;
    *) log_error "Unsupported OS: $os"; exit 1 ;;
  esac

  case "$arch" in
    x86_64|amd64)  ARCH="amd64" ;;
    aarch64|arm64) ARCH="arm64" ;;
    armv7l|armv8l) ARCH="arm64" ;;  # Raspberry Pi arm64
    *) log_error "Unsupported architecture: $arch"; exit 1 ;;
  esac

  log_info "Platform: ${OS}-${ARCH}"
}

# Get latest release tag from GitHub API
get_latest_version() {
  json="$(download "https://api.github.com/repos/${REPO}/releases/latest" "" 2>/dev/null)" || true
  tag="$(printf '%s' "$json" | sed -n 's/.*"tag_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)"

  if [ -z "$tag" ]; then
    # Fallback: try releases list
    json="$(download "https://api.github.com/repos/${REPO}/releases" "" 2>/dev/null)" || true
    tag="$(printf '%s' "$json" | sed -n 's/.*"tag_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)"
  fi

  if [ -z "$tag" ]; then
    log_warning "Could not fetch latest version from GitHub API (rate-limited?)."
    log_warning "Set NEONA_VERSION explicitly to continue."
    return 1
  fi

  printf '%s' "$tag"
}

# SHA256 tool detection
pick_sha_tool() {
  if have sha256sum; then printf 'sha256sum'; return 0; fi
  if have shasum; then printf 'shasum'; return 0; fi
  return 1
}

# Checksum verification
verify_sha256() {
  file="$1"
  sha_url="$2"
  tmp_sha="$3"

  if [ "$SKIP_VERIFY" = "1" ]; then
    log_warning "Checksum verification skipped (NEONA_SKIP_VERIFY=1)."
    return 0
  fi

  if ! download "$sha_url" "$tmp_sha" 2>/dev/null; then
    if [ "$REQUIRE_VERIFY" = "1" ]; then
      log_error "Checksum file missing and NEONA_REQUIRE_VERIFY=1. Aborting."
      return 1
    fi
    log_warning "No checksum file found. Proceeding without verification."
    return 0
  fi

  tool="$(pick_sha_tool || true)"
  if [ -z "$tool" ]; then
    log_warning "No sha256 tool available. Skipping verification."
    return 0
  fi

  expected="$(awk '{print $1}' "$tmp_sha" | head -n 1 | tr -d '\r\n')"
  if [ "${#expected}" -ne 64 ]; then
    log_warning "Invalid checksum format. Skipping verification."
    return 0
  fi

  if [ "$tool" = "sha256sum" ]; then
    actual="$(sha256sum "$file" | awk '{print $1}')"
  else
    actual="$(shasum -a 256 "$file" | awk '{print $1}')"
  fi

  if [ "$actual" != "$expected" ]; then
    log_error "Checksum verification failed!"
    log_error "Expected: $expected"
    log_error "Actual:   $actual"
    return 1
  fi

  log_info "Checksum verified."
}

# Ensure install directory exists
ensure_install_dir() {
  if [ ! -d "$INSTALL_DIR" ]; then
    mkdir -p "$INSTALL_DIR" || {
      log_error "Cannot create $INSTALL_DIR"
      return 1
    }
  fi
}

# PATH hint (non-intrusive by default)
maybe_add_path() {
  case ":${PATH}:" in
    *":${INSTALL_DIR}:"*) return 0 ;;
  esac

  log_warning "${INSTALL_DIR} is not on PATH."
  printf '[INFO] Add this to your shell profile:\n' >&2
  printf '  export PATH="%s:$PATH"\n' "$INSTALL_DIR" >&2

  # Only modify rc files if explicitly opted in
  if [ "$MODIFY_SHELL" = "1" ]; then
    line="export PATH=\"${INSTALL_DIR}:\$PATH\""
    for rc in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
      if [ -f "$rc" ]; then
        if ! grep -qF "$line" "$rc" 2>/dev/null; then
          printf '\n# Added by Neona installer\n%s\n' "$line" >> "$rc"
          log_info "Added PATH to $(basename "$rc")"
        fi
      fi
    done
  fi
}

# Install shell completions
install_completions() {
  bin="$1"

  if [ "$NO_COMPLETIONS" = "1" ]; then
    return 0
  fi

  # Check if binary supports completions
  "$bin" completion bash >/dev/null 2>&1 || return 0

  # Bash
  bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  mkdir -p "$bash_dir" 2>/dev/null || true
  "$bin" completion bash > "$bash_dir/neona" 2>/dev/null || true

  # Zsh
  zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  mkdir -p "$zsh_dir" 2>/dev/null || true
  "$bin" completion zsh > "$zsh_dir/_neona" 2>/dev/null || true

  # Fish
  fish_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
  mkdir -p "$fish_dir" 2>/dev/null || true
  "$bin" completion fish > "$fish_dir/neona.fish" 2>/dev/null || true

  log_info "Shell completions installed (bash/zsh/fish)."
}

# Post-install validation
validate_install() {
  bin="$1"
  if "$bin" version >/dev/null 2>&1; then
    version_out="$("$bin" version 2>/dev/null || echo 'unknown')"
    log_info "Installed version: $version_out"
    return 0
  elif "$bin" --version >/dev/null 2>&1; then
    version_out="$("$bin" --version 2>/dev/null || echo 'unknown')"
    log_info "Installed version: $version_out"
    return 0
  else
    log_warning "Binary installed but 'neona version' failed. May need dependencies."
    return 0
  fi
}

# Download and install pre-built binary
install_from_release() {
  detect_platform

  VERSION="${NEONA_VERSION:-}"
  if [ -z "$VERSION" ]; then
    VERSION="$(get_latest_version)" || return 1
  fi
  log_info "Target version: $VERSION"

  tmp="$(mktemp_dir)" || return 1
  trap 'rm -rf "$tmp"' EXIT INT TERM
  mkdir -p "$tmp/extract"

  asset_base="neona-${OS}-${ARCH}"
  url_tgz="https://github.com/${REPO}/releases/download/${VERSION}/${asset_base}.tar.gz"
  url_bin="https://github.com/${REPO}/releases/download/${VERSION}/${asset_base}"

  bin_path=""

  # Strategy 1: Try tar.gz first
  log_info "Trying ${asset_base}.tar.gz..."
  if download "$url_tgz" "$tmp/neona.tar.gz" 2>/dev/null; then
    verify_sha256 "$tmp/neona.tar.gz" "${url_tgz}.sha256" "$tmp/neona.tar.gz.sha256" || return 1

    if have tar; then
      tar -xzf "$tmp/neona.tar.gz" -C "$tmp/extract" 2>/dev/null || {
        log_warning "Failed to extract tar.gz. Trying raw binary..."
      }
      # Find binary inside extracted content
      bin_path="$(find "$tmp/extract" -type f -name "$BINARY_NAME" 2>/dev/null | head -n 1 || true)"
    else
      log_warning "tar not found. Trying raw binary..."
    fi
  fi

  # Strategy 2: Fallback to raw binary
  if [ -z "$bin_path" ] || [ ! -f "$bin_path" ]; then
    log_info "Trying raw binary ${asset_base}..."
    if download "$url_bin" "$tmp/neona" 2>/dev/null; then
      verify_sha256 "$tmp/neona" "${url_bin}.sha256" "$tmp/neona.sha256" || return 1
      bin_path="$tmp/neona"
    else
      log_error "Failed to download release asset."
      return 1
    fi
  fi

  chmod +x "$bin_path"
  ensure_install_dir || return 1

  dest="$INSTALL_DIR/$BINARY_NAME"

  # Atomic install
  tmp_dest="$dest.tmp.$$"
  cp "$bin_path" "$tmp_dest"
  chmod 755 "$tmp_dest"
  mv "$tmp_dest" "$dest"

  log_success "Neona ${VERSION} installed to $dest"
  maybe_add_path
  validate_install "$dest"
  install_completions "$dest"
  return 0
}

# Install via go install (fallback)
install_from_go() {
  have go || return 1
  log_info "Go detected: $(go version 2>/dev/null | head -n1 || echo 'unknown')"
  log_info "Installing via go install..."

  CGO_ENABLED=0 go install "${GO_MODULE}/cmd/neona@latest" || {
    log_error "go install failed."
    return 1
  }

  gobin="${GOBIN:-$(go env GOPATH 2>/dev/null)/bin}"
  src="$gobin/$BINARY_NAME"

  if [ ! -f "$src" ]; then
    log_error "go install succeeded but binary not found at $src"
    return 1
  fi

  ensure_install_dir || return 1

  dest="$INSTALL_DIR/$BINARY_NAME"
  cp "$src" "$dest"
  chmod 755 "$dest"

  log_success "Neona installed to $dest"
  maybe_add_path
  validate_install "$dest"
  install_completions "$dest"
  return 0
}

# Main
main() {
  show_banner
  log_info "Starting Neona installation..."

  # Try prebuilt first
  if install_from_release; then
    printf '\n' >&2
    log_success "Installation complete!"
    log_info "Run 'neona --help' to get started."
    exit 0
  fi

  # Fallback to Go
  log_warning "Prebuilt not available. Trying Go install..."
  if install_from_go; then
    printf '\n' >&2
    log_success "Installation complete!"
    log_info "Run 'neona --help' to get started."
    exit 0
  fi

  log_error "Installation failed."
  log_info "Options:"
  log_info "  1. Set NEONA_VERSION=vX.Y.Z and retry"
  log_info "  2. Install Go from https://go.dev/dl/ and retry"
  log_info "  3. Download manually from https://github.com/${REPO}/releases"
  exit 1
}

main "$@"
