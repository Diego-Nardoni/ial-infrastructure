import boto3
import json
import hashlib
import threading
from typing import List, Dict, Optional
from botocore.exceptions import ClientError

class BedrockEmbeddings:
    def __init__(self):
        try:
            self.bedrock = boto3.client('bedrock-runtime')
            self.embedding_model = 'amazon.titan-embed-text-v1'
            self.chat_model = 'anthropic.claude-3-sonnet-20240229-v1:0'
            self.available = True
        except Exception as e:
            print(f"Warning: Bedrock not available: {e}")
            self.available = False
    
    def generate_embedding(self, text: str) -> List[float]:
        """Gera embedding para texto"""
        if not self.available:
            return []
        
        # Validar texto não vazio
        if not text or not text.strip():
            print("Warning: Empty text for embedding, skipping")
            return []
            
        try:
            # Limitar texto para evitar erro de tamanho
            text_truncated = text[:8000] if len(text) > 8000 else text
            
            response = self.bedrock.invoke_model(
                modelId=self.embedding_model,
                body=json.dumps({
                    "inputText": text_truncated
                })
            )
            
            result = json.loads(response['body'].read())
            return result.get('embedding', [])
            
        except ClientError as e:
            print(f"Error generating embedding: {e}")
            return []
    
    def generate_embedding_async(self, text: str, callback=None):
        """Gera embedding em background"""
        if not self.available:
            return
            
        def _generate():
            try:
                embedding = self.generate_embedding(text)
                if callback and embedding:
                    callback(text, embedding)
            except Exception as e:
                print(f"Error in async embedding: {e}")
                
        thread = threading.Thread(target=_generate)
        thread.daemon = True
        thread.start()
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calcula similaridade coseno entre dois embeddings"""
        if not embedding1 or not embedding2:
            return 0.0
            
        try:
            import numpy as np
            
            # Converter para numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calcular similaridade coseno
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
                
            return dot_product / (norm1 * norm2)
            
        except ImportError:
            # Fallback sem numpy
            return self._cosine_similarity_manual(embedding1, embedding2)
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0.0
    
    def _cosine_similarity_manual(self, vec1: List[float], vec2: List[float]) -> float:
        """Calcula similaridade coseno sem numpy"""
        try:
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            norm1 = sum(a * a for a in vec1) ** 0.5
            norm2 = sum(b * b for b in vec2) ** 0.5
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
                
            return dot_product / (norm1 * norm2)
        except:
            return 0.0
    
    def generate_summary(self, messages: List[Dict]) -> str:
        """Gera resumo das mensagens usando Claude"""
        if not self.available or not messages:
            return "Nenhuma conversa anterior disponível."
        
        # Preparar contexto para Claude
        conversation_text = "\n".join([
            f"{msg.get('role', 'unknown')}: {msg.get('content', '')}" 
            for msg in messages[-10:]  # Últimas 10 mensagens
        ])
        
        if not conversation_text.strip():
            return "Primeira conversa com o usuário."
        
        prompt = f"""Resuma brevemente esta conversa em 2-3 frases, focando nos tópicos principais e contexto relevante para continuar a conversa:

{conversation_text}

Resumo conciso:"""

        try:
            response = self.bedrock.invoke_model(
                modelId=self.chat_model,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 150,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            result = json.loads(response['body'].read())
            return result['content'][0]['text'].strip()
            
        except ClientError as e:
            print(f"Error generating summary: {e}")
            return "Resumo não disponível no momento."
    
    def get_content_hash(self, text: str) -> str:
        """Gera hash único para o conteúdo"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def find_similar_conversations(self, query: str, messages: List[Dict], limit: int = 5) -> List[Dict]:
        """Encontra conversas similares (implementação básica)"""
        if not self.available or not messages:
            return []
        
        # Por enquanto, implementação simples baseada em palavras-chave
        # TODO: Implementar busca por embeddings quando tiver mais dados
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scored_messages = []
        for msg in messages:
            content = msg.get('content', '').lower()
            content_words = set(content.split())
            
            # Score baseado em palavras em comum
            common_words = query_words.intersection(content_words)
            score = len(common_words) / max(len(query_words), 1)
            
            if score > 0.1:  # Threshold mínimo
                scored_messages.append((score, msg))
        
        # Ordenar por score e retornar top N
        scored_messages.sort(key=lambda x: x[0], reverse=True)
        return [msg for score, msg in scored_messages[:limit]]
