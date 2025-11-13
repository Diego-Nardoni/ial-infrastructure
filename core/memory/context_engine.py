from typing import List, Dict, Optional
from .memory_manager import MemoryManager
from .bedrock_embeddings import BedrockEmbeddings

class ContextEngine:
    def __init__(self):
        self.memory = MemoryManager()
        self.embeddings = BedrockEmbeddings()
        
    def build_context_for_query(self, user_query: str) -> str:
        """Constrói contexto relevante para a query do usuário"""
        
        # 1. Contexto recente (últimas mensagens da sessão)
        recent_context = self.memory.get_recent_context(limit=10)
        print(f"[DEBUG] recent_context: {len(recent_context)} mensagens")
        
        # 2. Contexto semântico (busca por similaridade)
        semantic_context = []
        if self.embeddings.available:
            all_messages = self.memory.get_recent_context(limit=100)
            semantic_context = self.embeddings.find_similar_conversations(
                user_query, 
                all_messages,
                limit=3
            )
        
        # 3. Montar contexto final
        context_parts = []
        
        # Contexto completo do usuário (todas as sessões)
        if recent_context and len(recent_context) > 1:  # Mais de 1 mensagem total
            context_parts.append("## Histórico de Conversas:")
            for msg in recent_context[-8:]:  # Últimas 8 mensagens de todas as sessões
                role = "Você" if msg['role'] == 'user' else "IAL"
                content = msg['content'][:150] + "..." if len(msg['content']) > 150 else msg['content']
                context_parts.append(f"{role}: {content}")
            print(f"[DEBUG] Adicionadas {len(recent_context[-8:])} mensagens ao contexto")
        else:
            print(f"[DEBUG] Contexto vazio ou insuficiente")
        
        # Contexto semântico relevante (removido código duplicado)
        if semantic_context:
            context_parts.append("\n## Tópicos Relacionados:")
            for msg in semantic_context:
                if msg not in recent_context:  # Evitar duplicação
                    content = msg['content'][:120] + "..." if len(msg['content']) > 120 else msg['content']
                    context_parts.append(f"- {content}")
        
        result = "\n".join(context_parts) if context_parts else ""
        print(f"[DEBUG] Contexto final: {len(result)} chars")
        return result
    
    def save_interaction(self, user_input: str, assistant_response: str, metadata: Dict = None):
        """Salva interação completa"""
        # Salvar input do usuário
        self.memory.save_message('user', user_input, metadata)
        
        # Salvar resposta do assistente
        self.memory.save_message('assistant', assistant_response, metadata)
        
        # Gerar embeddings em background (não bloquear)
        if self.embeddings.available:
            try:
                self.embeddings.generate_embedding_async(user_input)
                self.embeddings.generate_embedding_async(assistant_response)
            except Exception as e:
                print(f"Warning: Could not generate embeddings: {e}")
    
    def get_conversation_summary(self) -> str:
        """Gera resumo da conversa para continuidade"""
        # Buscar apenas mensagens da sessão atual
        current_session = self.memory.session_id
        recent_messages = self.memory.get_recent_context(limit=10)
        
        if not recent_messages:
            return "Primeira conversa com o usuário."
        
        # Filtrar apenas mensagens da sessão atual
        current_session_messages = [
            msg for msg in recent_messages 
            if msg.get('session_id', '') == current_session
        ]
        
        if len(current_session_messages) < 2:
            return "Primeira conversa com o usuário."
        
        # Gerar resumo simples das últimas interações
        last_topics = []
        for msg in current_session_messages[-3:]:  # Últimas 3 mensagens
            content = msg.get('content', '').strip()
            if content and len(content) > 10:
                # Extrair tópico principal (primeiras palavras)
                topic = content.split('.')[0][:50]
                if topic not in last_topics:
                    last_topics.append(topic)
        
        if last_topics:
            return f"Últimas interações: {', '.join(last_topics)}"
        else:
            # Fallback simples
            last_topics = []
            for msg in recent_messages[-5:]:
                if msg['role'] == 'user':
                    content = msg['content'][:50]
                    if content not in last_topics:
                        last_topics.append(content)
            
            if last_topics:
                return f"Conversas anteriores sobre: {', '.join(last_topics[:3])}"
            else:
                return "Continuando conversa anterior."
    
    def clear_session_context(self):
        """Limpa contexto da sessão atual"""
        self.memory.clear_session_cache()
        print("🧹 Contexto da sessão atual limpo.")
    
    def get_user_history_summary(self) -> Dict:
        """Retorna resumo do histórico do usuário"""
        stats = self.memory.get_user_stats()
        recent_messages = self.memory.get_recent_context(limit=50)
        
        # Contar tipos de interação
        conversation_count = 0
        infrastructure_count = 0
        
        for msg in recent_messages:
            if msg['role'] == 'user':
                content = msg['content'].lower()
                if any(word in content for word in ['create', 'deploy', 'setup', 'delete', 'infrastructure']):
                    infrastructure_count += 1
                else:
                    conversation_count += 1
        
        return {
            **stats,
            'conversation_messages': conversation_count,
            'infrastructure_messages': infrastructure_count,
            'context_available': len(recent_messages) > 0
        }
    
    def enhance_query_with_context(self, user_query: str) -> str:
        """Adiciona contexto relevante à query do usuário"""
        context = self.build_context_for_query(user_query)
        
        if not context:
            return user_query
        
        # Adicionar contexto de forma explícita para o Bedrock
        if "ultima pergunta" in user_query.lower() or "histórico" in user_query.lower() or "conversa anterior" in user_query.lower():
            enhanced_query = f"""Pergunta do usuário: {user_query}

IMPORTANTE: Use o contexto abaixo para responder sobre o histórico de conversas:

{context}

Responda baseado no histórico acima."""
        else:
            enhanced_query = f"{user_query}\n\n--- Contexto da Conversa ---\n{context}"
        
        return enhanced_query
