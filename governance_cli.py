#!/usr/bin/env python3
import sys
import json
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from compliance.ial_config_rules import IaLConfigRules
from mcp.finops.server import FinOpsMCP
from sentinels.security_sentinel import SecuritySentinel

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 governance_cli.py <command> [args]")
        print("Commands:")
        print("  compliance-check <stack_dir> - Run compliance check")
        print("  budget-check <phase> [limit] - Check budget for phase")
        print("  security-event <event_json> - Process security event")
        print("  full-governance <phase> - Run full governance check")
        return
    
    command = sys.argv[1]
    
    if command == "compliance-check":
        if len(sys.argv) < 3:
            print("Usage: python3 governance_cli.py compliance-check <stack_dir>")
            return
        
        stack_dir = sys.argv[2]
        print(f"🔍 Running compliance check on {stack_dir}")
        
        config_rules = IaLConfigRules()
        result = config_rules.run_predeploy(stack_dir)
        
        print(f"📊 Compliance Result:")
        print(f"  Status: {result['status']}")
        print(f"  Rules Processed: {result['rules_processed']}")
        print(f"  Violations: {result['violations_count']}")
        
        if result['findings']:
            print("  Findings:")
            for finding in result['findings'][:3]:  # Show first 3
                print(f"    - {finding.get('rule')}: {finding.get('message')}")
        
    elif command == "budget-check":
        if len(sys.argv) < 3:
            print("Usage: python3 governance_cli.py budget-check <phase> [limit]")
            return
        
        phase = sys.argv[2]
        limit = float(sys.argv[3]) if len(sys.argv) > 3 else None
        
        print(f"💰 Checking budget for phase: {phase}")
        
        finops = FinOpsMCP()
        result = finops.check_budget(phase, limit)
        
        print(f"📊 Budget Result:")
        print(f"  Phase: {result['phase']}")
        print(f"  Estimated Cost: ${result['estimated_cost']:.2f}/month")
        print(f"  Budget Limit: ${result['budget_limit']:.2f}/month")
        print(f"  Status: {result['status']}")
        print(f"  Within Budget: {result['within_budget']}")
        
        if result['overage'] > 0:
            print(f"  ⚠️ Overage: ${result['overage']:.2f}")
        
    elif command == "security-event":
        if len(sys.argv) < 3:
            print("Usage: python3 governance_cli.py security-event <event_json>")
            return
        
        event_data = json.loads(sys.argv[2])
        print(f"🚨 Processing security event: {event_data.get('id', 'unknown')}")
        
        sentinel = SecuritySentinel()
        result = sentinel.handle_event(event_data)
        
        print(f"📊 Security Result:")
        print(f"  Event ID: {result['event_id']}")
        print(f"  Severity: {result['severity']}")
        print(f"  Action Taken: {result['action_taken']}")
        print(f"  Rationale: {result['rationale']}")
        
    elif command == "full-governance":
        if len(sys.argv) < 3:
            print("Usage: python3 governance_cli.py full-governance <phase>")
            return
        
        phase = sys.argv[2]
        print(f"🏛️ Running full governance check for phase: {phase}")
        
        # 1. Compliance Check
        print("\n1️⃣ Compliance Check...")
        config_rules = IaLConfigRules()
        compliance_result = config_rules.run_predeploy(f"phases/{phase}")
        print(f"   Status: {compliance_result['status']} ({compliance_result['violations_count']} violations)")
        
        # 2. Budget Check
        print("\n2️⃣ Budget Check...")
        finops = FinOpsMCP()
        budget_result = finops.check_budget(phase)
        print(f"   Status: {budget_result['status']} (${budget_result['estimated_cost']:.2f}/${budget_result['budget_limit']:.2f})")
        
        # 3. Rightsizing Suggestions
        print("\n3️⃣ Rightsizing Suggestions...")
        rightsizing_result = finops.suggest_rightsizing(phase)
        print(f"   Suggestions: {len(rightsizing_result['suggestions'])}")
        for suggestion in rightsizing_result['suggestions'][:2]:
            print(f"     - {suggestion}")
        
        # 4. Overall Status
        print("\n📋 Overall Governance Status:")
        overall_pass = compliance_result['status'] == 'PASS' and budget_result['status'] == 'PASS'
        print(f"   Status: {'✅ PASS' if overall_pass else '❌ FAIL'}")
        
        if not overall_pass:
            print("   🚫 Deployment would be blocked due to governance violations")
        
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
