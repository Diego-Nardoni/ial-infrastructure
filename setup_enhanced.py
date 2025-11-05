#!/usr/bin/env python3
"""
IaL Enhanced Setup - Support for Control Plane and Workloads separation
"""

import os
import sys
import subprocess
import json
import argparse
import yaml
from pathlib import Path
from datetime import datetime

class IaLEnhancedSetup:
    def __init__(self):
        self.phases_dir = Path("./phases")
        self.deployment_types = {
            'control_plane': 'deployment-control-plane.yaml',
            'workloads': 'deployment-workloads.yaml', 
            'full': 'deployment-order.yaml'
        }
        
    def load_deployment_order(self, deployment_type: str = 'full') -> dict:
        """Load deployment order based on type"""
        if deployment_type not in self.deployment_types:
            raise ValueError(f"Invalid deployment type: {deployment_type}")
            
        deployment_file = self.phases_dir / self.deployment_types[deployment_type]
        
        if not deployment_file.exists():
            raise FileNotFoundError(f"Deployment file not found: {deployment_file}")
            
        with open(deployment_file, 'r') as f:
            return yaml.safe_load(f)
            
    def deploy(self, deployment_type: str = 'full', dry_run: bool = False):
        """Execute deployment based on type"""
        print(f"🚀 Starting {deployment_type} deployment...")
        
        deployment_order = self.load_deployment_order(deployment_type)
        execution_order = deployment_order.get('execution_order', [])
        
        print(f"📋 Found {len(execution_order)} phases to deploy")
        
        if dry_run:
            print("🔍 DRY RUN - No actual deployment will occur")
            for phase in execution_order:
                print(f"  - {phase}")
            return
            
        # Call existing desired_state.py with filtered phases
        self.execute_deployment(execution_order, deployment_type)
        
    def execute_deployment(self, phases: list, deployment_type: str):
        """Execute the actual deployment"""
        print(f"⚡ Executing {deployment_type} deployment...")
        
        # Create temporary deployment order for this specific type
        temp_deployment = {
            'metadata': {
                'deployment_type': deployment_type,
                'generated_at': datetime.now().isoformat(),
                'total_phases': len(phases)
            },
            'execution_order': phases
        }
        
        temp_file = self.phases_dir / f"temp-{deployment_type}.yaml"
        with open(temp_file, 'w') as f:
            yaml.dump(temp_deployment, f, default_flow_style=False)
            
        try:
            # Call desired_state.py with the temporary deployment order
            cmd = [sys.executable, "core/desired_state.py", "--deployment-file", str(temp_file)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {deployment_type} deployment completed successfully")
            else:
                print(f"❌ {deployment_type} deployment failed:")
                print(result.stderr)
                
        finally:
            # Clean up temporary file
            if temp_file.exists():
                temp_file.unlink()
                
    def validate_prerequisites(self, deployment_type: str):
        """Validate prerequisites for deployment type"""
        if deployment_type == 'workloads':
            # Check if Control Plane is deployed
            print("🔍 Checking Control Plane prerequisites...")
            # Add validation logic here
            
        elif deployment_type == 'control_plane':
            # Check AWS credentials and basic setup
            print("🔍 Checking AWS prerequisites...")
            self.validate_aws_credentials()
            
            # Validate GitHub integration for GitOps
            self.validate_github_integration()
            
        # Add FinOps budget validation
        self.validate_finops_budget(deployment_type)
    
    def validate_aws_credentials(self):
        """Validate AWS credentials"""
        try:
            import boto3
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            print(f"✅ AWS Account: {identity['Account']}")
            print(f"✅ AWS User/Role: {identity['Arn']}")
        except Exception as e:
            print(f"❌ AWS credentials validation failed: {e}")
            raise
    
    def validate_github_integration(self):
        """Validate GitHub OIDC integration"""
        print("🔗 Validating GitHub integration...")
        
        try:
            import subprocess
            
            # Check if we're in a git repository
            result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("⚠️ Not in a git repository - GitHub integration may not work")
                return
            
            # Check if GitHub CLI is available
            result = subprocess.run(['gh', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("⚠️ GitHub CLI not found - install with: sudo apt install gh")
                return
            
            # Check GitHub authentication
            result = subprocess.run(['gh', 'auth', 'status'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("⚠️ GitHub not authenticated - run: gh auth login")
                return
            
            # Get current repository info
            result = subprocess.run(['gh', 'repo', 'view', '--json', 'nameWithOwner'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                import json
                repo_info = json.loads(result.stdout)
                repo_name = repo_info.get('nameWithOwner', 'unknown')
                print(f"✅ GitHub repository: {repo_name}")
                
                # Store repo info for OIDC configuration
                self.github_repo = repo_name
            else:
                print("⚠️ Could not determine GitHub repository")
                
        except Exception as e:
            print(f"⚠️ GitHub validation failed: {e}")
            
    def validate_finops_budget(self, deployment_type: str):
        """Validate FinOps budget before deployment"""
        print("💰 Validating FinOps budget...")
        
        try:
            # Load deployment order to get phases
            deployment_order = self.load_deployment_order(deployment_type)
            phases = deployment_order.get('execution_order', [])
            
            # Call FinOps MCP for budget enforcement
            import subprocess
            import json
            import os
            
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
                budget_result = json.loads(result.stdout)
                
                if budget_result["can_proceed"]:
                    print(f"✅ Budget validation passed: ${budget_result['total_estimated_cost']:.2f} within ${budget_result['total_budget_limit']:.2f} limit")
                else:
                    print(f"❌ Budget validation failed: ${budget_result['total_estimated_cost']:.2f} exceeds ${budget_result['total_budget_limit']:.2f} limit")
                    print(f"🚫 Blocked phases: {', '.join(budget_result['blocked_phases'])}")
                    raise Exception("Budget limit exceeded - deployment blocked")
            else:
                print(f"⚠️ Budget validation failed: {result.stderr}")
                
        except Exception as e:
            print(f"⚠️ FinOps budget validation error: {e}")
            # Continue deployment but warn user
            print("⚠️ Proceeding without budget validation")
            
    def status(self):
        """Show deployment status"""
        print("📊 IAL Deployment Status")
        print("=" * 40)
        
        for dep_type, dep_file in self.deployment_types.items():
            file_path = self.phases_dir / dep_file
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data = yaml.safe_load(f)
                    total_phases = data.get('metadata', {}).get('total_phases', 0)
                    print(f"  {dep_type:15}: {total_phases} phases available")
            else:
                print(f"  {dep_type:15}: Configuration not found")

def main():
    parser = argparse.ArgumentParser(description='IAL Enhanced Setup with Control Plane separation')
    parser.add_argument('--deployment-type', 
                       choices=['control_plane', 'workloads', 'full'],
                       default='full',
                       help='Type of deployment to execute')
    parser.add_argument('--dry-run', 
                       action='store_true',
                       help='Show what would be deployed without executing')
    parser.add_argument('--status',
                       action='store_true', 
                       help='Show deployment status')
    
    args = parser.parse_args()
    
    setup = IaLEnhancedSetup()
    
    if args.status:
        setup.status()
    else:
        setup.validate_prerequisites(args.deployment_type)
        setup.deploy(args.deployment_type, args.dry_run)

if __name__ == "__main__":
    main()
