#!/usr/bin/env bash
set -euo pipefail

: "${GH_VERSION:?GH_VERSION is required}"
GH_RELEASE_BASE_URL="${GH_RELEASE_BASE_URL:-https://github.com/cli/cli/releases/download}"
GH_INSTALL_DIR="${GH_INSTALL_DIR:-${RUNNER_TEMP:-/tmp}/gh-${GH_VERSION}-bin}"

if [[ -n "${GH_ARCH:-}" ]]; then
  arch="$GH_ARCH"
else
  case "$(uname -m)" in
    x86_64|amd64) arch="amd64" ;;
    aarch64|arm64) arch="arm64" ;;
    *) echo "unsupported architecture: $(uname -m)" >&2; exit 2 ;;
  esac
fi

archive="gh_${GH_VERSION}_linux_${arch}.tar.gz"
checksums="gh_${GH_VERSION}_checksums.txt"
release_url="${GH_RELEASE_BASE_URL%/}/v${GH_VERSION}"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

curl -fsSL "$release_url/$archive" -o "$tmp/$archive"
curl -fsSL "$release_url/$checksums" -o "$tmp/$checksums"
expected="$(awk -v file="$archive" '$2 == file || $2 == "*" file {print $1; exit}' "$tmp/$checksums")"
[[ "$expected" =~ ^[0-9a-fA-F]{64}$ ]] || {
  echo "checksum entry missing for $archive" >&2
  exit 3
}
actual="$(sha256sum "$tmp/$archive" | awk '{print $1}')"
[[ "${actual,,}" == "${expected,,}" ]] || {
  echo "checksum mismatch for $archive" >&2
  exit 4
}

tar -xzf "$tmp/$archive" -C "$tmp"
source_gh="$tmp/gh_${GH_VERSION}_linux_${arch}/bin/gh"
[[ -x "$source_gh" ]] || {
  echo "archive missing executable gh" >&2
  exit 5
}

mkdir -p "$GH_INSTALL_DIR"
install -m 0755 "$source_gh" "$GH_INSTALL_DIR/gh"
if [[ -n "${GITHUB_PATH:-}" ]]; then
  printf '%s\n' "$GH_INSTALL_DIR" >> "$GITHUB_PATH"
fi
"$GH_INSTALL_DIR/gh" --version
