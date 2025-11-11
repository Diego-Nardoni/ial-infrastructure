#!/usr/bin/env python3
"""
Desired State Builder - Core do IAL v3.1
Transforma phases/*.yaml em desired_spec.json canônico
"""

import yaml
import json
import os
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import sys

# Try to import CloudFormation YAML loader
try:
    from .cf_yaml_loader import load_cf_yaml
    CF_LOADER_AVAILABLE = True
except ImportError:
    CF_LOADER_AVAILABLE = False

class DesiredStateBuilder:
    def __init__(self, phases_dir: str = "phases"):
        # Usar path absoluto baseado no diretório do projeto
        if not os.path.isabs(phases_dir):
            # Se for path relativo, usar baseado no diretório pai do core
            project_root = Path(__file__).parent.parent
            self.phases_dir = project_root / phases_dir
        else:
            self.phases_dir = Path(phases_dir)
            
        self.reports_dir = Path("./reports")
        self.reports_dir.mkdir(exist_ok=True)
        
    def load_phases(self) -> List[Dict]:
        """Carrega todas as fases dos arquivos YAML"""
        phases = []
        
        if not self.phases_dir.exists():
            print(f"❌ Diretório de fases não encontrado: {self.phases_dir}")
            return phases
            
        
        for domain_dir in self.phases_dir.iterdir():
            if not domain_dir.is_dir() or domain_dir.name.startswith('.'):
                continue
                
            domain_name = domain_dir.name
            print(f"📁 Processando domínio: {domain_name}")
            
            for yaml_file in domain_dir.glob('*.yaml'):
                if yaml_file.name in ['domain-metadata.yaml', 'deployment-order.yaml']:
                    continue
                    
                try:
                    # Usar CF YAML loader se disponível
                    if CF_LOADER_AVAILABLE:
                        with open(yaml_file, 'r') as f:
                            content = load_cf_yaml(f)
                    else:
                        with open(yaml_file, 'r') as f:
                            content = yaml.safe_load(f)
                    
                    if content:
                        phase_info = {
                            'domain': domain_name,
                            'phase_name': yaml_file.stem,
                            'file_path': str(yaml_file),
                            'content': content,
                            'loaded_at': datetime.utcnow().isoformat()
                        }
                        phases.append(phase_info)
                        print(f"  ✅ {yaml_file.name}")
                        
                except Exception as e:
                    print(f"  ❌ Erro ao carregar {yaml_file.name}: {e}")
                    
        print(f"📊 Total de fases carregadas: {len(phases)}")
        return phases
    
    def extract_resources_from_phase(self, phase: Dict) -> List[Dict]:
        """Extrai recursos de uma fase específica"""
        resources = []
        content = phase.get('content', {})
        
        # CloudFormation Resources
        if 'Resources' in content:
            cf_resources = content['Resources']
            if isinstance(cf_resources, dict):
                for resource_name, resource_def in cf_resources.items():
                    resource = {
                        'id': f"{phase['domain']}/{phase['phase_name']}/{resource_name}",
                        'name': resource_name,
                        'type': resource_def.get('Type', 'Unknown'),
                        'properties': resource_def.get('Properties', {}),
                        'domain': phase['domain'],
                        'phase': phase['phase_name'],
                        'file_path': phase['file_path'],
                        'depends_on': resource_def.get('DependsOn', []),
                        'metadata': resource_def.get('Metadata', {}),
                        'condition': resource_def.get('Condition'),
                        'deletion_policy': resource_def.get('DeletionPolicy'),
                        'update_replace_policy': resource_def.get('UpdateReplacePolicy')
                    }
                    resources.append(resource)
        
        # Custom phase resources (formato IAL)
        if 'resources' in content:
            ial_resources = content['resources']
            if isinstance(ial_resources, dict):
                for resource_name, resource_def in ial_resources.items():
                    resource = {
                        'id': f"{phase['domain']}/{phase['phase_name']}/{resource_name}",
                        'name': resource_name,
                        'type': resource_def.get('type', 'Custom'),
                        'properties': resource_def,
                        'domain': phase['domain'],
                        'phase': phase['phase_name'],
                        'file_path': phase['file_path'],
                        'custom_ial_resource': True
                    }
                    resources.append(resource)
            elif isinstance(ial_resources, list):
                # Handle list format
                for i, resource_def in enumerate(ial_resources):
                    if isinstance(resource_def, dict):
                        resource_name = resource_def.get('name', f'resource_{i}')
                        resource = {
                            'id': f"{phase['domain']}/{phase['phase_name']}/{resource_name}",
                            'name': resource_name,
                            'type': resource_def.get('type', 'Custom'),
                            'properties': resource_def,
                            'domain': phase['domain'],
                            'phase': phase['phase_name'],
                            'file_path': phase['file_path'],
                            'custom_ial_resource': True
                        }
                        resources.append(resource)
                
        return resources
    
    def build_desired_spec(self, phases: List[Dict]) -> Dict:
        """Constrói especificação desejada canônica"""
        print("🏗️ Construindo desired_spec...")
        
        spec = {
            'metadata': {
                'version': '3.1',
                'generated_at': datetime.utcnow().isoformat(),
                'generator': 'desired_state_builder',
                'total_phases': len(phases),
                'total_domains': len(set(p['domain'] for p in phases))
            },
            'domains': {},
            'resources': [],
            'dependencies': {},
            'parameters': {},
            'outputs': {}
        }
        
        all_resources = []
        
        # Processar cada fase
        for phase in phases:
            domain = phase['domain']
            if domain not in spec['domains']:
                spec['domains'][domain] = {
                    'phases': [],
                    'resource_count': 0
                }
            
            # Adicionar fase ao domínio
            phase_info = {
                'name': phase['phase_name'],
                'file_path': phase['file_path'],
                'loaded_at': phase['loaded_at']
            }
            spec['domains'][domain]['phases'].append(phase_info)
            
            # Extrair recursos da fase
            phase_resources = self.extract_resources_from_phase(phase)
            all_resources.extend(phase_resources)
            spec['domains'][domain]['resource_count'] += len(phase_resources)
            
            # Extrair parâmetros e outputs se existirem
            content = phase.get('content', {})
            if 'Parameters' in content:
                spec['parameters'].update(content['Parameters'])
            if 'Outputs' in content:
                spec['outputs'].update(content['Outputs'])
        
        # Adicionar recursos ao spec
        spec['resources'] = all_resources
        spec['metadata']['total_resources'] = len(all_resources)
        
        # Construir mapa de dependências
        for resource in all_resources:
            if resource.get('depends_on'):
                spec['dependencies'][resource['id']] = resource['depends_on']
        
        print(f"📊 Spec construído: {len(all_resources)} recursos em {len(spec['domains'])} domínios")
        return spec
    
    def calculate_spec_hash(self, spec: Dict) -> str:
        """Calcula hash da especificação para versionamento"""
        # Remove metadata temporal para hash consistente
        spec_copy = spec.copy()
        if 'metadata' in spec_copy:
            spec_copy['metadata'] = {k: v for k, v in spec_copy['metadata'].items() 
                                   if k not in ['generated_at']}
        
        spec_str = json.dumps(spec_copy, sort_keys=True)
        return hashlib.sha256(spec_str.encode()).hexdigest()[:16]
    
    def save_desired_spec(self, spec: Dict, version: Optional[str] = None) -> str:
        """Salva especificação desejada com versionamento"""
        spec_hash = self.calculate_spec_hash(spec)
        
        if not version:
            version = spec_hash
            
        spec['metadata']['spec_hash'] = spec_hash
        spec['metadata']['version'] = version
        
        # Salvar versão atual
        current_file = self.reports_dir / 'desired_spec.json'
        with open(current_file, 'w') as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
        
        # Salvar versão histórica
        versioned_file = self.reports_dir / f'desired_spec_{version}.json'
        with open(versioned_file, 'w') as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Desired spec salvo:")
        print(f"  📄 Atual: {current_file}")
        print(f"  📄 Versionado: {versioned_file}")
        print(f"  🔑 Hash: {spec_hash}")
        
        return spec_hash
    
    def validate_spec(self, spec: Dict) -> List[str]:
        """Valida especificação desejada"""
        errors = []
        
        # Validações básicas
        if not spec.get('resources'):
            errors.append("Nenhum recurso encontrado na especificação")
        
        if not spec.get('domains'):
            errors.append("Nenhum domínio encontrado na especificação")
        
        # Validar recursos
        resource_ids = set()
        for resource in spec.get('resources', []):
            if not resource.get('id'):
                errors.append(f"Recurso sem ID: {resource}")
                continue
                
            if resource['id'] in resource_ids:
                errors.append(f"ID duplicado: {resource['id']}")
            resource_ids.add(resource['id'])
            
            if not resource.get('type'):
                errors.append(f"Recurso sem tipo: {resource['id']}")
        
        # Validar dependências
        for resource_id, deps in spec.get('dependencies', {}).items():
            if resource_id not in resource_ids:
                errors.append(f"Dependência para recurso inexistente: {resource_id}")
            
            for dep in deps:
                if dep not in resource_ids:
                    errors.append(f"Dependência inexistente: {dep} para {resource_id}")
        
        return errors
    
    def generate_summary_report(self, spec: Dict) -> Dict:
        """Gera relatório resumido da especificação"""
        summary = {
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': spec.get('metadata', {}),
            'domains_summary': {},
            'resource_types': {},
            'dependency_count': len(spec.get('dependencies', {})),
            'validation_errors': self.validate_spec(spec)
        }
        
        # Resumo por domínio
        for domain, info in spec.get('domains', {}).items():
            summary['domains_summary'][domain] = {
                'phases': len(info.get('phases', [])),
                'resources': info.get('resource_count', 0)
            }
        
        # Contagem por tipo de recurso
        for resource in spec.get('resources', []):
            resource_type = resource.get('type', 'Unknown')
            summary['resource_types'][resource_type] = summary['resource_types'].get(resource_type, 0) + 1
        
        return summary

def main():
    """Função principal para execução standalone"""
    print("🚀 IAL Desired State Builder v3.1")
    print("=" * 50)
    
    builder = DesiredStateBuilder()
    
    # Carregar fases
    phases = builder.load_phases()
    if not phases:
        print("❌ Nenhuma fase encontrada!")
        return 1
    
    # Construir especificação
    spec = builder.build_desired_spec(phases)
    
    # Validar especificação
    errors = builder.validate_spec(spec)
    if errors:
        print("⚠️ Erros de validação encontrados:")
        for error in errors:
            print(f"  ❌ {error}")
    
    # Salvar especificação
    spec_hash = builder.save_desired_spec(spec)
    
    # Gerar relatório resumido
    summary = builder.generate_summary_report(spec)
    summary_file = Path("./reports/desired_spec_summary.json")
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"📊 Relatório resumido: {summary_file}")
    
    # Exibir estatísticas
    print("\n📈 ESTATÍSTICAS:")
    print(f"  🏗️ Domínios: {len(spec['domains'])}")
    print(f"  📦 Recursos: {len(spec['resources'])}")
    print(f"  🔗 Dependências: {len(spec['dependencies'])}")
    print(f"  ⚠️ Erros: {len(errors)}")
    
    if errors:
        return 1
    
    print("\n✅ Desired State Builder executado com sucesso!")
    return 0

if __name__ == "__main__":
    exit(main())
