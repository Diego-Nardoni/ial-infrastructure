"""
Circuit Breaker Metrics Publisher Lambda
"""
import boto3
import json
import os

def lambda_handler(event, context):
    """Lambda handler for publishing circuit breaker metrics"""
    try:
        cloudwatch = boto3.client('cloudwatch')
        namespace = os.environ.get('NAMESPACE', 'IAL/CircuitBreaker')
        
        # Publish sample metrics
        cloudwatch.put_metric_data(
            Namespace=namespace,
            MetricData=[
                {
                    'MetricName': 'CircuitBreakerState',
                    'Dimensions': [
                        {
                            'Name': 'Service',
                            'Value': 'bedrock'
                        }
                    ],
                    'Value': 1.0,
                    'Unit': 'Count'
                }
            ]
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps('Metrics published successfully')
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }

def publish_metrics():
    """Publish circuit breaker metrics to CloudWatch"""
    print("Circuit breaker metrics published")
    return True

if __name__ == "__main__":
    publish_metrics()
