import hashlib
import platform
import getpass
import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Optional
import boto3
from botocore.exceptions import ClientError

class MemoryManager:
    def __init__(self):
        self.user_id = self._generate_user_id()
        self.session_id = self._generate_session_id()
        self.dynamodb = None
        self.table_name = None
        self.embeddings_table_name = None
        self.local_cache = self._load_local_cache()
        self._init_aws_resources()
        
    def _generate_user_id(self) -> str:
        """Gera ID único baseado em arquivo persistente"""
        user_id_file = os.path.expanduser('~/.ial_user_id')
        
        # Tentar ler user_id existente
        debug_mode = os.getenv('IAL_MODE', 'production') == 'debug'
        
        if os.path.exists(user_id_file):
            try:
                with open(user_id_file, 'r') as f:
                    user_id = f.read().strip()
                    if debug_mode:
                        print(f"[DEBUG] User ID lido de {user_id_file}: {user_id}")
                    return user_id
            except Exception as e:
                if debug_mode:
                    print(f"[DEBUG] Erro ao ler user_id: {e}")
        else:
            if debug_mode:
                print(f"[DEBUG] Arquivo {user_id_file} não existe")
        
        # Gerar novo user_id baseado em hostname + username
        hostname = platform.node()
        username = getpass.getuser()
        unique_string = f"{hostname}-{username}"
        user_id = hashlib.sha256(unique_string.encode()).hexdigest()[:16]
        if debug_mode:
            print(f"[DEBUG] Novo user_id gerado: {user_id}")
        
        # Salvar para próximas execuções
        try:
            with open(user_id_file, 'w') as f:
                f.write(user_id)
            if debug_mode:
                print(f"[DEBUG] User ID salvo em {user_id_file}")
        except Exception as e:
            if debug_mode:
                print(f"[DEBUG] Erro ao salvar user_id: {e}")
        
        return user_id
    
    def _generate_session_id(self) -> str:
        """Gera ID único para sessão atual"""
        timestamp = datetime.now(timezone.utc).isoformat()
        return hashlib.md5(f"{self.user_id}-{timestamp}".encode()).hexdigest()[:12]
    
    def _init_aws_resources(self):
        """Inicializa recursos AWS"""
        try:
            self.dynamodb = boto3.resource('dynamodb')
            self.table_name = self._get_table_name()
            self.embeddings_table_name = self._get_embeddings_table_name()
        except Exception as e:
            print(f"Warning: Could not initialize AWS resources: {e}")
    
    def _get_table_name(self) -> str:
        """Obtém nome da tabela DynamoDB"""
        # Tentar encontrar tabela de conversas
        try:
            dynamodb = boto3.client('dynamodb')
            tables = dynamodb.list_tables()['TableNames']
            for table in tables:
                if 'conversation' in table.lower() and 'ial-fork' in table:
                    return table
        except:
            pass
        return "ial-fork-05-memory-dynamodb-conversations"  # Fallback
    
    def _get_embeddings_table_name(self) -> str:
        """Obtém nome da tabela de embeddings"""
        # Tentar encontrar tabela de embeddings
        try:
            dynamodb = boto3.client('dynamodb')
            tables = dynamodb.list_tables()['TableNames']
            for table in tables:
                if 'embedding' in table.lower() and 'ial-fork' in table:
                    return table
        except:
            pass
        return "ial-fork-05-memory-dynamodb-embeddings"  # Fallback
    
    def save_message(self, role: str, content: str, metadata: Dict = None):
        """Salva mensagem no DynamoDB e cache local"""
        timestamp = datetime.now(timezone.utc).isoformat()
        
        item = {
            'user_id': self.user_id,
            'sort_key': timestamp,  # Usar timestamp como sort_key
            'timestamp': timestamp,
            'session_id': self.session_id,
            'role': role,  # 'user' or 'assistant'
            'content': content,
            'metadata': metadata or {},
            'archived': 'false'
        }
        
        # Salvar no DynamoDB
        if self.dynamodb and self.table_name:
            try:
                table = self.dynamodb.Table(self.table_name)
                table.put_item(Item=item)
            except ClientError as e:
                print(f"Warning: Could not save to DynamoDB: {e}")
        
        # Salvar no cache local
        self.local_cache.append(item)
        self._save_local_cache()
    
    def get_recent_context(self, limit: int = 20) -> List[Dict]:
        """Recupera contexto recente das conversas"""
        if self.dynamodb and self.table_name:
            try:
                table = self.dynamodb.Table(self.table_name)
                response = table.query(
                    KeyConditionExpression='user_id = :uid',
                    ExpressionAttributeValues={':uid': self.user_id},
                    ScanIndexForward=False,  # Ordem decrescente por sort_key
                    Limit=limit
                )
                return response['Items']
            except ClientError as e:
                print(f"Warning: Could not query DynamoDB: {e}")
        
        # Fallback para cache local
        return self.local_cache[-limit:] if self.local_cache else []
    
    def get_session_context(self, session_id: str = None) -> List[Dict]:
        """Recupera contexto de uma sessão específica"""
        target_session = session_id or self.session_id
        
        if self.dynamodb and self.table_name:
            try:
                table = self.dynamodb.Table(self.table_name)
                response = table.query(
                    IndexName='session-index',
                    KeyConditionExpression='session_id = :sid',
                    ExpressionAttributeValues={':sid': target_session},
                    ScanIndexForward=True
                )
                return response['Items']
            except ClientError as e:
                print(f"Warning: Could not query session: {e}")
        
        # Fallback para cache local
        return [msg for msg in self.local_cache if msg.get('session_id') == target_session]
    
    def _load_local_cache(self) -> List[Dict]:
        """Carrega cache local"""
        cache_file = os.path.expanduser('~/.ial/conversation_cache.json')
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def _save_local_cache(self):
        """Salva cache local"""
        cache_dir = os.path.expanduser('~/.ial')
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, 'conversation_cache.json')
        
        # Manter apenas últimas 100 mensagens no cache
        cache_to_save = self.local_cache[-100:] if len(self.local_cache) > 100 else self.local_cache
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache_to_save, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save local cache: {e}")
    
    def clear_session_cache(self):
        """Limpa cache da sessão atual"""
        self.local_cache = [msg for msg in self.local_cache if msg.get('session_id') != self.session_id]
        self._save_local_cache()
    
    def get_user_stats(self) -> Dict:
        """Retorna estatísticas do usuário"""
        recent_messages = self.get_recent_context(limit=1000)
        
        return {
            'user_id': self.user_id,
            'total_messages': len(recent_messages),
            'sessions': len(set(msg.get('session_id', '') for msg in recent_messages)),
            'first_interaction': min([msg.get('timestamp', '') for msg in recent_messages]) if recent_messages else None,
            'last_interaction': max([msg.get('timestamp', '') for msg in recent_messages]) if recent_messages else None
        }
