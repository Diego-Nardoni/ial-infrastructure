#!/bin/bash
# Policy as Code Validation Script

set -e

echo "🔐 Running Policy as Code Validation..."

# Install conftest if not present
if ! command -v conftest &> /dev/null; then
    echo "📦 Installing conftest..."
    curl -L https://github.com/open-policy-agent/conftest/releases/latest/download/conftest_Linux_x86_64.tar.gz | tar xz
    sudo mv conftest /usr/local/bin/
fi

# Validate all phases
POLICY_DIR="/home/ial/tools/policy-validation"
PHASES_DIR="/home/ial/phases"
VIOLATIONS=0

echo "📋 Validating CloudFormation templates..."

for phase_file in "$PHASES_DIR"/*.yaml; do
    if [[ -f "$phase_file" ]]; then
        phase_name=$(basename "$phase_file")
        echo "🔍 Validating $phase_name..."
        
        # Run conftest validation
        if conftest verify --policy "$POLICY_DIR/conftest-policies.rego" "$phase_file" 2>/dev/null; then
            echo "  ✅ $phase_name - No policy violations"
        else
            echo "  ⚠️ $phase_name - Policy violations found:"
            conftest verify --policy "$POLICY_DIR/conftest-policies.rego" "$phase_file" 2>&1 | grep -E "WARN|FAIL" | sed 's/^/    /'
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    fi
done

echo ""
echo "📊 Policy Validation Summary:"
echo "  Total phases checked: $(ls "$PHASES_DIR"/*.yaml | wc -l)"
echo "  Phases with violations: $VIOLATIONS"

if [ $VIOLATIONS -eq 0 ]; then
    echo "  🏆 All policies compliant!"
    exit 0
else
    echo "  ⚠️ $VIOLATIONS phases have policy violations"
    echo "  Review and fix violations before deployment"
    exit 1
fi
