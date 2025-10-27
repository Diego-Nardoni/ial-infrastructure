#!/usr/bin/env python3
"""Reconcile Engine - JSON Explicável com PR Comments"""

import boto3
import json
import yaml
import os
import requests
from pathlib import Path
from typing import Dict, List
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent

# AWS clients
dynamodb = boto3.client('dynamodb')
bedrock = boto3.client('bedrock-runtime')

class ReconcileEngine:
    def __init__(self):
        self.reconcile_results = []
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.github_repo = os.getenv('GITHUB_REPOSITORY', 'default/repo')
        self.pr_number = os.getenv('PR_NUMBER')
        
    def get_aws_state(self, resource_name: str, resource_type: str) -> Dict:
        """Obtém estado atual do recurso na AWS"""
        try:
            # Usar Cloud Control API quando possível
            cloudcontrol = boto3.client('cloudcontrol')
            
            response = cloudcontrol.get_resource(
                TypeName=resource_type,
                Identifier=resource_name
            )
            
            return json.loads(response.get('ResourceDescription', {}).get('Properties', '{}'))
            
        except Exception:
            # Fallback para APIs específicas
            return self._fallback_get_state(resource_name, resource_type)
    
    def _fallback_get_state(self, resource_name: str, resource_type: str) -> Dict:
        """Fallback para recursos não suportados pelo Cloud Control"""
        fallback_map = {
            'AWS::S3::Bucket': lambda name: self._get_s3_state(name),
            'AWS::DynamoDB::Table': lambda name: self._get_dynamodb_state(name),
            'AWS::IAM::Role': lambda name: self._get_iam_role_state(name)
        }
        
        if resource_type in fallback_map:
            try:
                return fallback_map[resource_type](resource_name)
            except:
                return {}
        
        return {}
    
    def _get_s3_state(self, bucket_name: str) -> Dict:
        """Estado do S3 bucket"""
        s3 = boto3.client('s3')
        try:
            # Verificar se existe
            s3.head_bucket(Bucket=bucket_name)
            
            # Obter configurações básicas
            encryption = {}
            try:
                enc_response = s3.get_bucket_encryption(Bucket=bucket_name)
                encryption = enc_response.get('ServerSideEncryptionConfiguration', {})
            except:
                pass
            
            return {
                'BucketName': bucket_name,
                'Encryption': encryption,
                'exists': True
            }
        except:
            return {'exists': False}
    
    def _get_dynamodb_state(self, table_name: str) -> Dict:
        """Estado da tabela DynamoDB"""
        dynamodb_client = boto3.client('dynamodb')
        try:
            response = dynamodb_client.describe_table(TableName=table_name)
            table = response.get('Table', {})
            
            return {
                'TableName': table_name,
                'TableStatus': table.get('TableStatus'),
                'BillingMode': table.get('BillingModeSummary', {}).get('BillingMode'),
                'exists': True
            }
        except:
            return {'exists': False}
    
    def _get_iam_role_state(self, role_name: str) -> Dict:
        """Estado do IAM role"""
        iam = boto3.client('iam')
        try:
            response = iam.get_role(RoleName=role_name)
            role = response.get('Role', {})
            
            return {
                'RoleName': role_name,
                'Arn': role.get('Arn'),
                'AssumeRolePolicyDocument': role.get('AssumeRolePolicyDocument'),
                'exists': True
            }
        except:
            return {'exists': False}
    
    def analyze_drift_with_ai(self, resource_name: str, desired: Dict, current: Dict) -> Dict:
        """Usa Bedrock para analisar drift e gerar reasoning"""
        
        prompt = f"""Analise o drift entre estado desejado e atual do recurso AWS:

RECURSO: {resource_name}

ESTADO DESEJADO:
{json.dumps(desired, indent=2)}

ESTADO ATUAL:
{json.dumps(current, indent=2)}

Determine:
1. action: "create", "update", "delete", "no_change"
2. confidence: 0.0-1.0 (confiança na análise)
3. reasoning: explicação clara das diferenças
4. changes: lista específica de mudanças necessárias
5. risk_level: "low", "medium", "high"

Retorne JSON:
{{
  "action": "update",
  "confidence": 0.95,
  "reasoning": "Explicação detalhada...",
  "changes": ["mudança1", "mudança2"],
  "risk_level": "medium"
}}"""

        try:
            response = bedrock.invoke_model(
                modelId='anthropic.claude-3-haiku-20240307-v1:0',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 1000,
                    'messages': [{'role': 'user', 'content': prompt}]
                })
            )
            
            result = json.loads(response['body'].read())
            content = result['content'][0]['text']
            
            # Extrair JSON da resposta
            start = content.find('{')
            end = content.rfind('}') + 1
            analysis_json = content[start:end]
            
            return json.loads(analysis_json)
            
        except Exception as e:
            # Fallback para análise simples
            return self._simple_drift_analysis(desired, current)
    
    def _simple_drift_analysis(self, desired: Dict, current: Dict) -> Dict:
        """Análise simples de drift como fallback"""
        if not current.get('exists', False):
            return {
                'action': 'create',
                'confidence': 1.0,
                'reasoning': 'Recurso não existe na AWS',
                'changes': ['Criar recurso'],
                'risk_level': 'low'
            }
        
        if desired == current:
            return {
                'action': 'no_change',
                'confidence': 1.0,
                'reasoning': 'Estados são idênticos',
                'changes': [],
                'risk_level': 'low'
            }
        
        return {
            'action': 'update',
            'confidence': 0.8,
            'reasoning': 'Diferenças detectadas entre estados',
            'changes': ['Atualizar configuração'],
            'risk_level': 'medium'
        }
    
    def reconcile_resources(self) -> List[Dict]:
        """Executa reconciliação de todos os recursos"""
        
        print("🔄 Iniciando reconciliação...")
        
        # Obter recursos do DynamoDB
        try:
            response = dynamodb.query(
                TableName='mcp-provisioning-checklist',
                KeyConditionExpression='#proj = :p',
                ExpressionAttributeNames={'#proj': 'Project'},
                ExpressionAttributeValues={':p': {'S': 'mcp-spring-boot'}}
            )
        except Exception as e:
            print(f"⚠️ Erro acessando DynamoDB: {e}")
            return []
        
        results = []
        
        for item in response.get('Items', []):
            resource_name = item['ResourceName']['S']
            
            if resource_name == 'DEPLOYMENT_LOCK':
                continue
            
            # Obter estados
            desired_state = json.loads(item.get('DesiredState', {}).get('S', '{}'))
            resource_type = item.get('ResourceType', {}).get('S', 'Unknown')
            
            current_state = self.get_aws_state(resource_name, resource_type)
            
            # Analisar com IA
            analysis = self.analyze_drift_with_ai(resource_name, desired_state, current_state)
            
            # Construir resultado padronizado
            result = {
                'resource_name': resource_name,
                'resource_type': resource_type,
                'timestamp': datetime.utcnow().isoformat(),
                'action': analysis['action'],
                'reasoning': analysis['reasoning'],
                'confidence': analysis['confidence'],
                'changes': analysis['changes'],
                'risk_level': analysis['risk_level'],
                'desired_state': desired_state,
                'current_state': current_state,
                'drift_detected': analysis['action'] != 'no_change'
            }
            
            results.append(result)
            
            # Log no console
            status_emoji = {
                'no_change': '✅',
                'create': '🆕',
                'update': '🔄',
                'delete': '🗑️'
            }
            
            emoji = status_emoji.get(analysis['action'], '❓')
            print(f"{emoji} {resource_name}: {analysis['reasoning']}")
        
        return results
    
    def generate_json_report(self, results: List[Dict]) -> str:
        """Gera relatório JSON padronizado"""
        
        summary = {
            'total_resources': len(results),
            'no_change': len([r for r in results if r['action'] == 'no_change']),
            'create': len([r for r in results if r['action'] == 'create']),
            'update': len([r for r in results if r['action'] == 'update']),
            'delete': len([r for r in results if r['action'] == 'delete']),
            'drift_detected': len([r for r in results if r['drift_detected']]),
            'high_risk': len([r for r in results if r['risk_level'] == 'high'])
        }
        
        report = {
            'reconcile_report': {
                'timestamp': datetime.utcnow().isoformat(),
                'summary': summary,
                'resources': results
            }
        }
        
        # Salvar arquivo
        report_file = PROJECT_ROOT / 'reports' / 'reconcile_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📄 Relatório salvo: {report_file}")
        
        return json.dumps(report, indent=2, default=str)
    
    def post_pr_comment(self, json_report: str) -> bool:
        """Posta comentário sticky no PR com o JSON"""
        
        if not all([self.github_token, self.pr_number]):
            print("⚠️ GitHub token ou PR number não configurados")
            return False
        
        # Formatar comentário
        comment_body = f"""## 🔄 Reconcile Report

<details>
<summary>📊 Resumo da Reconciliação</summary>

```json
{json_report}
```

</details>

**Gerado automaticamente pelo IAL Reconcile Engine**
*Timestamp: {datetime.utcnow().isoformat()}*
"""
        
        # API do GitHub
        url = f"https://api.github.com/repos/{self.github_repo}/issues/{self.pr_number}/comments"
        
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        data = {'body': comment_body}
        
        try:
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 201:
                print("✅ Comentário postado no PR")
                return True
            else:
                print(f"❌ Erro postando comentário: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erro na API do GitHub: {e}")
            return False

def main():
    """Execução principal"""
    try:
        engine = ReconcileEngine()
        
        # Executar reconciliação
        results = engine.reconcile_resources()
        
        # Gerar relatório JSON
        json_report = engine.generate_json_report(results)
        
        # Postar no PR se configurado
        if os.getenv('GITHUB_ACTIONS'):
            engine.post_pr_comment(json_report)
        
        # Determinar exit code
        drift_count = len([r for r in results if r['drift_detected']])
        high_risk_count = len([r for r in results if r['risk_level'] == 'high'])
        
        if high_risk_count > 0:
            print(f"⚠️ {high_risk_count} recursos de alto risco detectados")
            return 1
        elif drift_count > 0:
            print(f"🔄 {drift_count} recursos com drift detectado")
            return 0
        else:
            print("✅ Todos os recursos em conformidade")
            return 0
            
    except Exception as e:
        print(f"💥 Erro crítico: {e}")
        return 1

if __name__ == '__main__':
    exit(main())
