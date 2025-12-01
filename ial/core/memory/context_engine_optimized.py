#!/usr/bin/env python3
"""
Optimized Context Engine - Integra memory manager e embeddings otimizados
"""

from typing import List, Dict, Optional
from .memory_manager_optimized import OptimizedMemoryManager
from .bedrock_embeddings_optimized import OptimizedBedrockEmbeddings
import time

class OptimizedContextEngine:
    def __init__(self, project_name: str = "ial-fork"):
        self.memory = OptimizedMemoryManager(project_name)
        self.embeddings = OptimizedBedrockEmbeddings(project_name)
        
        # Performance tracking
        self.performance_metrics = {
            'context_build_time': [],
            'embedding_search_time': [],
            'cache_hit_rate': 0.0
        }
    
    def build_context_for_query_optimized(self, user_query: str, user_id: str, 
                                         session_id: str = None) -> str:
        """Constrói contexto otimizado para query do usuário"""
        
        start_time = time.time()
        
        # Set user context
        self.memory.user_id = user_id
        self.memory.session_id = session_id
        
        context_parts = []
        
        # 1. Contexto recente da sessão (se disponível)
        if session_id:
            session_context = self.memory.get_session_context_optimized(session_id, limit=5)
            if session_context:
                context_parts.append("## Contexto da Sessão Atual:")
                for msg in session_context[-3:]:  # Últimas 3 mensagens
                    role = "Você" if msg.get('role') == 'user' else "IAL"
                    summary = msg.get('summary', msg.get('content_hash', ''))[:100]
                    context_parts.append(f"{role}: {summary}")
        
        # 2. Contexto recente geral (otimizado)
        recent_context = self.memory.get_recent_context_optimized(limit=8)
        if recent_context and len(recent_context) > 1:
            context_parts.append("\n## Histórico Recente:")
            for msg in recent_context[-5:]:  # Últimas 5 mensagens
                role = "Você" if msg.get('role') == 'user' else "IAL"
                summary = msg.get('content_summary', '')[:120]
                if summary:
                    context_parts.append(f"{role}: {summary}")
        
        # 3. Contexto semântico (busca por similaridade otimizada)
        embedding_start = time.time()
        semantic_context = self.embeddings.find_similar_conversations_optimized(
            user_query, user_id, limit=2
        )
        embedding_time = time.time() - embedding_start
        self.performance_metrics['embedding_search_time'].append(embedding_time)
        
        if semantic_context:
            context_parts.append("\n## Tópicos Relacionados:")
            for item in semantic_context:
                preview = item.get('text_preview', '')[:100]
                similarity = item.get('similarity', 0)
                context_parts.append(f"- {preview} (relevância: {similarity:.2f})")
        
        # 4. Estatísticas do usuário (cache-friendly)
        user_stats = self.memory.get_user_stats()
        if user_stats.get('total_messages', 0) > 0:
            context_parts.append(f"\n## Estatísticas: {user_stats['total_messages']} mensagens, {user_stats['total_tokens']} tokens (7 dias)")
        
        # Montar contexto final
        result = "\n".join(context_parts) if context_parts else ""
        
        # Track performance
        total_time = time.time() - start_time
        self.performance_metrics['context_build_time'].append(total_time)
        
        # Log performance (only if > 100ms)
        if total_time > 0.1:
            print(f"⚡ Context build: {total_time*1000:.0f}ms (embedding: {embedding_time*1000:.0f}ms)")
        
        return result
    
    def save_interaction_optimized(self, user_input: str, assistant_response: str, 
                                  user_id: str, session_id: str, metadata: Dict = None):
        """Salva interação com embeddings otimizados"""
        
        # Set user context
        self.memory.user_id = user_id
        self.memory.session_id = session_id
        
        # Save conversation to optimized table
        success = self.memory.save_conversation_optimized(
            user_input, assistant_response, session_id, metadata
        )
        
        if success:
            # Generate and store embeddings for both messages (async-like)
            conversation_id = f"{user_id}_{session_id}_{int(time.time())}"
            
            # Store user input embedding
            self.embeddings.store_embedding_optimized(
                user_input, user_id, f"{conversation_id}_user", 
                {'type': 'user_input', 'session_id': session_id}
            )
            
            # Store assistant response embedding
            self.embeddings.store_embedding_optimized(
                assistant_response, user_id, f"{conversation_id}_assistant",
                {'type': 'assistant_response', 'session_id': session_id}
            )
    
    def get_performance_metrics(self) -> Dict:
        """Retorna métricas de performance"""
        
        metrics = {}
        
        if self.performance_metrics['context_build_time']:
            avg_context_time = sum(self.performance_metrics['context_build_time']) / len(self.performance_metrics['context_build_time'])
            metrics['avg_context_build_ms'] = avg_context_time * 1000
        
        if self.performance_metrics['embedding_search_time']:
            avg_embedding_time = sum(self.performance_metrics['embedding_search_time']) / len(self.performance_metrics['embedding_search_time'])
            metrics['avg_embedding_search_ms'] = avg_embedding_time * 1000
        
        # Cache hit rate (simplified)
        metrics['cache_hit_rate'] = self.performance_metrics.get('cache_hit_rate', 0.0)
        
        return metrics
    
    def cleanup_old_data(self, days_old: int = 30) -> Dict:
        """Cleanup de dados antigos"""
        
        result = {
            'embeddings_cleaned': 0,
            'conversations_cleaned': 0  # TTL handles this automatically
        }
        
        # Cleanup embeddings
        result['embeddings_cleaned'] = self.embeddings.cleanup_old_embeddings(days_old)
        
        return result
