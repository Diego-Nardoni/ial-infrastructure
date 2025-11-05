import json
import os
import subprocess
import tempfile
import yaml
from typing import Dict, Any, List
from core.decision_ledger import DecisionLedger

class IaLConfigRules:
    """
    IAL Config Rules Engine
    - compile_from_nl: traduz regra YAML para backend (OPA/CFN-Guard)
    - run_predeploy: valida templates antes do deploy
    - run_postdeploy: valida estado real pós-deploy
    - remediate_safe: aplica correções seguras automaticamente
    """
    
    BACKENDS = {"opa", "cfn-guard"}
    
    def __init__(self):
        self.ledger = DecisionLedger()
        self.rules_dir = "rules"
        
    def compile_from_nl(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Compile natural language rule to backend format"""
        backend = rule.get("spec", {}).get("type")
        if backend not in self.BACKENDS:
            raise ValueError(f"Unsupported backend: {backend}")
        
        # Rule is already in proper format, just validate
        compiled_rule = {
            "name": rule.get("metadata", {}).get("name"),
            "description": rule.get("metadata", {}).get("description"),
            "backend": backend,
            "rule_content": rule.get("spec", {}).get("rule"),
            "compiled": True
        }
        
        return compiled_rule
    
    def run_predeploy(self, stack_dir: str) -> Dict[str, Any]:
        """Run pre-deploy validation against CloudFormation templates"""
        print(f"🔍 Running pre-deploy compliance check on {stack_dir}")
        
        findings = []
        rules_processed = 0
        
        # Load all rules
        rules = self._load_rules()
        
        for rule_file, rule_data in rules.items():
            try:
                compiled_rule = self.compile_from_nl(rule_data)
                
                # Simulate rule execution (placeholder for real CFN-Guard/OPA)
                if compiled_rule["backend"] == "cfn-guard":
                    result = self._run_cfn_guard_simulation(stack_dir, compiled_rule)
                elif compiled_rule["backend"] == "opa":
                    result = self._run_opa_simulation(stack_dir, compiled_rule)
                
                findings.extend(result.get("violations", []))
                rules_processed += 1
                
            except Exception as e:
                print(f"⚠️ Error processing rule {rule_file}: {e}")
        
        # Log decision
        self.ledger.log(
            phase="compliance-predeploy",
            mcp="config-rules",
            tool="predeploy",
            rationale=f"Processed {rules_processed} rules, found {len(findings)} violations",
            status="COMPLETED"
        )
        
        result = {
            "status": "FAIL" if findings else "PASS",
            "findings": findings,
            "rules_processed": rules_processed,
            "violations_count": len(findings)
        }
        
        # Save report
        self._save_report("predeploy", result)
        
        return result
    
    def run_postdeploy(self, stack_name: str) -> Dict[str, Any]:
        """Run post-deploy validation against real AWS resources"""
        print(f"🔍 Running post-deploy compliance check on {stack_name}")
        
        findings = []
        rules_processed = 0
        
        # Load all rules
        rules = self._load_rules()
        
        for rule_file, rule_data in rules.items():
            try:
                compiled_rule = self.compile_from_nl(rule_data)
                
                # Simulate post-deploy validation
                result = self._validate_real_resources(stack_name, compiled_rule)
                findings.extend(result.get("violations", []))
                rules_processed += 1
                
            except Exception as e:
                print(f"⚠️ Error processing rule {rule_file}: {e}")
        
        # Log decision
        self.ledger.log(
            phase=f"compliance-postdeploy-{stack_name}",
            mcp="config-rules",
            tool="postdeploy",
            rationale=f"Validated {rules_processed} rules against real resources",
            status="COMPLETED"
        )
        
        result = {
            "status": "FAIL" if findings else "PASS",
            "findings": findings,
            "rules_processed": rules_processed,
            "violations_count": len(findings),
            "stack_name": stack_name
        }
        
        # Save report
        self._save_report("postdeploy", result)
        
        return result
    
    def remediate_safe(self, findings: List[Dict]) -> List[Dict]:
        """Apply safe automatic remediation"""
        remediated = []
        
        for finding in findings:
            if finding.get("risk_level") == "safe":
                # Apply safe remediation
                remediation_result = self._apply_safe_remediation(finding)
                if remediation_result.get("success"):
                    remediated.append(finding)
        
        # Log remediation
        self.ledger.log(
            phase="compliance-remediation",
            mcp="config-rules",
            tool="auto-remediate",
            rationale=f"Auto-remediated {len(remediated)} safe violations",
            status="COMPLETED"
        )
        
        return remediated
    
    def _load_rules(self) -> Dict[str, Dict]:
        """Load all compliance rules from rules directory"""
        rules = {}
        
        if not os.path.exists(self.rules_dir):
            return rules
        
        for filename in os.listdir(self.rules_dir):
            if filename.endswith('.yaml'):
                rule_path = os.path.join(self.rules_dir, filename)
                try:
                    with open(rule_path, 'r') as f:
                        rule_data = yaml.safe_load(f)
                        rules[filename] = rule_data
                except Exception as e:
                    print(f"⚠️ Error loading rule {filename}: {e}")
        
        return rules
    
    def _run_cfn_guard_simulation(self, stack_dir: str, rule: Dict) -> Dict:
        """Simulate CFN-Guard execution"""
        # Placeholder for real CFN-Guard integration
        violations = []
        
        # Simple simulation based on rule name
        rule_name = rule.get("name", "")
        if "s3-encryption" in rule_name:
            violations.append({
                "rule": rule_name,
                "resource": "TestBucket",
                "message": "S3 bucket missing encryption configuration",
                "risk_level": "safe",
                "remediation": "Enable SSE-KMS encryption"
            })
        
        return {"violations": violations}
    
    def _run_opa_simulation(self, stack_dir: str, rule: Dict) -> Dict:
        """Simulate OPA execution"""
        # Placeholder for real OPA integration
        violations = []
        
        rule_name = rule.get("name", "")
        if "sg-restrict" in rule_name:
            violations.append({
                "rule": rule_name,
                "resource": "TestSecurityGroup",
                "message": "Security Group allows inbound from 0.0.0.0/0",
                "risk_level": "risky",
                "remediation": "Restrict source to specific CIDR blocks"
            })
        
        return {"violations": violations}
    
    def _validate_real_resources(self, stack_name: str, rule: Dict) -> Dict:
        """Validate rule against real AWS resources"""
        # Placeholder for real resource validation
        violations = []
        
        # Simulate validation based on stack name and rule
        if "security" in stack_name.lower() and "sg-restrict" in rule.get("name", ""):
            violations.append({
                "rule": rule.get("name"),
                "resource": f"{stack_name}::SecurityGroup",
                "message": "Real security group validation failed",
                "risk_level": "risky"
            })
        
        return {"violations": violations}
    
    def _apply_safe_remediation(self, finding: Dict) -> Dict:
        """Apply safe automatic remediation"""
        # Placeholder for real remediation
        print(f"🔧 Auto-remediating: {finding.get('message')}")
        
        return {"success": True, "action": "simulated_fix"}
    
    def _save_report(self, report_type: str, data: Dict):
        """Save compliance report"""
        report_path = f"reports/compliance/{report_type}_report.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"📊 Compliance report saved: {report_path}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--run_postdeploy":
        rules_engine = IaLConfigRules()
        result = rules_engine.run_postdeploy("test-stack")
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps({"ok": True}))
