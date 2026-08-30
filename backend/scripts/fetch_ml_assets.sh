#!/usr/bin/env bash
# Fetch ML model + training data assets that are gitignored and therefore
# absent from the Render build. Run as part of the Render preDeploy/build.
#
# Set ML_ASSET_BASE_URL to a base URL holding:
#   models/delivery_failure_model_v2.pkl
#   models/label_encoders_v2.pkl
#   data/logistics_dataset_v3.csv
# e.g. ML_ASSET_BASE_URL=https://my-bucket.example.com/smart-logistics
#
# Also accepts individual *_URL vars. Skips files that already exist so the
# script is idempotent and does nothing if the files are already present.

set -euo pipefail

BASE="${ML_ASSET_BASE_URL:-}"
MODEL_URL="${MODEL_URL:-${BASE:+${BASE}/models/delivery_failure_model_v2.pkl}}"
ENCODER_URL="${ENCODER_URL:-${BASE:+${BASE}/models/label_encoders_v2.pkl}}"
DATA_URL="${DATA_URL:-${BASE:+${BASE}/data/logistics_dataset_v3.csv}}"

fetch() {
  local url="$1" dest="$2"
  if [ -z "$url" ]; then
    echo "[fetch-ml] no URL for ${dest}; skipping"
    return 0
  fi
  if [ -f "$dest" ]; then
    echo "[fetch-ml] already present: ${dest}"
    return 0
  fi
  mkdir -p "$(dirname "$dest")"
  echo "[fetch-ml] downloading ${url} -> ${dest}"
  curl -fsSL --retry 3 --retry-delay 2 -o "$dest.tmp" "$url"
  mv "$dest.tmp" "$dest"
}

# Resolve paths relative to this repo's backend dir.
BACKEND_DIR="$(cd "$(dirname "$0")/.." && pwd)"
fetch "$MODEL_URL"  "$BACKEND_DIR/models/delivery_failure_model_v2.pkl"
fetch "$ENCODER_URL" "$BACKEND_DIR/models/label_encoders_v2.pkl"
fetch "$DATA_URL"    "$BACKEND_DIR/data/logistics_dataset_v3.csv"

echo "[fetch-ml] done"
