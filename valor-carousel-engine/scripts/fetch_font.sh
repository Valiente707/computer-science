#!/usr/bin/env bash
# Downloads Inter-Bold.ttf into fonts/ (SIL OFL 1.1 — commercially redistributable).
set -euo pipefail

FONTS_DIR="$(dirname "$0")/../fonts"
DEST="$FONTS_DIR/Inter-Bold.ttf"
URL="https://github.com/rsms/inter/releases/download/v4.0/Inter-4.0.zip"

mkdir -p "$FONTS_DIR"
TMP=$(mktemp -d)
trap "rm -rf $TMP" EXIT

curl -sSL --fail -o "$TMP/inter.zip" "$URL"
unzip -o -j "$TMP/inter.zip" 'extras/ttf/Inter-Bold.ttf' -d "$FONTS_DIR"
echo "Downloaded: $DEST ($(wc -c < "$DEST") bytes)"
