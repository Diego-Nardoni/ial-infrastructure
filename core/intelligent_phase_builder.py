#!/usr/bin/env python3
"""
Intelligent Phase Builder
Gera CloudFormation YAML profissional via LLM
"""

import json
import boto3
from typing import Dict, Any, List
from datetime import datetime


class IntelligentPhaseBuilder:
    """Gera phases YAML usando LLM com best practices"""
    
    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime')
        self.model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'
    
    def build_phases(self, nl_intent: str) -> List[Dict[str, Any]]:
        """
        Gera lista de phases baseado em intenção NL
        
        Args:
            nl_intent: Intenção em linguagem natural
        
        Returns:
            Lista de phases com YAML content
        """
        # Implementação simplificada para compatibilidade
        return [{
            "phase_number": 1,
            "phase_name": "foundation",
            "yaml_content": "# Generated phase",
            "dependencies": [],
            "estimated_cost": 0.0
        }]
    
    def build_phase_from_intent(
        self,
        nl_intent: str,
        ias_result: Dict,
        cost_result: Dict
    ) -> Dict[str, Any]:
        """
        Gera phase YAML baseado em intenção NL + validações
        
        Args:
            nl_intent: Intenção em linguagem natural
            ias_result: Resultado da validação IAS
            cost_result: Resultado da estimativa de custo
        
        Returns:
            {
                "phase_number": int,
                "phase_name": str,
                "yaml_content": str,
                "dependencies": List[str],
                "estimated_cost": float
            }
        """
        
        # Construir prompt com contexto
        prompt = self._build_prompt(nl_intent, ias_result, cost_result)
        
        # Chamar LLM
        response = self.bedrock.converse(
            modelId=self.model_id,
            messages=[{
                "role": "user",
                "content": [{"text": prompt}]
            }]
        )
        
        yaml_content = response['output']['message']['content'][0]['text']
        
        # Extrair metadados
        phase_number = self._infer_phase_number(nl_intent)
        phase_name = self._generate_phase_name(nl_intent)
        dependencies = self._extract_dependencies(yaml_content)
        
        return {
            "phase_number": phase_number,
            "phase_name": phase_name,
            "yaml_content": yaml_content,
            "dependencies": dependencies,
            "estimated_cost": cost_result.get("total_monthly_cost", 0.0),
            "created_at": datetime.now().isoformat()
        }
    
    def _build_prompt(self, nl_intent: str, ias_result: Dict, cost_result: Dict) -> str:
        """Constrói prompt para LLM com contexto completo"""
        
        # Extrair riscos do IAS
        risks_summary = ""
        if ias_result.get("risks"):
            risks_summary = "\n".join([
                f"- {r['severity']}: {r['message']} → {r['recommendation']}"
                for r in ias_result["risks"]
            ])
        
        # Extrair custos
        cost_summary = f"Custo estimado: ${cost_result.get('total_monthly_cost', 0):.2f}/mês"
        
        prompt = f"""Você é um especialista em infraestrutura AWS e CloudFormation.

INTENÇÃO DO USUÁRIO:
{nl_intent}

VALIDAÇÕES DE SEGURANÇA (IAS):
{risks_summary if risks_summary else "✅ Nenhum risco detectado"}

ESTIMATIVA DE CUSTO:
{cost_summary}

TAREFA:
Gere um CloudFormation template YAML COMPLETO e PRODUCTION-READY seguindo AWS best practices:

1. SEGURANÇA:
   - Encryption at rest (KMS)
   - Encryption in transit (TLS)
   - Least privilege IAM
   - Security groups restritivos
   - Private subnets quando possível

2. ALTA DISPONIBILIDADE:
   - Multi-AZ quando aplicável
   - Auto Scaling quando aplicável
   - Health checks

3. CUSTO-OTIMIZADO:
   - Use instâncias adequadas ao workload
   - Considere Reserved Instances
   - Lifecycle policies para S3

4. OBSERVABILIDADE:
   - CloudWatch Logs
   - CloudWatch Alarms
   - Tags padronizadas

5. FORMATO:
   - YAML válido
   - Comentários explicativos
   - Outputs para exportação
   - Parameters quando necessário

IMPORTANTE:
- Corrija TODOS os riscos de segurança identificados pelo IAS
- Mantenha o custo dentro do orçamento
- Use nomes de recursos descritivos
- Adicione tags: ManagedBy=IAL, CreatedAt={datetime.now().isoformat()}

Gere APENAS o YAML, sem explicações adicionais:"""
        
        return prompt
    
    def _infer_phase_number(self, nl_intent: str) -> int:
        """Infere número da phase baseado no tipo de recurso"""
        nl_lower = nl_intent.lower()
        
        if "network" in nl_lower or "vpc" in nl_lower:
            return 20
        elif "compute" in nl_lower or "ec2" in nl_lower or "ecs" in nl_lower:
            return 30
        elif "database" in nl_lower or "rds" in nl_lower or "dynamodb" in nl_lower:
            return 40
        elif "storage" in nl_lower or "s3" in nl_lower:
            return 50
        elif "observability" in nl_lower or "monitoring" in nl_lower:
            return 60
        else:
            return 99  # misc
    
    def _generate_phase_name(self, nl_intent: str) -> str:
        """Gera nome da phase baseado na intenção"""
        nl_lower = nl_intent.lower()
        
        # Extract key services
        services = []
        if "vpc" in nl_lower or "network" in nl_lower:
            services.append("network")
        if "ec2" in nl_lower:
            services.append("ec2")
        if "ecs" in nl_lower:
            services.append("ecs")
        if "rds" in nl_lower or "database" in nl_lower:
            services.append("database")
        if "redis" in nl_lower or "elasticache" in nl_lower:
            services.append("cache")
        if "s3" in nl_lower or "bucket" in nl_lower:
            services.append("storage")
        if "alb" in nl_lower or "load balancer" in nl_lower:
            services.append("alb")
        
        if not services:
            services = ["custom"]
        
        return "-".join(services)
    
    def _extract_dependencies(self, yaml_content: str) -> List[str]:
        """Extrai dependências do YAML"""
        dependencies = []
        
        # Check for VPC dependency
        if "Fn::ImportValue" in yaml_content or "VPCId" in yaml_content:
            dependencies.append("20-network")
        
        # Check for subnet dependency
        if "SubnetId" in yaml_content or "Subnets" in yaml_content:
            dependencies.append("20-network")
        
        # Check for security group dependency
        if "SecurityGroupIds" in yaml_content:
            dependencies.append("20-network")
        
        return list(set(dependencies))  # Remove duplicates
