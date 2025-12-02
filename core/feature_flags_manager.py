#!/usr/bin/env python3
"""
Feature Flags Manager - Sistema genérico de feature flags
"""

import boto3
import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
from .drift_flag import DriftFlag, DriftState

class FeatureState(Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    ROLLOUT = "rollout"  # Gradual rollout

class FeatureFlagsManager:
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.dynamodb = boto3.resource("dynamodb", region_name=region)
        self.table_name = os.getenv("IAL_FEATURE_FLAGS_TABLE", "ial-feature-flags-dev")
        self.drift_flag = DriftFlag(region)
        
        try:
            self.table = self.dynamodb.Table(self.table_name)
        except Exception as e:
            logging.warning(f"Feature flags table not available: {e}")
            self.table = None
    
    def is_enabled(self, feature_name: str, scope: str = "global") -> bool:
        """Check if feature is enabled"""
        try:
            if not self.table:
                return self._get_default_state(feature_name)
            
            response = self.table.get_item(
                Key={"scope": scope, "flag_name": feature_name}
            )
            
            item = response.get("Item")
            if not item:
                return self._get_default_state(feature_name)
            
            state = item.get("state", "disabled")
            return state == "enabled"
            
        except Exception as e:
            logging.error(f"Error checking feature flag {feature_name}: {e}")
            return self._get_default_state(feature_name)
    
    def set_flag(self, feature_name: str, enabled: bool, scope: str = "global", 
                 reason: str = "", duration_hours: int = 0) -> Dict:
        """Set feature flag"""
        if not self.table:
            raise RuntimeError("Feature flags table not available")
        
        state = "enabled" if enabled else "disabled"
        current_time = int(time.time())
        
        item = {
            "scope": scope,
            "flag_name": feature_name,
            "state": state,
            "reason": reason,
            "created_at": datetime.utcnow().isoformat(),
            "created_timestamp": current_time
        }
        
        if duration_hours > 0:
            item["expire_at"] = current_time + (duration_hours * 3600)
        
        self.table.put_item(Item=item)
        logging.info(f"Feature flag set: {feature_name} -> {state}")
        return item
    
    def _get_default_state(self, feature_name: str) -> bool:
        """Get default state for known features"""
        defaults = {
            # Core features - enabled by default
            "drift_detection": True,
            "auto_healing": True,
            "phase_validation": True,
            
            # Advanced features - disabled by default
            "llm_prioritization": False,
            "advanced_monitoring": False,
            "experimental_features": False,
            
            # Step Functions migration
            "healing_orchestrator_sf": True,
            "phase_manager_sf": True,
            "audit_validator_sf": True
        }
        
        return defaults.get(feature_name, False)
    
    # Drift-specific methods (delegate to DriftFlag)
    def is_drift_enabled(self, scope: str) -> bool:
        """Check if drift detection is enabled for scope"""
        return self.drift_flag.is_drift_enabled(scope)
    
    def pause_drift(self, scope: str, duration_hours: int, reason: str, 
                   ticket: str = "", approved_by: List[str] = None) -> Dict:
        """Pause drift detection for scope"""
        return self.drift_flag.pause_drift(scope, duration_hours, reason, ticket, approved_by)
    
    def resume_drift(self, scope: str, reason: str = "Manual resume") -> Dict:
        """Resume drift detection for scope"""
        return self.drift_flag.resume_drift(scope, reason)

# Global instance
_feature_flags = None

def get_feature_flags() -> FeatureFlagsManager:
    """Get global feature flags instance"""
    global _feature_flags
    if _feature_flags is None:
        _feature_flags = FeatureFlagsManager()
    return _feature_flags

# Convenience functions
def is_feature_enabled(feature_name: str, scope: str = "global") -> bool:
    """Check if feature is enabled"""
    return get_feature_flags().is_enabled(feature_name, scope)

def is_drift_enabled(scope: str) -> bool:
    """Check if drift detection is enabled"""
    return get_feature_flags().is_drift_enabled(scope)
