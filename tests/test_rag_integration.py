#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.query_engine import RAGQueryEngine
from core.mcp_router import MCPRouter

def test_rag_integration():
    """Test RAG integration with MCP Router"""
    print("🧪 Testing RAG Integration...")
    
    # Test RAG Query Engine
    engine = RAGQueryEngine()
    result = engine.query("What is IAL?", {"phase": "foundation", "domain": "security"})
    
    assert "question" in result
    assert "answer" in result
    assert "sources" in result
    assert "confidence" in result
    
    print("✅ RAG Query Engine working")
    
    # Test MCP Router with RAG
    router = MCPRouter()
    rag_mcp = router.route("knowledge", "query", {"phase": "test"})
    
    assert rag_mcp is not None
    assert rag_mcp["name"] == "rag-mcp"
    
    print("✅ MCP Router routes to RAG correctly")
    
    print("🎉 All RAG integration tests passed!")

if __name__ == "__main__":
    test_rag_integration()
