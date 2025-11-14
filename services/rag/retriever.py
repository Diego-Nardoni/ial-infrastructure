"""RAG Retriever: carrega índice FAISS (local/S3) e retorna top‑K snippets."""
import time
import json
import os
from typing import List, Dict, Any
from services.rag.vector import FaissStore

def retrieve(query: str, k: int = 6, threshold: float = 0.65, cfg: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    t0 = time.time()
    
    # Load configuration
    config = cfg or {}
    faiss_path = config.get("local_path", ".rag/index.faiss")
    meta_path = config.get("local_meta", ".rag/index.json")
    
    # Load FAISS store
    store = FaissStore.local(path=meta_path)
    
    # Load metadata
    if os.path.exists(meta_path):
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                store._metas = data.get('metas', [])
        except Exception as e:
            print(f"Warning: Failed to load metadata: {e}")
            return []
    else:
        print(f"Warning: Metadata file not found: {meta_path}")
        return []
    
    # Load FAISS index
    store.load()
    
    # Generate query embedding
    try:
        from core.providers.bedrock_provider import embed_texts
        query_vectors = embed_texts([query], model="amazon.titan-embed-text-v2:0")
        if not query_vectors:
            print("Warning: Failed to generate query embedding")
            return []
        query_vector = query_vectors[0]
    except Exception as e:
        print(f"Warning: Failed to generate embedding: {e}")
        return []
    
    # Search using FAISS
    items = store.search(query_vector=query_vector, topk=k)
    results = [it for it in items if it.get("score", 0) >= threshold]
    
    latency = int((time.time() - t0) * 1000)
    
    try:
        from observability import put_metric
        put_metric("IaL", "RAG/QueryLatency", latency, unit="Milliseconds")
    except Exception:
        pass
        
    print(f"RAG retrieve k={k} thr={threshold:.2f} → {len(results)} hits ({latency}ms)")
    return results
