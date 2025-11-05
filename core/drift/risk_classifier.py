from typing import Dict, List, Any

class RiskClassifier:
    def __init__(self):
        # Define safe properties that can be auto-healed
        self.safe_properties = {
            'tags',
            'description', 
            'name',
            'monitoring',
            'backup_retention',
            'log_retention'
        }
        
        # Define risky properties that need human review
        self.risky_properties = {
            'security_groups',
            'subnets',
            'vpc_id',
            'iam_role',
            'iam_policy',
            'encryption',
            'public_access',
            'ingress_rules',
            'egress_rules'
        }
        
        # Define critical properties that always need approval
        self.critical_properties = {
            'deletion_protection',
            'backup_deletion',
            'encryption_key',
            'public_subnet',
            'internet_gateway'
        }
    
    def classify_drift(self, drift_item: Dict[str, Any]) -> str:
        """Classify drift as safe, risky, or critical"""
        
        drift_type = drift_item.get('drift_type')
        severity = drift_item.get('severity', 'medium')
        
        # Extra resources are always risky (need reverse sync)
        if drift_type == 'extra_resource':
            return 'risky'
        
        # Missing critical resources are critical
        if drift_type == 'missing_resource' and severity == 'high':
            return 'critical'
        
        # Configuration drift analysis
        if drift_type == 'configuration_drift':
            differences = drift_item.get('differences', [])
            return self._classify_configuration_drift(differences)
        
        # Default to risky for unknown cases
        return 'risky'
    
    def _classify_configuration_drift(self, differences: List[Dict]) -> str:
        """Classify configuration drift based on changed properties"""
        
        # Check for critical properties
        for diff in differences:
            prop = diff.get('property', '')
            if any(critical in prop.lower() for critical in self.critical_properties):
                return 'critical'
        
        # Check for risky properties
        for diff in differences:
            prop = diff.get('property', '')
            if any(risky in prop.lower() for risky in self.risky_properties):
                return 'risky'
        
        # Check if all changes are safe
        all_safe = True
        for diff in differences:
            prop = diff.get('property', '')
            if not any(safe in prop.lower() for safe in self.safe_properties):
                all_safe = False
                break
        
        return 'safe' if all_safe else 'risky'
    
    def get_rationale(self, drift_item: Dict[str, Any], classification: str) -> str:
        """Get human-readable rationale for classification"""
        
        drift_type = drift_item.get('drift_type')
        resource_id = drift_item.get('resource_id', 'unknown')
        
        if classification == 'safe':
            return f"Safe to auto-heal: {resource_id} has only non-critical changes (tags, descriptions, etc.)"
        
        elif classification == 'risky':
            if drift_type == 'extra_resource':
                return f"Resource {resource_id} was created outside IAL - needs reverse sync PR for review"
            else:
                return f"Resource {resource_id} has configuration changes that need human review"
        
        elif classification == 'critical':
            return f"CRITICAL: {resource_id} has security/infrastructure changes that require immediate attention"
        
        return f"Unknown classification for {resource_id}"
