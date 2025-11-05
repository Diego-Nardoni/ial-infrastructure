#!/usr/bin/env python3
"""
IaL Advanced NLP Engine
Infrastructure-aware conversation processing with hybrid deployment
"""

import boto3
import json
import subprocess
from datetime import datetime
from typing import Dict, List, Optional

# Import hybrid deployment
try:
    from hybrid_deployment_engine import HybridDeploymentEngine
    HYBRID_DEPLOYMENT_AVAILABLE = True
except ImportError:
    HYBRID_DEPLOYMENT_AVAILABLE = False

class AdvancedNLPEngine:
    def __init__(self, region='us-east-1'):
        self.dynamodb = boto3.client('dynamodb', region_name=region)
        self.cloudformation = boto3.client('cloudformation', region_name=region)
        
        # Initialize hybrid deployment
        if HYBRID_DEPLOYMENT_AVAILABLE:
            self.hybrid_deployer = HybridDeploymentEngine()
        else:
            self.hybrid_deployer = None
        
        # Infrastructure knowledge base
        self.domain_knowledge = {
            'security': {
                'phases': ['kms-security', 'security-services', 'secrets-manager', 'iam-roles', 'iam-bedrock-github', 'waf-cloudfront'],
                'duration': 30,
                'dependencies': ['foundation'],
                'stack_prefix': 'ial-security'
            },
            'networking': {
                'phases': ['networking', 'vpc-flow-logs'],
                'duration': 20,
                'dependencies': ['foundation', 'security'],
                'stack_prefix': 'ial-networking'
            },
            'compute': {
                'phases': ['ecr', 'ecs-cluster', 'ecs-task-service', 'ecs-autoscaling', 'alb'],
                'duration': 35,
                'dependencies': ['foundation', 'security', 'networking'],
                'stack_prefix': 'ial-compute'
            },
            'data': {
                'phases': ['redis', 'aurora-postgresql', 'aurora-postgresql-secure', 'dynamodb-tables', 's3-storage'],
                'duration': 40,
                'dependencies': ['foundation', 'security', 'networking'],
                'stack_prefix': 'ial-data'
            },
            'application': {
                'phases': ['lambda-functions', 'step-functions', 'sns-topics', 'parameter-store'],
                'duration': 25,
                'dependencies': ['foundation', 'security', 'networking', 'compute', 'data'],
                'stack_prefix': 'ial-application'
            },
            'observability': {
                'phases': ['enhanced-observability', 'observability', 'drift-detection'],
                'duration': 20,
                'dependencies': ['foundation', 'compute', 'data', 'application'],
                'stack_prefix': 'ial-observability'
            },
            'ai-ml': {
                'phases': ['rag-s3-tables'],
                'duration': 15,
                'dependencies': ['foundation', 'security', 'data', 'application'],
                'stack_prefix': 'ial-ai-ml'
            },
            'governance': {
                'phases': ['well-architected-assessment', 'budgets-resources', 'cost-guardrails', 'cost-performance-dashboard'],
                'duration': 15,
                'dependencies': ['foundation', 'security', 'networking', 'compute', 'data', 'application', 'observability', 'ai-ml'],
                'stack_prefix': 'ial-governance'
            }
        }

    def get_infrastructure_status(self, domain: str = None) -> Dict:
        """Get real infrastructure status from CloudFormation"""
        
        try:
            stacks = self.cloudformation.list_stacks(
                StackStatusFilter=[
                    'CREATE_COMPLETE', 'UPDATE_COMPLETE', 'CREATE_IN_PROGRESS', 
                    'UPDATE_IN_PROGRESS', 'CREATE_FAILED', 'UPDATE_FAILED'
                ]
            )
            
            status = {}
            for stack in stacks['StackSummaries']:
                stack_name = stack['StackName']
                
                # Map stack to domain
                for dom, info in self.domain_knowledge.items():
                    if domain and dom != domain:
                        continue
                        
                    if stack_name.startswith(info['stack_prefix']) or f"ial-{dom}" in stack_name:
                        if dom not in status:
                            status[dom] = {'stacks': [], 'overall_status': 'HEALTHY'}
                        
                        stack_status = stack['StackStatus']
                        status[dom]['stacks'].append({
                            'name': stack_name,
                            'status': stack_status,
                            'creation_time': stack.get('CreationTime', '').isoformat() if stack.get('CreationTime') else '',
                            'last_updated': stack.get('LastUpdatedTime', '').isoformat() if stack.get('LastUpdatedTime') else ''
                        })
                        
                        # Determine overall status
                        if 'FAILED' in stack_status:
                            status[dom]['overall_status'] = 'FAILED'
                        elif 'IN_PROGRESS' in stack_status and status[dom]['overall_status'] != 'FAILED':
                            status[dom]['overall_status'] = 'IN_PROGRESS'
            
            return status
            
        except Exception as e:
            return {'error': f"Unable to get infrastructure status: {e}"}

    def execute_deployment(self, domain: str, dry_run: bool = False, user_preference: str = None) -> Dict:
        """Execute deployment usando estratégia híbrida inteligente"""
        
        if domain not in self.domain_knowledge:
            return {'error': f"Unknown domain: {domain}"}
        
        # Use hybrid deployment if available
        if self.hybrid_deployer:
            # Escolhe estratégia baseada no contexto
            strategy_info = self.hybrid_deployer.choose_deployment_strategy(domain, user_preference)
            
            if dry_run:
                return {
                    'action': 'deploy',
                    'domain': domain,
                    'dry_run': True,
                    'strategy': strategy_info['strategy'],
                    'reason': strategy_info['reason'],
                    'estimated_time': strategy_info['estimated_time'],
                    'phases': self.domain_knowledge[domain]['phases']
                }
            
            # Se requer confirmação, retorna opções
            if strategy_info['requires_confirmation'] and not user_preference:
                return {
                    'action': 'deploy',
                    'domain': domain,
                    'requires_choice': True,
                    'options': self.hybrid_deployer.get_deployment_options(domain),
                    'context': self.hybrid_deployer.deployment_context
                }
            
            # Executa deployment
            return self.hybrid_deployer.execute_deployment(domain, strategy_info['strategy'], dry_run)
        
        # Fallback para deploy direto original
        else:
            return self.execute_direct_deployment(domain, dry_run)

    def execute_direct_deployment(self, domain: str, dry_run: bool = False) -> Dict:
        """Deploy direto original (fallback)"""
        
        domain_info = self.domain_knowledge[domain]
        
        if dry_run:
            return {
                'action': 'deploy',
                'domain': domain,
                'dry_run': True,
                'phases': domain_info['phases'],
                'estimated_duration': f"{domain_info['duration']} minutes",
                'dependencies': domain_info['dependencies'],
                'message': f"Would deploy {len(domain_info['phases'])} phases for {domain} domain"
            }
        
        # Check dependencies
        missing_deps = self.check_dependencies(domain_info['dependencies'])
        if missing_deps:
            return {
                'error': f"Missing dependencies: {', '.join(missing_deps)}",
                'required_dependencies': missing_deps
            }
        
        # Execute deployment
        results = []
        for phase in domain_info['phases']:
            phase_file = f"phases/{self.get_domain_folder(domain)}/{phase}.yaml"
            
            try:
                # Deploy using CloudFormation
                stack_name = f"ial-{domain}-{phase}"
                
                result = subprocess.run([
                    'aws', 'cloudformation', 'deploy',
                    '--template-file', phase_file,
                    '--stack-name', stack_name,
                    '--capabilities', 'CAPABILITY_IAM',
                    '--no-fail-on-empty-changeset'
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    results.append({'phase': phase, 'status': 'SUCCESS'})
                else:
                    results.append({'phase': phase, 'status': 'FAILED', 'error': result.stderr})
                    break  # Stop on first failure
                    
            except Exception as e:
                results.append({'phase': phase, 'status': 'FAILED', 'error': str(e)})
                break
        
        return {
            'action': 'deploy',
            'domain': domain,
            'strategy': 'direct',
            'results': results,
            'success': all(r['status'] == 'SUCCESS' for r in results)
        }

    def execute_rollback(self, domain: str) -> Dict:
        """Execute real infrastructure rollback"""
        
        if domain not in self.domain_knowledge:
            return {'error': f"Unknown domain: {domain}"}
        
        domain_info = self.domain_knowledge[domain]
        
        # Get stacks to rollback (reverse order)
        stacks_to_rollback = []
        for phase in reversed(domain_info['phases']):
            stack_name = f"ial-{domain}-{phase}"
            stacks_to_rollback.append(stack_name)
        
        results = []
        for stack_name in stacks_to_rollback:
            try:
                # Delete CloudFormation stack
                result = subprocess.run([
                    'aws', 'cloudformation', 'delete-stack',
                    '--stack-name', stack_name
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    results.append({'stack': stack_name, 'status': 'DELETION_INITIATED'})
                else:
                    results.append({'stack': stack_name, 'status': 'FAILED', 'error': result.stderr})
                    
            except Exception as e:
                results.append({'stack': stack_name, 'status': 'FAILED', 'error': str(e)})
        
        return {
            'action': 'rollback',
            'domain': domain,
            'results': results,
            'message': f"Initiated rollback for {len(results)} stacks"
        }

    def validate_infrastructure(self, domain: str) -> Dict:
        """Validate infrastructure configuration"""
        
        if domain not in self.domain_knowledge:
            return {'error': f"Unknown domain: {domain}"}
        
        domain_info = self.domain_knowledge[domain]
        validation_results = []
        
        for phase in domain_info['phases']:
            phase_file = f"phases/{self.get_domain_folder(domain)}/{phase}.yaml"
            
            try:
                # Validate CloudFormation template
                result = subprocess.run([
                    'aws', 'cloudformation', 'validate-template',
                    '--template-body', f'file://{phase_file}'
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    validation_results.append({'phase': phase, 'status': 'VALID'})
                else:
                    validation_results.append({'phase': phase, 'status': 'INVALID', 'error': result.stderr})
                    
            except Exception as e:
                validation_results.append({'phase': phase, 'status': 'ERROR', 'error': str(e)})
        
        return {
            'action': 'validate',
            'domain': domain,
            'results': validation_results,
            'valid': all(r['status'] == 'VALID' for r in validation_results)
        }

    def check_dependencies(self, dependencies: List[str]) -> List[str]:
        """Check if domain dependencies are satisfied"""
        
        missing = []
        for dep in dependencies:
            if dep == 'foundation':
                # Check if DynamoDB state table exists
                try:
                    self.dynamodb.describe_table(TableName='mcp-provisioning-checklist')
                except:
                    missing.append(dep)
            else:
                # Check if domain stacks exist
                status = self.get_infrastructure_status(dep)
                if not status or dep not in status:
                    missing.append(dep)
        
        return missing

    def get_domain_folder(self, domain: str) -> str:
        """Map domain to folder structure"""
        
        folder_mapping = {
            'security': '10-security',
            'networking': '20-network',
            'compute': '30-compute',
            'data': '40-data',
            'application': '50-application',
            'observability': '60-observability',
            'ai-ml': '70-ai-ml',
            'governance': '90-governance'
        }
        
        return folder_mapping.get(domain, f"unknown-{domain}")

    def generate_deployment_plan(self, domains: List[str]) -> Dict:
        """Generate intelligent deployment plan"""
        
        # Topological sort based on dependencies
        plan = []
        deployed = set()
        
        while len(deployed) < len(domains):
            for domain in domains:
                if domain in deployed:
                    continue
                
                domain_info = self.domain_knowledge.get(domain, {})
                dependencies = domain_info.get('dependencies', [])
                
                # Check if all dependencies are satisfied
                if all(dep in deployed or dep == 'foundation' for dep in dependencies):
                    plan.append({
                        'domain': domain,
                        'phases': domain_info.get('phases', []),
                        'duration': domain_info.get('duration', 0),
                        'dependencies': dependencies
                    })
                    deployed.add(domain)
                    break
            else:
                # Circular dependency or missing domain
                remaining = [d for d in domains if d not in deployed]
                return {'error': f"Cannot resolve dependencies for: {remaining}"}
        
        return {
            'deployment_plan': plan,
            'total_duration': sum(p['duration'] for p in plan),
            'total_phases': sum(len(p['phases']) for p in plan)
        }

# Example usage
if __name__ == "__main__":
    engine = AdvancedNLPEngine()
    
    # Test infrastructure status
    status = engine.get_infrastructure_status()
    print("Infrastructure Status:", json.dumps(status, indent=2))
    
    # Test deployment plan
    plan = engine.generate_deployment_plan(['security', 'networking', 'compute'])
    print("Deployment Plan:", json.dumps(plan, indent=2))
