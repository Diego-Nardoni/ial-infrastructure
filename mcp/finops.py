#!/usr/bin/env python3
"""
MCP FinOps Module - Budget and Cost Management
"""

import boto3
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

class FinOpsBudgetManager:
    def __init__(self):
        self.budgets = boto3.client('budgets')
        self.ce = boto3.client('ce')  # Cost Explorer
        
    def check_budget_status(self, budget_name: str = "ial-monthly-budget") -> Dict[str, Any]:
        """Check current budget status"""
        try:
            response = self.budgets.describe_budget(
                AccountId=boto3.client('sts').get_caller_identity()['Account'],
                BudgetName=budget_name
            )
            
            budget = response['Budget']
            return {
                'status': 'success',
                'budget_limit': float(budget['BudgetLimit']['Amount']),
                'budget_unit': budget['BudgetLimit']['Unit'],
                'time_period': budget['TimePeriod'],
                'budget_type': budget['BudgetType']
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NotFoundException':
                return {
                    'status': 'not_found',
                    'message': f"Budget '{budget_name}' not found"
                }
            else:
                return {
                    'status': 'error',
                    'message': str(e)
                }
    
    def get_current_spend(self) -> Dict[str, Any]:
        """Get current month spend"""
        try:
            import datetime
            
            # Current month
            now = datetime.datetime.now()
            start_date = now.replace(day=1).strftime('%Y-%m-%d')
            end_date = now.strftime('%Y-%m-%d')
            
            response = self.ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost']
            )
            
            if response['ResultsByTime']:
                amount = response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount']
                return {
                    'status': 'success',
                    'current_spend': float(amount),
                    'currency': 'USD',
                    'period': f"{start_date} to {end_date}"
                }
            else:
                return {
                    'status': 'no_data',
                    'current_spend': 0.0,
                    'currency': 'USD'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'current_spend': 0.0
            }
    
    def validate_budget_compliance(self, budget_limit: float = 50.0) -> Dict[str, Any]:
        """Validate if current spend is within budget"""
        spend_info = self.get_current_spend()
        
        if spend_info['status'] == 'success':
            current_spend = spend_info['current_spend']
            compliance = current_spend <= budget_limit
            
            return {
                'compliant': compliance,
                'current_spend': current_spend,
                'budget_limit': budget_limit,
                'remaining': budget_limit - current_spend,
                'utilization_percent': (current_spend / budget_limit) * 100
            }
        else:
            # If we can't get spend data, assume compliant but warn
            return {
                'compliant': True,
                'current_spend': 0.0,
                'budget_limit': budget_limit,
                'remaining': budget_limit,
                'utilization_percent': 0.0,
                'warning': 'Could not retrieve spend data'
            }

# Global instance
finops_manager = FinOpsBudgetManager()
