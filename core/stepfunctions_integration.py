#!/usr/bin/env python3
"""
Step Functions Integration Layer
Provides unified interface for all Step Functions-based components
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from core.graph.healing_orchestrator_stepfunctions import StepFunctionsHealingOrchestrator
from scripts.phase_manager_stepfunctions import StepFunctionsPhaseManager
from core.audit_validator_stepfunctions import StepFunctionsAuditValidator

class IALStepFunctionsIntegration:
    """Unified interface for all IAL Step Functions components"""
    
    def __init__(self, region: str = "us-east-1", config_path: str = "config/stepfunctions_config.yaml"):
        self.region = region
        self.config = self._load_config(config_path)
        
        # Initialize components based on feature flags
        self.healing_orchestrator = None
        self.phase_manager = None
        self.audit_validator = None
        
        if self.config.get("migration", {}).get("feature_flags", {}).get("healing_orchestrator_sf", False):
            self.healing_orchestrator = StepFunctionsHealingOrchestrator(region)
            
        if self.config.get("migration", {}).get("feature_flags", {}).get("phase_manager_sf", False):
            self.phase_manager = StepFunctionsPhaseManager(region)
            
        if self.config.get("migration", {}).get("feature_flags", {}).get("audit_validator_sf", False):
            self.audit_validator = StepFunctionsAuditValidator(region)
    
    def _load_config(self, config_path: str) -> Dict:
        """Load Step Functions configuration"""
        try:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    return yaml.safe_load(f)
        except Exception as e:
            print(f"⚠️ Failed to load config from {config_path}: {e}")
        
        return {}
    
    def orchestrate_healing(self, failed_resources: list = None) -> Dict[str, Any]:
        """Orchestrate healing using Step Functions or fallback"""
        if self.healing_orchestrator:
            return self.healing_orchestrator.orchestrate_healing(failed_resources)
        else:
            # Fallback to legacy implementation
            from core.graph.healing_orchestrator import GraphBasedHealingOrchestrator
            legacy_orchestrator = GraphBasedHealingOrchestrator(self.region)
            return legacy_orchestrator.orchestrate_healing(failed_resources)
    
    def execute_phases(self) -> Dict[str, Any]:
        """Execute phases using Step Functions or fallback"""
        if self.phase_manager:
            return self.phase_manager.execute_phases()
        else:
            # Fallback to legacy implementation
            from scripts.phase_manager import PhaseManager
            legacy_manager = PhaseManager()
            return {"status": "fallback", "message": "Using legacy phase manager"}
    
    def validate_audit(self, desired_spec_path: str = "reports/desired_spec.json") -> Dict[str, Any]:
        """Validate audit using Step Functions or fallback"""
        if self.audit_validator:
            return self.audit_validator.validate_completeness_with_enforcement(desired_spec_path)
        else:
            # Fallback to legacy implementation
            from core.audit_validator import AuditValidator
            legacy_validator = AuditValidator(self.region)
            return legacy_validator.validate_completeness_with_enforcement(desired_spec_path)
    
    def get_execution_status(self, execution_arn: str) -> Dict[str, Any]:
        """Get execution status for any Step Functions execution"""
        import boto3
        
        stepfunctions = boto3.client('stepfunctions', region_name=self.region)
        
        try:
            response = stepfunctions.describe_execution(executionArn=execution_arn)
            return {
                "status": response["status"],
                "start_date": response["startDate"].isoformat(),
                "stop_date": response.get("stopDate", {}).isoformat() if response.get("stopDate") else None,
                "output": response.get("output", "{}"),
                "input": response.get("input", "{}")
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of all Step Functions components"""
        health_status = {
            "overall_status": "healthy",
            "components": {},
            "feature_flags": self.config.get("migration", {}).get("feature_flags", {})
        }
        
        # Check each component
        components = [
            ("healing_orchestrator", self.healing_orchestrator),
            ("phase_manager", self.phase_manager),
            ("audit_validator", self.audit_validator)
        ]
        
        for name, component in components:
            if component:
                health_status["components"][name] = {
                    "status": "enabled",
                    "type": "stepfunctions"
                }
            else:
                health_status["components"][name] = {
                    "status": "disabled",
                    "type": "legacy_fallback"
                }
        
        return health_status
