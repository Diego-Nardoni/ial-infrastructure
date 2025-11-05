"""Context Builder: compõe contexto híbrido (short‑term + desired_spec + RAG)."""
import json
from typing import Dict, Any
from services.rag.retriever import retrieve

def build_context(short_term: str, desired_spec: Dict[str, Any], query: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    snippets = retrieve(query=query, k=cfg.get("k", 6), threshold=cfg.get("threshold", 0.65), cfg=cfg)
    return {
        "short_term": short_term,
        "desired_spec": desired_spec,
        "rag_snippets": snippets,
    }
