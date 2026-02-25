#!/bin/bash
# One-command local report generation
# Usage: ./run_reports.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HISTORY_DIR="$SCRIPT_DIR/../2025_10 Afore JSON cleanup"

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
PYTHONPATH=. python3 -m reports.generate_reports

echo ""
echo "=== Done ==="
echo "Reports saved to: $SCRIPT_DIR/output/"
ls -la "$SCRIPT_DIR/output/"*.pdf 2>/dev/null
