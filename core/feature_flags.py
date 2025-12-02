#!/usr/bin/env python3
"""
Feature Flags Manager - Controla funcionalidades opcionais do IAL
"""

import boto3
import json
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

class FeatureFlagsManager:
    def __init__(self, table_name: str = "ial-feature-flags", environment: str = "default"):
        self.dynamodb = boto3.client('dynamodb')
        self.table_name = table_name
        self.environment = environment
        
        # Default feature flags
        self.defaults = {
            'SECURITY_SERVICES_ENABLED': True,
            'WELL_ARCHITECTED_ENABLED': True,
            'COST_MONITORING_ENABLED': True,
            'DRIFT_DETECTION_ENABLED': True,
            'BUDGET_ENFORCEMENT_ENABLED': False  # Disabled by default
        }
    
    def get_flag(self, flag_name: str) -> bool:
        """Get feature flag value"""
        try:
            response = self.dynamodb.get_item(
                TableName=self.table_name,
                Key={
                    'flag_name': {'S': flag_name},
                    'environment': {'S': self.environment}
                }
            )
            
            if 'Item' in response:
                return response['Item']['enabled']['BOOL']
            else:
                # Return default if not found
                return self.defaults.get(flag_name, False)
                
        except ClientError as e:
            print(f"⚠️ Error getting feature flag {flag_name}: {e}")
            return self.defaults.get(flag_name, False)
    
    def set_flag(self, flag_name: str, enabled: bool, description: str = "") -> bool:
        """Set feature flag value"""
        try:
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item={
                    'flag_name': {'S': flag_name},
                    'environment': {'S': self.environment},
                    'enabled': {'BOOL': enabled},
                    'description': {'S': description},
                    'updated_at': {'S': boto3.Session().region_name}  # Timestamp placeholder
                }
            )
            return True
            
        except ClientError as e:
            print(f"❌ Error setting feature flag {flag_name}: {e}")
            return False
    
    def get_all_flags(self) -> Dict[str, bool]:
        """Get all feature flags"""
        flags = {}
        
        try:
            response = self.dynamodb.query(
                TableName=self.table_name,
                KeyConditionExpression='environment = :env',
                ExpressionAttributeValues={
                    ':env': {'S': self.environment}
                }
            )
            
            for item in response.get('Items', []):
                flag_name = item['flag_name']['S']
                enabled = item['enabled']['BOOL']
                flags[flag_name] = enabled
                
        except ClientError as e:
            print(f"⚠️ Error getting all flags: {e}")
        
        # Merge with defaults
        for flag, default_value in self.defaults.items():
            if flag not in flags:
                flags[flag] = default_value
                
        return flags
    
    def initialize_defaults(self):
        """Initialize default feature flags"""
        print("🔧 Initializing default feature flags...")
        
        for flag_name, default_value in self.defaults.items():
            descriptions = {
                'SECURITY_SERVICES_ENABLED': 'Enable AWS Security Services (GuardDuty, Security Hub, etc.) - ~$24/month',
                'WELL_ARCHITECTED_ENABLED': 'Enable Well-Architected Assessment automation',
                'COST_MONITORING_ENABLED': 'Enable cost monitoring and alerting',
                'DRIFT_DETECTION_ENABLED': 'Enable infrastructure drift detection',
                'BUDGET_ENFORCEMENT_ENABLED': 'Enable budget enforcement blocking (disabled by default for safety)'
            }
            
            self.set_flag(
                flag_name, 
                default_value, 
                descriptions.get(flag_name, f"Default flag: {flag_name}")
            )
            
        print("✅ Default feature flags initialized")

# Global instance
feature_flags = FeatureFlagsManager()
