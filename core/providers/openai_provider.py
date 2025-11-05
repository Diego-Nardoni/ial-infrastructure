import time
import os

def chat(prompt, context=None):
    """Chat completion using OpenAI"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        start = time.time()
        response = client.chat.completions.create(
            model=os.getenv("CHAT_MODEL", "gpt-4"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000
        )
        latency = time.time() - start
        
        return response.choices[0].message.content, latency
        
    except Exception as e:
        latency = time.time() - start if 'start' in locals() else 0
        return f"OpenAI error: {str(e)}", latency

def embed(text):
    """Generate embeddings using OpenAI"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.embeddings.create(
            model=os.getenv("EMBED_MODEL", "text-embedding-3-large"),
            input=text
        )
        
        return response.data[0].embedding
        
    except Exception as e:
        # Fallback to dummy embedding
        return [0.1] * 1536

def embed_texts(texts, model=None):
    """Generate embeddings for multiple texts"""
    embeddings = []
    for text in texts:
        embeddings.append(embed(text))
    return embeddings
