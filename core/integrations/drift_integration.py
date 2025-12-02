#!/usr/bin/env python3
"""
Drift Integration - Integra feature flags com drift detection
"""

import logging
from typing import Dict, List, Any
from ..feature_flags_manager import get_feature_flags

class DriftIntegration:
    def __init__(self):
        self.feature_flags = get_feature_flags()
    
    def should_detect_drift(self, scope: str) -> bool:
        """Check if drift detection should run for scope"""
        # Check global drift detection flag
        if not self.feature_flags.is_enabled("drift_detection"):
            logging.info("Drift detection globally disabled")
            return False
        
        # Check scope-specific drift flag
        if not self.feature_flags.is_drift_enabled(scope):
            logging.info(f"Drift detection disabled for scope: {scope}")
            return False
        
        return True
    
    def should_auto_heal(self, scope: str) -> bool:
        """Check if auto-healing should run for scope"""
        # First check if drift detection is enabled
        if not self.should_detect_drift(scope):
            return False
        
        # Check auto-healing flag
        if not self.feature_flags.is_enabled("auto_healing"):
            logging.info("Auto-healing globally disabled")
            return False
        
        # Check if drift is in PAUSED state (detect but don't heal)
        drift_state = self.feature_flags.drift_flag.get_drift_state(scope)
        if drift_state.value == "PAUSED":
            logging.info(f"Auto-healing paused for scope: {scope}")
            return False
        
        return True
    
    def get_drift_config(self, scope: str) -> Dict[str, Any]:
        """Get drift configuration for scope"""
        return {
            "detect_enabled": self.should_detect_drift(scope),
            "auto_heal_enabled": self.should_auto_heal(scope),
            "drift_state": self.feature_flags.drift_flag.get_drift_state(scope).value,
            "scope": scope
        }

# Global instance
_drift_integration = None

def get_drift_integration() -> DriftIntegration:
    """Get global drift integration instance"""
    global _drift_integration
    if _drift_integration is None:
        _drift_integration = DriftIntegration()
    return _drift_integration
