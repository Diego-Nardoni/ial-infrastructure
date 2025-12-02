"""Context Builder: orquestrador unificado de contexto."""
from typing import Dict, Any, Optional
from services.rag.retriever import retrieve

def build_enhanced_context(user_query: str, user_id: str = None, session_id: str = None) -> Dict[str, Any]:
    """Orquestrador unificado de contexto"""
    
    # 1. Context Engine (conversational memory)
    conversation_context = ""
    try:
        from ial.core.memory.context_engine_optimized import OptimizedContextEngine
        context_engine = OptimizedContextEngine()
        if user_id and session_id:
            conversation_context = context_engine.build_context_for_query_optimized(
                user_query, user_id, session_id
            )
        else:
            conversation_context = context_engine.build_context_for_query_optimized(
                user_query, "default_user", "default_session"
            )
    except Exception:
        pass
    
    # 2. RAG Knowledge (documentation/best practices)
    knowledge_snippets = []
    try:
        knowledge_snippets = retrieve(query=user_query, k=3, threshold=0.7)
    except Exception:
        pass
    
    # 3. Intent extraction (basic)
    intent = "conversational"
    if any(word in user_query.lower() for word in ["create", "deploy", "provision"]):
        intent = "infrastructure"
    elif any(word in user_query.lower() for word in ["cost", "billing", "optimize"]):
        intent = "finops"
    
    return {
        "conversation": conversation_context,
        "knowledge": knowledge_snippets,
        "intent": intent,
        "query": user_query
    }

# Backward compatibility
def build_context(short_term: str, desired_spec: Dict[str, Any], query: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy function - mantida para compatibilidade"""
    return build_enhanced_context(query)
