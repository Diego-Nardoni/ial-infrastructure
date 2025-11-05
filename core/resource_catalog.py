#!/usr/bin/env python3
"""
Resource Catalog - DynamoDB State Management
Registra e rastreia recursos AWS com metadados completos
"""

import boto3
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from botocore.config import Config
from botocore.exceptions import ClientError, BotoCoreError
import hashlib
import threading
from pathlib import Path

class ResourceCatalog:
    def __init__(self, table_name: str = "ial-state", region: str = "us-east-1"):
        self.table_name = table_name
        self.region = region
        
        # Configuração otimizada para produção
        config = Config(
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            max_pool_connections=50,
            region_name=region
        )
        
        self.dynamodb = boto3.client('dynamodb', config=config)
        self.dynamodb_resource = boto3.resource('dynamodb', config=config)
        
        # Cache local para reduzir chamadas
        self._cache = {}
        self._cache_ttl = 300  # 5 minutos
        self._cache_lock = threading.Lock()
        
        # Inicializar tabela se necessário
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Garante que a tabela DynamoDB existe"""
        try:
            self.dynamodb.describe_table(TableName=self.table_name)
            print(f"✅ Tabela {self.table_name} encontrada")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"⚠️ Tabela {self.table_name} não encontrada, criando...")
                self._create_table()
            else:
                raise
    
    def _create_table(self):
        """Cria tabela DynamoDB otimizada"""
        try:
            table = self.dynamodb_resource.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {'AttributeName': 'resource_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'resource_id', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'S'},
                    {'AttributeName': 'resource_type', 'AttributeType': 'S'},
                    {'AttributeName': 'phase', 'AttributeType': 'S'},
                    {'AttributeName': 'status', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'type-timestamp-index',
                        'KeySchema': [
                            {'AttributeName': 'resource_type', 'KeyType': 'HASH'},
                            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    },
                    {
                        'IndexName': 'phase-status-index',
                        'KeySchema': [
                            {'AttributeName': 'phase', 'KeyType': 'HASH'},
                            {'AttributeName': 'status', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                },
                Tags=[
                    {'Key': 'Project', 'Value': 'IAL'},
                    {'Key': 'Component', 'Value': 'ResourceCatalog'},
                    {'Key': 'Environment', 'Value': 'Production'}
                ]
            )
            
            # Aguardar tabela ficar ativa
            print("⏳ Aguardando tabela ficar ativa...")
            table.wait_until_exists()
            print(f"✅ Tabela {self.table_name} criada com sucesso")
            
        except Exception as e:
            print(f"❌ Erro ao criar tabela: {e}")
            raise
    
    def _get_cache_key(self, resource_id: str) -> str:
        """Gera chave de cache"""
        return f"resource:{resource_id}"
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Verifica se entrada do cache ainda é válida"""
        if not cache_entry:
            return False
        
        cached_at = cache_entry.get('cached_at', 0)
        return (time.time() - cached_at) < self._cache_ttl
    
    def _update_cache(self, resource_id: str, data: Dict):
        """Atualiza cache local"""
        with self._cache_lock:
            cache_key = self._get_cache_key(resource_id)
            self._cache[cache_key] = {
                'data': data,
                'cached_at': time.time()
            }
    
    def _get_from_cache(self, resource_id: str) -> Optional[Dict]:
        """Recupera do cache se válido"""
        with self._cache_lock:
            cache_key = self._get_cache_key(resource_id)
            cache_entry = self._cache.get(cache_key)
            
            if self._is_cache_valid(cache_entry):
                return cache_entry['data']
            
            # Remove entrada expirada
            if cache_key in self._cache:
                del self._cache[cache_key]
            
            return None
    
    def register_resource(self, resource_id: str, resource_type: str, 
                         phase: str, metadata: Dict, status: str = "desired") -> bool:
        """Registra recurso no catálogo"""
        try:
            timestamp = datetime.utcnow().isoformat()
            
            # Calcular hash dos metadados para detectar mudanças
            metadata_str = json.dumps(metadata, sort_keys=True)
            metadata_hash = hashlib.sha256(metadata_str.encode()).hexdigest()[:16]
            
            item = {
                'resource_id': {'S': resource_id},
                'timestamp': {'S': timestamp},
                'resource_type': {'S': resource_type},
                'phase': {'S': phase},
                'status': {'S': status},
                'metadata': {'S': metadata_str},
                'metadata_hash': {'S': metadata_hash},
                'created_at': {'S': timestamp},
                'updated_at': {'S': timestamp},
                'version': {'N': '1'}
            }
            
            # Adicionar TTL para limpeza automática (opcional)
            ttl_date = datetime.utcnow() + timedelta(days=365)  # 1 ano
            item['ttl'] = {'N': str(int(ttl_date.timestamp()))}
            
            response = self.dynamodb.put_item(
                TableName=self.table_name,
                Item=item,
                ReturnValues='ALL_OLD'
            )
            
            # Atualizar cache
            resource_data = {
                'resource_id': resource_id,
                'resource_type': resource_type,
                'phase': phase,
                'status': status,
                'metadata': metadata,
                'metadata_hash': metadata_hash,
                'timestamp': timestamp
            }
            self._update_cache(resource_id, resource_data)
            
            print(f"✅ Recurso registrado: {resource_id}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao registrar recurso {resource_id}: {e}")
            return False
    
    def get_resource(self, resource_id: str, use_cache: bool = True) -> Optional[Dict]:
        """Recupera recurso do catálogo"""
        # Tentar cache primeiro
        if use_cache:
            cached_data = self._get_from_cache(resource_id)
            if cached_data:
                return cached_data
        
        try:
            # Buscar versão mais recente
            response = self.dynamodb.query(
                TableName=self.table_name,
                KeyConditionExpression='resource_id = :rid',
                ExpressionAttributeValues={':rid': {'S': resource_id}},
                ScanIndexForward=False,  # Ordem decrescente por timestamp
                Limit=1
            )
            
            items = response.get('Items', [])
            if not items:
                return None
            
            item = items[0]
            
            # Converter para formato Python
            resource_data = {
                'resource_id': item['resource_id']['S'],
                'resource_type': item['resource_type']['S'],
                'phase': item['phase']['S'],
                'status': item['status']['S'],
                'metadata': json.loads(item['metadata']['S']),
                'metadata_hash': item['metadata_hash']['S'],
                'timestamp': item['timestamp']['S'],
                'created_at': item.get('created_at', {}).get('S'),
                'updated_at': item.get('updated_at', {}).get('S'),
                'version': int(item.get('version', {}).get('N', '1'))
            }
            
            # Atualizar cache
            if use_cache:
                self._update_cache(resource_id, resource_data)
            
            return resource_data
            
        except Exception as e:
            print(f"❌ Erro ao recuperar recurso {resource_id}: {e}")
            return None
    
    def update_resource_status(self, resource_id: str, new_status: str, 
                              additional_metadata: Optional[Dict] = None) -> bool:
        """Atualiza status do recurso"""
        try:
            # Recuperar recurso atual
            current = self.get_resource(resource_id, use_cache=False)
            if not current:
                print(f"⚠️ Recurso não encontrado para atualização: {resource_id}")
                return False
            
            # Preparar metadados atualizados
            updated_metadata = current['metadata'].copy()
            if additional_metadata:
                updated_metadata.update(additional_metadata)
            
            # Registrar nova versão
            return self.register_resource(
                resource_id=resource_id,
                resource_type=current['resource_type'],
                phase=current['phase'],
                metadata=updated_metadata,
                status=new_status
            )
            
        except Exception as e:
            print(f"❌ Erro ao atualizar status do recurso {resource_id}: {e}")
            return False
    
    def list_resources(self, resource_type: Optional[str] = None, 
                      phase: Optional[str] = None, status: Optional[str] = None,
                      limit: int = 100) -> List[Dict]:
        """Lista recursos com filtros opcionais"""
        try:
            resources = []
            
            if resource_type:
                # Usar índice por tipo
                response = self.dynamodb.query(
                    TableName=self.table_name,
                    IndexName='type-timestamp-index',
                    KeyConditionExpression='resource_type = :type',
                    ExpressionAttributeValues={':type': {'S': resource_type}},
                    ScanIndexForward=False,
                    Limit=limit
                )
            elif phase and status:
                # Usar índice por fase e status
                response = self.dynamodb.query(
                    TableName=self.table_name,
                    IndexName='phase-status-index',
                    KeyConditionExpression='phase = :phase AND #status = :status',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':phase': {'S': phase},
                        ':status': {'S': status}
                    },
                    Limit=limit
                )
            else:
                # Scan completo (menos eficiente)
                scan_params = {
                    'TableName': self.table_name,
                    'Limit': limit
                }
                
                # Adicionar filtros se especificados
                filter_expressions = []
                expression_values = {}
                
                if phase:
                    filter_expressions.append('phase = :phase')
                    expression_values[':phase'] = {'S': phase}
                
                if status:
                    filter_expressions.append('#status = :status')
                    expression_values[':status'] = {'S': status}
                    scan_params['ExpressionAttributeNames'] = {'#status': 'status'}
                
                if filter_expressions:
                    scan_params['FilterExpression'] = ' AND '.join(filter_expressions)
                    scan_params['ExpressionAttributeValues'] = expression_values
                
                response = self.dynamodb.scan(**scan_params)
            
            # Processar resultados
            for item in response.get('Items', []):
                resource_data = {
                    'resource_id': item['resource_id']['S'],
                    'resource_type': item['resource_type']['S'],
                    'phase': item['phase']['S'],
                    'status': item['status']['S'],
                    'metadata': json.loads(item['metadata']['S']),
                    'timestamp': item['timestamp']['S']
                }
                resources.append(resource_data)
            
            # Remover duplicatas (manter apenas a versão mais recente de cada recurso)
            unique_resources = {}
            for resource in resources:
                rid = resource['resource_id']
                if rid not in unique_resources or resource['timestamp'] > unique_resources[rid]['timestamp']:
                    unique_resources[rid] = resource
            
            return list(unique_resources.values())
            
        except Exception as e:
            print(f"❌ Erro ao listar recursos: {e}")
            return []
    
    def get_resource_history(self, resource_id: str, limit: int = 10) -> List[Dict]:
        """Recupera histórico de mudanças do recurso"""
        try:
            response = self.dynamodb.query(
                TableName=self.table_name,
                KeyConditionExpression='resource_id = :rid',
                ExpressionAttributeValues={':rid': {'S': resource_id}},
                ScanIndexForward=False,  # Mais recente primeiro
                Limit=limit
            )
            
            history = []
            for item in response.get('Items', []):
                history_entry = {
                    'resource_id': item['resource_id']['S'],
                    'timestamp': item['timestamp']['S'],
                    'status': item['status']['S'],
                    'metadata_hash': item['metadata_hash']['S'],
                    'version': int(item.get('version', {}).get('N', '1'))
                }
                history.append(history_entry)
            
            return history
            
        except Exception as e:
            print(f"❌ Erro ao recuperar histórico do recurso {resource_id}: {e}")
            return []
    
    def batch_register_resources(self, resources: List[Dict]) -> Dict[str, bool]:
        """Registra múltiplos recursos em lote"""
        results = {}
        
        # Processar em lotes de 25 (limite do DynamoDB)
        batch_size = 25
        for i in range(0, len(resources), batch_size):
            batch = resources[i:i + batch_size]
            
            try:
                with self.dynamodb_resource.Table(self.table_name).batch_writer() as batch_writer:
                    for resource in batch:
                        timestamp = datetime.utcnow().isoformat()
                        metadata_str = json.dumps(resource.get('metadata', {}), sort_keys=True)
                        metadata_hash = hashlib.sha256(metadata_str.encode()).hexdigest()[:16]
                        
                        item = {
                            'resource_id': resource['resource_id'],
                            'timestamp': timestamp,
                            'resource_type': resource['resource_type'],
                            'phase': resource['phase'],
                            'status': resource.get('status', 'desired'),
                            'metadata': metadata_str,
                            'metadata_hash': metadata_hash,
                            'created_at': timestamp,
                            'updated_at': timestamp,
                            'version': 1
                        }
                        
                        batch_writer.put_item(Item=item)
                        results[resource['resource_id']] = True
                        
            except Exception as e:
                print(f"❌ Erro no lote {i//batch_size + 1}: {e}")
                for resource in batch:
                    results[resource['resource_id']] = False
        
        return results
    
    def get_catalog_statistics(self) -> Dict:
        """Recupera estatísticas do catálogo"""
        try:
            # Contar recursos por tipo
            type_counts = {}
            status_counts = {}
            phase_counts = {}
            
            # Scan para estatísticas (pode ser custoso para tabelas grandes)
            paginator = self.dynamodb.get_paginator('scan')
            
            for page in paginator.paginate(TableName=self.table_name):
                for item in page.get('Items', []):
                    resource_type = item['resource_type']['S']
                    status = item['status']['S']
                    phase = item['phase']['S']
                    
                    type_counts[resource_type] = type_counts.get(resource_type, 0) + 1
                    status_counts[status] = status_counts.get(status, 0) + 1
                    phase_counts[phase] = phase_counts.get(phase, 0) + 1
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'total_resources': sum(type_counts.values()),
                'resource_types': type_counts,
                'status_distribution': status_counts,
                'phase_distribution': phase_counts,
                'cache_size': len(self._cache)
            }
            
        except Exception as e:
            print(f"❌ Erro ao recuperar estatísticas: {e}")
            return {}
    
    def add_resource_relationship(self, source_id: str, target_id: str, 
                                 relationship_type: str, metadata: Optional[Dict] = None) -> bool:
        """
        Adiciona relacionamento entre recursos no grafo
        
        Args:
            source_id: ID do recurso dependente
            target_id: ID do recurso de que depende
            relationship_type: Tipo do relacionamento (ex: 'subnet_vpc', 'ecs_alb')
            metadata: Metadados adicionais do relacionamento
        """
        try:
            timestamp = datetime.utcnow().isoformat()
            
            if metadata is None:
                metadata = {}
            
            # Item principal: dependência
            dependency_item = {
                'PK': {'S': f'RESOURCE#{source_id}'},
                'SK': {'S': f'DEPENDS_ON#{target_id}'},
                'type': {'S': 'dependency'},
                'relationship_type': {'S': relationship_type},
                'confidence': {'N': str(metadata.get('confidence', 1.0))},
                'auto_detected': {'BOOL': metadata.get('auto_detected', True)},
                'created_at': {'S': timestamp},
                'metadata': {'S': json.dumps(metadata)}
            }
            
            # Item reverso: dependente (para queries eficientes)
            reverse_item = {
                'PK': {'S': f'RESOURCE#{target_id}'},
                'SK': {'S': f'DEPENDENT#{source_id}'},
                'type': {'S': 'reverse_dependency'},
                'relationship_type': {'S': relationship_type},
                'GSI1PK': {'S': f'DEPENDENTS#{target_id}'},
                'GSI1SK': {'S': source_id},
                'created_at': {'S': timestamp}
            }
            
            # Batch write para atomicidade
            self.dynamodb.batch_write_item(
                RequestItems={
                    self.table_name: [
                        {'PutRequest': {'Item': dependency_item}},
                        {'PutRequest': {'Item': reverse_item}}
                    ]
                }
            )
            
            print(f"✅ Relacionamento adicionado: {source_id} → {target_id} ({relationship_type})")
            return True
            
        except Exception as e:
            print(f"❌ Erro adicionando relacionamento {source_id} → {target_id}: {e}")
            return False
    
    def get_resource_dependencies(self, resource_id: str) -> List[Dict]:
        """
        Recupera todas as dependências de um recurso
        
        Args:
            resource_id: ID do recurso
            
        Returns:
            Lista de dependências com metadados
        """
        try:
            response = self.dynamodb.query(
                TableName=self.table_name,
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                ExpressionAttributeValues={
                    ':pk': {'S': f'RESOURCE#{resource_id}'},
                    ':sk_prefix': {'S': 'DEPENDS_ON#'}
                }
            )
            
            dependencies = []
            for item in response.get('Items', []):
                target_id = item['SK']['S'].replace('DEPENDS_ON#', '')
                dependencies.append({
                    'target_id': target_id,
                    'relationship_type': item.get('relationship_type', {}).get('S', 'unknown'),
                    'confidence': float(item.get('confidence', {}).get('N', '1.0')),
                    'auto_detected': item.get('auto_detected', {}).get('BOOL', True),
                    'created_at': item.get('created_at', {}).get('S', ''),
                    'metadata': json.loads(item.get('metadata', {}).get('S', '{}'))
                })
            
            return dependencies
            
        except Exception as e:
            print(f"❌ Erro recuperando dependências de {resource_id}: {e}")
            return []
    
    def get_resource_dependents(self, resource_id: str) -> List[Dict]:
        """
        Recupera todos os recursos que dependem deste recurso
        
        Args:
            resource_id: ID do recurso
            
        Returns:
            Lista de dependentes com metadados
        """
        try:
            # Usar GSI para query eficiente
            response = self.dynamodb.query(
                TableName=self.table_name,
                IndexName='dependents-index',  # Assumindo que existe este GSI
                KeyConditionExpression='GSI1PK = :gsi1pk',
                ExpressionAttributeValues={
                    ':gsi1pk': {'S': f'DEPENDENTS#{resource_id}'}
                }
            )
            
            dependents = []
            for item in response.get('Items', []):
                source_id = item['GSI1SK']['S']
                dependents.append({
                    'source_id': source_id,
                    'relationship_type': item.get('relationship_type', {}).get('S', 'unknown'),
                    'created_at': item.get('created_at', {}).get('S', '')
                })
            
            return dependents
            
        except Exception as e:
            print(f"❌ Erro recuperando dependentes de {resource_id}: {e}")
            return []
    
    def remove_resource_relationship(self, source_id: str, target_id: str) -> bool:
        """
        Remove relacionamento entre recursos
        
        Args:
            source_id: ID do recurso dependente
            target_id: ID do recurso de que depende
        """
        try:
            # Remover item principal e reverso
            self.dynamodb.batch_write_item(
                RequestItems={
                    self.table_name: [
                        {
                            'DeleteRequest': {
                                'Key': {
                                    'PK': {'S': f'RESOURCE#{source_id}'},
                                    'SK': {'S': f'DEPENDS_ON#{target_id}'}
                                }
                            }
                        },
                        {
                            'DeleteRequest': {
                                'Key': {
                                    'PK': {'S': f'RESOURCE#{target_id}'},
                                    'SK': {'S': f'DEPENDENT#{source_id}'}
                                }
                            }
                        }
                    ]
                }
            )
            
            print(f"✅ Relacionamento removido: {source_id} → {target_id}")
            return True
            
        except Exception as e:
            print(f"❌ Erro removendo relacionamento {source_id} → {target_id}: {e}")
            return False
    
    def get_resource_graph_data(self, resource_id: str) -> Dict:
        """
        Recupera dados completos do grafo para um recurso
        
        Args:
            resource_id: ID do recurso
            
        Returns:
            Dicionário com dependências, dependentes e metadados
        """
        return {
            'resource_id': resource_id,
            'dependencies': self.get_resource_dependencies(resource_id),
            'dependents': self.get_resource_dependents(resource_id),
            'metadata': self.get_resource(resource_id)
        }
        """Remove versões antigas mantendo apenas as mais recentes"""
        cleaned_count = 0
        
        try:
            # Recuperar todos os resource_ids únicos
            resource_ids = set()
            paginator = self.dynamodb.get_paginator('scan')
            
            for page in paginator.paginate(
                TableName=self.table_name,
                ProjectionExpression='resource_id'
            ):
                for item in page.get('Items', []):
                    resource_ids.add(item['resource_id']['S'])
            
            # Para cada recurso, manter apenas as versões mais recentes
            for resource_id in resource_ids:
                history = self.get_resource_history(resource_id, limit=100)
                
                if len(history) > keep_versions:
                    # Remover versões antigas
                    to_delete = history[keep_versions:]
                    
                    for old_version in to_delete:
                        try:
                            self.dynamodb.delete_item(
                                TableName=self.table_name,
                                Key={
                                    'resource_id': {'S': resource_id},
                                    'timestamp': {'S': old_version['timestamp']}
                                }
                            )
                            cleaned_count += 1
                        except Exception as e:
                            print(f"⚠️ Erro ao remover versão antiga de {resource_id}: {e}")
            
            print(f"🧹 Limpeza concluída: {cleaned_count} versões antigas removidas")
            return cleaned_count
            
        except Exception as e:
            print(f"❌ Erro durante limpeza: {e}")
            return 0
    
    # ========================================
    # KNOWLEDGE GRAPH RELATIONSHIP METHODS
    # ========================================
    
    def add_resource_relationship(self, source_id: str, target_id: str, 
                                relationship_type: str, metadata: Optional[Dict] = None) -> bool:
        """Adiciona relacionamento entre recursos no grafo"""
        try:
            timestamp = datetime.utcnow().isoformat()
            
            if metadata is None:
                metadata = {}
            
            # Item principal: dependência
            dependency_item = {
                'resource_id': {'S': f'RESOURCE#{source_id}'},
                'timestamp': {'S': f'DEPENDS_ON#{target_id}#{timestamp}'},
                'type': {'S': 'dependency'},
                'relationship_type': {'S': relationship_type},
                'target_id': {'S': target_id},
                'confidence': {'N': str(metadata.get('confidence', 1.0))},
                'auto_detected': {'BOOL': metadata.get('auto_detected', False)},
                'created_at': {'S': timestamp},
                'detection_method': {'S': metadata.get('detection_method', 'manual')},
                'phase_source': {'S': metadata.get('phase_source', 'unknown')},
                'phase_target': {'S': metadata.get('phase_target', 'unknown')}
            }
            
            # Item reverso: dependente
            reverse_item = {
                'resource_id': {'S': f'RESOURCE#{target_id}'},
                'timestamp': {'S': f'DEPENDENT#{source_id}#{timestamp}'},
                'type': {'S': 'reverse_dependency'},
                'relationship_type': {'S': f'{relationship_type}_reverse'},
                'source_id': {'S': source_id},
                'created_at': {'S': timestamp}
            }
            
            # Batch write para atomicidade
            self.dynamodb.batch_write_item(
                RequestItems={
                    self.table_name: [
                        {'PutRequest': {'Item': dependency_item}},
                        {'PutRequest': {'Item': reverse_item}}
                    ]
                }
            )
            
            print(f"✅ Relacionamento adicionado: {source_id} → {target_id} ({relationship_type})")
            return True
            
        except Exception as e:
            print(f"❌ Erro adicionando relacionamento: {e}")
            return False
    
    def get_resource_dependencies(self, resource_id: str) -> List[Dict]:
        """Obtém todas as dependências de um recurso"""
        try:
            response = self.dynamodb.query(
                TableName=self.table_name,
                KeyConditionExpression='resource_id = :rid AND begins_with(#ts, :prefix)',
                ExpressionAttributeNames={'#ts': 'timestamp'},
                ExpressionAttributeValues={
                    ':rid': {'S': f'RESOURCE#{resource_id}'},
                    ':prefix': {'S': 'DEPENDS_ON#'}
                }
            )
            
            dependencies = []
            for item in response.get('Items', []):
                dependencies.append({
                    'target_id': item.get('target_id', {}).get('S', ''),
                    'relationship_type': item.get('relationship_type', {}).get('S', 'unknown'),
                    'confidence': float(item.get('confidence', {}).get('N', '1.0')),
                    'auto_detected': item.get('auto_detected', {}).get('BOOL', False),
                    'created_at': item.get('created_at', {}).get('S', ''),
                    'detection_method': item.get('detection_method', {}).get('S', 'unknown')
                })
            
            return dependencies
            
        except Exception as e:
            print(f"❌ Erro obtendo dependências: {e}")
            return []
    
    def get_resource_dependents(self, resource_id: str) -> List[Dict]:
        """Obtém todos os recursos que dependem deste recurso"""
        try:
            response = self.dynamodb.query(
                TableName=self.table_name,
                KeyConditionExpression='resource_id = :rid AND begins_with(#ts, :prefix)',
                ExpressionAttributeNames={'#ts': 'timestamp'},
                ExpressionAttributeValues={
                    ':rid': {'S': f'RESOURCE#{resource_id}'},
                    ':prefix': {'S': 'DEPENDENT#'}
                }
            )
            
            dependents = []
            for item in response.get('Items', []):
                dependents.append({
                    'source_id': item.get('source_id', {}).get('S', ''),
                    'relationship_type': item.get('relationship_type', {}).get('S', 'unknown'),
                    'created_at': item.get('created_at', {}).get('S', '')
                })
            
            return dependents
            
        except Exception as e:
            print(f"❌ Erro obtendo dependentes: {e}")
            return []
    
    def remove_resource_relationship(self, source_id: str, target_id: str) -> bool:
        """Remove relacionamento entre recursos"""
        try:
            # Buscar itens específicos para deletar
            dep_response = self.dynamodb.query(
                TableName=self.table_name,
                KeyConditionExpression='resource_id = :rid AND begins_with(#ts, :prefix)',
                ExpressionAttributeNames={'#ts': 'timestamp'},
                ExpressionAttributeValues={
                    ':rid': {'S': f'RESOURCE#{source_id}'},
                    ':prefix': {'S': f'DEPENDS_ON#{target_id}#'}
                }
            )
            
            rev_response = self.dynamodb.query(
                TableName=self.table_name,
                KeyConditionExpression='resource_id = :rid AND begins_with(#ts, :prefix)',
                ExpressionAttributeNames={'#ts': 'timestamp'},
                ExpressionAttributeValues={
                    ':rid': {'S': f'RESOURCE#{target_id}'},
                    ':prefix': {'S': f'DEPENDENT#{source_id}#'}
                }
            )
            
            # Deletar itens encontrados
            delete_requests = []
            
            for item in dep_response.get('Items', []):
                delete_requests.append({
                    'DeleteRequest': {
                        'Key': {
                            'resource_id': item['resource_id'],
                            'timestamp': item['timestamp']
                        }
                    }
                })
            
            for item in rev_response.get('Items', []):
                delete_requests.append({
                    'DeleteRequest': {
                        'Key': {
                            'resource_id': item['resource_id'],
                            'timestamp': item['timestamp']
                        }
                    }
                })
            
            if delete_requests:
                self.dynamodb.batch_write_item(
                    RequestItems={self.table_name: delete_requests}
                )
            
            print(f"✅ Relacionamento removido: {source_id} → {target_id}")
            return True
            
        except Exception as e:
            print(f"❌ Erro removendo relacionamento: {e}")
            return False

def main():
    """Função principal para testes"""
    print("🗄️ IAL Resource Catalog v3.1")
    print("=" * 50)
    
    catalog = ResourceCatalog()
    
    # Teste básico
    test_resource = {
        'resource_id': 'test/example/vpc-123',
        'resource_type': 'AWS::EC2::VPC',
        'phase': '20-network/01-networking',
        'metadata': {
            'cidr': '10.0.0.0/16',
            'region': 'us-east-1',
            'test': True
        }
    }
    
    # Registrar recurso de teste
    success = catalog.register_resource(**test_resource)
    if success:
        print("✅ Recurso de teste registrado")
        
        # Recuperar recurso
        retrieved = catalog.get_resource(test_resource['resource_id'])
        if retrieved:
            print(f"✅ Recurso recuperado: {retrieved['resource_id']}")
        
        # Listar recursos
        resources = catalog.list_resources(limit=5)
        print(f"📋 Recursos encontrados: {len(resources)}")
        
        # Estatísticas
        stats = catalog.get_catalog_statistics()
        print(f"📊 Total de recursos no catálogo: {stats.get('total_resources', 0)}")
    
    return 0

if __name__ == "__main__":
    exit(main())
