"""Constrói índice FAISS a partir de docs relevantes do repositório."""
import os
import json
import time
import glob
from typing import List, Dict, Any
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.providers.bedrock_provider import embed_texts
from services.rag.util import walk_files, chunk_text
from services.rag.vector import FaissStore

DOCROOTS = ["docs", "phases", "templates", "outputs_contract", "schemas"]

def build_index(config: Dict[str, Any]) -> Dict[str, Any]:
    t0 = time.time()
    files = walk_files(DOCROOTS, exts=(".md", ".yaml", ".yml", ".json"))
    records = []
    
    for f in files:
        try:
            with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                text = fh.read()
            for part in chunk_text(text, target_tokens=512):
                records.append({"source": f, "text": part})
        except Exception as e:
            print(f"RAG: skip {f} ({e})")

    texts = [r["text"] for r in records]
    vectors = embed_texts(texts=texts, model=config.get("embed_model", "amazon.titan-embed-text-v2:0"))

    store = FaissStore.local(path=config.get("local_path", ".rag/index.faiss"))
    store.build(vectors=vectors, metas=records)
    store.persist_meta(path=config.get("local_meta", ".rag/index.json"))

    # TODO: sync to S3 via boto3 when bucket/prefix provided
    idx_size = len(records)
    latency = int((time.time() - t0) * 1000)
    
    try:
        # Import observability if available
        from observability import put_metric
        put_metric("IaL", "RAG/IndexSize", idx_size, unit="Count")
        put_metric("IaL", "RAG/BuildLatency", latency, unit="Milliseconds")
    except Exception:
        pass
        
    print(f"RAG index built: {idx_size} chunks | {latency}ms")
    return {"chunks": idx_size, "latency_ms": latency}
