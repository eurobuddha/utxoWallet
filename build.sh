#!/usr/bin/env bash
#
# Builds utxoWallet_<version>.mds.zip with dapp.conf as the literal first entry.
# (MDS install silently fails if dapp.conf is not first — per staticMLS/feedback_mds_zip_order.)
#
set -euo pipefail
cd "$(dirname "$0")"

VERSION="$(grep -Eo '"version"[[:space:]]*:[[:space:]]*"[^"]+"' dapp.conf | grep -Eo '[0-9][0-9A-Za-z.\-]*' | head -1)"
[ -z "${VERSION}" ] && { echo "Could not extract version from dapp.conf" >&2; exit 1; }
OUT="utxoWallet_${VERSION}.mds.zip"

rm -f "${OUT}"

# Step 1: dapp.conf MUST be the first entry in the archive.
zip -q "${OUT}" dapp.conf

# Step 2: everything else.
zip -q "${OUT}" index.html mds.js favicon.png

echo
echo "Archive contents (dapp.conf must be the first entry below):"
echo "----------------------------------------------------------"
unzip -l "${OUT}"
echo "----------------------------------------------------------"
echo "Built ${OUT}"
