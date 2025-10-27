#!/usr/bin/env python3
"""Phase Manager - DAG Cognitivo Determinístico"""

import boto3
import yaml
import json
import os
from pathlib import Path
from typing import Dict, List, Set
import networkx as nx

# AWS clients
bedrock = boto3.client('bedrock-runtime')

PROJECT_ROOT = Path(__file__).parent.parent
PHASES_DIR = PROJECT_ROOT / 'phases'

class PhaseManager:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.phases = {}
        self.dependencies = {}
        
    def discover_phases(self) -> Dict:
        """Descobre todas as fases dos arquivos YAML"""
        phases = {}
        
        for domain_dir in PHASES_DIR.iterdir():
            if not domain_dir.is_dir() or domain_dir.name.startswith('.'):
                continue
                
            domain_name = domain_dir.name
            phases[domain_name] = []
            
            for yaml_file in domain_dir.glob('*.yaml'):
                if yaml_file.name == 'domain-metadata.yaml':
                    continue
                    
                phase_name = yaml_file.stem
                phases[domain_name].append({
                    'name': phase_name,
                    'file': str(yaml_file),
                    'domain': domain_name
                })
                
        return phases
    
    def infer_dependencies_with_ai(self, phases: Dict) -> Dict:
        """Usa Bedrock para inferir dependências entre recursos"""
        
        # Preparar contexto para IA
        phase_context = []
        for domain, phase_list in phases.items():
            for phase in phase_list:
                with open(phase['file'], 'r') as f:
                    content = f.read()
                phase_context.append({
                    'domain': domain,
                    'phase': phase['name'],
                    'resources': self._extract_resources(content)
                })
        
        prompt = f"""Analise as fases de infraestrutura AWS e determine dependências:

{json.dumps(phase_context, indent=2)}

Regras de dependência AWS:
- VPC antes de Subnets, Security Groups, etc
- IAM roles antes de recursos que os usam
- KMS keys antes de recursos criptografados
- Secrets Manager antes de recursos que usam secrets
- ECR antes de ECS tasks
- ALB antes de ECS services
- DynamoDB antes de aplicações que o usam

Retorne JSON com depends_on e reasoning:
{{
  "domain/phase": {{
    "depends_on": ["domain/phase1", "domain/phase2"],
    "reasoning": "Explicação clara da dependência"
  }}
}}"""

        try:
            response = bedrock.invoke_model(
                modelId='anthropic.claude-3-haiku-20240307-v1:0',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 4000,
                    'messages': [{'role': 'user', 'content': prompt}]
                })
            )
            
            result = json.loads(response['body'].read())
            content = result['content'][0]['text']
            
            # Extrair JSON da resposta
            start = content.find('{')
            end = content.rfind('}') + 1
            dependencies_json = content[start:end]
            
            return json.loads(dependencies_json)
            
        except Exception as e:
            print(f"⚠️ Erro na inferência IA: {e}")
            return self._fallback_dependencies()
    
    def _extract_resources(self, yaml_content: str) -> List[str]:
        """Extrai tipos de recursos do YAML"""
        try:
            data = yaml.safe_load(yaml_content)
            resources = []
            
            if isinstance(data, dict) and 'Resources' in data:
                for resource_name, resource_def in data['Resources'].items():
                    if 'Type' in resource_def:
                        resources.append(resource_def['Type'])
                        
            return list(set(resources))
        except:
            return []
    
    def _fallback_dependencies(self) -> Dict:
        """Dependências básicas como fallback"""
        return {
            "10-security/01-kms-security": {"depends_on": ["00-foundation/01-dynamodb-state"], "reasoning": "KMS precisa de logging básico"},
            "20-network/01-networking": {"depends_on": ["10-security/01-kms-security"], "reasoning": "VPC precisa de KMS para logs"},
            "30-compute/01-ecr": {"depends_on": ["10-security/04-iam-roles"], "reasoning": "ECR precisa de IAM roles"},
            "30-compute/02-ecs-cluster": {"depends_on": ["20-network/01-networking"], "reasoning": "ECS precisa de VPC"},
            "40-data/01-redis": {"depends_on": ["20-network/01-networking", "10-security/01-kms-security"], "reasoning": "Redis precisa de VPC e KMS"}
        }
    
    def build_dag(self, dependencies: Dict) -> nx.DiGraph:
        """Constrói o DAG a partir das dependências"""
        graph = nx.DiGraph()
        
        # Adicionar todos os nós
        for phase_key in dependencies.keys():
            graph.add_node(phase_key)
            
        # Adicionar arestas de dependência
        for phase, deps in dependencies.items():
            for dep in deps.get('depends_on', []):
                if dep in dependencies:
                    graph.add_edge(dep, phase)
                    
        return graph
    
    def validate_dag(self, graph: nx.DiGraph) -> bool:
        """Valida se o DAG não tem ciclos"""
        try:
            list(nx.topological_sort(graph))
            return True
        except nx.NetworkXError:
            return False
    
    def generate_deployment_order(self) -> Dict:
        """Gera o arquivo deployment-order.yaml atualizado"""
        
        # 1. Descobrir fases
        phases = self.discover_phases()
        
        # 2. Inferir dependências com IA
        dependencies = self.infer_dependencies_with_ai(phases)
        
        # 3. Construir DAG
        graph = self.build_dag(dependencies)
        
        # 4. Validar DAG
        if not self.validate_dag(graph):
            raise Exception("❌ DAG contém ciclos - dependências inválidas")
        
        # 5. Gerar ordem topológica
        execution_order = list(nx.topological_sort(graph))
        
        # 6. Construir estrutura final
        deployment_order = {
            'metadata': {
                'version': '3.0',
                'architecture': 'dag-cognitive',
                'generated_by': 'phase_manager_ai',
                'total_phases': len(execution_order),
                'generated_at': str(pd.Timestamp.now())
            },
            'execution_order': execution_order,
            'dependencies': dependencies,
            'dag_validation': {
                'is_valid': True,
                'has_cycles': False,
                'total_nodes': graph.number_of_nodes(),
                'total_edges': graph.number_of_edges()
            }
        }
        
        return deployment_order

def main():
    """Execução principal"""
    try:
        manager = PhaseManager()
        deployment_order = manager.generate_deployment_order()
        
        # Salvar arquivo
        output_file = PHASES_DIR / 'deployment-order.yaml'
        with open(output_file, 'w') as f:
            yaml.dump(deployment_order, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ DAG cognitivo gerado: {output_file}")
        print(f"📊 Total fases: {deployment_order['metadata']['total_phases']}")
        print(f"🔗 Total dependências: {deployment_order['dag_validation']['total_edges']}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return 1
        
    return 0

if __name__ == '__main__':
    import pandas as pd
    exit(main())
