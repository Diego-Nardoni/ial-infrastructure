import json
import os
import boto3
import yaml
import requests
from typing import Dict, Any, List
from datetime import datetime
from core.decision_ledger import DecisionLedger

class FinOpsMCP:
    """
    FinOps MCP - Controle de custos e otimização financeira
    - estimate_costs: heurística/Cost Explorer para estimativas
    - check_budget: compara com limites configurados
    - suggest_rightsizing: sugestões de otimização
    """
    
    def __init__(self):
        self.ledger = DecisionLedger()
        self.ce = None
        
        # Initialize Cost Explorer if enabled
        if os.getenv("FINOPS_USE_COST_EXPLORER", "false").lower() == "true":
            try:
                self.ce = boto3.client("ce")
            except Exception as e:
                print(f"⚠️ Cost Explorer not available: {e}")
        
        # Load governance config
        self.config = self._load_governance_config()
    
    def estimate_costs(self, phase: str) -> Dict[str, Any]:
        """Estimate monthly costs for a phase"""
        
        if self.ce:
            # Use real Cost Explorer data
            estimate = self._get_cost_explorer_estimate(phase)
        else:
            # Use heuristic estimation
            estimate = self._get_heuristic_estimate(phase)
        
        # Log decision
        self.ledger.log(
            phase=phase,
            mcp="finops",
            tool="estimate",
            rationale=f"Estimated ${estimate['monthly_usd']:.2f}/month",
            status="COMPLETED"
        )
        
        return estimate
    
    def check_budget(self, phase: str, limit: float = None) -> Dict[str, Any]:
        """Check if phase costs are within budget"""
        
        # Get configured limit if not provided
        if limit is None:
            limit = self._get_phase_budget(phase)
        
        # Get cost estimate
        estimate = self.estimate_costs(phase)
        estimated_cost = estimate["monthly_usd"]
        
        # Check against budget
        within_budget = estimated_cost <= limit
        status = "PASS" if within_budget else "BLOCK"
        
        result = {
            "phase": phase,
            "estimated_cost": estimated_cost,
            "budget_limit": limit,
            "within_budget": within_budget,
            "status": status,
            "overage": max(0, estimated_cost - limit),
            "utilization_percent": (estimated_cost / limit * 100) if limit > 0 else 0
        }
        
        # Log decision
        self.ledger.log(
            phase=phase,
            mcp="finops",
            tool="budget_check",
            rationale=f"Budget check: ${estimated_cost:.2f} vs ${limit:.2f} limit",
            status=status
        )
        
        # Save report
        self._save_budget_report(result)
        
        return result
    
    def suggest_rightsizing(self, phase: str) -> Dict[str, Any]:
        """Suggest cost optimization opportunities"""
        
        suggestions = []
        
        # Heuristic suggestions based on phase
        if "compute" in phase.lower():
            suggestions.extend([
                "Consider using Spot Instances for non-critical workloads",
                "Evaluate instance types - t3.micro may be sufficient for development",
                "Implement auto-scaling to optimize capacity utilization"
            ])
        
        if "storage" in phase.lower() or "data" in phase.lower():
            suggestions.extend([
                "Use S3 Intelligent Tiering for automatic cost optimization",
                "Consider EBS gp3 volumes instead of gp2 for better price/performance",
                "Implement lifecycle policies for log retention"
            ])
        
        if "network" in phase.lower():
            suggestions.extend([
                "Optimize data transfer costs with CloudFront",
                "Consider VPC endpoints to reduce NAT Gateway costs"
            ])
        
        result = {
            "phase": phase,
            "suggestions": suggestions,
            "potential_savings_percent": 15  # Heuristic estimate
        }
        
        # Log decision
        self.ledger.log(
            phase=phase,
            mcp="finops",
            tool="rightsizing",
            rationale=f"Generated {len(suggestions)} optimization suggestions",
            status="COMPLETED"
        )
        
        return result
    
    def _load_governance_config(self) -> Dict:
        """Load governance configuration"""
        config_path = "config/governance.yaml"
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        
        # Default config
        return {
            "budget": {
                "default_monthly_usd": 100.0,
                "by_phase": {}
            }
        }
    
    def _get_phase_budget(self, phase: str) -> float:
        """Get budget limit for a phase"""
        phase_budgets = self.config.get("budget", {}).get("by_phase", {})
        default_budget = self.config.get("budget", {}).get("default_monthly_usd", 100.0)
        
        return phase_budgets.get(phase, default_budget)
    
    def _get_cost_explorer_estimate(self, phase: str) -> Dict[str, Any]:
        """Get cost estimate using Cost Explorer"""
        # Placeholder for real Cost Explorer integration
        return {
            "phase": phase,
            "monthly_usd": 45.0,
            "source": "cost_explorer",
            "confidence": "high"
        }
    
    def _get_heuristic_estimate(self, phase: str) -> Dict[str, Any]:
        """Get heuristic cost estimate"""
        
        # Simple heuristic based on phase type
        base_costs = {
            "foundation": 20.0,
            "security": 15.0,
            "network": 30.0,
            "compute": 50.0,
            "data": 40.0,
            "application": 35.0
        }
        
        # Find matching phase
        estimated_cost = 25.0  # default
        for phase_type, cost in base_costs.items():
            if phase_type in phase.lower():
                estimated_cost = cost
                break
        
        return {
            "phase": phase,
            "monthly_usd": estimated_cost,
            "source": "heuristic",
            "confidence": "medium"
        }
    
    def check_budget_enforcement(self, phases: List[str], deployment_type: str = "full") -> Dict[str, Any]:
        """Check budget enforcement for multiple phases - blocks deployment if exceeded"""
        
        total_estimated = 0.0
        total_limit = 0.0
        phase_results = []
        blocked_phases = []
        
        for phase in phases:
            result = self.check_budget(phase)
            phase_results.append(result)
            
            total_estimated += result["estimated_cost"]
            total_limit += result["budget_limit"]
            
            if not result["within_budget"]:
                blocked_phases.append(phase)
        
        # Overall enforcement decision
        enforcement_status = "BLOCK" if blocked_phases else "PASS"
        
        enforcement_result = {
            "deployment_type": deployment_type,
            "total_phases": len(phases),
            "total_estimated_cost": total_estimated,
            "total_budget_limit": total_limit,
            "enforcement_status": enforcement_status,
            "blocked_phases": blocked_phases,
            "phase_results": phase_results,
            "timestamp": datetime.now().isoformat(),
            "can_proceed": len(blocked_phases) == 0
        }
        
        # Log enforcement decision
        self.ledger.log(
            phase=f"deployment-{deployment_type}",
            mcp="finops",
            tool="budget_enforcement",
            rationale=f"Budget enforcement: {enforcement_status} - ${total_estimated:.2f} vs ${total_limit:.2f}",
            status=enforcement_status
        )
        
        # Save enforcement report
        self._save_enforcement_report(enforcement_result)
        
        return enforcement_result
    
    def generate_cost_report(self, phases: List[str], pr_number: str = None) -> Dict[str, Any]:
        """Generate comprehensive cost report for PR commenting"""
        
        phase_estimates = []
        total_cost = 0.0
        
        for phase in phases:
            estimate = self.estimate_costs(phase)
            suggestions = self.suggest_rightsizing(phase)
            
            phase_info = {
                "phase": phase,
                "estimated_monthly_cost": estimate["monthly_usd"],
                "confidence": estimate["confidence"],
                "optimization_suggestions": suggestions["suggestions"][:2],  # Top 2 suggestions
                "potential_savings": f"{suggestions['potential_savings_percent']}%"
            }
            
            phase_estimates.append(phase_info)
            total_cost += estimate["monthly_usd"]
        
        # Generate report
        report = {
            "pr_number": pr_number,
            "total_estimated_monthly_cost": total_cost,
            "phase_count": len(phases),
            "phase_estimates": phase_estimates,
            "report_timestamp": datetime.now().isoformat(),
            "summary": {
                "high_cost_phases": [p for p in phase_estimates if p["estimated_monthly_cost"] > 50],
                "optimization_opportunities": sum(1 for p in phase_estimates if p["optimization_suggestions"]),
                "total_potential_savings": f"${total_cost * 0.15:.2f}/month"  # 15% heuristic
            }
        }
        
        # Save report
        self._save_cost_report(report)
        
        return report
    
    def comment_on_pr(self, pr_number: str, phases: List[str], github_token: str = None) -> Dict[str, Any]:
        """Generate and post cost estimate comment on GitHub PR"""
        
        if not github_token:
            github_token = os.getenv("GITHUB_TOKEN")
        
        if not github_token:
            return {"error": "GitHub token not available", "status": "SKIP"}
        
        # Generate cost report
        report = self.generate_cost_report(phases, pr_number)
        
        # Format comment
        comment = self._format_pr_comment(report)
        
        # Post to GitHub (if token available)
        try:
            result = self._post_github_comment(pr_number, comment, github_token)
            
            self.ledger.log(
                phase=f"pr-{pr_number}",
                mcp="finops",
                tool="pr_comment",
                rationale=f"Posted cost estimate comment: ${report['total_estimated_monthly_cost']:.2f}/month",
                status="COMPLETED"
            )
            
            return {"status": "SUCCESS", "comment_posted": True, "report": report}
            
        except Exception as e:
            return {"status": "ERROR", "error": str(e), "report": report}
    
    def _format_pr_comment(self, report: Dict[str, Any]) -> str:
        """Format cost report as GitHub PR comment"""
        
        comment = f"""## 💰 FinOps Cost Estimate

**Total Estimated Monthly Cost: ${report['total_estimated_monthly_cost']:.2f}**

### Phase Breakdown
| Phase | Monthly Cost | Confidence | Top Optimization |
|-------|-------------|------------|------------------|
"""
        
        for phase in report["phase_estimates"]:
            top_suggestion = phase["optimization_suggestions"][0] if phase["optimization_suggestions"] else "None"
            comment += f"| `{phase['phase']}` | ${phase['estimated_monthly_cost']:.2f} | {phase['confidence']} | {top_suggestion[:50]}... |\n"
        
        comment += f"""
### Summary
- 📊 **{report['phase_count']} phases** analyzed
- 🔥 **{len(report['summary']['high_cost_phases'])} high-cost phases** (>${50}/month)
- 💡 **{report['summary']['optimization_opportunities']} optimization opportunities** identified
- 💰 **Potential savings: {report['summary']['total_potential_savings']}**

### High-Cost Phases
"""
        
        if report["summary"]["high_cost_phases"]:
            for phase in report["summary"]["high_cost_phases"]:
                comment += f"- `{phase['phase']}`: ${phase['estimated_monthly_cost']:.2f}/month\n"
        else:
            comment += "✅ No high-cost phases detected\n"
        
        comment += f"""
---
*Generated by IAL FinOps MCP at {report['report_timestamp']}*
"""
        
        return comment
    
    def _post_github_comment(self, pr_number: str, comment: str, token: str) -> Dict[str, Any]:
        """Post comment to GitHub PR"""
        
        # Get repo info from environment or config
        repo_owner = os.getenv("GITHUB_REPOSITORY_OWNER", "Diego-Nardoni")
        repo_name = os.getenv("GITHUB_REPOSITORY_NAME", "ial-infrastructure")
        
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{pr_number}/comments"
        
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        data = {"body": comment}
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def _save_enforcement_report(self, data: Dict):
        """Save budget enforcement report"""
        report_path = f"reports/finops/enforcement_{data['deployment_type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"🚫 FinOps enforcement report saved: {report_path}")
    
    def _save_budget_report(self, data: Dict):
        """Save budget report"""
        report_path = f"reports/finops/budget_check.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Only print if not in CLI mode
        if not os.getenv("FINOPS_QUIET_MODE"):
            print(f"💰 FinOps budget report saved: {report_path}")
    
    def _save_cost_report(self, data: Dict):
        """Save cost report"""
        report_path = f"reports/finops/cost_report_{data.get('pr_number', 'manual')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Only print if not in CLI mode
        if not os.getenv("FINOPS_QUIET_MODE"):
            print(f"📊 FinOps cost report saved: {report_path}")
    
    def _save_enforcement_report(self, data: Dict):
        """Save budget enforcement report"""
        report_path = f"reports/finops/enforcement_{data['deployment_type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Only print if not in CLI mode
        if not os.getenv("FINOPS_QUIET_MODE"):
            print(f"🚫 FinOps enforcement report saved: {report_path}")

if __name__ == "__main__":
    import sys
    
    finops = FinOpsMCP()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "check_budget":
            phase = sys.argv[2] if len(sys.argv) > 2 else "global"
            limit = float(sys.argv[3]) if len(sys.argv) > 3 else None
            result = finops.check_budget(phase, limit)
            print(json.dumps(result, indent=2))
            
        elif command == "enforce_budget":
            phases = sys.argv[2].split(",") if len(sys.argv) > 2 else ["global"]
            deployment_type = sys.argv[3] if len(sys.argv) > 3 else "full"
            result = finops.check_budget_enforcement(phases, deployment_type)
            print(json.dumps(result, indent=2))
            
        elif command == "cost_report":
            phases = sys.argv[2].split(",") if len(sys.argv) > 2 else ["global"]
            pr_number = sys.argv[3] if len(sys.argv) > 3 else None
            result = finops.generate_cost_report(phases, pr_number)
            print(json.dumps(result, indent=2))
            
        elif command == "comment_pr":
            pr_number = sys.argv[2] if len(sys.argv) > 2 else "1"
            phases = sys.argv[3].split(",") if len(sys.argv) > 3 else ["global"]
            result = finops.comment_on_pr(pr_number, phases)
            print(json.dumps(result, indent=2))
            
        else:
            print(json.dumps({"error": f"Unknown command: {command}"}))
    else:
        print(json.dumps({"ok": True, "available_commands": ["check_budget", "enforce_budget", "cost_report", "comment_pr"]}))
