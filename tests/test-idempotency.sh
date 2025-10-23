#!/bin/bash
set -e

echo "🧪 Testing Idempotency..."

python scripts/reconcile.py > /tmp/run1.log 2>&1
python scripts/reconcile.py > /tmp/run2.log 2>&1

if grep -q "matches" /tmp/run2.log; then
    echo "✅ Idempotency PASSED"
    exit 0
else
    echo "❌ Idempotency FAILED"
    exit 1
fi
