#!/usr/bin/env python3
"""
IAL Drift Control Flag Management
Provides granular control over drift detection behavior with TTL and auditoria
"""

import boto3
import os
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from enum import Enum

class DriftState(Enum):
    ENABLED = "ENABLED"      # Normal drift detection + auto-reconcile
    PAUSED = "PAUSED"        # Detect + record + PR, but no auto-reconcile
    DISABLED = "DISABLED"    # Skip drift detection completely

class DriftFlag:
    """Manages drift control flags with DynamoDB persistence and TTL"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.dynamodb = boto3.resource("dynamodb", region_name=region)
        self.table_name = os.getenv("IAL_FEATURE_FLAGS_TABLE", "ial_feature_flags")
        
        try:
            self.table = self.dynamodb.Table(self.table_name)
        except Exception as e:
            logging.warning(f"DynamoDB table {self.table_name} not accessible: {e}")
            self.table = None
    
    def set_flag(self, scope: str, state: DriftState, reason: str, 
                 ticket: str = "", approved_by: List[str] = None, 
                 duration_hours: int = 0) -> Dict:
        """Set drift control flag with TTL"""
        
        if not self.table:
            raise RuntimeError("DynamoDB table not available")
        
        approved_by = approved_by or []
        current_time = int(time.time())
        
        # Calculate expiration (0 = no expiration for ENABLED/DISABLED)
        expire_at = None
        auto_resume = False
        
        if duration_hours > 0 and state == DriftState.PAUSED:
            expire_at = current_time + (duration_hours * 3600)
            auto_resume = True
        
        item = {
            "scope": scope,
            "flag_name": "drift_control",
            "state": state.value,
            "reason": reason,
            "ticket": ticket,
            "approved_by": approved_by,
            "created_at": datetime.utcnow().isoformat(),
            "created_timestamp": current_time,
            "auto_resume": auto_resume
        }
        
        if expire_at:
            item["expire_at"] = expire_at
        
        try:
            self.table.put_item(Item=item)
            logging.info(f"Drift flag set: {scope} -> {state.value} (TTL: {duration_hours}h)")
            return item
        except Exception as e:
            logging.error(f"Failed to set drift flag: {e}")
            raise
    
    def get_flag(self, scope: str) -> Dict:
        """Get current drift control flag for scope"""
        
        if not self.table:
            # Fallback to ENABLED if no DynamoDB access
            return {
                "scope": scope,
                "flag_name": "drift_control", 
                "state": DriftState.ENABLED.value,
                "reason": "default_fallback",
                "fallback": True
            }
        
        try:
            response = self.table.get_item(
                Key={"scope": scope, "flag_name": "drift_control"}
            )
            
            item = response.get("Item")
            if not item:
                # No flag set, default to ENABLED
                return {
                    "scope": scope,
                    "flag_name": "drift_control",
                    "state": DriftState.ENABLED.value,
                    "reason": "default_enabled",
                    "default": True
                }
            
            # Check if TTL expired (DynamoDB TTL might have delay)
            current_time = int(time.time())
            expire_at = item.get("expire_at")
            
            if expire_at and current_time >= expire_at:
                # TTL expired, auto-resume to ENABLED
                if item.get("auto_resume", False):
                    logging.info(f"TTL expired for {scope}, auto-resuming drift control")
                    self.set_flag(scope, DriftState.ENABLED, "auto_resume_ttl_expired")
                    item["state"] = DriftState.ENABLED.value
                    item["reason"] = "auto_resume_ttl_expired"
            
            return item
            
        except Exception as e:
            logging.error(f"Failed to get drift flag: {e}")
            # Fallback to ENABLED on error
            return {
                "scope": scope,
                "state": DriftState.ENABLED.value,
                "reason": "error_fallback",
                "error": str(e)
            }
    
    def is_drift_enabled(self, scope: str) -> bool:
        """Check if drift detection is enabled for scope"""
        flag = self.get_flag(scope)
        return flag["state"] == DriftState.ENABLED.value
    
    def is_drift_paused(self, scope: str) -> bool:
        """Check if drift detection is paused for scope"""
        flag = self.get_flag(scope)
        return flag["state"] == DriftState.PAUSED.value
    
    def is_drift_disabled(self, scope: str) -> bool:
        """Check if drift detection is disabled for scope"""
        flag = self.get_flag(scope)
        return flag["state"] == DriftState.DISABLED.value
    
    def get_drift_state(self, scope: str) -> DriftState:
        """Get current drift state as enum"""
        flag = self.get_flag(scope)
        return DriftState(flag["state"])
    
    def pause_drift(self, scope: str, duration_hours: int, reason: str, 
                   ticket: str = "", approved_by: List[str] = None) -> Dict:
        """Pause drift detection for specified duration"""
        return self.set_flag(scope, DriftState.PAUSED, reason, ticket, 
                           approved_by, duration_hours)
    
    def resume_drift(self, scope: str, reason: str = "manual_resume") -> Dict:
        """Resume drift detection (set to ENABLED)"""
        return self.set_flag(scope, DriftState.ENABLED, reason)
    
    def disable_drift(self, scope: str, reason: str, approved_by: List[str] = None) -> Dict:
        """Disable drift detection completely"""
        return self.set_flag(scope, DriftState.DISABLED, reason, "", approved_by)
    
    def list_flags(self, state_filter: Optional[DriftState] = None) -> List[Dict]:
        """List all drift control flags, optionally filtered by state"""
        
        if not self.table:
            return []
        
        try:
            # Scan for all drift_control flags
            response = self.table.scan(
                FilterExpression="flag_name = :flag_name",
                ExpressionAttributeValues={":flag_name": "drift_control"}
            )
            
            items = response.get("Items", [])
            
            # Filter by state if specified
            if state_filter:
                items = [item for item in items if item["state"] == state_filter.value]
            
            return items
            
        except Exception as e:
            logging.error(f"Failed to list drift flags: {e}")
            return []
    
    def get_flag_history(self, scope: str, limit: int = 10) -> List[Dict]:
        """Get history of flag changes for scope (requires additional GSI)"""
        # This would require a GSI on created_timestamp
        # For now, return current flag only
        current_flag = self.get_flag(scope)
        return [current_flag] if not current_flag.get("default") else []

def parse_duration(duration_str: str) -> int:
    """Parse duration string (e.g., '3h', '30m', '2d') to hours"""
    
    duration_str = duration_str.lower().strip()
    
    if duration_str.endswith('h'):
        return int(duration_str[:-1])
    elif duration_str.endswith('m'):
        return int(duration_str[:-1]) / 60
    elif duration_str.endswith('d'):
        return int(duration_str[:-1]) * 24
    else:
        # Assume hours if no unit
        return int(duration_str)

# Global instance for easy import
drift_flag = DriftFlag()

# Convenience functions
def is_drift_enabled(scope: str) -> bool:
    """Check if drift is enabled for scope"""
    return drift_flag.is_drift_enabled(scope)

def get_drift_state(scope: str) -> DriftState:
    """Get drift state for scope"""
    return drift_flag.get_drift_state(scope)

def pause_drift(scope: str, duration_hours: int, reason: str, 
               ticket: str = "", approved_by: List[str] = None) -> Dict:
    """Pause drift for scope"""
    return drift_flag.pause_drift(scope, duration_hours, reason, ticket, approved_by)

def resume_drift(scope: str) -> Dict:
    """Resume drift for scope"""
    return drift_flag.resume_drift(scope)
