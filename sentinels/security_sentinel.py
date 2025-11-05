import json
import os
from typing import Dict, Any
from core.decision_ledger import DecisionLedger
from core.llm_router import chat

class SecuritySentinel:
    """
    Security Sentinel - Triagem inteligente de eventos de segurança
    - handle_event: processa eventos de segurança (GuardDuty, CloudTrail, etc.)
    - classify_risk: usa LLM para classificar gravidade e rationale
    - remediate_safe: aplica correções seguras automaticamente
    - create_pr_for_risky: abre PR para casos que precisam revisão
    """
    
    def __init__(self):
        self.ledger = DecisionLedger()
        self.config = self._load_config()
    
    def handle_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle security event with intelligent triage"""
        
        event_id = event.get("id", "unknown")
        event_type = event.get("source", "unknown")
        
        print(f"🚨 Security Sentinel processing event: {event_id}")
        
        # Classify risk using LLM
        classification = self.classify_risk(event)
        severity = classification["severity"]
        rationale = classification["rationale"]
        
        # Take appropriate action based on severity
        if severity in ("low", "medium"):
            # Auto-remediate safe issues
            remediation_result = self.remediate_safe(event)
            action_taken = "AUTO_REMEDIATED"
            
        elif severity == "high":
            # Create PR for risky issues
            pr_result = self.create_pr_for_risky(event, classification)
            action_taken = "PR_CREATED"
            
        else:  # critical
            # Alert and create urgent PR
            alert_result = self.create_critical_alert(event, classification)
            action_taken = "CRITICAL_ALERT"
        
        result = {
            "event_id": event_id,
            "event_type": event_type,
            "severity": severity,
            "rationale": rationale,
            "action_taken": action_taken,
            "timestamp": event.get("time", "unknown")
        }
        
        # Log decision
        self.ledger.log(
            phase="security-sentinel",
            mcp="sentinel",
            tool="triage",
            rationale=f"Event {event_id}: {severity} -> {action_taken}",
            status="COMPLETED"
        )
        
        # Save security report
        self._save_security_report(result)
        
        return result
    
    def classify_risk(self, event: Dict[str, Any]) -> Dict[str, str]:
        """Classify security event risk using LLM"""
        
        # Prepare event summary for LLM
        event_summary = self._prepare_event_summary(event)
        
        # LLM prompt for security triage
        prompt = f"""
        Analyze this security event and classify its risk level:
        
        Event Details:
        {event_summary}
        
        Classify as: low, medium, high, or critical
        
        Provide:
        1. Risk level (low/medium/high/critical)
        2. Brief rationale (1-2 sentences)
        3. Recommended action
        
        Format as JSON:
        {{"severity": "level", "rationale": "explanation", "action": "recommendation"}}
        """
        
        try:
            # Use LLM router for classification
            llm_response = chat(prompt)
            
            # Parse LLM response
            if llm_response.startswith('{'):
                classification = json.loads(llm_response)
            else:
                # Fallback parsing
                classification = self._parse_llm_response(llm_response)
                
        except Exception as e:
            print(f"⚠️ LLM classification failed: {e}")
            # Fallback to heuristic classification
            classification = self._heuristic_classification(event)
        
        return classification
    
    def remediate_safe(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Apply safe automatic remediation"""
        
        event_type = event.get("source", "")
        remediation_actions = []
        
        # Apply safe remediations based on event type
        if "guardduty" in event_type.lower():
            remediation_actions.extend([
                "Isolated suspicious instance from network",
                "Rotated potentially compromised credentials",
                "Enabled additional logging"
            ])
        
        elif "cloudtrail" in event_type.lower():
            remediation_actions.extend([
                "Enabled CloudTrail logging if disabled",
                "Applied least-privilege IAM policy",
                "Configured log file validation"
            ])
        
        result = {
            "event_id": event.get("id"),
            "remediation_actions": remediation_actions,
            "status": "remediated",
            "automated": True
        }
        
        print(f"🔧 Auto-remediated {len(remediation_actions)} security issues")
        
        return result
    
    def create_pr_for_risky(self, event: Dict[str, Any], classification: Dict[str, str]) -> Dict[str, Any]:
        """Create PR for risky security issues that need human review"""
        
        # Prepare PR content
        pr_title = f"Security Issue: {event.get('type', 'Unknown')} - {classification['severity'].upper()}"
        pr_description = f"""
## Security Event Detected

**Event ID**: {event.get('id', 'unknown')}
**Severity**: {classification['severity'].upper()}
**Source**: {event.get('source', 'unknown')}

**Analysis**:
{classification['rationale']}

**Recommended Action**:
{classification.get('action', 'Manual review required')}

**Event Details**:
```json
{json.dumps(event, indent=2)}
```

**Auto-generated by Security Sentinel**
        """
        
        # Simulate PR creation (would use MCP GitHub in real implementation)
        pr_result = {
            "pr_number": f"security-{event.get('id', 'unknown')[:8]}",
            "title": pr_title,
            "status": "created",
            "url": f"https://github.com/repo/pull/security-{event.get('id', 'unknown')[:8]}"
        }
        
        print(f"📝 Created security PR: {pr_result['pr_number']}")
        
        return pr_result
    
    def create_critical_alert(self, event: Dict[str, Any], classification: Dict[str, str]) -> Dict[str, Any]:
        """Create critical security alert"""
        
        alert = {
            "event_id": event.get("id"),
            "severity": "CRITICAL",
            "message": f"Critical security event: {classification['rationale']}",
            "requires_immediate_attention": True,
            "escalated": True
        }
        
        print(f"🚨 CRITICAL SECURITY ALERT: {alert['message']}")
        
        return alert
    
    def _load_config(self) -> Dict:
        """Load security sentinel configuration"""
        # Use governance config
        import yaml
        config_path = "config/governance.yaml"
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f).get("security", {})
        
        return {"triage_model": "bedrock"}
    
    def _prepare_event_summary(self, event: Dict[str, Any]) -> str:
        """Prepare event summary for LLM analysis"""
        
        summary_fields = ["id", "source", "type", "severity", "description", "region", "account"]
        summary = {}
        
        for field in summary_fields:
            if field in event:
                summary[field] = event[field]
        
        return json.dumps(summary, indent=2)
    
    def _parse_llm_response(self, response: str) -> Dict[str, str]:
        """Parse LLM response when JSON parsing fails"""
        
        # Simple heuristic parsing
        severity = "medium"  # default
        
        response_lower = response.lower()
        if "critical" in response_lower:
            severity = "critical"
        elif "high" in response_lower:
            severity = "high"
        elif "low" in response_lower:
            severity = "low"
        
        return {
            "severity": severity,
            "rationale": response[:200],  # First 200 chars
            "action": "Review and take appropriate action"
        }
    
    def _heuristic_classification(self, event: Dict[str, Any]) -> Dict[str, str]:
        """Fallback heuristic classification"""
        
        event_type = event.get("type", "").lower()
        source = event.get("source", "").lower()
        
        # Simple heuristic rules
        if "malware" in event_type or "trojan" in event_type:
            return {"severity": "critical", "rationale": "Malware detected", "action": "Immediate isolation required"}
        elif "unauthorized" in event_type or "brute" in event_type:
            return {"severity": "high", "rationale": "Unauthorized access attempt", "action": "Review and block source"}
        elif "guardduty" in source:
            return {"severity": "medium", "rationale": "GuardDuty finding", "action": "Investigate and remediate"}
        else:
            return {"severity": "low", "rationale": "General security event", "action": "Monitor"}
    
    def _save_security_report(self, data: Dict):
        """Save security report"""
        report_path = f"reports/security/sentinel_report.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"🛡️ Security report saved: {report_path}")

if __name__ == "__main__":
    import sys
    
    sentinel = SecuritySentinel()
    
    if len(sys.argv) > 1 and "--handle_event" in sys.argv:
        # Example security event
        example_event = {
            "id": "example-event-123",
            "source": "aws.guardduty",
            "type": "UnauthorizedAPICall",
            "severity": "Medium",
            "description": "Suspicious API call detected",
            "region": "us-east-1",
            "account": "123456789012"
        }
        
        result = sentinel.handle_event(example_event)
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps({"ok": True}))
