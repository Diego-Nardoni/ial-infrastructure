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
            'backup_policy',
            'access_policy'
        }
        
        # Risk levels by resource type and change type
        self.risk_matrix = {
            'AWS::S3::Bucket': {
                'tag_update': 'LOW',
                'policy_change': 'HIGH',
                'deletion': 'CRITICAL'
            },
            'AWS::RDS::DBInstance': {
                'tag_update': 'LOW',
                'parameter_change': 'MEDIUM',
                'deletion': 'CRITICAL'
            },
            'AWS::IAM::Role': {
                'tag_update': 'LOW',
                'policy_change': 'CRITICAL',
                'deletion': 'CRITICAL'
            }
        }
    
    def classify_risk(self, change: Dict[str, Any]) -> Dict[str, Any]:
        """Classifica o risco de uma mudança"""
        
        resource_type = change.get('resource_type', '')
        change_type = change.get('change_type', '')
        impact_scope = change.get('impact_scope', 'single_resource')
        
        # Determinar nível base de risco
        base_risk = self._get_base_risk(resource_type, change_type)
        
        # Ajustar baseado no escopo de impacto
        final_risk = self._adjust_risk_by_scope(base_risk, impact_scope)
        
        return {
            'level': final_risk,
            'resource_type': resource_type,
            'change_type': change_type,
            'impact_scope': impact_scope,
            'reasoning': self._get_risk_reasoning(resource_type, change_type, final_risk),
            'mitigation_steps': self._get_mitigation_steps(final_risk)
        }
    
    def _get_base_risk(self, resource_type: str, change_type: str) -> str:
        """Determina o risco base baseado no tipo de recurso e mudança"""
        
        if resource_type in self.risk_matrix:
            return self.risk_matrix[resource_type].get(change_type, 'MEDIUM')
        
        # Fallback baseado no tipo de mudança
        if change_type == 'deletion':
            return 'HIGH'
        elif change_type in ['policy_change', 'security_change']:
            return 'HIGH'
        elif change_type in ['tag_update', 'description_change']:
            return 'LOW'
        else:
            return 'MEDIUM'
    
    def _adjust_risk_by_scope(self, base_risk: str, impact_scope: str) -> str:
        """Ajusta o risco baseado no escopo de impacto"""
        
        risk_levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        current_level = risk_levels.index(base_risk) if base_risk in risk_levels else 1
        
        if impact_scope == 'account_wide':
            # Aumenta o risco para mudanças que afetam toda a conta
            return risk_levels[min(current_level + 1, len(risk_levels) - 1)]
        elif impact_scope == 'multi_resource':
            # Aumenta ligeiramente para mudanças que afetam múltiplos recursos
            return risk_levels[min(current_level + 1, len(risk_levels) - 1)]
        
        return base_risk
    
    def _get_risk_reasoning(self, resource_type: str, change_type: str, risk_level: str) -> str:
        """Fornece justificativa para o nível de risco"""
        
        if risk_level == 'CRITICAL':
            return f"Critical risk: {change_type} on {resource_type} can cause significant impact"
        elif risk_level == 'HIGH':
            return f"High risk: {change_type} on {resource_type} requires careful review"
        elif risk_level == 'MEDIUM':
            return f"Medium risk: {change_type} on {resource_type} should be monitored"
        else:
            return f"Low risk: {change_type} on {resource_type} is generally safe"
    
    def _get_mitigation_steps(self, risk_level: str) -> List[str]:
        """Fornece passos de mitigação baseados no nível de risco"""
        
        if risk_level == 'CRITICAL':
            return [
                "Require manual approval",
                "Create backup before change",
                "Test in staging environment",
                "Have rollback plan ready"
            ]
        elif risk_level == 'HIGH':
            return [
                "Require senior approval",
                "Monitor closely after change",
                "Have rollback plan ready"
            ]
        elif risk_level == 'MEDIUM':
            return [
                "Monitor after change",
                "Document change reason"
            ]
        else:
            return [
                "Standard monitoring"
            ]
    
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
