#!/usr/bin/env python3
"""
Bootstrap Mode - Detecta se sistema está em modo bootstrap
"""

import os
import boto3
import logging
from typing import Dict, Any, Optional

class BootstrapDetector:
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self._bootstrap_cache = None
        
    def is_bootstrap_mode(self) -> bool:
        """Detecta se sistema está em modo bootstrap (primeira execução)"""
        if self._bootstrap_cache is not None:
            return self._bootstrap_cache
            
        # Check 1: Environment variable override
        if os.getenv("IAL_BOOTSTRAP_MODE", "").lower() == "true":
            self._bootstrap_cache = True
            return True
            
        # Check 2: Feature flags table exists?
        if not self._check_feature_flags_table():
            self._bootstrap_cache = True
            return True
            
        # Check 3: Foundation stacks exist?
        if not self._check_foundation_stacks():
            self._bootstrap_cache = True
            return True
            
        self._bootstrap_cache = False
        return False
    
    def _check_feature_flags_table(self) -> bool:
        """Check if feature flags table exists"""
        try:
            dynamodb = boto3.client('dynamodb', region_name=self.region)
            table_name = os.getenv("IAL_FEATURE_FLAGS_TABLE", "ial-feature-flags-dev")
            
            dynamodb.describe_table(TableName=table_name)
            return True
        except Exception:
            return False
    
    def _check_foundation_stacks(self) -> bool:
        """Check if foundation stacks exist"""
        try:
            cf = boto3.client('cloudformation', region_name=self.region)
            
            # Check for key foundation stacks
            key_stacks = [
                "ial-00-foundation",
                "ial-01-networking", 
                "ial-18-feature-flags"
            ]
            
            for stack_name in key_stacks:
                try:
                    cf.describe_stacks(StackName=stack_name)
                except cf.exceptions.ClientError as e:
                    if "does not exist" in str(e):
                        return False
                        
            return True
        except Exception:
            return False
    
    def get_bootstrap_config(self) -> Dict[str, Any]:
        """Get bootstrap configuration"""
        is_bootstrap = self.is_bootstrap_mode()
        
        return {
            "bootstrap_mode": is_bootstrap,
            "feature_flags_enabled": not is_bootstrap,
            "drift_detection_enabled": not is_bootstrap,
            "contract_validation_enabled": not is_bootstrap,
            "fallback_mode": is_bootstrap
        }

# Global instance
_bootstrap_detector = None

def get_bootstrap_detector() -> BootstrapDetector:
    """Get global bootstrap detector"""
    global _bootstrap_detector
    if _bootstrap_detector is None:
        _bootstrap_detector = BootstrapDetector()
    return _bootstrap_detector

def is_bootstrap_mode() -> bool:
    """Check if system is in bootstrap mode"""
    return get_bootstrap_detector().is_bootstrap_mode()

def get_bootstrap_config() -> Dict[str, Any]:
    """Get bootstrap configuration"""
    return get_bootstrap_detector().get_bootstrap_config()
