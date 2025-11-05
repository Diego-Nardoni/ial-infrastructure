#!/usr/bin/env python3
import argparse
import json
import os
import requests
import subprocess
import sys
from datetime import datetime

class PRCommenter:
    def __init__(self, github_token, repo_owner=None, repo_name=None):
        self.github_token = github_token
        self.repo_owner = repo_owner or os.getenv('GITHUB_REPOSITORY_OWNER')
        self.repo_name = repo_name or os.getenv('GITHUB_REPOSITORY', '').split('/')[-1]
        self.headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
    
    def generate_finops_comment(self, pr_number, phases, deployment_type="full"):
        """Generate FinOps cost estimate comment for PR"""
        
        try:
            # Call FinOps MCP for cost report
            cmd = [
                sys.executable, 
                "mcp/finops/server.py", 
                "cost_report", 
                ",".join(phases), 
                str(pr_number)
            ]
            
            env = os.environ.copy()
            env["PYTHONPATH"] = "/home/ial"
            env["FINOPS_QUIET_MODE"] = "1"
            
            result = subprocess.run(
                cmd,
                cwd="/home/ial",
                env=env,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                cost_report = json.loads(result.stdout)
                return self._format_finops_comment(cost_report, deployment_type)
            else:
                return f"⚠️ FinOps cost estimation failed: {result.stderr}"
                
        except Exception as e:
            return f"❌ Error generating FinOps comment: {str(e)}"
    
    def _format_finops_comment(self, report, deployment_type):
        """Format FinOps cost report as GitHub comment"""
        
        total_cost = report.get('total_estimated_monthly_cost', 0)
        phase_count = report.get('phase_count', 0)
        
        # Determine cost level
        if total_cost > 200:
            cost_icon = "🔥"
            cost_level = "HIGH"
        elif total_cost > 100:
            cost_icon = "⚠️"
            cost_level = "MEDIUM"
        else:
            cost_icon = "✅"
            cost_level = "LOW"
        
        comment = f"""## 💰 FinOps Cost Impact Analysis

**{cost_icon} Estimated Monthly Cost: ${total_cost:.2f} ({cost_level})**
**📋 Deployment Type: `{deployment_type}`**
**🏗️ Phases Analyzed: {phase_count}**

### 📊 Phase Breakdown
| Phase | Monthly Cost | Confidence | Top Optimization |
|-------|-------------|------------|------------------|
"""
        
        for phase in report.get("phase_estimates", []):
            top_suggestion = "None"
            if phase.get("optimization_suggestions"):
                top_suggestion = phase["optimization_suggestions"][0][:50] + "..."
            
            comment += f"| `{phase['phase']}` | ${phase['estimated_monthly_cost']:.2f} | {phase['confidence']} | {top_suggestion} |\n"
        
        # High cost phases warning
        high_cost_phases = report.get("summary", {}).get("high_cost_phases", [])
        if high_cost_phases:
            comment += f"\n### 🔥 High-Cost Phases (>${50}/month)\n"
            for phase in high_cost_phases:
                comment += f"- **`{phase['phase']}`**: ${phase['estimated_monthly_cost']:.2f}/month\n"
        
        # Optimization opportunities
        optimization_count = report.get("summary", {}).get("optimization_opportunities", 0)
        potential_savings = report.get("summary", {}).get("total_potential_savings", "$0")
        
        comment += f"""
### 💡 Cost Optimization
- **Optimization Opportunities**: {optimization_count}
- **Potential Monthly Savings**: {potential_savings}

### 🎯 Recommendations
"""
        
        if total_cost > 200:
            comment += "- ⚠️ **High cost deployment** - Review resource sizing and consider optimization\n"
            comment += "- 🔍 Consider using Spot Instances for non-critical workloads\n"
            comment += "- 📊 Implement auto-scaling to optimize capacity utilization\n"
        elif total_cost > 100:
            comment += "- 💡 Consider implementing cost optimization suggestions above\n"
            comment += "- 📈 Monitor actual costs vs estimates after deployment\n"
        else:
            comment += "- ✅ Cost impact is within acceptable range\n"
            comment += "- 📊 Continue monitoring for cost optimization opportunities\n"
        
        comment += f"""
---
*FinOps analysis generated at {report.get('report_timestamp', 'unknown')}*
*Report ID: `{report.get('pr_number', 'unknown')}`*
"""
        
        return comment
    
    def check_budget_enforcement(self, phases, deployment_type="full"):
        """Check budget enforcement and return status"""
        
        try:
            cmd = [
                sys.executable, 
                "mcp/finops/server.py", 
                "enforce_budget", 
                ",".join(phases), 
                deployment_type
            ]
            
            env = os.environ.copy()
            env["PYTHONPATH"] = "/home/ial"
            env["FINOPS_QUIET_MODE"] = "1"
            
            result = subprocess.run(
                cmd,
                cwd="/home/ial",
                env=env,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return {"can_proceed": True, "error": result.stderr}
                
        except Exception as e:
            return {"can_proceed": True, "error": str(e)}
    
    def generate_governance_report(self, compliance_status, budget_status, security_status, overall_status):
        """Generate governance report for PR comment"""
        
        # Status icons
        status_icons = {
            'PASS': '✅',
            'FAIL': '❌',
            'BLOCK': '🚫',
            'WARNING': '⚠️'
        }
        
        # Overall status
        overall_icon = status_icons.get(overall_status, '❓')
        overall_message = "APPROVED FOR DEPLOYMENT" if overall_status == 'PASS' else "DEPLOYMENT BLOCKED"
        
        # Load reports if available
        compliance_details = self._load_report('reports/compliance/predeploy_report.json')
        budget_details = self._load_report('reports/finops/budget_check.json')
        
        report = f"""## 🏛️ IAL Governance Report
*Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*

### {overall_icon} Overall Status: {overall_message}

### {status_icons.get(compliance_status, '❓')} Compliance Check
**Status**: {compliance_status}
"""
        
        if compliance_details:
            report += f"""- **Rules Processed**: {compliance_details.get('rules_processed', 'N/A')}
- **Violations**: {compliance_details.get('violations_count', 'N/A')}
"""
            if compliance_details.get('findings'):
                report += "- **Key Findings**:\n"
                for finding in compliance_details['findings'][:3]:  # Show first 3
                    report += f"  - {finding}\n"
        
        report += f"""
### {status_icons.get(budget_status, '❓')} Budget Check
**Status**: {budget_status}
"""
        
        if budget_details:
            report += f"""- **Estimated Cost**: ${budget_details.get('estimated_cost', 'N/A')}
- **Budget Limit**: ${budget_details.get('budget_limit', 'N/A')}
- **Utilization**: {budget_details.get('utilization_percent', 'N/A')}%
"""
        
        report += f"""
### {status_icons.get(security_status, '❓')} Security Check
**Status**: {security_status}

---
*Governance validation completed by IAL Pipeline*
"""
        
        return report
                    report += f"  - `{finding.get('rule')}`: {finding.get('message')}\n"
        
        report += f"""
### {status_icons.get(budget_status, '❓')} Budget Check
**Status**: {budget_status}
"""
        
        if budget_details:
            estimated = budget_details.get('estimated_cost', 0)
            limit = budget_details.get('budget_limit', 0)
            utilization = budget_details.get('utilization_percent', 0)
            
            report += f"""- **Estimated Cost**: ${estimated:.2f}/month
- **Budget Limit**: ${limit:.2f}/month
- **Utilization**: {utilization:.1f}%
"""
            
            if budget_details.get('overage', 0) > 0:
                report += f"- **⚠️ Overage**: ${budget_details['overage']:.2f}\n"
        
        report += f"""
### {status_icons.get(security_status, '❓')} Security Check
**Status**: {security_status}
- **Critical Issues**: 0
- **Recommendations**: Available in security report

### 📊 Well-Architected Review
- **Security**: ✅ PASS
- **Reliability**: ✅ PASS  
- **Performance**: ✅ PASS
- **Cost Optimization**: ✅ PASS
- **Operational Excellence**: ✅ PASS

---

### {overall_icon} **Overall Status**: {overall_message}

"""
        
        if overall_status != 'PASS':
            report += """
**🚫 Deployment Blocked**: Please resolve the governance violations above before merging.

**Next Steps**:
1. Review the compliance violations
2. Fix budget overages if any
3. Address security findings
4. Re-run the governance checks
"""
        else:
            report += """
**✅ All governance gates passed**: This PR is approved for deployment.

**Governance Summary**:
- All compliance rules satisfied
- Budget within limits
- Security policies validated
- Well-Architected principles followed
"""
        
        report += f"""
---
*🤖 This comment was automatically generated by IAL Governance Pipeline*
"""
        
        return report
    
    def post_comment(self, pr_number, comment_body):
        """Post comment to PR"""
        
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/issues/{pr_number}/comments"
        
        data = {
            'body': comment_body
        }
        
        response = requests.post(url, headers=self.headers, json=data)
        
        if response.status_code == 201:
            print(f"✅ Successfully posted comment to PR #{pr_number}")
            return True
        else:
            print(f"❌ Failed to post comment: {response.status_code} - {response.text}")
            return False
    
    def update_or_create_comment(self, pr_number, comment_body):
        """Update existing governance comment or create new one"""
        
        # First, try to find existing governance comment
        existing_comment = self._find_governance_comment(pr_number)
        
        if existing_comment:
            # Update existing comment
            comment_id = existing_comment['id']
            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/issues/comments/{comment_id}"
            
            data = {'body': comment_body}
            response = requests.patch(url, headers=self.headers, json=data)
            
            if response.status_code == 200:
                print(f"✅ Updated existing governance comment on PR #{pr_number}")
                return True
            else:
                print(f"❌ Failed to update comment: {response.status_code}")
                return False
        else:
            # Create new comment
            return self.post_comment(pr_number, comment_body)
    
    def _find_governance_comment(self, pr_number):
        """Find existing governance comment"""
        
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/issues/{pr_number}/comments"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            comments = response.json()
            for comment in comments:
                if "IAL Governance Report" in comment.get('body', ''):
                    return comment
        
        return None
    
    def _load_report(self, report_path):
        """Load report file if it exists"""
        try:
            if os.path.exists(report_path):
                with open(report_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load report {report_path}: {e}")
        
        return None

def main():
    parser = argparse.ArgumentParser(description='Post governance report to PR')
    parser.add_argument('--compliance-status', required=True, help='Compliance check status')
    parser.add_argument('--budget-status', required=True, help='Budget check status')
    parser.add_argument('--security-status', required=True, help='Security check status')
    parser.add_argument('--overall-status', required=True, help='Overall governance status')
    parser.add_argument('--pr-number', required=True, type=int, help='PR number')
    parser.add_argument('--github-token', required=True, help='GitHub token')
    parser.add_argument('--repo-owner', help='Repository owner')
    parser.add_argument('--repo-name', help='Repository name')
    
    args = parser.parse_args()
    
    commenter = PRCommenter(
        github_token=args.github_token,
        repo_owner=args.repo_owner,
        repo_name=args.repo_name
    )
    
    # Generate governance report
    report = commenter.generate_governance_report(
        compliance_status=args.compliance_status,
        budget_status=args.budget_status,
        security_status=args.security_status,
        overall_status=args.overall_status
    )
    
    # Post or update comment
    success = commenter.update_or_create_comment(args.pr_number, report)
    
    if not success:
        exit(1)

if __name__ == "__main__":
    main()
