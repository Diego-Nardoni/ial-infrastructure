#!/usr/bin/env python3
"""
Budget Configuration - Limites por phase com persistência DynamoDB
"""

import boto3
from typing import Dict
from botocore.exceptions import ClientError

class BudgetConfig:
    """Configuração de limites de budget por phase com persistência"""
    
    def __init__(self):
        self.dynamodb = boto3.client('dynamodb')
        self.table_name = "ial-budget-config"
        
        # Default budget limits per phase (USD/month)
        self.default_limits = {
            '00-foundation': 50.0,      # DynamoDB, S3, Lambda básico
            '10-security': 30.0,        # Security services (~$24 + overhead)
            '20-network': 20.0,         # VPC, subnets, NAT gateway
            '30-compute': 100.0,        # EC2, ECS, ALB
            '40-data': 80.0,           # RDS, DynamoDB workload tables
            '50-application': 60.0,     # Lambda, API Gateway, SQS
            '60-observability': 40.0,   # CloudWatch, X-Ray
            '70-ai-ml': 150.0,         # Bedrock, SageMaker
            '90-governance': 10.0       # Budgets, Config rules
        }
        
        # Ensure table exists
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Ensure DynamoDB table exists for budget config"""
        try:
            self.dynamodb.describe_table(TableName=self.table_name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                self._create_table()
    
    def _create_table(self):
        """Create DynamoDB table for budget config"""
        try:
            self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {'AttributeName': 'phase', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'phase', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST',
                Tags=[
                    {'Key': 'Project', 'Value': 'IAL'},
                    {'Key': 'Component', 'Value': 'BudgetConfig'}
                ]
            )
            
            # Wait for table to be active
            waiter = self.dynamodb.get_waiter('table_exists')
            waiter.wait(TableName=self.table_name)
            
            # Initialize with defaults
            self._initialize_defaults()
            
        except ClientError as e:
            print(f"⚠️ Error creating budget config table: {e}")
    
    def _initialize_defaults(self):
        """Initialize table with default values"""
        for phase, limit in self.default_limits.items():
            try:
                self.dynamodb.put_item(
                    TableName=self.table_name,
                    Item={
                        'phase': {'S': phase},
                        'limit': {'N': str(limit)},
                        'created_at': {'S': str(int(__import__('time').time()))}
                    }
                )
            except Exception as e:
                print(f"⚠️ Error initializing {phase}: {e}")
    
    def set_phase_limit(self, phase: str, limit: float):
        """Set budget limit for a phase with persistence"""
        try:
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item={
                    'phase': {'S': phase},
                    'limit': {'N': str(limit)},
                    'updated_at': {'S': str(int(__import__('time').time()))}
                }
            )
            print(f"✅ Budget limit for {phase} set to ${limit}/month")
        except ClientError as e:
            print(f"❌ Error setting budget limit: {e}")
    
    def get_phase_limit(self, phase: str) -> float:
        """Get budget limit for a phase from DynamoDB"""
        try:
            response = self.dynamodb.get_item(
                TableName=self.table_name,
                Key={'phase': {'S': phase}}
            )
            
            if 'Item' in response:
                return float(response['Item']['limit']['N'])
            else:
                # Return default if not found
                return self.default_limits.get(phase, 50.0)
                
        except ClientError as e:
            print(f"⚠️ Error getting budget limit: {e}")
            return self.default_limits.get(phase, 50.0)
    
    def get_all_limits(self) -> Dict[str, float]:
        """Get all phase limits"""
        limits = {}
        try:
            response = self.dynamodb.scan(TableName=self.table_name)
            
            for item in response.get('Items', []):
                phase = item['phase']['S']
                limit = float(item['limit']['N'])
                limits[phase] = limit
                
        except ClientError as e:
            print(f"⚠️ Error getting all limits: {e}")
            return self.default_limits
        
        # Merge with defaults for missing phases
        for phase, default_limit in self.default_limits.items():
            if phase not in limits:
                limits[phase] = default_limit
                
        return limits
    
    @property
    def total_budget(self) -> float:
        """Calculate total budget from all phases"""
        return sum(self.get_all_limits().values())

# Global instance
budget_config = BudgetConfig()
