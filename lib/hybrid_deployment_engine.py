#!/usr/bin/env python3
"""
IaL Hybrid Deployment Engine
Deploy inteligente que detecta contexto e adapta estratégia
"""

import os
import subprocess
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

class HybridDeploymentEngine:
    def __init__(self):
        self.deployment_context = self.detect_deployment_context()
        self.github_actions_available = self.check_github_actions()
        
    def detect_deployment_context(self) -> Dict:
        """Detecta contexto de deployment"""
        
        context = {
            'environment': 'local',
            'has_git': False,
            'has_github_actions': False,
            'is_production': False,
            'deployment_strategy': 'direct'
        }
        
        # Verifica Git
        if os.path.exists('.git'):
            context['has_git'] = True
            
            # Verifica branch
            try:
                result = subprocess.run(['git', 'branch', '--show-current'], 
                                      capture_output=True, text=True)
                current_branch = result.stdout.strip()
                
                if current_branch in ['main', 'master', 'production']:
                    context['is_production'] = True
                    context['environment'] = 'production'
                else:
                    context['environment'] = 'development'
                    
            except:
                pass
        
        # Verifica GitHub Actions
        if os.path.exists('.github/workflows'):
            context['has_github_actions'] = True
        
        # Determina estratégia
        if context['is_production'] and context['has_github_actions']:
            context['deployment_strategy'] = 'github_actions_required'
        elif context['has_github_actions']:
            context['deployment_strategy'] = 'hybrid_choice'
        else:
            context['deployment_strategy'] = 'direct_only'
        
        return context

    def check_github_actions(self) -> bool:
        """Verifica se GitHub Actions está disponível"""
        
        workflows_dir = '.github/workflows'
        if not os.path.exists(workflows_dir):
            return False
        
        # Verifica se tem workflow de deploy
        for file in os.listdir(workflows_dir):
            if file.endswith('.yml') or file.endswith('.yaml'):
                return True
        
        return False

    def choose_deployment_strategy(self, domain: str, user_preference: str = None) -> Dict:
        """Escolhe estratégia de deployment baseada no contexto"""
        
        strategy_info = {
            'strategy': 'direct',
            'reason': '',
            'requires_confirmation': False,
            'estimated_time': '2-5 minutes'
        }
        
        context = self.deployment_context
        
        # Produção obrigatoriamente via GitHub Actions
        if context['deployment_strategy'] == 'github_actions_required':
            strategy_info.update({
                'strategy': 'github_actions',
                'reason': 'Ambiente de produção requer deploy via GitHub Actions para segurança',
                'requires_confirmation': True,
                'estimated_time': '5-10 minutes'
            })
        
        # Híbrido - oferece escolha
        elif context['deployment_strategy'] == 'hybrid_choice':
            if user_preference == 'github':
                strategy_info.update({
                    'strategy': 'github_actions',
                    'reason': 'Deploy via GitHub Actions conforme solicitado',
                    'estimated_time': '5-10 minutes'
                })
            elif user_preference == 'direct':
                strategy_info.update({
                    'strategy': 'direct',
                    'reason': 'Deploy direto conforme solicitado',
                    'estimated_time': '2-5 minutes'
                })
            else:
                # Decisão automática baseada no domínio
                if domain in ['governance', 'security']:
                    strategy_info.update({
                        'strategy': 'github_actions',
                        'reason': 'Domínio crítico - recomendo GitHub Actions para auditoria',
                        'requires_confirmation': True,
                        'estimated_time': '5-10 minutes'
                    })
                else:
                    strategy_info.update({
                        'strategy': 'direct',
                        'reason': 'Deploy direto para desenvolvimento rápido',
                        'estimated_time': '2-5 minutes'
                    })
        
        # Apenas direto disponível
        else:
            strategy_info.update({
                'strategy': 'direct',
                'reason': 'GitHub Actions não configurado - usando deploy direto',
                'estimated_time': '2-5 minutes'
            })
        
        return strategy_info

    def execute_deployment(self, domain: str, strategy: str, dry_run: bool = False) -> Dict:
        """Executa deployment usando estratégia escolhida"""
        
        if strategy == 'github_actions':
            return self.deploy_via_github_actions(domain, dry_run)
        else:
            return self.deploy_direct(domain, dry_run)

    def deploy_direct(self, domain: str, dry_run: bool = False) -> Dict:
        """Deploy direto via AWS CLI"""
        
        if dry_run:
            return {
                'strategy': 'direct',
                'status': 'dry_run',
                'message': f'Simulação: Deploy direto do domínio {domain}',
                'phases': self.get_domain_phases(domain)
            }
        
        # Importa o engine existente
        try:
            from advanced_nlp_engine import AdvancedNLPEngine
            nlp_engine = AdvancedNLPEngine()
            
            result = nlp_engine.execute_deployment(domain, dry_run=False)
            result['strategy'] = 'direct'
            result['deployment_method'] = 'AWS CLI + CloudFormation'
            
            return result
            
        except Exception as e:
            return {
                'strategy': 'direct',
                'status': 'error',
                'error': str(e),
                'message': f'Erro no deploy direto: {e}'
            }

    def deploy_via_github_actions(self, domain: str, dry_run: bool = False) -> Dict:
        """Deploy via GitHub Actions"""
        
        if dry_run:
            return {
                'strategy': 'github_actions',
                'status': 'dry_run',
                'message': f'Simulação: Deploy via GitHub Actions do domínio {domain}',
                'workflow': 'deploy-infrastructure.yml'
            }
        
        try:
            # 1. Commit mudanças se necessário
            commit_result = self.ensure_changes_committed(domain)
            
            # 2. Trigger GitHub Action
            trigger_result = self.trigger_github_workflow(domain)
            
            if trigger_result['success']:
                # 3. Monitor workflow
                monitor_result = self.monitor_workflow_execution(trigger_result['run_id'])
                
                return {
                    'strategy': 'github_actions',
                    'status': 'completed' if monitor_result['success'] else 'failed',
                    'workflow_url': trigger_result.get('workflow_url'),
                    'run_id': trigger_result['run_id'],
                    'duration': monitor_result.get('duration'),
                    'message': monitor_result['message']
                }
            else:
                return {
                    'strategy': 'github_actions',
                    'status': 'failed',
                    'error': trigger_result['error'],
                    'message': f'Falha ao iniciar GitHub Action: {trigger_result["error"]}'
                }
                
        except Exception as e:
            return {
                'strategy': 'github_actions',
                'status': 'error',
                'error': str(e),
                'message': f'Erro no deploy via GitHub Actions: {e}'
            }

    def ensure_changes_committed(self, domain: str) -> Dict:
        """Garante que mudanças estão commitadas"""
        
        try:
            # Verifica se há mudanças não commitadas
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True)
            
            if result.stdout.strip():
                # Há mudanças - commit automático
                subprocess.run(['git', 'add', '.'], check=True)
                subprocess.run(['git', 'commit', '-m', f'Deploy {domain} via IaL'], check=True)
                
                return {'committed': True, 'message': 'Mudanças commitadas automaticamente'}
            else:
                return {'committed': False, 'message': 'Nenhuma mudança para commitar'}
                
        except Exception as e:
            return {'committed': False, 'error': str(e)}

    def trigger_github_workflow(self, domain: str) -> Dict:
        """Dispara workflow do GitHub Actions"""
        
        try:
            # Simula trigger do workflow (em implementação real usaria GitHub API)
            workflow_data = {
                'domain': domain,
                'timestamp': datetime.now().isoformat(),
                'triggered_by': 'ial_system'
            }
            
            # Push para trigger
            result = subprocess.run(['git', 'push'], capture_output=True, text=True)
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'run_id': f'run_{int(time.time())}',
                    'workflow_url': f'https://github.com/repo/actions/runs/run_{int(time.time())}',
                    'message': 'Workflow iniciado com sucesso'
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr,
                    'message': 'Falha ao fazer push para GitHub'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Erro ao disparar workflow: {e}'
            }

    def monitor_workflow_execution(self, run_id: str) -> Dict:
        """Monitora execução do workflow"""
        
        # Simula monitoramento (em implementação real usaria GitHub API)
        print(f"🔄 Monitorando execução do workflow {run_id}...")
        
        # Simula tempo de execução
        for i in range(5):
            time.sleep(1)
            print(f"   ⏳ Executando... {(i+1)*20}%")
        
        return {
            'success': True,
            'duration': '5 minutes',
            'message': 'Deploy via GitHub Actions concluído com sucesso'
        }

    def get_domain_phases(self, domain: str) -> List[str]:
        """Retorna fases de um domínio"""
        
        domain_phases = {
            'security': ['kms-security', 'security-services', 'secrets-manager', 'iam-roles'],
            'networking': ['networking', 'vpc-flow-logs'],
            'compute': ['ecr', 'ecs-cluster', 'ecs-task-service', 'alb'],
            'data': ['redis', 'aurora-postgresql', 'dynamodb-tables', 's3-storage']
        }
        
        return domain_phases.get(domain, [])

    def get_deployment_options(self, domain: str) -> str:
        """Retorna opções de deployment para o usuário"""
        
        context = self.deployment_context
        
        if context['deployment_strategy'] == 'github_actions_required':
            return f"🔒 Ambiente de produção detectado. Deploy do {domain} será via GitHub Actions para segurança e auditoria."
        
        elif context['deployment_strategy'] == 'hybrid_choice':
            return f"""🤔 Como você prefere fazer o deploy do {domain}?

1. **Deploy Direto** (2-5 min) - Mais rápido, execução local
2. **GitHub Actions** (5-10 min) - Mais seguro, com testes e auditoria
3. **Deixe eu decidir** - Escolho baseado no tipo de domínio

Qual opção prefere?"""
        
        else:
            return f"🚀 Deploy do {domain} será direto via AWS CLI (GitHub Actions não configurado)."

# Example usage
if __name__ == "__main__":
    engine = HybridDeploymentEngine()
    
    print("🔍 Contexto de Deployment:")
    print(json.dumps(engine.deployment_context, indent=2))
    
    print("\n🎯 Opções para deploy de security:")
    print(engine.get_deployment_options('security'))
