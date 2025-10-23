#!/bin/bash
set -e

echo "🧪 Testing Drift Detection..."

python scripts/detect-drift.py > /tmp/drift.log 2>&1

if grep -q "No drifts detected\|Detected.*drifts" /tmp/drift.log; then
    echo "✅ Drift Detection PASSED"
    exit 0
else
    echo "❌ Drift Detection FAILED"
    exit 1
fi
