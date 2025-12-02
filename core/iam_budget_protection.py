#!/usr/bin/env python3
"""
IAM Budget Protection - Controle de permissões para modificações de budget
"""

import boto3
import json
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

class IAMBudgetProtection:
    """Proteção IAM para modificações de budget"""
    
    def __init__(self):
        self.sts = boto3.client('sts')
        self.iam = boto3.client('iam')
        
    def get_current_user_info(self) -> Dict[str, str]:
        """Get current user/role information"""
        try:
            identity = self.sts.get_caller_identity()
            return {
                'user_id': identity.get('UserId', 'unknown'),
                'account': identity.get('Account', 'unknown'),
                'arn': identity.get('Arn', 'unknown'),
                'user_name': self._extract_user_name(identity.get('Arn', ''))
            }
        except Exception as e:
            return {
                'user_id': 'unknown',
                'account': 'unknown', 
                'arn': 'unknown',
                'user_name': 'unknown',
                'error': str(e)
            }
    
    def _extract_user_name(self, arn: str) -> str:
        """Extract user name from ARN"""
        if ':user/' in arn:
            return arn.split(':user/')[-1]
        elif ':role/' in arn:
            return arn.split(':role/')[-1]
        elif ':assumed-role/' in arn:
            parts = arn.split(':assumed-role/')[-1].split('/')
            return f"{parts[0]}/{parts[1]}" if len(parts) > 1 else parts[0]
        return 'unknown'
    
    def check_budget_modify_permission(self) -> Dict[str, Any]:
        """Check if current user has permission to modify budgets"""
        try:
            # Simulate IAM policy check by attempting DynamoDB access
            # In real implementation, this would check specific IAM permissions
            
            user_info = self.get_current_user_info()
            
            # For now, allow if user has DynamoDB access to feature flags table
            dynamodb = boto3.client('dynamodb')
            
            # Test access to feature flags table
            try:
                dynamodb.describe_table(TableName='ial-feature-flags')
                has_permission = True
                reason = "User has DynamoDB access to feature flags table"
            except ClientError as e:
                if 'AccessDenied' in str(e):
                    has_permission = False
                    reason = "Access denied to DynamoDB feature flags table"
                else:
                    # Table doesn't exist, assume permission for now
                    has_permission = True
                    reason = "Feature flags table not found, assuming permission"
            
            return {
                'has_permission': has_permission,
                'user_info': user_info,
                'reason': reason,
                'required_permission': 'ial:ModifyBudget (simulated via DynamoDB access)'
            }
            
        except Exception as e:
            return {
                'has_permission': False,
                'user_info': self.get_current_user_info(),
                'reason': f"Error checking permissions: {e}",
                'required_permission': 'ial:ModifyBudget'
            }
    
    def enforce_budget_permission(self, action: str) -> bool:
        """Enforce budget modification permission"""
        permission_check = self.check_budget_modify_permission()
        
        if not permission_check['has_permission']:
            print(f"❌ ACCESS DENIED: {action}")
            print(f"   User: {permission_check['user_info']['user_name']}")
            print(f"   Reason: {permission_check['reason']}")
            print(f"   Required: {permission_check['required_permission']}")
            print(f"")
            print(f"   Contact your administrator to grant budget modification permissions.")
            return False
        
        print(f"✅ ACCESS GRANTED: {action}")
        print(f"   User: {permission_check['user_info']['user_name']}")
        return True

# Global instance
iam_protection = IAMBudgetProtection()
