#!/usr/bin/env bash
#
# download_pdfs.sh
#
# Download PDF files from a list of URLs
#
# Usage:
#   ./download_pdfs.sh -i urls.txt [-o pdfs]
#

set -euo pipefail

INPUT_FILE=""
OUTPUT_DIR="pdfs"
USER_AGENT="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"

usage() {
  cat <<EOF
Usage: $0 -i <input_file> [-o output_dir]

Options:
  -i FILE   Input file containing URLs (one per line)
  -o DIR    Output directory (default: pdfs)
  -h        Show this help

Example:
  $0 -i netdocs_pdfs.txt -o downloads
EOF
}

# -------------------------
# Parse arguments
# -------------------------
while getopts ":i:o:h" opt; do
  case "$opt" in
    i) INPUT_FILE="$OPTARG" ;;
    o) OUTPUT_DIR="$OPTARG" ;;
    h) usage; exit 0 ;;
    *) usage; exit 1 ;;
  esac
done

if [[ -z "$INPUT_FILE" ]]; then
  echo "[!] Input file required"
  usage
  exit 1
fi

if [[ ! -f "$INPUT_FILE" ]]; then
  echo "[!] Input file not found: $INPUT_FILE"
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

# -------------------------
# Clean input (strip junk)
# -------------------------
TMP_URLS="$(mktemp)"
grep -Eiv '^\s*$|^\s*#' "$INPUT_FILE" > "$TMP_URLS"

URL_COUNT=$(wc -l < "$TMP_URLS" | tr -d ' ')
if [[ "$URL_COUNT" -eq 0 ]]; then
  echo "[!] No valid URLs found in input file"
  rm -f "$TMP_URLS"
  exit 1
fi

echo "[+] URLs to download: $URL_COUNT"
echo "[+] Saving to: $OUTPUT_DIR/"

# -------------------------
# Download
# -------------------------
wget \
  --input-file="$TMP_URLS" \
  --directory-prefix="$OUTPUT_DIR" \
  --content-disposition \
  --trust-server-names \
  --continue \
  --no-verbose \
  --https-only \
  --no-directories \
  --user-agent="$USER_AGENT" \
  --timeout=30 \
  --tries=3 \
  --wait=1 \
  --random-wait

rm -f "$TMP_URLS"

echo "[+] Done"
