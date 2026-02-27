#!/bin/bash
# One-command local report generation
# Usage: ./scripts/run_reports.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HISTORY_DIR="$SCRIPT_DIR/../consar-siefore-history"

echo "=== Pulling latest code ==="
cd "$SCRIPT_DIR"
git pull

echo ""
echo "=== Pulling latest database ==="
cd "$HISTORY_DIR"
git pull

echo ""
echo "=== Generating reports ==="
cd "$SCRIPT_DIR"
python -m consar.reports.generate

echo ""
echo "=== Done ==="
echo "Reports saved to: $SCRIPT_DIR/output/"
ls -la "$SCRIPT_DIR/output/"*.pdf 2>/dev/null
