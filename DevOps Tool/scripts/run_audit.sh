#!/bin/bash
# Run full audit: assets list, compliance, and change diff
set -e
cd "$(dirname "$0")/.."
export CSPM_SNAPSHOTS_DIR="${CSPM_SNAPSHOTS_DIR:-snapshots}"
echo "=== CSPM Audit ==="
echo "1. Running scan and saving snapshot..."
python -m cspm.cli scan aws --save-snapshot --output json > /dev/null
echo "2. Listing assets (JSON)..."
python -m cspm.cli assets list --cloud aws --output json | head -100
echo "3. Compliance (CIS)..."
python -m cspm.cli compliance --framework cis --output json
echo "4. Changes since last run..."
python -m cspm.cli changes --output json
