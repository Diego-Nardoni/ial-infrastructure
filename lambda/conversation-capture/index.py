#!/usr/bin/env python3
"""
Lambda Function: Conversation Capture with S3 Tables Vector Store
Captures Amazon Q conversations and stores with embeddings for RAG
"""
import json
import boto3
import os
from datetime import datetime
import uuid
import hashlib

s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')
bedrock = boto3.client('bedrock-runtime')

def lambda_handler(event, context):
    """
    Capture and store Amazon Q conversation with embeddings
    
    Event format:
    {
        "body": {
            "user": "diego",
            "text": "How do I add port 8443 to ALB?",
            "metadata": {
                "project": "ial-infrastructure",
                "phase": "10-alb"
            }
        }
    }
    """
    try:
        # Parse input
        if isinstance(event.get('body'), str):
            conversation = json.loads(event['body'])
        else:
            conversation = event.get('body', event)
        
        # Generate IDs
        conversation_id = str(uuid.uuid4())
        timestamp = int(datetime.utcnow().timestamp())
        
        # Extract data
        user = conversation.get('user', 'unknown')
        text = conversation.get('text', '')
        metadata = conversation.get('metadata', {})
        
        # Validate
        if not text:
            return error_response(400, "Text is required")
        
        # Generate embedding
        print(f"Generating embedding for conversation: {conversation_id}")
        embedding = generate_embedding(text)
        
        # Prepare S3 key
        date_path = datetime.utcnow().strftime('%Y/%m/%d')
        s3_key = f"conversations/{date_path}/{conversation_id}.json"
        
        # Store in S3 Tables (with vector)
        conversation_data = {
            'conversation_id': conversation_id,
            'timestamp': timestamp,
            'user': user,
            'text': text,
            'embedding': embedding,
            'metadata': metadata,
            'text_hash': hashlib.sha256(text.encode()).hexdigest()
        }
        
        print(f"Storing conversation in S3: {s3_key}")
        s3.put_object(
            Bucket=os.environ['S3_BUCKET'],
            Key=s3_key,
            Body=json.dumps(conversation_data),
            ContentType='application/json',
            Metadata={
                'conversation-id': conversation_id,
                'user': user,
                'timestamp': str(timestamp)
            }
        )
        
        # Store metadata in DynamoDB
        print(f"Storing metadata in DynamoDB")
        dynamodb.put_item(
            TableName=os.environ['DYNAMODB_TABLE'],
            Item={
                'ConversationId': {'S': conversation_id},
                'Timestamp': {'N': str(timestamp)},
                'User': {'S': user},
                'S3Key': {'S': s3_key},
                'TextPreview': {'S': text[:200]},
                'TextLength': {'N': str(len(text))},
                'Project': {'S': metadata.get('project', 'unknown')},
                'Phase': {'S': metadata.get('phase', 'unknown')},
                'TTL': {'N': str(timestamp + 7776000)}  # 90 days
            }
        )
        
        print(f"✅ Conversation stored successfully: {conversation_id}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'conversation_id': conversation_id,
                'timestamp': timestamp,
                's3_key': s3_key,
                'message': 'Conversation stored successfully'
            })
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return error_response(500, str(e))

def generate_embedding(text):
    """Generate embedding using Bedrock Titan"""
    try:
        response = bedrock.invoke_model(
            modelId=os.environ.get('BEDROCK_MODEL', 'amazon.titan-embed-text-v2:0'),
            body=json.dumps({
                'inputText': text[:8000]  # Titan limit
            })
        )
        
        result = json.loads(response['body'].read())
        return result['embedding']
        
    except Exception as e:
        print(f"⚠️  Bedrock embedding error: {e}")
        # Return zero vector as fallback
        return [0.0] * 1024

def error_response(status_code, message):
    """Return error response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': message
        })
    }

# For local testing
if __name__ == '__main__':
    # Test event
    test_event = {
        'body': json.dumps({
            'user': 'diego',
            'text': 'How do I add port 8443 to ALB security group?',
            'metadata': {
                'project': 'ial-infrastructure',
                'phase': '10-alb'
            }
        })
    }
    
    # Mock environment
    os.environ['S3_BUCKET'] = 'ial-conversations-test'
    os.environ['DYNAMODB_TABLE'] = 'ial-conversations-metadata'
    os.environ['BEDROCK_MODEL'] = 'amazon.titan-embed-text-v2:0'
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
