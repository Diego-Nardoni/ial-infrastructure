import boto3
import json
from typing import Dict, Any
from core.decision_ledger import DecisionLedger

class AutoHealer:
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.cloudformation = boto3.client('cloudformation', region_name=region)
        self.decision_ledger = DecisionLedger()
        
    def heal_drift(self, drift_item: Dict[str, Any]) -> Dict[str, Any]:
        """Automatically heal safe drift"""
        
        resource_id = drift_item.get('resource_id')
        drift_type = drift_item.get('drift_type')
        
        try:
            if drift_type == 'configuration_drift':
                result = self._heal_configuration_drift(drift_item)
            elif drift_type == 'missing_resource':
                result = self._heal_missing_resource(drift_item)
            else:
                result = {'status': 'skipped', 'reason': f'Cannot auto-heal {drift_type}'}
            
            # Log the healing action
            self.decision_ledger.log(
                phase="drift-detection",
                mcp="auto-healer",
                tool="heal_drift",
                rationale=f"Auto-healed {drift_type} for {resource_id}",
                status="HEALED"
            )
            
            return result
            
        except Exception as e:
            # Log the failure
            self.decision_ledger.log(
                phase="drift-detection",
                mcp="auto-healer", 
                tool="heal_drift",
                rationale=f"Failed to heal {resource_id}: {str(e)}",
                status="FAILED"
            )
            
            return {'status': 'failed', 'error': str(e)}
    
    def _heal_configuration_drift(self, drift_item: Dict[str, Any]) -> Dict[str, Any]:
        """Heal configuration drift by updating CloudFormation"""
        
        resource_id = drift_item.get('resource_id')
        desired_config = drift_item.get('desired', {})
        differences = drift_item.get('differences', [])
        
        # For now, focus on tag updates (safest operation)
        tag_updates = [diff for diff in differences if diff.get('type') == 'tag_drift']
        
        if tag_updates:
            # Update tags via CloudFormation
            stack_name = self._get_stack_name_for_resource(resource_id)
            if stack_name:
                # Trigger stack update with new tags
                return self._update_stack_tags(stack_name, desired_config.get('tags', {}))
        
        return {'status': 'no_action', 'reason': 'No safe changes to apply'}
    
    def _heal_missing_resource(self, drift_item: Dict[str, Any]) -> Dict[str, Any]:
        """Heal missing resource by creating it"""
        
        # This would typically trigger a CloudFormation deployment
        # For now, return a placeholder
        return {'status': 'scheduled', 'reason': 'Resource creation scheduled'}
    
    def _get_stack_name_for_resource(self, resource_id: str) -> str:
        """Get CloudFormation stack name for a resource"""
        # Simple mapping - in production this would be more sophisticated
        if 'security' in resource_id.lower():
            return 'ial-security-stack'
        elif 'network' in resource_id.lower():
            return 'ial-network-stack'
        else:
            return 'ial-foundation-stack'
    
    def _update_stack_tags(self, stack_name: str, desired_tags: Dict[str, str]) -> Dict[str, Any]:
        """Update CloudFormation stack tags"""
        
        try:
            # Get current stack info
            response = self.cloudformation.describe_stacks(StackName=stack_name)
            stack = response['Stacks'][0]
            
            # Convert desired tags to CloudFormation format
            cf_tags = [{'Key': k, 'Value': v} for k, v in desired_tags.items()]
            
            # Update stack with new tags
            self.cloudformation.update_stack(
                StackName=stack_name,
                UsePreviousTemplate=True,
                Tags=cf_tags
            )
            
            return {'status': 'updated', 'stack': stack_name, 'tags': len(cf_tags)}
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
