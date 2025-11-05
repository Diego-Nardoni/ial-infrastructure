import boto3
import json
import os
import time
from botocore.config import Config

def chat(prompt, context=None):
    """Chat completion using Bedrock Claude"""
    client = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "us-east-1"))
    start = time.time()
    
    try:
        response = client.invoke_model(
            modelId=os.getenv("CHAT_MODEL", "anthropic.claude-3-sonnet-20240229-v1:0"),
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [{"role": "user", "content": prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        latency = time.time() - start
        return result['content'][0]['text'], latency
        
    except Exception as e:
        latency = time.time() - start
        return f"Bedrock error: {str(e)}", latency

def embed(text):
    """Generate embeddings using Bedrock Titan"""
    client = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "us-east-1"))
    
    try:
        response = client.invoke_model(
            modelId=os.getenv("EMBED_MODEL", "amazon.titan-embed-text-v2:0"),
            body=json.dumps({"inputText": text[:8000]})
        )
        
        result = json.loads(response['body'].read())
        return result['embedding']
        
    except Exception as e:
        # Fallback to dummy embedding
        return [0.1] * 1536

def embed_texts(texts, model=None):
    """Generate embeddings for multiple texts (backward compatibility)"""
    embeddings = []
    for text in texts:
        embeddings.append(embed(text))
    return embeddings
