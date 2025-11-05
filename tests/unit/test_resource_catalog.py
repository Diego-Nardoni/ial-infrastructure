#!/usr/bin/env python3
"""
Testes unitários para Resource Catalog
"""

import unittest
import json
import time
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add core to path
sys.path.append(str(Path(__file__).parent.parent.parent / 'core'))

from resource_catalog import ResourceCatalog

class TestResourceCatalog(unittest.TestCase):
    
    def setUp(self):
        """Setup para cada teste"""
        # Mock AWS clients para evitar chamadas reais
        self.mock_dynamodb = Mock()
        self.mock_dynamodb_resource = Mock()
        
        with patch('boto3.client') as mock_client, \
             patch('boto3.resource') as mock_resource:
            
            mock_client.return_value = self.mock_dynamodb
            mock_resource.return_value = self.mock_dynamodb_resource
            
            # Mock describe_table para simular tabela existente
            self.mock_dynamodb.describe_table.return_value = {'Table': {'TableName': 'test-table'}}
            
            self.catalog = ResourceCatalog(table_name='test-table', region='us-east-1')
    
    def test_register_resource_success(self):
        """Testa registro bem-sucedido de recurso"""
        # Mock successful put_item
        self.mock_dynamodb.put_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        
        result = self.catalog.register_resource(
            resource_id='test/vpc-123',
            resource_type='AWS::EC2::VPC',
            phase='20-network/01-vpc',
            metadata={'cidr': '10.0.0.0/16'},
            status='desired'
        )
        
        self.assertTrue(result)
        self.mock_dynamodb.put_item.assert_called_once()
        
        # Verificar argumentos da chamada
        call_args = self.mock_dynamodb.put_item.call_args
        self.assertEqual(call_args[1]['TableName'], 'test-table')
        self.assertIn('Item', call_args[1])
        
        item = call_args[1]['Item']
        self.assertEqual(item['resource_id']['S'], 'test/vpc-123')
        self.assertEqual(item['resource_type']['S'], 'AWS::EC2::VPC')
        self.assertEqual(item['phase']['S'], '20-network/01-vpc')
        self.assertEqual(item['status']['S'], 'desired')
    
    def test_register_resource_failure(self):
        """Testa falha no registro de recurso"""
        # Mock failed put_item
        self.mock_dynamodb.put_item.side_effect = Exception("DynamoDB error")
        
        result = self.catalog.register_resource(
            resource_id='test/vpc-123',
            resource_type='AWS::EC2::VPC',
            phase='20-network/01-vpc',
            metadata={'cidr': '10.0.0.0/16'}
        )
        
        self.assertFalse(result)
    
    def test_get_resource_success(self):
        """Testa recuperação bem-sucedida de recurso"""
        # Mock successful query
        mock_response = {
            'Items': [{
                'resource_id': {'S': 'test/vpc-123'},
                'resource_type': {'S': 'AWS::EC2::VPC'},
                'phase': {'S': '20-network/01-vpc'},
                'status': {'S': 'desired'},
                'metadata': {'S': '{"cidr": "10.0.0.0/16"}'},
                'metadata_hash': {'S': 'abc123'},
                'timestamp': {'S': '2023-01-01T00:00:00'},
                'version': {'N': '1'}
            }]
        }
        
        self.mock_dynamodb.query.return_value = mock_response
        
        result = self.catalog.get_resource('test/vpc-123', use_cache=False)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['resource_id'], 'test/vpc-123')
        self.assertEqual(result['resource_type'], 'AWS::EC2::VPC')
        self.assertEqual(result['metadata']['cidr'], '10.0.0.0/16')
        self.assertEqual(result['version'], 1)
    
    def test_get_resource_not_found(self):
        """Testa recuperação de recurso inexistente"""
        # Mock empty response
        self.mock_dynamodb.query.return_value = {'Items': []}
        
        result = self.catalog.get_resource('nonexistent/resource')
        
        self.assertIsNone(result)
    
    def test_cache_functionality(self):
        """Testa funcionalidade de cache"""
        # Primeiro, adicionar item ao cache
        test_data = {
            'resource_id': 'test/vpc-123',
            'resource_type': 'AWS::EC2::VPC',
            'timestamp': '2023-01-01T00:00:00'
        }
        
        self.catalog._update_cache('test/vpc-123', test_data)
        
        # Verificar se está no cache
        cached_data = self.catalog._get_from_cache('test/vpc-123')
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data['resource_id'], 'test/vpc-123')
        
        # Testar expiração do cache
        # Simular cache expirado alterando TTL
        original_ttl = self.catalog._cache_ttl
        self.catalog._cache_ttl = -1  # TTL negativo para forçar expiração
        
        cached_data = self.catalog._get_from_cache('test/vpc-123')
        self.assertIsNone(cached_data)
        
        # Restaurar TTL original
        self.catalog._cache_ttl = original_ttl
    
    def test_update_resource_status(self):
        """Testa atualização de status do recurso"""
        # Mock get_resource para retornar recurso existente
        existing_resource = {
            'resource_id': 'test/vpc-123',
            'resource_type': 'AWS::EC2::VPC',
            'phase': '20-network/01-vpc',
            'metadata': {'cidr': '10.0.0.0/16'},
            'status': 'desired'
        }
        
        with patch.object(self.catalog, 'get_resource', return_value=existing_resource), \
             patch.object(self.catalog, 'register_resource', return_value=True) as mock_register:
            
            result = self.catalog.update_resource_status('test/vpc-123', 'deployed')
            
            self.assertTrue(result)
            mock_register.assert_called_once()
            
            # Verificar argumentos da chamada
            call_args = mock_register.call_args[1]
            self.assertEqual(call_args['status'], 'deployed')
    
    def test_list_resources_by_type(self):
        """Testa listagem de recursos por tipo"""
        mock_response = {
            'Items': [
                {
                    'resource_id': {'S': 'test/vpc-1'},
                    'resource_type': {'S': 'AWS::EC2::VPC'},
                    'phase': {'S': '20-network/01-vpc'},
                    'status': {'S': 'desired'},
                    'metadata': {'S': '{"cidr": "10.0.0.0/16"}'},
                    'timestamp': {'S': '2023-01-01T00:00:00'}
                },
                {
                    'resource_id': {'S': 'test/vpc-2'},
                    'resource_type': {'S': 'AWS::EC2::VPC'},
                    'phase': {'S': '20-network/01-vpc'},
                    'status': {'S': 'deployed'},
                    'metadata': {'S': '{"cidr": "10.1.0.0/16"}'},
                    'timestamp': {'S': '2023-01-01T01:00:00'}
                }
            ]
        }
        
        self.mock_dynamodb.query.return_value = mock_response
        
        resources = self.catalog.list_resources(resource_type='AWS::EC2::VPC')
        
        self.assertEqual(len(resources), 2)
        self.assertEqual(resources[0]['resource_type'], 'AWS::EC2::VPC')
        self.assertEqual(resources[1]['resource_type'], 'AWS::EC2::VPC')
    
    def test_batch_register_resources(self):
        """Testa registro em lote de recursos"""
        # Mock batch writer
        mock_batch_writer = MagicMock()
        mock_table = Mock()
        
        # Mock context manager properly
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__ = MagicMock(return_value=mock_batch_writer)
        mock_context_manager.__exit__ = MagicMock(return_value=None)
        mock_table.batch_writer.return_value = mock_context_manager
        
        self.mock_dynamodb_resource.Table.return_value = mock_table
        
        resources = [
            {
                'resource_id': 'test/vpc-1',
                'resource_type': 'AWS::EC2::VPC',
                'phase': '20-network/01-vpc',
                'metadata': {'cidr': '10.0.0.0/16'}
            },
            {
                'resource_id': 'test/vpc-2',
                'resource_type': 'AWS::EC2::VPC',
                'phase': '20-network/01-vpc',
                'metadata': {'cidr': '10.1.0.0/16'}
            }
        ]
        
        results = self.catalog.batch_register_resources(resources)
        
        # Verificar que todos os recursos foram processados
        self.assertEqual(len(results), 2)
        self.assertTrue(all(results.values()))
        
        # Verificar que put_item foi chamado para cada recurso
        self.assertEqual(mock_batch_writer.put_item.call_count, 2)
    
    def test_get_resource_history(self):
        """Testa recuperação do histórico de recursos"""
        mock_response = {
            'Items': [
                {
                    'resource_id': {'S': 'test/vpc-123'},
                    'timestamp': {'S': '2023-01-01T02:00:00'},
                    'status': {'S': 'deployed'},
                    'metadata_hash': {'S': 'def456'},
                    'version': {'N': '2'}
                },
                {
                    'resource_id': {'S': 'test/vpc-123'},
                    'timestamp': {'S': '2023-01-01T01:00:00'},
                    'status': {'S': 'desired'},
                    'metadata_hash': {'S': 'abc123'},
                    'version': {'N': '1'}
                }
            ]
        }
        
        self.mock_dynamodb.query.return_value = mock_response
        
        history = self.catalog.get_resource_history('test/vpc-123')
        
        self.assertEqual(len(history), 2)
        # Verificar ordem (mais recente primeiro)
        self.assertEqual(history[0]['status'], 'deployed')
        self.assertEqual(history[1]['status'], 'desired')
        self.assertEqual(history[0]['version'], 2)
        self.assertEqual(history[1]['version'], 1)
    
    def test_get_catalog_statistics(self):
        """Testa recuperação de estatísticas do catálogo"""
        # Mock paginator
        mock_paginator = Mock()
        mock_pages = [
            {
                'Items': [
                    {
                        'resource_type': {'S': 'AWS::EC2::VPC'},
                        'status': {'S': 'desired'},
                        'phase': {'S': '20-network/01-vpc'}
                    },
                    {
                        'resource_type': {'S': 'AWS::KMS::Key'},
                        'status': {'S': 'deployed'},
                        'phase': {'S': '10-security/01-kms'}
                    }
                ]
            }
        ]
        
        mock_paginator.paginate.return_value = mock_pages
        self.mock_dynamodb.get_paginator.return_value = mock_paginator
        
        stats = self.catalog.get_catalog_statistics()
        
        self.assertIn('total_resources', stats)
        self.assertIn('resource_types', stats)
        self.assertIn('status_distribution', stats)
        self.assertIn('phase_distribution', stats)
        
        self.assertEqual(stats['total_resources'], 2)
        self.assertEqual(stats['resource_types']['AWS::EC2::VPC'], 1)
        self.assertEqual(stats['resource_types']['AWS::KMS::Key'], 1)
        self.assertEqual(stats['status_distribution']['desired'], 1)
        self.assertEqual(stats['status_distribution']['deployed'], 1)

if __name__ == '__main__':
    unittest.main()
