#!/usr/bin/env python3
"""
Feature Flags Manager - Controla funcionalidades opcionais do IAL
"""

import boto3
import json
import time
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
            'BUDGET_ENFORCEMENT_ENABLED': True  # Enabled by default with IAM protection
        }
    
    def get_flag(self, flag_name: str) -> bool:
        """Get feature flag value"""
        # Ensure table exists first
        if not hasattr(self, '_table_checked'):
            self.ensure_table_exists()
            self._table_checked = True
            
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
        """Set feature flag value with IAM protection and audit trail"""
        from core.iam_budget_protection import iam_protection
        from core.budget_audit_trail import audit_trail
        
        # Check if this is a budget-related flag that needs protection
        if self._is_budget_flag(flag_name):
            # Enforce IAM permission
            if not iam_protection.enforce_budget_permission(f"Modify {flag_name}"):
                return False
        
        # Get current value for audit trail
        old_value = self.get_flag(flag_name)
        
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
            
            # Log to audit trail if budget-related
            if self._is_budget_flag(flag_name):
                user_info = iam_protection.get_current_user_info()
                audit_trail.log_budget_change(
                    action=f"set_flag",
                    flag_name=flag_name,
                    old_value=old_value,
                    new_value=enabled,
                    user_info=user_info
                )
            
            return True
            
        except ClientError as e:
            print(f"❌ Error setting feature flag {flag_name}: {e}")
            return False
    
    def _is_budget_flag(self, flag_name: str) -> bool:
        """Check if flag is budget-related and needs protection"""
        budget_flags = [
            'BUDGET_ENFORCEMENT_ENABLED',
            'COST_MONITORING_ENABLED'
        ]
        return flag_name in budget_flags or 'BUDGET' in flag_name.upper()
    
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
    
    def ensure_table_exists(self):
        """Ensure DynamoDB table exists, create if not"""
        try:
            # Check if table exists
            self.dynamodb.describe_table(TableName=self.table_name)
            print(f"✅ Feature flags table '{self.table_name}' exists")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"🔧 Creating feature flags table '{self.table_name}'...")
                return self._create_table()
            else:
                print(f"❌ Error checking table: {e}")
                return False
    
    def _create_table(self):
        """Create DynamoDB table for feature flags"""
        try:
            self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {'AttributeName': 'flag_name', 'KeyType': 'HASH'},
                    {'AttributeName': 'environment', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'flag_name', 'AttributeType': 'S'},
                    {'AttributeName': 'environment', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST',
                Tags=[
                    {'Key': 'Project', 'Value': 'IAL'},
                    {'Key': 'Component', 'Value': 'FeatureFlags'},
                    {'Key': 'Environment', 'Value': self.environment}
                ]
            )
            
            # Wait for table to be active
            waiter = self.dynamodb.get_waiter('table_exists')
            waiter.wait(TableName=self.table_name)
            
            print(f"✅ Feature flags table '{self.table_name}' created successfully")
            
            # Initialize with defaults
            self._initialize_defaults()
            return True
            
        except ClientError as e:
            print(f"❌ Error creating table: {e}")
            return False
        """Initialize default feature flags"""
        print("🔧 Initializing default feature flags...")
        
        for flag_name, default_value in self.defaults.items():
            descriptions = {
                'SECURITY_SERVICES_ENABLED': 'Enable AWS Security Services (GuardDuty, Security Hub, etc.) - ~$24/month',
                'WELL_ARCHITECTED_ENABLED': 'Enable Well-Architected Assessment automation',
                'COST_MONITORING_ENABLED': 'Enable cost monitoring and alerting',
                'DRIFT_DETECTION_ENABLED': 'Enable infrastructure drift detection',
                'BUDGET_ENFORCEMENT_ENABLED': 'Enable budget enforcement blocking (enabled by default with IAM protection)'
            }
            
            self.set_flag(
                flag_name, 
                default_value, 
                descriptions.get(flag_name, f"Default flag: {flag_name}")
            )
            
        print("✅ Default feature flags initialized")

    def _initialize_defaults(self):
        """Initialize default feature flags"""
        print("🔧 Initializing default feature flags...")
        
        for flag_name, default_value in self.defaults.items():
            descriptions = {
                'SECURITY_SERVICES_ENABLED': 'Enable AWS Security Services (GuardDuty, Security Hub, etc.) - ~$24/month',
                'WELL_ARCHITECTED_ENABLED': 'Enable Well-Architected Assessment automation',
                'COST_MONITORING_ENABLED': 'Enable cost monitoring and alerting',
                'DRIFT_DETECTION_ENABLED': 'Enable infrastructure drift detection',
                'BUDGET_ENFORCEMENT_ENABLED': 'Enable budget enforcement blocking (enabled by default with IAM protection)'
            }
            
            try:
                self.dynamodb.put_item(
                    TableName=self.table_name,
                    Item={
                        'flag_name': {'S': flag_name},
                        'environment': {'S': self.environment},
                        'enabled': {'BOOL': default_value},
                        'description': {'S': descriptions.get(flag_name, f"Default flag: {flag_name}")},
                        'created_at': {'S': str(int(time.time()))}
                    }
                )
            except Exception as e:
                print(f"⚠️ Error setting default flag {flag_name}: {e}")
            
        print("✅ Default feature flags initialized")

# Global instance
feature_flags = FeatureFlagsManager()
