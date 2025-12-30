#!/usr/bin/env bash

set -euo pipefail

INPUT_FILE=""
OUTPUT_DIR="pdfs"
USER_AGENT="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"

if [[ ! -f "$INPUT_FILE" ]]; then
  echo "[!] Input file not found: $INPUT_FILE"
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

echo "[+] Downloading PDFs from $INPUT_FILE"
echo "[+] Saving to $OUTPUT_DIR/"

wget \
  --input-file="$INPUT_FILE" \
  --directory-prefix="$OUTPUT_DIR" \
  --content-disposition \
  --trust-server-names \
  --continue \
  --no-verbose \
  --user-agent="$USER_AGENT" \
  --timeout=30 \
  --tries=3 \
  --wait=1

echo "[+] Done"

