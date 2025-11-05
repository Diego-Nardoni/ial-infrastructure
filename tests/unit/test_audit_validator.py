#!/usr/bin/env python3
"""
Testes unitários para Audit Validator
"""

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add core to path
sys.path.append(str(Path(__file__).parent.parent.parent / 'core'))

from audit_validator import AuditValidator

class TestAuditValidator(unittest.TestCase):
    
    def setUp(self):
        """Setup para cada teste"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock AWS clients
        self.mock_cloudformation = Mock()
        self.mock_resource_catalog = Mock()
        self.mock_observability = Mock()
        
        with patch('boto3.client') as mock_client, \
             patch('audit_validator.ResourceCatalog') as mock_catalog_class, \
             patch('audit_validator.ObservabilityEngine') as mock_obs_class:
            
            mock_client.return_value = self.mock_cloudformation
            mock_catalog_class.return_value = self.mock_resource_catalog
            mock_obs_class.return_value = self.mock_observability
            
            self.validator = AuditValidator(region='us-east-1')
    
    def create_test_desired_spec(self) -> Dict:
        """Cria desired spec de teste"""
        return {
            'metadata': {
                'version': '3.1',
                'total_resources': 3
            },
            'resources': [
                {
                    'id': 'test/vpc-123',
                    'name': 'TestVPC',
                    'type': 'AWS::EC2::VPC'
                },
                {
                    'id': 'test/subnet-456',
                    'name': 'TestSubnet',
                    'type': 'AWS::EC2::Subnet'
                },
                {
                    'id': 'test/sg-789',
                    'name': 'TestSG',
                    'type': 'AWS::EC2::SecurityGroup'
                }
            ]
        }
    
    def test_load_desired_spec_success(self):
        """Testa carregamento bem-sucedido do desired spec"""
        # Criar arquivo temporário
        spec = self.create_test_desired_spec()
        spec_file = Path(self.temp_dir) / 'desired_spec.json'
        
        with open(spec_file, 'w') as f:
            json.dump(spec, f)
        
        # Testar carregamento
        loaded_spec = self.validator.load_desired_spec(str(spec_file))
        
        self.assertEqual(len(loaded_spec['resources']), 3)
        self.assertEqual(loaded_spec['metadata']['version'], '3.1')
    
    def test_load_desired_spec_file_not_found(self):
        """Testa erro quando arquivo não existe"""
        with self.assertRaises(FileNotFoundError):
            self.validator.load_desired_spec('/nonexistent/file.json')
    
    def test_inspect_cloudformation(self):
        """Testa inspeção do CloudFormation"""
        # Mock response
        mock_stacks = {
            'Stacks': [
                {
                    'StackName': 'test-stack',
                    'StackStatus': 'CREATE_COMPLETE',
                    'CreationTime': '2023-01-01T00:00:00Z'
                }
            ]
        }
        
        mock_resources = {
            'StackResources': [
                {
                    'LogicalResourceId': 'TestVPC',
                    'PhysicalResourceId': 'vpc-123456',
                    'ResourceType': 'AWS::EC2::VPC',
                    'ResourceStatus': 'CREATE_COMPLETE'
                }
            ]
        }
        
        # Configure mocks
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [mock_stacks]
        
        mock_resource_paginator = Mock()
        mock_resource_paginator.paginate.return_value = [mock_resources]
        
        self.mock_cloudformation.get_paginator.side_effect = [
            mock_paginator,  # For describe_stacks
            mock_resource_paginator  # For describe_stack_resources
        ]
        
        # Execute test
        result = self.validator.inspect_cloudformation()
        
        # Verify results
        self.assertEqual(result['total_stacks'], 1)
        self.assertEqual(len(result['stacks']), 1)
        self.assertEqual(result['stacks'][0]['name'], 'test-stack')
        self.assertEqual(len(result['stacks'][0]['resources']), 1)
    
    def test_inspect_real_resources(self):
        """Testa consulta de recursos reais"""
        # Mock resource catalog response
        mock_resources = [
            {
                'resource_id': 'test/vpc-123',
                'resource_type': 'AWS::EC2::VPC',
                'status': 'deployed'
            },
            {
                'resource_id': 'test/subnet-456',
                'resource_type': 'AWS::EC2::Subnet',
                'status': 'deployed'
            }
        ]
        
        self.mock_resource_catalog.list_resources.return_value = mock_resources
        
        # Execute test
        result = self.validator.inspect_real_resources()
        
        # Verify results
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['resource_id'], 'test/vpc-123')
    
    def test_compare_state_complete(self):
        """Testa comparação de estado com 100% completeness"""
        desired_spec = self.create_test_desired_spec()
        
        cfn_state = {
            'total_stacks': 1,
            'stack_resources': {}
        }
        
        catalog_resources = [
            {'resource_id': 'test/vpc-123'},
            {'resource_id': 'test/subnet-456'},
            {'resource_id': 'test/sg-789'}
        ]
        
        result = self.validator.compare_state(desired_spec, cfn_state, catalog_resources)
        
        self.assertEqual(result['completeness'], 100)
        self.assertTrue(result['audit_passed'])
        self.assertEqual(len(result['missing_resources']), 0)
        self.assertEqual(len(result['extra_resources']), 0)
    
    def test_compare_state_incomplete(self):
        """Testa comparação de estado com recursos ausentes"""
        desired_spec = self.create_test_desired_spec()
        
        cfn_state = {
            'total_stacks': 1,
            'stack_resources': {}
        }
        
        # Apenas 2 dos 3 recursos desejados
        catalog_resources = [
            {'resource_id': 'test/vpc-123'},
            {'resource_id': 'test/subnet-456'}
        ]
        
        result = self.validator.compare_state(desired_spec, cfn_state, catalog_resources)
        
        self.assertEqual(result['completeness'], 66)  # 2/3 = 66%
        self.assertFalse(result['audit_passed'])
        self.assertEqual(len(result['missing_resources']), 1)
        self.assertIn('test/sg-789', result['missing_resources'])
    
    def test_compare_state_with_extra_resources(self):
        """Testa comparação de estado com recursos extras"""
        desired_spec = self.create_test_desired_spec()
        
        cfn_state = {
            'total_stacks': 1,
            'stack_resources': {}
        }
        
        # Todos os recursos desejados + 1 extra
        catalog_resources = [
            {'resource_id': 'test/vpc-123'},
            {'resource_id': 'test/subnet-456'},
            {'resource_id': 'test/sg-789'},
            {'resource_id': 'test/extra-resource'}  # Extra
        ]
        
        result = self.validator.compare_state(desired_spec, cfn_state, catalog_resources)
        
        self.assertEqual(result['completeness'], 100)
        self.assertTrue(result['audit_passed'])
        self.assertEqual(len(result['missing_resources']), 0)
        self.assertEqual(len(result['extra_resources']), 1)
        self.assertIn('test/extra-resource', result['extra_resources'])
    
    def test_generate_audit_report(self):
        """Testa geração de relatório de auditoria"""
        audit_result = {
            'completeness': 100,
            'audit_passed': True,
            'missing_resources': [],
            'extra_resources': []
        }
        
        report_file = Path(self.temp_dir) / 'test_audit.json'
        
        result_path = self.validator.generate_audit_report(
            audit_result, 
            str(report_file)
        )
        
        # Verificar se arquivo foi criado
        self.assertTrue(Path(result_path).exists())
        
        # Verificar conteúdo
        with open(result_path, 'r') as f:
            saved_report = json.load(f)
        
        self.assertEqual(saved_report['completeness'], 100)
        self.assertTrue(saved_report['audit_passed'])
    
    def test_validate_completeness_gate_pass(self):
        """Testa gate de completeness que passa"""
        audit_result = {
            'completeness': 100,
            'audit_passed': True
        }
        
        result = self.validator.validate_completeness_gate(audit_result)
        self.assertTrue(result)
    
    def test_validate_completeness_gate_fail(self):
        """Testa gate de completeness que falha"""
        audit_result = {
            'completeness': 80,
            'audit_passed': False
        }
        
        result = self.validator.validate_completeness_gate(audit_result)
        self.assertFalse(result)
    
    def tearDown(self):
        """Cleanup após cada teste"""
        import shutil
        shutil.rmtree(self.temp_dir)

if __name__ == '__main__':
    unittest.main()
