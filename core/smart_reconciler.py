#!/usr/bin/env python3
"""
Smart Reconciler - Reconciliação Inteligente com IA
Comparação automática, classificação de drift, e auto-remediation
"""

import json
import boto3
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import hashlib
import sys

# Add existing components
sys.path.append(str(Path(__file__).parent.parent / 'scripts'))
sys.path.append(str(Path(__file__).parent))

from resource_catalog import ResourceCatalog
from advanced_validator import AdvancedValidator

class SmartReconciler:
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.resource_catalog = ResourceCatalog(region=region)
        self.validator = AdvancedValidator()
        
        # Initialize Bedrock for AI analysis
        try:
            self.bedrock = boto3.client('bedrock-runtime', region_name=region)
            self.ai_available = True
        except Exception as e:
            self.ai_available = False
        
        # Drift classification rules
        self.drift_rules = {
            'critical': {
                'security_changes': ['AWS::IAM::Role', 'AWS::KMS::Key', 'AWS::EC2::SecurityGroup'],
                'data_changes': ['AWS::RDS::DBInstance', 'AWS::DynamoDB::Table', 'AWS::S3::Bucket'],
                'network_changes': ['AWS::EC2::VPC', 'AWS::EC2::Subnet']
            },
            'warning': {
                'configuration_changes': ['AWS::EC2::Instance', 'AWS::Lambda::Function'],
                'monitoring_changes': ['AWS::CloudWatch::Alarm', 'AWS::CloudWatch::Dashboard']
            },
            'info': {
                'metadata_changes': ['Tags', 'Description'],
                'non_functional_changes': ['AWS::CloudFormation::Stack']
            }
        }
    
    def analyze_drift_with_ai(self, desired_resource: Dict, actual_resource: Dict) -> Dict:
        """Analisa drift usando IA (Bedrock)"""
        if not self.ai_available:
            return self._fallback_drift_analysis(desired_resource, actual_resource)
        
        try:
            # Preparar prompt para análise
            prompt = self._build_drift_analysis_prompt(desired_resource, actual_resource)
            
            # Chamar Bedrock
            response = self.bedrock.invoke_model(
                modelId='anthropic.claude-3-haiku-20240307-v1:0',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 1000,
                    'messages': [
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ]
                })
            )
            
            # Processar resposta
            response_body = json.loads(response['body'].read())
            ai_analysis = response_body['content'][0]['text']
            
            # Parsear análise estruturada
            return self._parse_ai_analysis(ai_analysis, desired_resource, actual_resource)
            
        except Exception as e:
            print(f"⚠️ Erro na análise com IA: {e}")
            return self._fallback_drift_analysis(desired_resource, actual_resource)
    
    def _build_drift_analysis_prompt(self, desired: Dict, actual: Dict) -> str:
        """Constrói prompt para análise de drift"""
        return f"""
Analise as diferenças entre o estado desejado e atual de um recurso AWS.

RECURSO: {desired.get('name', 'Unknown')}
TIPO: {desired.get('type', 'Unknown')}

ESTADO DESEJADO:
{json.dumps(desired, indent=2)}

ESTADO ATUAL:
{json.dumps(actual, indent=2)}

Por favor, forneça uma análise estruturada no seguinte formato JSON:

{{
    "drift_detected": true/false,
    "severity": "critical/warning/info",
    "drift_type": "configuration/security/data/network/metadata",
    "changes": [
        {{
            "field": "nome_do_campo",
            "desired": "valor_desejado",
            "actual": "valor_atual",
            "impact": "descrição_do_impacto"
        }}
    ],
    "recommended_action": "deploy/update/review/ignore",
    "confidence": 0.0-1.0,
    "reasoning": "explicação_detalhada",
    "auto_remediable": true/false,
    "remediation_steps": ["passo1", "passo2"]
}}

Foque em:
1. Identificar mudanças significativas vs. mudanças cosméticas
2. Avaliar impacto de segurança e funcionalidade
3. Recomendar ações apropriadas
4. Determinar se pode ser corrigido automaticamente
"""
    
    def _parse_ai_analysis(self, ai_response: str, desired: Dict, actual: Dict) -> Dict:
        """Parseia resposta da IA em formato estruturado"""
        try:
            # Tentar extrair JSON da resposta
            import re
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            
            if json_match:
                analysis = json.loads(json_match.group())
                
                # Validar e enriquecer análise
                analysis['resource_id'] = desired.get('id', 'unknown')
                analysis['resource_type'] = desired.get('type', 'unknown')
                analysis['analyzed_at'] = datetime.utcnow().isoformat()
                analysis['analysis_method'] = 'ai_bedrock'
                
                return analysis
            else:
                # Fallback se não conseguir parsear JSON
                return self._create_basic_analysis(ai_response, desired, actual)
                
        except Exception as e:
            print(f"⚠️ Erro ao parsear análise da IA: {e}")
            return self._fallback_drift_analysis(desired, actual)
    
    def _create_basic_analysis(self, ai_text: str, desired: Dict, actual: Dict) -> Dict:
        """Cria análise básica a partir de texto da IA"""
        return {
            'resource_id': desired.get('id', 'unknown'),
            'resource_type': desired.get('type', 'unknown'),
            'drift_detected': True,
            'severity': 'warning',
            'drift_type': 'configuration',
            'recommended_action': 'review',
            'confidence': 0.5,
            'reasoning': ai_text,
            'auto_remediable': False,
            'analysis_method': 'ai_text_fallback',
            'analyzed_at': datetime.utcnow().isoformat()
        }
    
    def _fallback_drift_analysis(self, desired: Dict, actual: Dict) -> Dict:
        """Análise de drift sem IA (fallback)"""
        resource_type = desired.get('type', 'unknown')
        
        # Calcular hash dos metadados para comparação
        desired_hash = self._calculate_resource_hash(desired)
        actual_hash = self._calculate_resource_hash(actual)
        
        drift_detected = desired_hash != actual_hash
        
        # Classificar severidade baseada no tipo de recurso
        severity = 'info'
        if resource_type in self.drift_rules['critical']['security_changes']:
            severity = 'critical'
        elif resource_type in self.drift_rules['critical']['data_changes']:
            severity = 'critical'
        elif resource_type in self.drift_rules['warning']['configuration_changes']:
            severity = 'warning'
        
        return {
            'resource_id': desired.get('id', 'unknown'),
            'resource_type': resource_type,
            'drift_detected': drift_detected,
            'severity': severity,
            'drift_type': 'configuration',
            'recommended_action': 'update' if drift_detected else 'none',
            'confidence': 0.8,
            'reasoning': f"Comparação de hash: desired={desired_hash[:8]}, actual={actual_hash[:8]}",
            'auto_remediable': severity != 'critical',
            'analysis_method': 'hash_comparison',
            'analyzed_at': datetime.utcnow().isoformat()
        }
    
    def _calculate_resource_hash(self, resource: Dict) -> str:
        """Calcula hash de um recurso para comparação"""
        # Remover campos que mudam frequentemente
        filtered_resource = {k: v for k, v in resource.items() 
                           if k not in ['timestamp', 'updated_at', 'created_at', 'last_modified']}
        
        resource_str = json.dumps(filtered_resource, sort_keys=True)
        return hashlib.sha256(resource_str.encode()).hexdigest()
    
    def detect_all_drifts(self, desired_spec: Dict) -> List[Dict]:
        """Detecta todos os drifts comparando desired state com recursos deployados"""
        print("🔍 Detectando drifts...")
        
        drift_results = []
        
        # Recuperar recursos do catálogo
        desired_resources = {r['id']: r for r in desired_spec.get('resources', [])}
        deployed_resources = {r['resource_id']: r for r in self.resource_catalog.list_resources(status='deployed')}
        
        # Analisar recursos desejados vs deployados
        for resource_id, desired in desired_resources.items():
            deployed = deployed_resources.get(resource_id)
            
            if not deployed:
                # Recurso ausente
                drift_results.append({
                    'resource_id': resource_id,
                    'resource_type': desired.get('type'),
                    'drift_detected': True,
                    'severity': 'critical',
                    'drift_type': 'missing',
                    'recommended_action': 'deploy',
                    'confidence': 1.0,
                    'reasoning': 'Recurso definido no desired state mas não encontrado no ambiente',
                    'auto_remediable': True,
                    'analysis_method': 'missing_resource_check'
                })
            else:
                # Comparar configurações
                analysis = self.analyze_drift_with_ai(desired, deployed)
                if analysis.get('drift_detected'):
                    drift_results.append(analysis)
        
        # Detectar recursos órfãos
        orphaned_resources = set(deployed_resources.keys()) - set(desired_resources.keys())
        for resource_id in orphaned_resources:
            deployed = deployed_resources[resource_id]
            drift_results.append({
                'resource_id': resource_id,
                'resource_type': deployed.get('resource_type'),
                'drift_detected': True,
                'severity': 'warning',
                'drift_type': 'orphaned',
                'recommended_action': 'review',
                'confidence': 0.9,
                'reasoning': 'Recurso deployado mas não definido no desired state atual',
                'auto_remediable': False,
                'analysis_method': 'orphaned_resource_check'
            })
        
        print(f"📊 Detectados {len(drift_results)} drifts")
        return drift_results
    
    def classify_drifts_by_priority(self, drifts: List[Dict]) -> Dict[str, List[Dict]]:
        """Classifica drifts por prioridade"""
        classified = {
            'critical': [],
            'warning': [],
            'info': []
        }
        
        for drift in drifts:
            severity = drift.get('severity', 'info')
            classified[severity].append(drift)
        
        return classified
    
    def generate_remediation_plan(self, drifts: List[Dict]) -> Dict:
        """Gera plano de remediação para drifts"""
        plan = {
            'generated_at': datetime.utcnow().isoformat(),
            'total_drifts': len(drifts),
            'auto_remediable_count': len([d for d in drifts if d.get('auto_remediable', False)]),
            'phases': {
                'immediate': [],  # Critical, auto-remediable
                'scheduled': [],  # Warning, auto-remediable
                'manual': []      # Requires manual intervention
            },
            'estimated_duration': '0 minutes',
            'risk_assessment': 'low'
        }
        
        # Classificar drifts em fases
        for drift in drifts:
            severity = drift.get('severity', 'info')
            auto_remediable = drift.get('auto_remediable', False)
            
            remediation_item = {
                'resource_id': drift['resource_id'],
                'action': drift.get('recommended_action', 'review'),
                'reasoning': drift.get('reasoning', ''),
                'confidence': drift.get('confidence', 0.5),
                'steps': drift.get('remediation_steps', [])
            }
            
            if severity == 'critical' and auto_remediable:
                plan['phases']['immediate'].append(remediation_item)
            elif auto_remediable:
                plan['phases']['scheduled'].append(remediation_item)
            else:
                plan['phases']['manual'].append(remediation_item)
        
        # Calcular estimativas
        immediate_count = len(plan['phases']['immediate'])
        scheduled_count = len(plan['phases']['scheduled'])
        manual_count = len(plan['phases']['manual'])
        
        estimated_minutes = (immediate_count * 2) + (scheduled_count * 5) + (manual_count * 15)
        plan['estimated_duration'] = f"{estimated_minutes} minutes"
        
        # Avaliar risco
        if immediate_count > 5 or any(d.get('severity') == 'critical' for d in drifts):
            plan['risk_assessment'] = 'high'
        elif immediate_count > 0 or scheduled_count > 10:
            plan['risk_assessment'] = 'medium'
        else:
            plan['risk_assessment'] = 'low'
        
        return plan
    
    def execute_auto_remediation(self, remediation_plan: Dict, dry_run: bool = True) -> Dict:
        """Executa remediação automática (com dry-run por padrão)"""
        print(f"🔧 Executando remediação automática (dry_run={dry_run})...")
        
        execution_result = {
            'started_at': datetime.utcnow().isoformat(),
            'dry_run': dry_run,
            'phases_executed': {},
            'total_actions': 0,
            'successful_actions': 0,
            'failed_actions': 0,
            'errors': []
        }
        
        # Executar fase imediata
        immediate_actions = remediation_plan['phases']['immediate']
        if immediate_actions:
            print(f"⚡ Executando {len(immediate_actions)} ações imediatas...")
            
            phase_result = self._execute_remediation_phase(immediate_actions, dry_run)
            execution_result['phases_executed']['immediate'] = phase_result
            execution_result['total_actions'] += phase_result['total_actions']
            execution_result['successful_actions'] += phase_result['successful_actions']
            execution_result['failed_actions'] += phase_result['failed_actions']
            execution_result['errors'].extend(phase_result['errors'])
        
        # Executar fase agendada (apenas em dry_run ou com confirmação)
        scheduled_actions = remediation_plan['phases']['scheduled']
        if scheduled_actions and dry_run:
            print(f"📅 Simulando {len(scheduled_actions)} ações agendadas...")
            
            phase_result = self._execute_remediation_phase(scheduled_actions, True)
            execution_result['phases_executed']['scheduled'] = phase_result
            execution_result['total_actions'] += phase_result['total_actions']
        
        execution_result['completed_at'] = datetime.utcnow().isoformat()
        execution_result['success_rate'] = (
            execution_result['successful_actions'] / execution_result['total_actions'] * 100
            if execution_result['total_actions'] > 0 else 100
        )
        
        return execution_result
    
    def _execute_remediation_phase(self, actions: List[Dict], dry_run: bool) -> Dict:
        """Executa uma fase de remediação"""
        phase_result = {
            'total_actions': len(actions),
            'successful_actions': 0,
            'failed_actions': 0,
            'errors': [],
            'actions_executed': []
        }
        
        for action in actions:
            try:
                if dry_run:
                    # Simular execução
                    action_result = {
                        'resource_id': action['resource_id'],
                        'action': action['action'],
                        'status': 'simulated',
                        'message': f"Simulação: {action['action']} para {action['resource_id']}"
                    }
                    phase_result['successful_actions'] += 1
                else:
                    # Executar ação real
                    action_result = self._execute_single_action(action)
                    
                    if action_result['status'] == 'success':
                        phase_result['successful_actions'] += 1
                    else:
                        phase_result['failed_actions'] += 1
                        phase_result['errors'].append(action_result.get('error', 'Unknown error'))
                
                phase_result['actions_executed'].append(action_result)
                
            except Exception as e:
                error_msg = f"Erro ao executar ação para {action['resource_id']}: {e}"
                phase_result['errors'].append(error_msg)
                phase_result['failed_actions'] += 1
        
        return phase_result
    
    def _execute_single_action(self, action: Dict) -> Dict:
        """Executa uma ação individual de remediação"""
        resource_id = action['resource_id']
        action_type = action['action']
        
        try:
            if action_type == 'deploy':
                # Atualizar status no catálogo para 'pending_deployment'
                success = self.resource_catalog.update_resource_status(
                    resource_id, 'pending_deployment',
                    {'remediation_requested_at': datetime.utcnow().isoformat()}
                )
                
                return {
                    'resource_id': resource_id,
                    'action': action_type,
                    'status': 'success' if success else 'failed',
                    'message': 'Recurso marcado para deployment' if success else 'Falha ao marcar recurso'
                }
            
            elif action_type == 'update':
                # Atualizar status no catálogo para 'pending_update'
                success = self.resource_catalog.update_resource_status(
                    resource_id, 'pending_update',
                    {'remediation_requested_at': datetime.utcnow().isoformat()}
                )
                
                return {
                    'resource_id': resource_id,
                    'action': action_type,
                    'status': 'success' if success else 'failed',
                    'message': 'Recurso marcado para atualização' if success else 'Falha ao marcar recurso'
                }
            
            elif action_type == 'review':
                # Marcar para revisão manual
                success = self.resource_catalog.update_resource_status(
                    resource_id, 'needs_review',
                    {'remediation_requested_at': datetime.utcnow().isoformat()}
                )
                
                return {
                    'resource_id': resource_id,
                    'action': action_type,
                    'status': 'success' if success else 'failed',
                    'message': 'Recurso marcado para revisão' if success else 'Falha ao marcar recurso'
                }
            
            else:
                return {
                    'resource_id': resource_id,
                    'action': action_type,
                    'status': 'failed',
                    'error': f"Ação não suportada: {action_type}"
                }
                
        except Exception as e:
            return {
                'resource_id': resource_id,
                'action': action_type,
                'status': 'failed',
                'error': str(e)
            }
    
    def generate_reconciliation_report(self, drifts: List[Dict], remediation_plan: Dict, 
                                     execution_result: Optional[Dict] = None) -> Dict:
        """Gera relatório completo de reconciliação"""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'report_version': '3.1',
            'summary': {
                'total_drifts': len(drifts),
                'critical_drifts': len([d for d in drifts if d.get('severity') == 'critical']),
                'warning_drifts': len([d for d in drifts if d.get('severity') == 'warning']),
                'info_drifts': len([d for d in drifts if d.get('severity') == 'info']),
                'auto_remediable': len([d for d in drifts if d.get('auto_remediable', False)])
            },
            'drift_analysis': drifts,
            'remediation_plan': remediation_plan,
            'execution_result': execution_result,
            'recommendations': self._generate_recommendations(drifts)
        }
        
        return report
    
    def _generate_recommendations(self, drifts: List[Dict]) -> List[str]:
        """Gera recomendações baseadas nos drifts encontrados"""
        recommendations = []
        
        critical_count = len([d for d in drifts if d.get('severity') == 'critical'])
        missing_count = len([d for d in drifts if d.get('drift_type') == 'missing'])
        orphaned_count = len([d for d in drifts if d.get('drift_type') == 'orphaned'])
        
        if critical_count > 0:
            recommendations.append(f"🚨 {critical_count} drift(s) crítico(s) detectado(s). Ação imediata requerida.")
        
        if missing_count > 0:
            recommendations.append(f"📦 {missing_count} recurso(s) ausente(s). Execute deployment para criar recursos.")
        
        if orphaned_count > 0:
            recommendations.append(f"🔍 {orphaned_count} recurso(s) órfão(s). Revise se devem ser mantidos ou removidos.")
        
        if len(drifts) == 0:
            recommendations.append("✅ Nenhum drift detectado. Sistema está em conformidade com o desired state.")
        
        return recommendations

def main():
    """Função principal para testes"""
    print("🔄 IAL Smart Reconciler v3.1")
    print("=" * 50)
    
    reconciler = SmartReconciler()
    
    # Teste básico com spec de exemplo
    test_spec = {
        'metadata': {'version': '3.1'},
        'resources': [
            {
                'id': 'test/vpc-123',
                'name': 'TestVPC',
                'type': 'AWS::EC2::VPC',
                'properties': {'CidrBlock': '10.0.0.0/16'}
            }
        ]
    }
    
    # Detectar drifts
    drifts = reconciler.detect_all_drifts(test_spec)
    print(f"📊 Drifts detectados: {len(drifts)}")
    
    if drifts:
        # Gerar plano de remediação
        plan = reconciler.generate_remediation_plan(drifts)
        print(f"🔧 Plano de remediação gerado:")
        print(f"  ⚡ Ações imediatas: {len(plan['phases']['immediate'])}")
        print(f"  📅 Ações agendadas: {len(plan['phases']['scheduled'])}")
        print(f"  👤 Ações manuais: {len(plan['phases']['manual'])}")
        
        # Executar remediação (dry-run)
        execution = reconciler.execute_auto_remediation(plan, dry_run=True)
        print(f"🎯 Execução simulada: {execution['success_rate']:.1f}% sucesso")
    
    return 0

if __name__ == "__main__":
    exit(main())
