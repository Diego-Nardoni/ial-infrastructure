"""
Circuit Breaker Metrics Publisher
Publishes circuit breaker state changes to CloudWatch
"""

import boto3
import json
import time
from datetime import datetime
from typing import Dict, Any

class CircuitBreakerMetrics:
    def __init__(self, namespace: str = "IAL/CircuitBreaker"):
        self.cloudwatch = boto3.client('cloudwatch')
        self.namespace = namespace
    
    def publish_state_change(self, service: str, old_state: str, new_state: str, 
                           failure_count: int = 0, success_count: int = 0):
        """Publish circuit breaker state change metrics"""
        
        timestamp = datetime.utcnow()
        
        metrics = [
            {
                'MetricName': 'CircuitBreakerState',
                'Dimensions': [
                    {'Name': 'Service', 'Value': service},
                    {'Name': 'Environment', 'Value': 'prod'}
                ],
                'Value': self._state_to_numeric(new_state),
                'Unit': 'None',
                'Timestamp': timestamp
            },
            {
                'MetricName': 'CircuitBreakerFailures',
                'Dimensions': [
                    {'Name': 'Service', 'Value': service},
                    {'Name': 'Environment', 'Value': 'prod'}
                ],
                'Value': failure_count,
                'Unit': 'Count',
                'Timestamp': timestamp
            },
            {
                'MetricName': 'CircuitBreakerSuccesses',
                'Dimensions': [
                    {'Name': 'Service', 'Value': service},
                    {'Name': 'Environment', 'Value': 'prod'}
                ],
                'Value': success_count,
                'Unit': 'Count',
                'Timestamp': timestamp
            }
        ]
        
        try:
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=metrics
            )
            print(f"✅ Published metrics for {service}: {old_state} → {new_state}")
        except Exception as e:
            print(f"❌ Failed to publish metrics: {e}")
    
    def _state_to_numeric(self, state: str) -> float:
        """Convert circuit breaker state to numeric value"""
        state_map = {
            'CLOSED': 0.0,
            'HALF_OPEN': 0.5,
            'OPEN': 1.0
        }
        return state_map.get(state.upper(), -1.0)

def lambda_handler(event, context):
    """Lambda handler for SSM Parameter change events"""
    
    metrics_publisher = CircuitBreakerMetrics()
    
    try:
        # Parse SSM Parameter change event
        for record in event.get('Records', []):
            if record.get('eventSource') == 'aws:ssm':
                parameter_name = record['eventSourceARN'].split('/')[-1]
                
                if 'circuit-breaker' in parameter_name:
                    # Extract service name from parameter
                    service = parameter_name.replace('circuit-breaker-', '').replace('-state', '')
                    
                    # Get current parameter value
                    ssm = boto3.client('ssm')
                    response = ssm.get_parameter(Name=parameter_name)
                    
                    parameter_data = json.loads(response['Parameter']['Value'])
                    
                    metrics_publisher.publish_state_change(
                        service=service,
                        old_state=parameter_data.get('previous_state', 'UNKNOWN'),
                        new_state=parameter_data.get('current_state', 'UNKNOWN'),
                        failure_count=parameter_data.get('failure_count', 0),
                        success_count=parameter_data.get('success_count', 0)
                    )
        
        return {
            'statusCode': 200,
            'body': json.dumps('Metrics published successfully')
        }
        
    except Exception as e:
        print(f"❌ Error processing event: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }
