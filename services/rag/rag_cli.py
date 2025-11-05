#!/usr/bin/env python3
import sys
import os
import yaml
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.rag.index_builder import build_index
from services.rag.retriever import retrieve

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 rag_cli.py <command> [args]")
        print("Commands:")
        print("  index - Build RAG index from IAL documents")
        print("  query <question> - Ask a question")
        return
    
    command = sys.argv[1]
    
    # Load config
    try:
        with open('config/rag.yaml', 'r') as f:
            config = yaml.safe_load(f)
    except:
        config = {
            "k": 6,
            "threshold": 0.65,
            "local_path": ".rag/index.faiss",
            "local_meta": ".rag/index.json"
        }
    
    if command == "index":
        print("🔍 Building RAG index from IAL documents...")
        result = build_index(config)
        print(f"✅ Built index: {result['chunks']} chunks in {result['latency_ms']}ms")
        
    elif command == "query":
        if len(sys.argv) < 3:
            print("Usage: python3 rag_cli.py query <question>")
            return
            
        question = " ".join(sys.argv[2:])
        print(f"🤔 Question: {question}")
        
        results = retrieve(query=question, k=config.get("k", 6), threshold=config.get("threshold", 0.65), cfg=config)
        
        print(f"💡 Found {len(results)} relevant snippets:")
        for i, result in enumerate(results[:3], 1):
            print(f"  {i}. {result['source']} (score: {result['score']:.2f})")
            print(f"     {result['text'][:100]}...")
        
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
