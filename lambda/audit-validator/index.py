import json
import boto3
import os

def lambda_handler(event, context):
    """Audit validator Lambda function"""
    
    # Initialize AWS clients
    sns = boto3.client('sns')
    
    # Get environment variables
    sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')
    
    try:
        # Get validation request
        phase = event.get('phase')
        resources = event.get('resources', [])
        
        # Basic validation logic
        validation_result = validate_phase(phase, resources)
        
        # Send alert if validation failed
        if validation_result == 'FAIL' and sns_topic_arn:
            message = f"Validation failed for phase: {phase}"
            sns.publish(
                TopicArn=sns_topic_arn,
                Message=message,
                Subject="IAL Audit Validation Failed"
            )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'validation_result': validation_result,
                'phase': phase,
                'resources_validated': len(resources)
            })
        }
        
    except Exception as e:
        print(f"Error in audit validator: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def validate_phase(phase, resources):
    """Validate phase resources"""
    # Placeholder validation logic
    if not phase or not resources:
        return 'FAIL'
    
    # Basic validation checks
    for resource in resources:
        if not resource.get('type') or not resource.get('name'):
            return 'FAIL'
    
    return 'PASS'
