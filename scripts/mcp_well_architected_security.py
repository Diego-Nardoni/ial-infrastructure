#!/usr/bin/env python3
"""MCP Well-Architected Security Assessment"""

import boto3
import json
import yaml
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Import CloudFormation YAML loader
import sys
sys.path.append(str(Path(__file__).parent))
from cf_yaml_loader import load_cf_yaml

PROJECT_ROOT = Path(__file__).parent.parent
PHASES_DIR = PROJECT_ROOT / 'phases'

# AWS clients
bedrock = boto3.client('bedrock-runtime')
s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')

class WellArchitectedAssessment:
    def __init__(self):
        self.phases_data = {}
        self.assessment_results = {}
        self.s3_bucket = os.getenv('S3_REPORTS_BUCKET', 'ial-reports-bucket')
        
    def collect_phases_data(self) -> Dict:
        """Coleta dados de todas as fases para análise"""
        phases = {}
        
        for domain_dir in PHASES_DIR.iterdir():
            if not domain_dir.is_dir() or domain_dir.name.startswith('.'):
                continue
                
            domain_name = domain_dir.name
            phases[domain_name] = {
                'resources': [],
                'security_configs': [],
                'cost_configs': [],
                'reliability_configs': []
            }
            
            for yaml_file in domain_dir.glob('*.yaml'):
                if yaml_file.name in ['domain-metadata.yaml', 'deployment-order.yaml']:
                    continue
                    
                try:
                    content = load_cf_yaml(yaml_file)
                    if isinstance(content, dict) and 'Resources' in content:
                        for resource_name, resource_def in content['Resources'].items():
                            resource_data = {
                                'name': resource_name,
                                'type': resource_def.get('Type'),
                                'properties': resource_def.get('Properties', {}),
                                'phase': yaml_file.stem,
                                'domain': domain_name
                            }
                            phases[domain_name]['resources'].append(resource_data)
                            
                            # Categorizar configurações por pilar
                            self._categorize_resource(resource_data, phases[domain_name])
                            
                except Exception as e:
                    print(f"⚠️ Erro lendo {yaml_file}: {e}")
                    
        return phases
    
    def _categorize_resource(self, resource: Dict, domain_data: Dict):
        """Categoriza recursos por pilares Well-Architected"""
        resource_type = resource.get('type', '')
        properties = resource.get('properties', {})
        
        # Security configurations
        if 'KMS' in resource_type or properties.get('KmsKeyId'):
            domain_data['security_configs'].append({
                'type': 'encryption',
                'resource': resource['name'],
                'config': properties.get('KmsKeyId', 'KMS enabled')
            })
            
        if resource_type == 'AWS::IAM::Role':
            domain_data['security_configs'].append({
                'type': 'iam_role',
                'resource': resource['name'],
                'policies': len(properties.get('Policies', []))
            })
            
        # Reliability configurations
        if properties.get('MultiAZ') or properties.get('AvailabilityZone'):
            domain_data['reliability_configs'].append({
                'type': 'multi_az',
                'resource': resource['name'],
                'config': properties.get('MultiAZ', 'AZ configured')
            })
            
        # Cost configurations
        if 'InstanceType' in properties:
            domain_data['cost_configs'].append({
                'type': 'instance_sizing',
                'resource': resource['name'],
                'instance_type': properties['InstanceType']
            })
    
    def assess_with_bedrock(self, phases_data: Dict) -> Dict:
        """Avalia arquitetura usando Bedrock"""
        
        # Preparar contexto para IA
        context = {
            'total_domains': len(phases_data),
            'total_resources': sum(len(domain['resources']) for domain in phases_data.values()),
            'security_resources': sum(len(domain['security_configs']) for domain in phases_data.values()),
            'reliability_resources': sum(len(domain['reliability_configs']) for domain in phases_data.values()),
            'domains': phases_data
        }
        
        prompt = f"""Avalie esta arquitetura AWS baseada no Well-Architected Framework:

CONTEXTO DA ARQUITETURA:
{json.dumps(context, indent=2)}

Avalie os 5 pilares e retorne scores (0-100) com justificativas:

1. SECURITY: Criptografia, IAM, network security
2. RELIABILITY: Multi-AZ, backup, fault tolerance  
3. PERFORMANCE: Instance sizing, caching, CDN
4. COST_OPTIMIZATION: Right-sizing, reserved instances
5. OPERATIONAL_EXCELLENCE: Monitoring, automation

Retorne JSON:
{{
  "security": {{
    "score": 85,
    "findings": ["KMS encryption enabled", "IAM roles properly configured"],
    "recommendations": ["Enable GuardDuty", "Add WAF rules"]
  }},
  "reliability": {{
    "score": 78,
    "findings": ["Multi-AZ configured for RDS"],
    "recommendations": ["Add backup strategy", "Implement circuit breakers"]
  }},
  "performance": {{
    "score": 82,
    "findings": ["Redis caching enabled"],
    "recommendations": ["Consider CDN", "Optimize instance types"]
  }},
  "cost_optimization": {{
    "score": 75,
    "findings": ["Serverless Redis used"],
    "recommendations": ["Review instance sizing", "Consider reserved instances"]
  }},
  "operational_excellence": {{
    "score": 88,
    "findings": ["CloudWatch monitoring", "Automated deployment"],
    "recommendations": ["Add chaos engineering", "Improve alerting"]
  }},
  "overall_score": 82,
  "critical_issues": [],
  "high_priority_recommendations": ["Enable GuardDuty", "Add backup strategy"]
}}"""

        try:
            response = bedrock.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
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
            assessment_json = content[start:end]
            
            return json.loads(assessment_json)
            
        except Exception as e:
            print(f"⚠️ Erro na avaliação Bedrock: {e}")
            return self._fallback_assessment()
    
    def _fallback_assessment(self) -> Dict:
        """Assessment básico como fallback"""
        return {
            "security": {
                "score": 75,
                "findings": ["Basic security configurations detected"],
                "recommendations": ["Enable comprehensive security monitoring"]
            },
            "reliability": {
                "score": 70,
                "findings": ["Some reliability measures in place"],
                "recommendations": ["Implement comprehensive backup strategy"]
            },
            "performance": {
                "score": 80,
                "findings": ["Performance optimizations detected"],
                "recommendations": ["Monitor and optimize continuously"]
            },
            "cost_optimization": {
                "score": 75,
                "findings": ["Some cost optimizations in place"],
                "recommendations": ["Regular cost reviews needed"]
            },
            "operational_excellence": {
                "score": 85,
                "findings": ["Good automation and monitoring"],
                "recommendations": ["Enhance observability"]
            },
            "overall_score": 77,
            "critical_issues": [],
            "high_priority_recommendations": ["Comprehensive security review needed"]
        }
    
    def save_to_s3(self, assessment: Dict) -> str:
        """Salva relatório no S3"""
        timestamp = datetime.now().strftime('%Y%m%d')
        key = f"reports/well-architected/security-{timestamp}.json"
        
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'assessment': assessment,
            'metadata': {
                'version': '1.0',
                'generated_by': 'mcp_well_architected_security',
                'total_domains': len(self.phases_data),
                'total_resources': sum(len(domain['resources']) for domain in self.phases_data.values())
            }
        }
        
        try:
            s3.put_object(
                Bucket=self.s3_bucket,
                Key=key,
                Body=json.dumps(report, indent=2, default=str),
                ContentType='application/json'
            )
            
            s3_url = f"s3://{self.s3_bucket}/{key}"
            print(f"📄 Relatório salvo: {s3_url}")
            return s3_url
            
        except Exception as e:
            print(f"⚠️ Erro salvando no S3: {e}")
            # Salvar localmente como fallback
            local_path = PROJECT_ROOT / 'reports' / f'well-architected-{timestamp}.json'
            with open(local_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            return str(local_path)
    
    def save_to_dynamodb(self, assessment: Dict, s3_url: str):
        """Salva resumo no DynamoDB"""
        try:
            item = {
                'Project': {'S': 'ial'},
                'AssessmentId': {'S': f"wa-{datetime.now().strftime('%Y%m%d-%H%M%S')}"},
                'Timestamp': {'S': datetime.utcnow().isoformat()},
                'SecurityScore': {'N': str(assessment.get('security', {}).get('score', 0))},
                'ReliabilityScore': {'N': str(assessment.get('reliability', {}).get('score', 0))},
                'OverallScore': {'N': str(assessment.get('overall_score', 0))},
                'S3ReportUrl': {'S': s3_url},
                'CriticalIssues': {'N': str(len(assessment.get('critical_issues', [])))},
                'Status': {'S': 'COMPLETED'}
            }
            
            dynamodb.put_item(
                TableName='mcp-provisioning-checklist',
                Item=item
            )
            
            print("✅ Resumo salvo no DynamoDB")
            
        except Exception as e:
            print(f"⚠️ Erro salvando no DynamoDB: {e}")
    
    def run_assessment(self) -> Dict:
        """Executa assessment completo"""
        print("🔍 Coletando dados das fases...")
        self.phases_data = self.collect_phases_data()
        
        print("🧠 Avaliando com Bedrock...")
        assessment = self.assess_with_bedrock(self.phases_data)
        
        print("💾 Salvando relatórios...")
        s3_url = self.save_to_s3(assessment)
        self.save_to_dynamodb(assessment, s3_url)
        
        # Console output
        print(f"\n📊 WELL-ARCHITECTED ASSESSMENT")
        print(f"{'='*50}")
        print(f"Security: {assessment.get('security', {}).get('score', 0)}/100")
        print(f"Reliability: {assessment.get('reliability', {}).get('score', 0)}/100")
        print(f"Performance: {assessment.get('performance', {}).get('score', 0)}/100")
        print(f"Cost Optimization: {assessment.get('cost_optimization', {}).get('score', 0)}/100")
        print(f"Operational Excellence: {assessment.get('operational_excellence', {}).get('score', 0)}/100")
        print(f"Overall Score: {assessment.get('overall_score', 0)}/100")
        
        if assessment.get('critical_issues'):
            print(f"\n❌ CRITICAL ISSUES:")
            for issue in assessment['critical_issues']:
                print(f"  - {issue}")
        
        return assessment

def main():
    """Execução principal"""
    try:
        assessor = WellArchitectedAssessment()
        assessment = assessor.run_assessment()
        
        # Determinar exit code baseado nos scores
        security_score = assessment.get('security', {}).get('score', 0)
        reliability_score = assessment.get('reliability', {}).get('score', 0)
        
        min_security = int(os.getenv('MIN_SECURITY_SCORE', '80'))
        min_reliability = int(os.getenv('MIN_RELIABILITY_SCORE', '80'))
        
        if security_score < min_security:
            print(f"❌ Security score {security_score} < {min_security} (FAILED)")
            return 1
        elif reliability_score < min_reliability:
            print(f"❌ Reliability score {reliability_score} < {min_reliability} (FAILED)")
            return 1
        else:
            print(f"✅ Security ({security_score}) and Reliability ({reliability_score}) scores PASSED")
            return 0
            
    except Exception as e:
        print(f"💥 Erro crítico: {e}")
        return 1

if __name__ == '__main__':
    exit(main())
