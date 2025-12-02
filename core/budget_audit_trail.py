#!/usr/bin/env python3
"""
Budget Audit Trail - Log automático de mudanças de budget
"""

import boto3
import json
from datetime import datetime
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

class BudgetAuditTrail:
    """Audit trail para mudanças de budget"""
    
    def __init__(self):
        self.dynamodb = boto3.client('dynamodb')
        self.sns = boto3.client('sns')
        self.audit_table = 'ial-budget-audit-trail'
        self.alert_topic = 'ial-alerts-critical'
        
    def log_budget_change(self, 
                         action: str,
                         flag_name: str, 
                         old_value: Any,
                         new_value: Any,
                         user_info: Dict[str, str]) -> bool:
        """Log budget change to audit trail"""
        
        try:
            timestamp = datetime.utcnow().isoformat()
            audit_id = f"{timestamp}_{user_info.get('user_id', 'unknown')}"
            
            # Prepare audit record
            audit_record = {
                'audit_id': {'S': audit_id},
                'timestamp': {'S': timestamp},
                'action': {'S': action},
                'flag_name': {'S': flag_name},
                'old_value': {'S': str(old_value)},
                'new_value': {'S': str(new_value)},
                'user_id': {'S': user_info.get('user_id', 'unknown')},
                'user_name': {'S': user_info.get('user_name', 'unknown')},
                'user_arn': {'S': user_info.get('arn', 'unknown')},
                'account': {'S': user_info.get('account', 'unknown')},
                'change_type': {'S': self._classify_change(flag_name, old_value, new_value)},
                'severity': {'S': self._assess_severity(flag_name, old_value, new_value)}
            }
            
            # Try to save to DynamoDB audit table
            try:
                self.dynamodb.put_item(
                    TableName=self.audit_table,
                    Item=audit_record
                )
                print(f"📝 Audit logged: {action} by {user_info.get('user_name', 'unknown')}")
                
            except ClientError as e:
                if 'ResourceNotFoundException' in str(e):
                    # Audit table doesn't exist, log to console
                    print(f"📝 Audit (console): {action} by {user_info.get('user_name', 'unknown')}")
                    print(f"   {flag_name}: {old_value} → {new_value}")
                else:
                    print(f"⚠️ Audit logging failed: {e}")
            
            # Send alert if significant change
            if self._is_significant_change(flag_name, old_value, new_value):
                self._send_alert(action, flag_name, old_value, new_value, user_info)
            
            return True
            
        except Exception as e:
            print(f"❌ Audit trail error: {e}")
            return False
    
    def _classify_change(self, flag_name: str, old_value: Any, new_value: Any) -> str:
        """Classify type of change"""
        if 'BUDGET' in flag_name.upper():
            if 'ENFORCEMENT' in flag_name.upper():
                return 'enforcement_toggle'
            else:
                return 'budget_limit_change'
        return 'config_change'
    
    def _assess_severity(self, flag_name: str, old_value: Any, new_value: Any) -> str:
        """Assess severity of change"""
        if 'BUDGET_ENFORCEMENT_ENABLED' == flag_name:
            if old_value == True and new_value == False:
                return 'HIGH'  # Disabling budget enforcement
            elif old_value == False and new_value == True:
                return 'MEDIUM'  # Enabling budget enforcement
        
        if 'BUDGET' in flag_name.upper() and flag_name != 'BUDGET_ENFORCEMENT_ENABLED':
            try:
                old_val = float(old_value)
                new_val = float(new_value)
                if new_val > old_val * 2:  # 100% increase
                    return 'HIGH'
                elif new_val > old_val * 1.5:  # 50% increase
                    return 'MEDIUM'
            except:
                pass
        
        return 'LOW'
    
    def _is_significant_change(self, flag_name: str, old_value: Any, new_value: Any) -> bool:
        """Determine if change requires alert"""
        severity = self._assess_severity(flag_name, old_value, new_value)
        return severity in ['HIGH', 'MEDIUM']
    
    def _send_alert(self, action: str, flag_name: str, old_value: Any, new_value: Any, user_info: Dict[str, str]):
        """Send SNS alert for significant changes"""
        try:
            severity = self._assess_severity(flag_name, old_value, new_value)
            
            message = f"""
🚨 IAL BUDGET CONFIGURATION CHANGE

Action: {action}
Flag: {flag_name}
Change: {old_value} → {new_value}
Severity: {severity}

User: {user_info.get('user_name', 'unknown')}
Account: {user_info.get('account', 'unknown')}
Time: {datetime.utcnow().isoformat()}

This change may impact cost controls and budget enforcement.
Review immediately if unauthorized.
            """.strip()
            
            # Try to send SNS alert
            try:
                topic_arn = f"arn:aws:sns:{boto3.Session().region_name}:{user_info.get('account', 'unknown')}:{self.alert_topic}"
                
                self.sns.publish(
                    TopicArn=topic_arn,
                    Subject=f"IAL Budget Change Alert - {severity}",
                    Message=message
                )
                print(f"🚨 Alert sent: {severity} budget change")
                
            except ClientError as e:
                if 'NotFound' in str(e):
                    print(f"⚠️ SNS topic not found: {self.alert_topic}")
                else:
                    print(f"⚠️ Alert sending failed: {e}")
                    
        except Exception as e:
            print(f"❌ Alert error: {e}")

# Global instance
audit_trail = BudgetAuditTrail()
