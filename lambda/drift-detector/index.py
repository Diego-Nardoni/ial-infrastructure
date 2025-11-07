import json
import boto3
import os

def lambda_handler(event, context):
    """Drift detector Lambda function"""
    
    # Initialize AWS clients
    dynamodb = boto3.resource('dynamodb')
    sns = boto3.client('sns')
    
    # Get environment variables
    project_name = os.environ.get('PROJECT_NAME', 'ial')
    table_name = os.environ.get('DYNAMODB_TABLE')
    sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')
    
    try:
        # Basic drift detection logic
        table = dynamodb.Table(table_name)
        
        # Scan for resources to check
        response = table.scan()
        drift_items = []
        
        for item in response['Items']:
            # Simple drift check (placeholder)
            if item.get('Status') == 'DRIFT_DETECTED':
                drift_items.append(item)
        
        # Send alert if drift detected
        if drift_items and sns_topic_arn:
            message = f"Drift detected in {len(drift_items)} resources"
            sns.publish(
                TopicArn=sns_topic_arn,
                Message=message,
                Subject=f"IAL Drift Alert - {project_name}"
            )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'drift_count': len(drift_items),
                'drift_items': drift_items
            })
        }
        
    except Exception as e:
        print(f"Error in drift detector: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
