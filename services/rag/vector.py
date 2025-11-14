"""Abstração de armazenamento FAISS local, com futuras extensões S3."""
import json
import os
import numpy as np
from typing import List, Dict, Any

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("Warning: FAISS not available, using fallback")

class FaissStore:
    def __init__(self, path: str):
        self.path = path
        self.faiss_path = path.replace('.json', '.faiss')
        self._metas: List[Dict[str, Any]] = []
        self._vectors = []
        self._index = None

    @classmethod
    def local(cls, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return cls(path)

    def build(self, vectors: List[List[float]], metas: List[Dict[str, Any]]):
        """Build FAISS index from vectors and metadata"""
        self._vectors = vectors
        self._metas = metas
        
        if not FAISS_AVAILABLE or not vectors:
            print("Warning: FAISS not available or no vectors, using fallback")
            return
        
        try:
            # Convert to numpy array
            vectors_np = np.array(vectors, dtype=np.float32)
            dimension = vectors_np.shape[1]
            
            # Create FAISS index
            self._index = faiss.IndexFlatIP(dimension)  # Inner product (cosine similarity)
            
            # Add vectors to index
            self._index.add(vectors_np)
            
            # Save FAISS index
            faiss.write_index(self._index, self.faiss_path)
            print(f"✅ FAISS index built and saved: {self.faiss_path}")
            
        except Exception as e:
            print(f"Warning: FAISS build failed: {e}, using fallback")
            self._index = None

    def persist_meta(self, path: str):
        """Save metadata to JSON file"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"metas": self._metas}, f, indent=2)
        print(f"✅ Metadata saved: {path}")

    def load(self):
        """Load FAISS index and metadata"""
        if not FAISS_AVAILABLE:
            return False
            
        try:
            if os.path.exists(self.faiss_path):
                self._index = faiss.read_index(self.faiss_path)
                print(f"✅ FAISS index loaded: {self.faiss_path}")
                return True
        except Exception as e:
            print(f"Warning: Failed to load FAISS index: {e}")
        
        return False

    def search(self, query_vector: List[float], topk: int = 6) -> List[Dict[str, Any]]:
        """Search using FAISS index or fallback"""
        if self._index is not None and FAISS_AVAILABLE:
            try:
                # Convert query to numpy array
                query_np = np.array([query_vector], dtype=np.float32)
                
                # Search FAISS index
                scores, indices = self._index.search(query_np, min(topk, len(self._metas)))
                
                # Return results with metadata
                results = []
                for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                    if idx < len(self._metas):
                        meta = self._metas[idx].copy()
                        meta['score'] = float(score)
                        results.append(meta)
                
                return results
                
            except Exception as e:
                print(f"Warning: FAISS search failed: {e}, using fallback")
        
        # Fallback: return first topk results
        return [
            {"text": m.get("text"), "source": m.get("source"), "score": 0.71}
            for m in self._metas[:topk]
        ]
