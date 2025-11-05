import os
import time
import boto3
from core.providers import bedrock_provider, openai_provider, deepseek_provider

def choose_provider():
    """Choose LLM provider based on environment"""
    return os.getenv("MODEL_PROVIDER", "bedrock").lower()

def chat(prompt, context=None):
    """Route chat request to appropriate provider with fallback"""
    provider = choose_provider()
    providers_to_try = [provider]
    
    # Add fallback providers
    if provider != "bedrock":
        providers_to_try.append("bedrock")
    if provider != "openai" and "openai" not in providers_to_try:
        providers_to_try.append("openai")
    
    for current_provider in providers_to_try:
        try:
            if current_provider == "bedrock":
                response, latency = bedrock_provider.chat(prompt, context)
            elif current_provider == "openai":
                response, latency = openai_provider.chat(prompt, context)
            elif current_provider == "deepseek":
                response, latency = deepseek_provider.chat(prompt, context)
            else:
                continue
                
            # Check if response is valid (not an error message)
            if not response.startswith(f"{current_provider.title()} error:"):
                _publish_metrics(current_provider, latency)
                return response
                
        except Exception as e:
            print(f"Provider {current_provider} failed: {e}")
            continue
    
    # All providers failed
    return "All LLM providers failed. Please check configuration."

def embed(text):
    """Route embedding request to appropriate provider with fallback"""
    provider = choose_provider()
    providers_to_try = [provider, "bedrock", "openai"]
    
    for current_provider in providers_to_try:
        try:
            if current_provider == "bedrock":
                return bedrock_provider.embed(text)
            elif current_provider == "openai":
                return openai_provider.embed(text)
            elif current_provider == "deepseek":
                return deepseek_provider.embed(text)
        except Exception as e:
            print(f"Embedding provider {current_provider} failed: {e}")
            continue
    
    # Fallback to dummy embedding
    return [0.1] * 1536

def embed_texts(texts, model=None):
    """Generate embeddings for multiple texts with routing"""
    embeddings = []
    for text in texts:
        embeddings.append(embed(text))
    return embeddings

def _publish_metrics(provider, latency):
    """Publish metrics to CloudWatch"""
    try:
        cloudwatch = boto3.client("cloudwatch")
        
        # Estimate cost based on provider
        cost_estimates = {
            "bedrock": 0.003,  # per 1K tokens
            "openai": 0.01,    # per 1K tokens  
            "deepseek": 0.001  # per 1K tokens
        }
        
        estimated_cost = cost_estimates.get(provider, 0.003)
        
        cloudwatch.put_metric_data(
            Namespace="IaL",
            MetricData=[
                {
                    "MetricName": "LLM/CostPerConversation",
                    "Value": estimated_cost,
                    "Unit": "None",
                    "Dimensions": [{"Name": "Provider", "Value": provider}]
                },
                {
                    "MetricName": "LLM/Latency", 
                    "Value": latency,
                    "Unit": "Seconds",
                    "Dimensions": [{"Name": "Provider", "Value": provider}]
                }
            ]
        )
    except Exception as e:
        print(f"Failed to publish metrics: {e}")
        pass
