"""Abstração de armazenamento FAISS local, com futuras extensões S3."""
import json
import os
from typing import List, Dict, Any

class FaissStore:
    def __init__(self, path: str):
        self.path = path
        self._metas: List[Dict[str, Any]] = []
        self._vectors = []

    @classmethod
    def local(cls, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return cls(path)

    def build(self, vectors: List[List[float]], metas: List[Dict[str, Any]]):
        # Placeholder: persist raw arrays (substituir por FAISS real na etapa de build do CI)
        self._vectors = vectors
        self._metas = metas

    def persist_meta(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"metas": self._metas}, f, indent=2)

    def search(self, query: str, topk: int = 6) -> List[Dict[str, Any]]:
        # Placeholder para ranking: retornos estáticos (substituir por FAISS real no build)
        return [
            {"text": m.get("text"), "source": m.get("source"), "score": 0.71}
            for m in self._metas[:topk]
        ]
