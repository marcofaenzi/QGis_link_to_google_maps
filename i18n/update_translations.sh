#!/usr/bin/env bash
set -euo pipefail

# Update and compile translations for LinkToGoogleMaps plugin
# Requirements: pylupdate5, lrelease (Qt tools)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "Updating TS files from Python sources..."
pylupdate5 "${PLUGIN_DIR}/link_google_maps_plugin.py" -ts \
  "${SCRIPT_DIR}/LinkToGoogleMaps_en.ts" \
  "${SCRIPT_DIR}/LinkToGoogleMaps_it.ts"

echo "Compiling QM files..."
mkdir -p "${SCRIPT_DIR}"
lrelease "${SCRIPT_DIR}/LinkToGoogleMaps_it.ts" -qm "${SCRIPT_DIR}/LinkToGoogleMaps_it.qm"
# English is source language; en.qm is optional. Uncomment if needed:
# lrelease "${SCRIPT_DIR}/LinkToGoogleMaps_en.ts" -qm "${SCRIPT_DIR}/LinkToGoogleMaps_en.qm"

echo "Done."


