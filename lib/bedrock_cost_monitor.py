#!/usr/bin/env python3
"""
IaL Bedrock Cost Monitor
Real-time cost tracking and optimization for Bedrock usage
"""

import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class BedrockCostMonitor:
    def __init__(self, region='us-east-1'):
        self.dynamodb = boto3.client('dynamodb', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        
        # Bedrock pricing (per 1M tokens)
        self.pricing = {
            'anthropic.claude-3-5-sonnet-20241022-v2:0': {
                'input': 0.003,   # $3 per 1M input tokens
                'output': 0.015   # $15 per 1M output tokens
            },
            'anthropic.claude-3-haiku-20240307-v1:0': {
                'input': 0.00025, # $0.25 per 1M input tokens
                'output': 0.00125 # $1.25 per 1M output tokens
            }
        }
        
        # Cost thresholds
        self.thresholds = {
            'daily_warning': 2.0,    # $2/day
            'daily_critical': 5.0,   # $5/day
            'monthly_warning': 40.0, # $40/month
            'monthly_critical': 80.0 # $80/month
        }

    def track_token_usage(self, user_id: str, model_id: str, input_tokens: int, output_tokens: int):
        """Track token usage for cost calculation"""
        
        now = datetime.now()
        date_hour = now.strftime('%Y-%m-%d-%H')
        
        # Calculate cost
        model_pricing = self.pricing.get(model_id, {'input': 0, 'output': 0})
        input_cost = (input_tokens / 1_000_000) * model_pricing['input']
        output_cost = (output_tokens / 1_000_000) * model_pricing['output']
        total_cost = input_cost + output_cost
        
        try:
            # Store in DynamoDB
            self.dynamodb.update_item(
                TableName='ial-token-usage',
                Key={
                    'user_id': {'S': user_id},
                    'date_hour': {'S': date_hour}
                },
                UpdateExpression='ADD input_tokens :input, output_tokens :output, total_cost :cost SET model_id = :model, updated_at = :timestamp',
                ExpressionAttributeValues={
                    ':input': {'N': str(input_tokens)},
                    ':output': {'N': str(output_tokens)},
                    ':cost': {'N': str(total_cost)},
                    ':model': {'S': model_id},
                    ':timestamp': {'S': now.isoformat()}
                }
            )
            
            # Send metrics to CloudWatch
            self.cloudwatch.put_metric_data(
                Namespace='IaL/Conversations',
                MetricData=[
                    {
                        'MetricName': 'TokensUsed',
                        'Dimensions': [
                            {'Name': 'Model', 'Value': model_id.split('.')[-1].split('-')[0]},
                            {'Name': 'UserId', 'Value': user_id}
                        ],
                        'Value': input_tokens + output_tokens,
                        'Unit': 'Count'
                    },
                    {
                        'MetricName': 'CostIncurred',
                        'Dimensions': [
                            {'Name': 'Model', 'Value': model_id.split('.')[-1].split('-')[0]},
                            {'Name': 'UserId', 'Value': user_id}
                        ],
                        'Value': total_cost,
                        'Unit': 'None'
                    }
                ]
            )
            
            # Check thresholds
            self.check_cost_thresholds(user_id)
            
        except Exception as e:
            print(f"Error tracking token usage: {e}")

    def get_daily_usage(self, user_id: str, date: str = None) -> Dict:
        """Get daily token usage and cost for a user"""
        
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            response = self.dynamodb.query(
                TableName='ial-token-usage',
                KeyConditionExpression='user_id = :user_id AND begins_with(date_hour, :date)',
                ExpressionAttributeValues={
                    ':user_id': {'S': user_id},
                    ':date': {'S': date}
                }
            )
            
            total_input = 0
            total_output = 0
            total_cost = 0.0
            model_breakdown = {}
            
            for item in response.get('Items', []):
                input_tokens = int(item.get('input_tokens', {}).get('N', '0'))
                output_tokens = int(item.get('output_tokens', {}).get('N', '0'))
                cost = float(item.get('total_cost', {}).get('N', '0'))
                model = item.get('model_id', {}).get('S', 'unknown')
                
                total_input += input_tokens
                total_output += output_tokens
                total_cost += cost
                
                model_name = model.split('.')[-1].split('-')[0] if '.' in model else model
                if model_name not in model_breakdown:
                    model_breakdown[model_name] = {'input': 0, 'output': 0, 'cost': 0.0}
                
                model_breakdown[model_name]['input'] += input_tokens
                model_breakdown[model_name]['output'] += output_tokens
                model_breakdown[model_name]['cost'] += cost
            
            return {
                'date': date,
                'total_input_tokens': total_input,
                'total_output_tokens': total_output,
                'total_cost': round(total_cost, 4),
                'model_breakdown': model_breakdown
            }
            
        except Exception as e:
            print(f"Error getting daily usage: {e}")
            return {}

    def get_monthly_usage(self, user_id: str, year_month: str = None) -> Dict:
        """Get monthly token usage and cost for a user"""
        
        if not year_month:
            year_month = datetime.now().strftime('%Y-%m')
        
        try:
            response = self.dynamodb.query(
                TableName='ial-token-usage',
                KeyConditionExpression='user_id = :user_id AND begins_with(date_hour, :month)',
                ExpressionAttributeValues={
                    ':user_id': {'S': user_id},
                    ':month': {'S': year_month}
                }
            )
            
            total_input = 0
            total_output = 0
            total_cost = 0.0
            daily_breakdown = {}
            model_breakdown = {}
            
            for item in response.get('Items', []):
                input_tokens = int(item.get('input_tokens', {}).get('N', '0'))
                output_tokens = int(item.get('output_tokens', {}).get('N', '0'))
                cost = float(item.get('total_cost', {}).get('N', '0'))
                model = item.get('model_id', {}).get('S', 'unknown')
                date_hour = item.get('date_hour', {}).get('S', '')
                date = date_hour.split('-')[:3]  # Extract date part
                date_key = '-'.join(date) if len(date) >= 3 else 'unknown'
                
                total_input += input_tokens
                total_output += output_tokens
                total_cost += cost
                
                # Daily breakdown
                if date_key not in daily_breakdown:
                    daily_breakdown[date_key] = {'input': 0, 'output': 0, 'cost': 0.0}
                daily_breakdown[date_key]['input'] += input_tokens
                daily_breakdown[date_key]['output'] += output_tokens
                daily_breakdown[date_key]['cost'] += cost
                
                # Model breakdown
                model_name = model.split('.')[-1].split('-')[0] if '.' in model else model
                if model_name not in model_breakdown:
                    model_breakdown[model_name] = {'input': 0, 'output': 0, 'cost': 0.0}
                model_breakdown[model_name]['input'] += input_tokens
                model_breakdown[model_name]['output'] += output_tokens
                model_breakdown[model_name]['cost'] += cost
            
            return {
                'year_month': year_month,
                'total_input_tokens': total_input,
                'total_output_tokens': total_output,
                'total_cost': round(total_cost, 4),
                'daily_breakdown': daily_breakdown,
                'model_breakdown': model_breakdown
            }
            
        except Exception as e:
            print(f"Error getting monthly usage: {e}")
            return {}

    def check_cost_thresholds(self, user_id: str):
        """Check if cost thresholds are exceeded and send alerts"""
        
        # Check daily usage
        daily_usage = self.get_daily_usage(user_id)
        daily_cost = daily_usage.get('total_cost', 0)
        
        if daily_cost >= self.thresholds['daily_critical']:
            self.send_cost_alert(user_id, 'CRITICAL', 'daily', daily_cost)
        elif daily_cost >= self.thresholds['daily_warning']:
            self.send_cost_alert(user_id, 'WARNING', 'daily', daily_cost)
        
        # Check monthly usage
        monthly_usage = self.get_monthly_usage(user_id)
        monthly_cost = monthly_usage.get('total_cost', 0)
        
        if monthly_cost >= self.thresholds['monthly_critical']:
            self.send_cost_alert(user_id, 'CRITICAL', 'monthly', monthly_cost)
        elif monthly_cost >= self.thresholds['monthly_warning']:
            self.send_cost_alert(user_id, 'WARNING', 'monthly', monthly_cost)

    def send_cost_alert(self, user_id: str, severity: str, period: str, cost: float):
        """Send cost alert via SNS"""
        
        try:
            message = f"""
🚨 IaL Bedrock Cost Alert - {severity}

User: {user_id}
Period: {period}
Cost: ${cost:.4f}
Threshold: ${self.thresholds[f'{period}_{severity.lower()}']}

Please review your Bedrock usage and consider optimization strategies.
            """
            
            # Send to SNS topic (if configured)
            # self.sns.publish(
            #     TopicArn='arn:aws:sns:region:account:ial-cost-alerts',
            #     Message=message,
            #     Subject=f'IaL Bedrock Cost Alert - {severity}'
            # )
            
            print(f"Cost alert sent: {severity} - {period} cost ${cost:.4f}")
            
        except Exception as e:
            print(f"Error sending cost alert: {e}")

    def get_cost_optimization_suggestions(self, user_id: str) -> List[str]:
        """Get cost optimization suggestions based on usage patterns"""
        
        monthly_usage = self.get_monthly_usage(user_id)
        suggestions = []
        
        if not monthly_usage:
            return suggestions
        
        model_breakdown = monthly_usage.get('model_breakdown', {})
        total_cost = monthly_usage.get('total_cost', 0)
        
        # Suggest using Haiku for simple tasks
        if 'sonnet' in model_breakdown and 'haiku' in model_breakdown:
            sonnet_cost = model_breakdown['sonnet'].get('cost', 0)
            haiku_cost = model_breakdown['haiku'].get('cost', 0)
            
            if sonnet_cost > haiku_cost * 3:
                suggestions.append("💡 Consider using Claude Haiku for simple status checks and basic questions to reduce costs by up to 90%")
        
        # Suggest conversation caching
        if total_cost > 10:
            suggestions.append("💡 Implement conversation caching for frequently asked questions to reduce token usage")
        
        # Suggest rate limiting
        daily_breakdown = monthly_usage.get('daily_breakdown', {})
        high_usage_days = [day for day, data in daily_breakdown.items() if data.get('cost', 0) > 3]
        
        if len(high_usage_days) > 5:
            suggestions.append("💡 Consider implementing rate limiting to control daily usage spikes")
        
        # Suggest conversation summarization
        total_tokens = monthly_usage.get('total_input_tokens', 0) + monthly_usage.get('total_output_tokens', 0)
        if total_tokens > 1_000_000:
            suggestions.append("💡 Implement conversation summarization to reduce context window size and token usage")
        
        return suggestions

# Example usage
if __name__ == "__main__":
    monitor = BedrockCostMonitor()
    
    # Test cost tracking
    test_user = "test-user-123"
    
    # Simulate token usage
    monitor.track_token_usage(
        user_id=test_user,
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        input_tokens=1500,
        output_tokens=800
    )
    
    # Get usage reports
    daily_usage = monitor.get_daily_usage(test_user)
    monthly_usage = monitor.get_monthly_usage(test_user)
    suggestions = monitor.get_cost_optimization_suggestions(test_user)
    
    print("📊 Daily Usage:", daily_usage)
    print("📊 Monthly Usage:", monthly_usage)
    print("💡 Optimization Suggestions:", suggestions)
