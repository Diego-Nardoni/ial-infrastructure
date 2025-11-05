#!/usr/bin/env python3
"""
Testes unitários para Desired State Builder
"""

import unittest
import tempfile
import json
import yaml
from pathlib import Path
import sys
import os

# Add core to path
sys.path.append(str(Path(__file__).parent.parent.parent / 'core'))

from desired_state import DesiredStateBuilder

class TestDesiredStateBuilder(unittest.TestCase):
    
    def setUp(self):
        """Setup para cada teste"""
        self.temp_dir = tempfile.mkdtemp()
        self.phases_dir = Path(self.temp_dir) / 'phases'
        self.reports_dir = Path(self.temp_dir) / 'reports'
        
        # Criar estrutura de diretórios
        self.phases_dir.mkdir(parents=True)
        self.reports_dir.mkdir(parents=True)
        
        # Criar builder com diretório temporário
        self.builder = DesiredStateBuilder(str(self.phases_dir))
        self.builder.reports_dir = self.reports_dir
    
    def tearDown(self):
        """Cleanup após cada teste"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_test_phase(self, domain: str, phase_name: str, resources: dict):
        """Cria fase de teste"""
        domain_dir = self.phases_dir / domain
        domain_dir.mkdir(exist_ok=True)
        
        phase_file = domain_dir / f"{phase_name}.yaml"
        phase_content = {
            'Resources': resources
        }
        
        with open(phase_file, 'w') as f:
            yaml.dump(phase_content, f)
        
        return phase_file
    
    def test_load_phases_empty_directory(self):
        """Testa carregamento com diretório vazio"""
        phases = self.builder.load_phases()
        self.assertEqual(len(phases), 0)
    
    def test_load_phases_with_resources(self):
        """Testa carregamento com recursos"""
        # Criar fase de teste
        test_resources = {
            'TestVPC': {
                'Type': 'AWS::EC2::VPC',
                'Properties': {
                    'CidrBlock': '10.0.0.0/16'
                }
            }
        }
        
        self.create_test_phase('10-security', '01-vpc', test_resources)
        
        phases = self.builder.load_phases()
        
        self.assertEqual(len(phases), 1)
        self.assertEqual(phases[0]['domain'], '10-security')
        self.assertEqual(phases[0]['phase_name'], '01-vpc')
        self.assertIn('Resources', phases[0]['content'])
    
    def test_extract_resources_from_phase(self):
        """Testa extração de recursos de uma fase"""
        phase = {
            'domain': '10-security',
            'phase_name': '01-vpc',
            'file_path': '/test/path',
            'content': {
                'Resources': {
                    'TestVPC': {
                        'Type': 'AWS::EC2::VPC',
                        'Properties': {'CidrBlock': '10.0.0.0/16'},
                        'DependsOn': ['TestKMS']
                    }
                }
            }
        }
        
        resources = self.builder.extract_resources_from_phase(phase)
        
        self.assertEqual(len(resources), 1)
        resource = resources[0]
        
        self.assertEqual(resource['id'], '10-security/01-vpc/TestVPC')
        self.assertEqual(resource['name'], 'TestVPC')
        self.assertEqual(resource['type'], 'AWS::EC2::VPC')
        self.assertEqual(resource['domain'], '10-security')
        self.assertEqual(resource['phase'], '01-vpc')
        self.assertEqual(resource['depends_on'], ['TestKMS'])
    
    def test_build_desired_spec(self):
        """Testa construção da especificação desejada"""
        # Criar múltiplas fases
        self.create_test_phase('10-security', '01-kms', {
            'TestKMS': {
                'Type': 'AWS::KMS::Key',
                'Properties': {'Description': 'Test key'}
            }
        })
        
        self.create_test_phase('20-network', '01-vpc', {
            'TestVPC': {
                'Type': 'AWS::EC2::VPC',
                'Properties': {'CidrBlock': '10.0.0.0/16'},
                'DependsOn': ['TestKMS']
            }
        })
        
        phases = self.builder.load_phases()
        spec = self.builder.build_desired_spec(phases)
        
        # Verificar estrutura do spec
        self.assertIn('metadata', spec)
        self.assertIn('domains', spec)
        self.assertIn('resources', spec)
        self.assertIn('dependencies', spec)
        
        # Verificar metadados
        self.assertEqual(spec['metadata']['total_phases'], 2)
        self.assertEqual(spec['metadata']['total_domains'], 2)
        self.assertEqual(spec['metadata']['total_resources'], 2)
        
        # Verificar domínios
        self.assertIn('10-security', spec['domains'])
        self.assertIn('20-network', spec['domains'])
        
        # Verificar recursos
        self.assertEqual(len(spec['resources']), 2)
        
        # Verificar dependências
        vpc_resource_id = '20-network/01-vpc/TestVPC'
        self.assertIn(vpc_resource_id, spec['dependencies'])
        self.assertEqual(spec['dependencies'][vpc_resource_id], ['TestKMS'])
    
    def test_calculate_spec_hash(self):
        """Testa cálculo de hash da especificação"""
        spec1 = {
            'metadata': {'generated_at': '2023-01-01'},
            'resources': [{'id': 'test', 'type': 'AWS::Test'}]
        }
        
        spec2 = {
            'metadata': {'generated_at': '2023-01-02'},  # Diferente timestamp
            'resources': [{'id': 'test', 'type': 'AWS::Test'}]  # Mesmo conteúdo
        }
        
        hash1 = self.builder.calculate_spec_hash(spec1)
        hash2 = self.builder.calculate_spec_hash(spec2)
        
        # Hashes devem ser iguais (timestamp é ignorado)
        self.assertEqual(hash1, hash2)
        
        # Mudança no conteúdo deve gerar hash diferente
        spec3 = {
            'metadata': {'generated_at': '2023-01-01'},
            'resources': [{'id': 'test2', 'type': 'AWS::Test'}]  # ID diferente
        }
        
        hash3 = self.builder.calculate_spec_hash(spec3)
        self.assertNotEqual(hash1, hash3)
    
    def test_validate_spec(self):
        """Testa validação da especificação"""
        # Spec válido
        valid_spec = {
            'domains': {'test': {}},
            'resources': [
                {
                    'id': 'test/resource1',
                    'type': 'AWS::Test::Resource'
                }
            ],
            'dependencies': {}
        }
        
        errors = self.builder.validate_spec(valid_spec)
        self.assertEqual(len(errors), 0)
        
        # Spec inválido - sem recursos
        invalid_spec1 = {
            'domains': {'test': {}},
            'resources': [],
            'dependencies': {}
        }
        
        errors = self.builder.validate_spec(invalid_spec1)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any('Nenhum recurso encontrado' in error for error in errors))
        
        # Spec inválido - ID duplicado
        invalid_spec2 = {
            'domains': {'test': {}},
            'resources': [
                {'id': 'test/resource1', 'type': 'AWS::Test::Resource'},
                {'id': 'test/resource1', 'type': 'AWS::Test::Resource2'}  # ID duplicado
            ],
            'dependencies': {}
        }
        
        errors = self.builder.validate_spec(invalid_spec2)
        self.assertTrue(any('ID duplicado' in error for error in errors))
        
        # Spec inválido - dependência inexistente
        invalid_spec3 = {
            'domains': {'test': {}},
            'resources': [
                {'id': 'test/resource1', 'type': 'AWS::Test::Resource'}
            ],
            'dependencies': {
                'test/resource1': ['nonexistent/resource']
            }
        }
        
        errors = self.builder.validate_spec(invalid_spec3)
        self.assertTrue(any('Dependência inexistente' in error for error in errors))
    
    def test_save_and_load_spec(self):
        """Testa salvamento e carregamento da especificação"""
        # Criar spec de teste
        test_spec = {
            'metadata': {'version': '3.1'},
            'domains': {'test': {}},
            'resources': [{'id': 'test/resource1', 'type': 'AWS::Test'}],
            'dependencies': {}
        }
        
        # Salvar spec
        spec_hash = self.builder.save_desired_spec(test_spec)
        
        # Verificar arquivos criados
        current_file = self.reports_dir / 'desired_spec.json'
        versioned_file = self.reports_dir / f'desired_spec_{spec_hash}.json'
        
        self.assertTrue(current_file.exists())
        self.assertTrue(versioned_file.exists())
        
        # Carregar e verificar conteúdo
        with open(current_file, 'r') as f:
            loaded_spec = json.load(f)
        
        self.assertEqual(loaded_spec['metadata']['spec_hash'], spec_hash)
        self.assertEqual(len(loaded_spec['resources']), 1)
    
    def test_generate_summary_report(self):
        """Testa geração de relatório resumido"""
        spec = {
            'metadata': {'version': '3.1', 'total_resources': 2},
            'domains': {
                'security': {'phases': [{'name': 'kms'}], 'resource_count': 1},
                'network': {'phases': [{'name': 'vpc'}], 'resource_count': 1}
            },
            'resources': [
                {'type': 'AWS::KMS::Key'},
                {'type': 'AWS::EC2::VPC'}
            ],
            'dependencies': {'vpc': ['kms']}
        }
        
        summary = self.builder.generate_summary_report(spec)
        
        # Verificar estrutura do resumo
        self.assertIn('timestamp', summary)
        self.assertIn('metadata', summary)
        self.assertIn('domains_summary', summary)
        self.assertIn('resource_types', summary)
        self.assertIn('dependency_count', summary)
        self.assertIn('validation_errors', summary)
        
        # Verificar conteúdo
        self.assertEqual(summary['dependency_count'], 1)
        self.assertEqual(len(summary['domains_summary']), 2)
        self.assertEqual(summary['resource_types']['AWS::KMS::Key'], 1)
        self.assertEqual(summary['resource_types']['AWS::EC2::VPC'], 1)

if __name__ == '__main__':
    unittest.main()
