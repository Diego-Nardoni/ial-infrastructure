import time
import os
import json

def chat(prompt, context=None):
    """Chat completion using DeepSeek"""
    try:
        import requests
        
        start = time.time()
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": os.getenv("CHAT_MODEL", "deepseek-chat"),
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000
            },
            timeout=30
        )
        latency = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'], latency
        else:
            return f"DeepSeek API error: {response.status_code}", latency
            
    except Exception as e:
        latency = time.time() - start if 'start' in locals() else 0
        return f"DeepSeek error: {str(e)}", latency

def embed(text):
    """Generate embeddings using DeepSeek (placeholder)"""
    # DeepSeek doesn't have embedding API yet
    # Fallback to dummy embedding
    return [0.1] * 1536

def embed_texts(texts, model=None):
    """Generate embeddings for multiple texts"""
    embeddings = []
    for text in texts:
        embeddings.append(embed(text))
    return embeddings
