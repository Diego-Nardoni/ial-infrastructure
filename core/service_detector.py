#!/usr/bin/env python3
"""
Service Detector - Detecção automática de serviços AWS em texto
Parte do MCP Router Inteligente
"""

import re
from typing import List, Dict, Set
from dataclasses import dataclass

@dataclass
class DetectedService:
    name: str
    confidence: float
    keywords_matched: List[str]
    domain: str

class ServiceDetector:
    def __init__(self):
        # Padrões de serviços AWS com keywords e sinônimos
        self.service_patterns = {
            'compute': {
                'ecs': ['ecs', 'container', 'fargate', 'task', 'service', 'cluster'],
                'lambda': ['lambda', 'function', 'serverless', 'event', 'trigger'],
                'eks': ['eks', 'kubernetes', 'k8s', 'pod', 'deployment'],
                'ec2': ['ec2', 'instance', 'virtual machine', 'vm', 'server']
            },
            'data': {
                'rds': ['rds', 'database', 'mysql', 'postgres', 'aurora', 'db'],
                'dynamodb': ['dynamodb', 'nosql', 'table', 'item', 'key-value'],
                'elasticache': ['redis', 'memcached', 'cache', 'elasticache'],
                's3': ['s3', 'bucket', 'object', 'storage', 'file']
            },
            'networking': {
                'elb': ['elb', 'alb', 'nlb', 'load balancer', 'balancer', 'lb'],
                'vpc': ['vpc', 'network', 'subnet', 'security group', 'routing'],
                'apigateway': ['api gateway', 'api', 'rest', 'http', 'endpoint']
            },
            'security': {
                'iam': ['iam', 'role', 'policy', 'permission', 'access', 'user'],
                'kms': ['kms', 'encryption', 'key', 'encrypt', 'decrypt'],
                'secrets': ['secrets manager', 'secret', 'password', 'credential']
            },
            'serverless': {
                'stepfunctions': ['step functions', 'workflow', 'state machine', 'orchestration'],
                'sns': ['sns', 'notification', 'topic', 'message', 'publish'],
                'sqs': ['sqs', 'queue', 'message', 'fifo', 'dead letter']
            },
            'observability': {
                'cloudwatch': ['cloudwatch', 'monitoring', 'metrics', 'logs', 'alarm'],
                'xray': ['xray', 'tracing', 'trace', 'distributed']
            },
            'devops': {
                'github': ['github', 'git', 'repository', 'repo', 'pull request', 'pr', 'commit', 'branch', 'merge', 'issue', 'workflow', 'action', 'ci/cd', 'pipeline', 'deployment', 'release'],
                'xray': ['xray', 'tracing', 'trace', 'distributed']
            },
            'finops': {
                'billing': ['billing', 'cost', 'budget', 'pricing', 'expense'],
                'costexplorer': ['cost explorer', 'cost analysis', 'spend']
            }
        }
        
        # Padrões arquiteturais
        self.architecture_patterns = {
            '3-tier': ['3 tier', '3 camadas', 'three tier', 'web app', 'presentation data'],
            'microservices': ['microservices', 'micro services', 'service mesh'],
            'serverless': ['serverless', 'event driven', 'lambda architecture'],
            'data-pipeline': ['data pipeline', 'etl', 'data processing', 'analytics']
        }

    def detect(self, text: str) -> Dict[str, List[DetectedService]]:
        """Detecta serviços AWS no texto fornecido"""
        text_lower = text.lower()
        detected = {'services': [], 'patterns': []}
        
        # Detectar serviços específicos
        for domain, services in self.service_patterns.items():
            for service, keywords in services.items():
                matched_keywords = []
                confidence = 0.0
                
                for keyword in keywords:
                    if keyword in text_lower:
                        matched_keywords.append(keyword)
                        confidence += 1.0
                
                if matched_keywords:
                    # Normalizar confiança baseada no número de keywords
                    confidence = min(confidence / len(keywords), 1.0)
                    
                    detected['services'].append(DetectedService(
                        name=service,
                        confidence=confidence,
                        keywords_matched=matched_keywords,
                        domain=domain
                    ))
        
        # Detectar padrões arquiteturais
        for pattern, keywords in self.architecture_patterns.items():
            matched_keywords = []
            for keyword in keywords:
                if keyword in text_lower:
                    matched_keywords.append(keyword)
            
            if matched_keywords:
                detected['patterns'].append({
                    'name': pattern,
                    'keywords_matched': matched_keywords,
                    'confidence': len(matched_keywords) / len(keywords)
                })
        
        return detected

    def infer_dependencies(self, detected_services: List[DetectedService]) -> List[str]:
        """Infere dependências implícitas baseado nos serviços detectados"""
        dependencies = set()
        service_names = [s.name for s in detected_services]
        
        # Regras de dependência
        dependency_rules = {
            # Se tem compute, precisa de networking
            ('ecs', 'lambda', 'eks'): ['vpc', 'iam'],
            # Se tem database, precisa de networking e security
            ('rds', 'dynamodb'): ['vpc', 'iam', 'kms'],
            # Se tem load balancer, precisa de networking
            ('elb',): ['vpc'],
            # Qualquer serviço precisa de IAM
            ('*',): ['iam']
        }
        
        for trigger_services, deps in dependency_rules.items():
            if trigger_services == ('*',) or any(svc in service_names for svc in trigger_services):
                dependencies.update(deps)
        
        return list(dependencies)

    def get_domain_priority(self, detected_services: List[DetectedService]) -> List[str]:
        """Determina ordem de prioridade dos domínios para deployment"""
        domain_scores = {}
        
        for service in detected_services:
            domain_scores[service.domain] = domain_scores.get(service.domain, 0) + service.confidence
        
        # Ordem padrão de deployment (foundation first)
        deployment_order = ['security', 'networking', 'data', 'compute', 'serverless', 'observability']
        
        # Ordenar domínios detectados pela ordem de deployment
        prioritized = []
        for domain in deployment_order:
            if domain in domain_scores:
                prioritized.append(domain)
        
        # Adicionar domínios não previstos no final
        for domain in domain_scores:
            if domain not in prioritized:
                prioritized.append(domain)
        
        return prioritized
