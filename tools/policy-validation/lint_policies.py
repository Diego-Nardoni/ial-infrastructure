#!/usr/bin/env python3
"""Advanced Policy Linter for IAM/SG/WAF"""

import json
import yaml
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Import CloudFormation YAML loader
sys.path.append(str(Path(__file__).parent.parent.parent / 'scripts'))
from cf_yaml_loader import load_cf_yaml

PROJECT_ROOT = Path(__file__).parent.parent.parent
PHASES_DIR = PROJECT_ROOT / 'phases'

class PolicyLinter:
    def __init__(self):
        self.violations = []
        self.warnings = []
        
    def lint_iam_policies(self, resource: Dict, resource_name: str, file_path: str) -> List[Dict]:
        """Lint IAM policies for security violations"""
        violations = []
        properties = resource.get('Properties', {})
        
        # Check inline policies
        for policy in properties.get('Policies', []):
            policy_doc = policy.get('PolicyDocument', {})
            
            for statement in policy_doc.get('Statement', []):
                if isinstance(statement, dict):
                    # Check for wildcard actions
                    actions = statement.get('Action', [])
                    if isinstance(actions, str):
                        actions = [actions]
                    
                    for action in actions:
                        if action == "*":
                            # Check for exception tag
                            tags = properties.get('Tags', [])
                            has_exception = any(
                                tag.get('Key') == 'SecurityException' and 
                                'wildcard-action' in tag.get('Value', '')
                                for tag in tags
                            )
                            
                            if not has_exception:
                                violations.append({
                                    'type': 'IAM_WILDCARD_ACTION',
                                    'severity': 'HIGH',
                                    'resource': resource_name,
                                    'file': str(file_path),
                                    'message': 'IAM policy contains wildcard (*) action without SecurityException tag',
                                    'recommendation': 'Add SecurityException tag or use specific actions'
                                })
                    
                    # Check for wildcard resources
                    resources = statement.get('Resource', [])
                    if isinstance(resources, str):
                        resources = [resources]
                    
                    for resource_arn in resources:
                        if resource_arn == "*" and not any(action in ['sts:GetCallerIdentity', 'sts:GetAccessKeyInfo'] for action in actions):
                            violations.append({
                                'type': 'IAM_WILDCARD_RESOURCE',
                                'severity': 'MEDIUM',
                                'resource': resource_name,
                                'file': str(file_path),
                                'message': 'IAM policy uses wildcard (*) resource',
                                'recommendation': 'Specify exact resource ARNs'
                            })
        
        return violations
    
    def lint_security_groups(self, resource: Dict, resource_name: str, file_path: str) -> List[Dict]:
        """Lint Security Group rules"""
        violations = []
        properties = resource.get('Properties', {})
        
        # Check ingress rules
        for rule in properties.get('SecurityGroupIngress', []):
            cidr_ip = rule.get('CidrIp', '')
            cidr_ipv6 = rule.get('CidrIpv6', '')
            
            if cidr_ip == '0.0.0.0/0' or cidr_ipv6 == '::/0':
                # Check for exception tag
                tags = properties.get('Tags', [])
                has_exception = any(
                    tag.get('Key') == 'SecurityException' and 
                    'public-access' in tag.get('Value', '')
                    for tag in tags
                )
                
                if not has_exception:
                    violations.append({
                        'type': 'SG_OPEN_TO_WORLD',
                        'severity': 'HIGH',
                        'resource': resource_name,
                        'file': str(file_path),
                        'message': f'Security Group allows access from 0.0.0.0/0 on port {rule.get("FromPort", "all")}',
                        'recommendation': 'Restrict to specific IP ranges or add SecurityException tag'
                    })
        
        return violations
    
    def lint_waf_coverage(self, resources: Dict, file_path: str) -> List[Dict]:
        """Check WAF coverage for edge resources"""
        violations = []
        
        # Find CloudFront and ALB resources
        edge_resources = []
        waf_resources = []
        
        for name, resource in resources.items():
            resource_type = resource.get('Type', '')
            
            if resource_type in ['AWS::CloudFront::Distribution', 'AWS::ElasticLoadBalancingV2::LoadBalancer']:
                edge_resources.append({
                    'name': name,
                    'type': resource_type,
                    'properties': resource.get('Properties', {})
                })
            elif 'WAF' in resource_type:
                waf_resources.append(name)
        
        # Check if edge resources have WAF protection
        for edge_resource in edge_resources:
            has_waf = False
            properties = edge_resource['properties']
            
            if edge_resource['type'] == 'AWS::CloudFront::Distribution':
                # Check for WebACLId in distribution config
                dist_config = properties.get('DistributionConfig', {})
                if dist_config.get('WebACLId'):
                    has_waf = True
            elif edge_resource['type'] == 'AWS::ElasticLoadBalancingV2::LoadBalancer':
                # WAF association is typically done separately, check if any WAF resources exist
                if waf_resources:
                    has_waf = True
            
            if not has_waf and edge_resource['type'] == 'AWS::CloudFront::Distribution':
                violations.append({
                    'type': 'MISSING_WAF_PROTECTION',
                    'severity': 'MEDIUM',
                    'resource': edge_resource['name'],
                    'file': str(file_path),
                    'message': f'{edge_resource["type"]} lacks WAF protection',
                    'recommendation': 'Associate with AWS WAF WebACL for security'
                })
        
        return violations
    
    def lint_encryption_standards(self, resource: Dict, resource_name: str, file_path: str) -> List[Dict]:
        """Check encryption standards"""
        violations = []
        resource_type = resource.get('Type', '')
        properties = resource.get('Properties', {})
        
        # S3 Bucket encryption
        if resource_type == 'AWS::S3::Bucket':
            encryption = properties.get('BucketEncryption', {})
            if not encryption:
                violations.append({
                    'type': 'MISSING_ENCRYPTION',
                    'severity': 'HIGH',
                    'resource': resource_name,
                    'file': str(file_path),
                    'message': 'S3 bucket lacks encryption configuration',
                    'recommendation': 'Enable SSE-KMS encryption'
                })
            else:
                # Check if using KMS
                rules = encryption.get('ServerSideEncryptionConfiguration', [])
                uses_kms = any(
                    rule.get('ServerSideEncryptionByDefault', {}).get('SSEAlgorithm') == 'aws:kms'
                    for rule in rules
                )
                if not uses_kms:
                    violations.append({
                        'type': 'WEAK_ENCRYPTION',
                        'severity': 'MEDIUM',
                        'resource': resource_name,
                        'file': str(file_path),
                        'message': 'S3 bucket not using KMS encryption',
                        'recommendation': 'Use SSE-KMS with customer-managed key'
                    })
        
        # DynamoDB encryption
        elif resource_type == 'AWS::DynamoDB::Table':
            sse_spec = properties.get('SSESpecification', {})
            if not sse_spec.get('SSEEnabled'):
                violations.append({
                    'type': 'MISSING_ENCRYPTION',
                    'severity': 'HIGH',
                    'resource': resource_name,
                    'file': str(file_path),
                    'message': 'DynamoDB table lacks encryption at rest',
                    'recommendation': 'Enable SSE with KMS'
                })
        
        return violations
    
    def lint_file(self, file_path: Path) -> Tuple[List[Dict], List[Dict]]:
        """Lint a single CloudFormation file"""
        violations = []
        warnings = []
        
        try:
            content = load_cf_yaml(file_path)
            if not isinstance(content, dict) or 'Resources' not in content:
                return violations, warnings
            
            resources = content['Resources']
            
            # Lint each resource
            for resource_name, resource in resources.items():
                resource_type = resource.get('Type', '')
                
                # IAM policies
                if resource_type == 'AWS::IAM::Role':
                    violations.extend(self.lint_iam_policies(resource, resource_name, file_path))
                
                # Security Groups
                elif resource_type == 'AWS::EC2::SecurityGroup':
                    violations.extend(self.lint_security_groups(resource, resource_name, file_path))
                
                # Encryption standards
                elif resource_type in ['AWS::S3::Bucket', 'AWS::DynamoDB::Table']:
                    violations.extend(self.lint_encryption_standards(resource, resource_name, file_path))
            
            # WAF coverage (file-level check)
            violations.extend(self.lint_waf_coverage(resources, file_path))
            
        except Exception as e:
            warnings.append({
                'type': 'PARSE_ERROR',
                'severity': 'LOW',
                'file': str(file_path),
                'message': f'Could not parse file: {e}',
                'recommendation': 'Check YAML syntax'
            })
        
        return violations, warnings
    
    def lint_all_phases(self) -> Dict:
        """Lint all phase files"""
        all_violations = []
        all_warnings = []
        
        for domain_dir in PHASES_DIR.iterdir():
            if not domain_dir.is_dir() or domain_dir.name.startswith('.'):
                continue
            
            for yaml_file in domain_dir.glob('*.yaml'):
                if yaml_file.name in ['domain-metadata.yaml', 'deployment-order.yaml']:
                    continue
                
                violations, warnings = self.lint_file(yaml_file)
                all_violations.extend(violations)
                all_warnings.extend(warnings)
        
        return {
            'violations': all_violations,
            'warnings': all_warnings,
            'summary': {
                'total_violations': len(all_violations),
                'high_severity': len([v for v in all_violations if v['severity'] == 'HIGH']),
                'medium_severity': len([v for v in all_violations if v['severity'] == 'MEDIUM']),
                'low_severity': len([v for v in all_violations if v['severity'] == 'LOW']),
                'total_warnings': len(all_warnings)
            }
        }

def main():
    """Execução principal"""
    try:
        linter = PolicyLinter()
        results = linter.lint_all_phases()
        
        # Console output
        print("🔒 POLICY LINTER RESULTS")
        print("=" * 50)
        
        summary = results['summary']
        print(f"Total Violations: {summary['total_violations']}")
        print(f"  High Severity: {summary['high_severity']}")
        print(f"  Medium Severity: {summary['medium_severity']}")
        print(f"  Low Severity: {summary['low_severity']}")
        print(f"Total Warnings: {summary['total_warnings']}")
        
        # Show violations
        if results['violations']:
            print(f"\n❌ POLICY VIOLATIONS:")
            for violation in results['violations']:
                severity_emoji = {'HIGH': '🚨', 'MEDIUM': '⚠️', 'LOW': '💡'}
                emoji = severity_emoji.get(violation['severity'], '❓')
                print(f"{emoji} {violation['type']} - {violation['resource']}")
                print(f"   File: {violation['file']}")
                print(f"   Issue: {violation['message']}")
                print(f"   Fix: {violation['recommendation']}")
                print()
        
        # Show warnings
        if results['warnings']:
            print(f"\n⚠️ WARNINGS:")
            for warning in results['warnings']:
                print(f"💡 {warning['type']} - {warning['file']}")
                print(f"   Issue: {warning['message']}")
                print()
        
        # Save results
        report_file = PROJECT_ROOT / 'reports' / 'policy_lint_report.json'
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"📄 Report saved: {report_file}")
        
        # Exit code based on high severity violations
        if summary['high_severity'] > 0:
            print(f"\n❌ FAILED: {summary['high_severity']} high severity violations found")
            return 1
        elif summary['medium_severity'] > 0:
            print(f"\n⚠️ WARNING: {summary['medium_severity']} medium severity violations found")
            return 0  # Don't fail on medium severity
        else:
            print(f"\n✅ PASSED: No high severity violations found")
            return 0
            
    except Exception as e:
        print(f"💥 Error: {e}")
        return 1

if __name__ == '__main__':
    exit(main())
