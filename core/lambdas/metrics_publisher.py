"""
Circuit Breaker Metrics Publisher Lambda Function
Triggered by SSM Parameter Store changes to publish CloudWatch metrics
"""

import json
import boto3
import os
from datetime import datetime
from typing import Dict, Any

# Initialize AWS clients
cloudwatch = boto3.client('cloudwatch')
ssm = boto3.client('ssm')

def lambda_handler(event, context):
    """
    Lambda function handler for SSM Parameter Store changes
    Publishes circuit breaker state changes to CloudWatch metrics
    """
    try:
        print(f"Received event: {json.dumps(event)}")
        
        # Handle CloudWatch Events (SSM Parameter changes)
        if 'source' in event and event['source'] == 'aws.ssm':
            return handle_ssm_parameter_change(event, context)
        
        # Handle direct invocation for testing
        elif 'test' in event:
            return handle_test_invocation(event, context)
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Unsupported event type'})
            }
            
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def handle_ssm_parameter_change(event, context):
    """Handle SSM Parameter Store change events"""
    try:
        detail = event.get('detail', {})
        parameter_name = detail.get('name', '')
        new_value = detail.get('value', '')
        operation = detail.get('operation', '')
        
        print(f"SSM Parameter change: {parameter_name} = {new_value} ({operation})")
        
        # Check if this is a circuit breaker parameter
        if '/circuit_breaker/' not in parameter_name or not parameter_name.endswith('/state'):
            print(f"Ignoring non-circuit-breaker parameter: {parameter_name}")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Parameter ignored (not circuit breaker)'})
            }
        
        # Extract service name from parameter path
        # Expected format: /ial/circuit_breaker/{service}/state
        try:
            service = parameter_name.split('/circuit_breaker/')[1].split('/state')[0]
        except IndexError:
            raise ValueError(f"Invalid parameter name format: {parameter_name}")
        
        # Validate state value
        valid_states = ['open', 'closed', 'half_open']
        if new_value not in valid_states:
            raise ValueError(f"Invalid circuit breaker state: {new_value}")
        
        # Get previous state from parameter history (if available)
        old_state = get_previous_state(parameter_name)
        
        # Publish metrics to CloudWatch
        success = publish_circuit_breaker_metrics(
            service=service,
            old_state=old_state,
            new_state=new_value,
            timestamp=datetime.utcnow()
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Circuit breaker metrics published for {service}',
                'success': success,
                'service': service,
                'old_state': old_state,
                'new_state': new_value,
                'parameter_name': parameter_name
            })
        }
        
    except Exception as e:
        print(f"Error handling SSM parameter change: {e}")
        raise

def handle_test_invocation(event, context):
    """Handle test invocations for debugging"""
    try:
        test_data = event.get('test', {})
        service = test_data.get('service', 'test-service')
        old_state = test_data.get('old_state', 'closed')
        new_state = test_data.get('new_state', 'open')
        
        success = publish_circuit_breaker_metrics(
            service=service,
            old_state=old_state,
            new_state=new_state,
            timestamp=datetime.utcnow()
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Test metrics published',
                'success': success,
                'service': service,
                'old_state': old_state,
                'new_state': new_state
            })
        }
        
    except Exception as e:
        print(f"Error in test invocation: {e}")
        raise

def get_previous_state(parameter_name: str) -> str:
    """Get the previous state of the circuit breaker parameter"""
    try:
        # Try to get parameter history
        response = ssm.get_parameter_history(
            Name=parameter_name,
            MaxResults=2  # Current + previous
        )
        
        parameters = response.get('Parameters', [])
        if len(parameters) >= 2:
            # Return the second most recent value (previous state)
            return parameters[1]['Value']
        else:
            # Default to closed if no history available
            return 'closed'
            
    except Exception as e:
        print(f"Could not get parameter history for {parameter_name}: {e}")
        return 'closed'  # Default fallback

def publish_circuit_breaker_metrics(service: str, 
                                   old_state: str, 
                                   new_state: str, 
                                   timestamp: datetime) -> bool:
    """Publish circuit breaker metrics to CloudWatch"""
    try:
        namespace = "IAL/CircuitBreaker"
        environment = os.environ.get('ENVIRONMENT', 'prod')
        
        # Convert states to numeric values for easier graphing
        state_values = {
            'closed': 0.0,
            'half_open': 0.5,
            'open': 1.0
        }
        
        metric_data = [
            # Current state metric
            {
                'MetricName': 'CircuitBreakerState',
                'Dimensions': [
                    {'Name': 'Service', 'Value': service},
                    {'Name': 'Environment', 'Value': environment}
                ],
                'Value': state_values.get(new_state, -1.0),
                'Unit': 'None',
                'Timestamp': timestamp
            },
            # State transition counter
            {
                'MetricName': 'StateTransition',
                'Dimensions': [
                    {'Name': 'Service', 'Value': service},
                    {'Name': 'Environment', 'Value': environment},
                    {'Name': 'FromState', 'Value': old_state},
                    {'Name': 'ToState', 'Value': new_state}
                ],
                'Value': 1,
                'Unit': 'Count',
                'Timestamp': timestamp
            }
        ]
        
        # Add specific metrics for state changes
        if new_state == 'open':
            metric_data.append({
                'MetricName': 'CircuitBreakerOpened',
                'Dimensions': [
                    {'Name': 'Service', 'Value': service},
                    {'Name': 'Environment', 'Value': environment}
                ],
                'Value': 1,
                'Unit': 'Count',
                'Timestamp': timestamp
            })
        elif new_state == 'closed' and old_state in ['open', 'half_open']:
            metric_data.append({
                'MetricName': 'CircuitBreakerClosed',
                'Dimensions': [
                    {'Name': 'Service', 'Value': service},
                    {'Name': 'Environment', 'Value': environment}
                ],
                'Value': 1,
                'Unit': 'Count',
                'Timestamp': timestamp
            })
        
        # Publish metrics to CloudWatch
        response = cloudwatch.put_metric_data(
            Namespace=namespace,
            MetricData=metric_data
        )
        
        print(f"✅ Published {len(metric_data)} metrics for {service}: {old_state} → {new_state}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to publish metrics: {e}")
        return False

# For local testing
if __name__ == "__main__":
    # Test event simulation
    test_event = {
        "source": "aws.ssm",
        "detail": {
            "name": "/ial/circuit_breaker/bedrock-api/state",
            "value": "open",
            "operation": "Update"
        }
    }
    
    result = lambda_handler(test_event, None)
    print(f"Test result: {result}")
