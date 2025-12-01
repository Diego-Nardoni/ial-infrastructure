import json
import boto3
from typing import Dict, List, Any
from core.desired_state import DesiredStateBuilder
from core.audit_validator import AuditValidator

class DriftDetector:
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.desired_state_builder = DesiredStateBuilder()
        self.audit_validator = AuditValidator()
        
    def detect_drift(self, stack_name: str = None) -> Dict[str, Any]:
        """Detect drift between Git (desired) and AWS (current)"""
        
        if stack_name:
            # Detectar drift para stack específico
            return self._detect_stack_drift(stack_name)
        else:
            # Detectar drift geral
            return self._detect_general_drift()
    
    def _detect_stack_drift(self, stack_name: str) -> Dict[str, Any]:
        """Detectar drift para um stack específico do CloudFormation"""
        try:
            cf_client = boto3.client('cloudformation', region_name=self.region)
            
            # Verificar status do stack
            response = cf_client.describe_stacks(StackName=stack_name)
            stack = response['Stacks'][0]
            
            drift_info = stack.get('DriftInformation', {})
            drift_status = drift_info.get('StackDriftStatus', 'UNKNOWN')
            
            return {
                'stack_name': stack_name,
                'drift_status': drift_status,
                'stack_status': stack.get('StackStatus'),
                'last_updated': stack.get('LastUpdatedTime'),
                'drift_detection_time': drift_info.get('LastDriftDetectionTime')
            }
            
        except Exception as e:
            return {
                'stack_name': stack_name,
                'drift_status': 'ERROR',
                'error': str(e)
            }
    
    def _detect_general_drift(self) -> List[Dict[str, Any]]:
        """Detect drift between Git (desired) and AWS (current)"""
        
        # Get desired state from Git (using all phases)
        phases = ["00-foundation", "10-security", "20-network", "30-compute"]
        desired_spec = self.desired_state_builder.build_desired_spec(phases)
        
        # Get current state from AWS
        current_state = self.audit_validator.get_current_aws_state()
        
        # Compare and find differences
        drift_items = self._compare_states(desired_spec, current_state)
        
        return {
            'drift_status': 'DRIFTED' if drift_items else 'IN_SYNC',
            'drift_items': drift_items,
            'total_drifts': len(drift_items)
        }
    
    def _compare_states(self, desired: Dict, current: Dict) -> List[Dict[str, Any]]:
        """Compare desired vs current state and identify drift"""
        drift_items = []
        
        # Check for missing resources (in desired but not in AWS)
        for resource_id, desired_config in desired.get('resources', {}).items():
            if resource_id not in current.get('resources', {}):
                drift_items.append({
                    'resource_id': resource_id,
                    'drift_type': 'missing_resource',
                    'desired': desired_config,
                    'current': None,
                    'severity': 'high'
                })
        
        # Check for extra resources (in AWS but not in desired)
        for resource_id, current_config in current.get('resources', {}).items():
            if resource_id not in desired.get('resources', {}):
                drift_items.append({
                    'resource_id': resource_id,
                    'drift_type': 'extra_resource',
                    'desired': None,
                    'current': current_config,
                    'severity': 'medium'
                })
        
        # Check for configuration drift (resource exists in both but differs)
        for resource_id in desired.get('resources', {}):
            if resource_id in current.get('resources', {}):
                desired_config = desired['resources'][resource_id]
                current_config = current['resources'][resource_id]
                
                config_drift = self._compare_resource_config(desired_config, current_config)
                if config_drift:
                    drift_items.append({
                        'resource_id': resource_id,
                        'drift_type': 'configuration_drift',
                        'desired': desired_config,
                        'current': current_config,
                        'differences': config_drift,
                        'severity': self._calculate_severity(config_drift)
                    })
        
        return drift_items
    
    def _compare_resource_config(self, desired: Dict, current: Dict) -> List[Dict]:
        """Compare individual resource configuration"""
        differences = []
        
        # Compare tags
        desired_tags = desired.get('tags', {})
        current_tags = current.get('tags', {})
        
        for tag_key, tag_value in desired_tags.items():
            if current_tags.get(tag_key) != tag_value:
                differences.append({
                    'property': f'tags.{tag_key}',
                    'desired': tag_value,
                    'current': current_tags.get(tag_key),
                    'type': 'tag_drift'
                })
        
        # Compare other properties (simplified)
        for prop in ['description', 'name', 'state']:
            if prop in desired and desired.get(prop) != current.get(prop):
                differences.append({
                    'property': prop,
                    'desired': desired.get(prop),
                    'current': current.get(prop),
                    'type': 'property_drift'
                })
        
        return differences
    
    def _calculate_severity(self, differences: List[Dict]) -> str:
        """Calculate drift severity based on differences"""
        critical_props = ['security_groups', 'subnets', 'vpc_id', 'iam_role']
        
        for diff in differences:
            if any(critical in diff['property'] for critical in critical_props):
                return 'critical'
        
        if len(differences) > 5:
            return 'high'
        elif len(differences) > 2:
            return 'medium'
        else:
            return 'low'
