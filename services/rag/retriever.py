"""RAG Retriever: carrega índice FAISS (local/S3) e retorna top‑K snippets."""
import time
import json
import os
from typing import List, Dict, Any
from services.rag.vector import FaissStore

def retrieve(query: str, k: int = 6, threshold: float = 0.65, cfg: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    t0 = time.time()
    store = FaissStore.local(path=(cfg or {}).get("local_path", ".rag/index.faiss"))
    items = store.search(query=query, topk=k)
    results = [it for it in items if it.get("score", 0) >= threshold]
    latency = int((time.time() - t0) * 1000)
    
    try:
        from observability import put_metric
        put_metric("IaL", "RAG/QueryLatency", latency, unit="Milliseconds")
    except Exception:
        pass
        
    print(f"RAG retrieve k={k} thr={threshold:.2f} → {len(results)} hits ({latency}ms)")
    return results
