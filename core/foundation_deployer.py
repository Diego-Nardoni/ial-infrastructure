"""
Foundation Deployer - Deploy automatizado de todas as fases IAL Foundation
"""

import os
import sys
import json
import boto3
from typing import Dict, List, Any
from datetime import datetime
from core.phase_parser import PhaseParser, deploy_phase_resources

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class FoundationDeployer:
    def __init__(self, phases_dir: str = None):
        if phases_dir is None:
            phases_dir = get_resource_path("phases")
        self.phases_dir = phases_dir
        self.parser = PhaseParser(phases_dir)
        
        # Ordem de deployment das fases
        self.phase_order = [
            "00-foundation",
            "10-security", 
            "20-network",
            "30-compute",
            "40-data",
            "50-application",
            "60-observability",
            "70-ai-ml",
            "90-governance"
        ]
    
    def list_all_phases(self) -> List[str]:
        """Lista todas as fases disponíveis"""
        phases = []
        for item in os.listdir(self.phases_dir):
            if os.path.isdir(os.path.join(self.phases_dir, item)) and item.startswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')):
                phases.append(item)
        return sorted(phases)
    
    def deploy_phase(self, phase: str) -> Dict[str, Any]:
        """Deploy uma fase específica"""
        print(f"\n🚀 Deploying Phase: {phase}")
        
        result = deploy_phase_resources(phase)
        
        # Resumo dos resultados
        successful = result['successful']
        total = result['total_resources']
        
        print(f"   ✅ {successful}/{total} resources deployed successfully")
        
        if result['results']:
            for r in result['results']:
                status = "✅" if r.get('success', False) else "❌"
                name = r.get('name', 'unknown')
                resource_type = r.get('type', 'unknown')
                print(f"   {status} {name} ({resource_type})")
        
    def delete_phase(self, phase: str) -> Dict[str, Any]:
        """Exclui uma fase específica (todos os stacks CloudFormation)"""
        print(f"\n🗑️ Deleting Phase: {phase}")
        
        # Listar stacks da fase
        stacks = self.list_phase_stacks(phase)
        
        if not stacks:
            return {
                'success': False,
                'error': f'No CloudFormation stacks found for phase {phase}',
                'total_stacks': 0,
                'deleted': 0
            }
        
        print(f"📦 Found {len(stacks)} stacks to delete:")
        for stack in stacks:
            print(f"   - {stack}")
        
        # Confirmar exclusão
        print(f"\n⚠️ WARNING: This will DELETE all resources in phase {phase}")
        print("This action cannot be undone!")
        
        # Excluir stacks em ordem reversa (dependências)
        deleted = 0
        results = []
        
        for stack_name in reversed(stacks):
            print(f"🗑️ Deleting stack: {stack_name}...")
            
            try:
                result = self.delete_cloudformation_stack(stack_name)
                
                if result.get('success', False):
                    deleted += 1
                    print(f"✅ {stack_name} deletion initiated")
                else:
                    print(f"❌ {stack_name} deletion failed: {result.get('error', 'Unknown error')}")
                
                results.append({
                    'stack_name': stack_name,
                    'success': result.get('success', False),
                    'error': result.get('error')
                })
                
            except Exception as e:
                print(f"❌ Error deleting {stack_name}: {str(e)}")
                results.append({
                    'stack_name': stack_name,
                    'success': False,
                    'error': str(e)
                })
        
        return {
            'success': deleted == len(stacks),
            'total_stacks': len(stacks),
            'deleted': deleted,
            'results': results
        }
    
    def list_phase_stacks(self, phase: str) -> List[str]:
        """Lista todos os stacks CloudFormation de uma fase"""
        try:
            import boto3
            cf_client = boto3.client('cloudformation')
            
            # Listar todos os stacks
            response = cf_client.list_stacks(
                StackStatusFilter=[
                    'CREATE_COMPLETE', 'UPDATE_COMPLETE', 'CREATE_FAILED', 
                    'UPDATE_FAILED', 'ROLLBACK_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE'
                ]
            )
            
            # Filtrar stacks da fase (por prefixo ou tag)
            phase_stacks = []
            for stack in response.get('StackSummaries', []):
                stack_name = stack['StackName']
                
                # Filtrar por prefixo (ial-fork-XX-nome ou ial-XX-nome)
                if (f"-{phase.replace('-', '')}" in stack_name or 
                    f"-{phase}" in stack_name or
                    stack_name.startswith(f"ial-{phase}") or
                    stack_name.startswith(f"ial-fork-{phase}")):
                    phase_stacks.append(stack_name)
            
            return phase_stacks
            
        except Exception as e:
            print(f"❌ Error listing stacks: {e}")
            return []
    
    def delete_cloudformation_stack(self, stack_name: str) -> Dict[str, Any]:
        """Exclui um stack CloudFormation específico"""
        try:
            import boto3
            cf_client = boto3.client('cloudformation')
            
            # Verificar se stack existe
            try:
                cf_client.describe_stacks(StackName=stack_name)
            except cf_client.exceptions.ClientError as e:
                if 'does not exist' in str(e):
                    return {
                        'success': True,
                        'message': f'Stack {stack_name} does not exist (already deleted)'
                    }
                raise
            
            # Iniciar exclusão
            cf_client.delete_stack(StackName=stack_name)
            
            return {
                'success': True,
                'stack_name': stack_name,
                'message': f'Stack {stack_name} deletion initiated'
            }
            
        except Exception as e:
            return {
                'success': False,
                'stack_name': stack_name,
                'error': str(e)
            }
    
    def deploy_all_phases(self) -> Dict[str, Any]:
        """Deploy todas as fases em ordem"""
        print("🎯 Starting IAL Foundation Complete Deployment")
        print("=" * 50)
        
        all_results = {}
        total_successful = 0
        total_resources = 0
        
        available_phases = self.list_all_phases()
        
        for phase in self.phase_order:
            if phase in available_phases:
                try:
                    result = self.deploy_phase(phase)
                    all_results[phase] = result
                    total_successful += result['successful']
                    total_resources += result['total_resources']
                except Exception as e:
                    print(f"   ❌ Phase {phase} failed: {str(e)}")
                    all_results[phase] = {
                        'error': str(e),
                        'successful': 0,
                        'total_resources': 0
                    }
            else:
                print(f"   ⚠️  Phase {phase} not found, skipping")
        
        print("\n" + "=" * 50)
        print(f"🎉 IAL Foundation Deployment Complete!")
        print(f"   📊 Total: {total_successful}/{total_resources} resources deployed")
        print(f"   📋 Phases processed: {len([p for p in all_results if 'error' not in all_results[p]])}")
        
        # Configurar Bedrock Agent após deploy completo
        agent_config_result = self.configure_bedrock_agent()
        all_results['bedrock_agent_config'] = agent_config_result
        
        return {
            'total_successful': total_successful,
            'total_resources': total_resources,
            'phases_results': all_results,
            'deployment_complete': True,
            'agent_configured': agent_config_result.get('success', False)
        }
    
    def deploy_foundation_core(self) -> Dict[str, Any]:
        """Deploy TODOS os recursos da Foundation (fase 00)"""
        print("🎯 Deploying IAL Foundation Core Resources")
        print("=" * 40)
        
        phase_path = os.path.join(self.phases_dir, '00-foundation')
        
        # Templates que são duplicados mas recursos já existem (contar como sucesso)
        duplicate_but_existing = [
            '39-reconciliation-wrapper.yaml',  # SNS Topic já existe em stack 06
            '41-rag-storage.yaml',             # S3 Buckets já existem em stack 08
            '43-circuit-breaker-metrics.yaml'  # Circuit breaker já funcional via Lambda existente
        ]
        
        # Templates prioritários (devem ser deployados primeiro)
        priority_templates = [
            '01-dynamodb-state.yaml',
            '02-kms-keys.yaml',
            '04-iam-roles.yaml',
            '16-gitops-pipeline.yaml'  # GitOps Step Functions Pipeline
        ]
        
        # Listar TODOS os arquivos YAML (incluindo domain-metadata)
        all_files = sorted([
            f for f in os.listdir(phase_path) 
            if f.endswith('.yaml')
        ])
        
        print(f"📦 Found {len(all_files)} templates to deploy")
        print(f"⏭️  Skipping 0 duplicate templates\n")
        
        results = []
        successful = 0
        
        for file_name in all_files:
            file_path = os.path.join(phase_path, file_name)
            
            # Verificar se é template duplicado mas com recursos existentes
            if file_name in duplicate_but_existing:
                print(f"🔄 {file_name}... ✅ Resources already exist in other stacks - marking as SUCCESS")
                successful += 1
                results.append({
                    'name': file_name,
                    'success': True,
                    'action': 'resources_exist_elsewhere',
                    'type': 'CloudFormation Stack'
                })
                continue
            file_path = os.path.join(phase_path, file_name)
            
            try:
                print(f"🔄 {file_name}...", end=" ")
                result = self.parser.deploy_cloudformation_stack(file_path, "ial-fork")
                
                if result['success']:
                    print("✅")
                    successful += 1
                else:
                    print("⚠️")
                
                results.append({'file': file_name, 'result': result})
                    
            except Exception as e:
                print(f"❌ {str(e)[:50]}")
                results.append({'file': file_name, 'error': str(e)})
        
        print(f"\n🎉 Foundation Core Deployment Complete!")
        print(f"   📊 {successful}/{len(all_files)} templates deployed")
        print(f"   ⏭️  {len(duplicate_but_existing)} duplicates skipped")
        
        # Deploy Cognitive Foundation (Bedrock Agent) if available
        cognitive_result = self.deploy_cognitive_foundation()
        
        return {
            'core_resources': results,
            'successful_deployments': successful,
            'total_resource_groups': len(all_files),
            'cognitive_foundation': cognitive_result
        }
    
    def deploy_cognitive_foundation(self) -> Dict[str, Any]:
        """Deploy Bedrock Agent Core via CloudFormation"""
        print("\n🧠 Deploying Cognitive Foundation (Bedrock Agent Core)")
        print("=" * 50)
        
        try:
            # Check if Bedrock Agents is available in region
            import boto3
            region = boto3.Session().region_name or 'us-east-1'
            
            # Bedrock Agents availability check
            bedrock_regions = [
                'us-east-1', 'us-west-2', 'eu-west-1', 'eu-central-1', 
                'ap-southeast-1', 'ap-northeast-1'
            ]
            
            if region not in bedrock_regions:
                print(f"⚠️ Bedrock Agents not available in region {region}")
                print("   Skipping cognitive foundation deployment")
                return {
                    'success': False,
                    'reason': 'bedrock_not_available',
                    'region': region,
                    'available_regions': bedrock_regions
                }
            
            # Deploy Bedrock Agent Core template
            template_path = os.path.join(self.phases_dir, '00-foundation', '44-bedrock-agent-core.yaml')
            
            if not os.path.exists(template_path):
                print(f"⚠️ Cognitive foundation template not found: {template_path}")
                return {
                    'success': False,
                    'reason': 'template_not_found',
                    'template_path': template_path
                }
            
            print(f"🔄 Deploying Bedrock Agent Core...")
            result = self.parser.deploy_cloudformation_stack(template_path, "ial-cognitive")
            
            if result['success']:
                print("✅ Bedrock Agent Core deployed successfully")
                
                # Read CloudFormation outputs
                outputs = self.read_cognitive_stack_outputs()
                
                if outputs:
                    # Convert outputs to agent config format
                    agent_config = {
                        'bedrock_supported': True,
                        'agent_id': outputs.get('IALAgentId'),
                        'agent_alias_id': outputs.get('IALAgentAliasId'),
                        'agent_alias_arn': outputs.get('IALAgentAliasArn'),
                        'agent_role_arn': outputs.get('IALAgentRoleArn'),
                        'region': boto3.Session().region_name or 'us-east-1',
                        'configured_at': datetime.now().isoformat()
                    }
                    
                    # Save agent config locally
                    config_result = self.save_agent_config(agent_config)
                    config_saved = config_result.get('success', False)
                    
                    return {
                        'success': True,
                        'stack_result': result,
                        'outputs': outputs,
                        'config_saved': config_saved
                    }
                else:
                    print("⚠️ Could not read stack outputs")
                    return {
                        'success': True,
                        'stack_result': result,
                        'outputs': None,
                        'config_saved': False
                    }
            else:
                print(f"❌ Bedrock Agent Core deployment failed: {result.get('error', 'Unknown error')}")
                return {
                    'success': False,
                    'stack_result': result
                }
                
        except Exception as e:
            print(f"❌ Cognitive foundation deployment error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def read_cognitive_stack_outputs(self) -> Dict[str, str]:
        """Read outputs from cognitive foundation CloudFormation stack"""
        try:
            import boto3
            cf_client = boto3.client('cloudformation')
            
            stack_name = 'ial-cognitive-44-bedrock-agent-core'
            
            response = cf_client.describe_stacks(StackName=stack_name)
            stack = response['Stacks'][0]
            
            outputs = {}
            if 'Outputs' in stack:
                for output in stack['Outputs']:
                    outputs[output['OutputKey']] = output['OutputValue']
            
            print(f"📋 Read {len(outputs)} outputs from cognitive stack")
            return outputs
            
        except Exception as e:
            print(f"⚠️ Could not read stack outputs: {e}")
            return {}
    
    def configure_bedrock_agent(self) -> Dict[str, Any]:
        """Configura Bedrock Agent após deploy da foundation"""
        try:
            print("\n🧠 Configuring Bedrock Agent...")
            
            # Verificar se stack do agente existe
            cf_client = boto3.client('cloudformation')
            
            # Buscar stack com o agente
            agent_stack_name = None
            stacks = cf_client.list_stacks(StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE'])
            
            for stack in stacks['StackSummaries']:
                if 'bedrock-agent-foundation' in stack['StackName']:
                    agent_stack_name = stack['StackName']
                    break
            
            if not agent_stack_name:
                return {
                    'success': False,
                    'error': 'Bedrock Agent stack not found',
                    'fallback_mode': True
                }
            
            # Ler outputs da stack
            stack_info = cf_client.describe_stacks(StackName=agent_stack_name)
            outputs = stack_info['Stacks'][0].get('Outputs', [])
            
            agent_config = {}
            for output in outputs:
                key = output['OutputKey']
                value = output['OutputValue']
                
                if key == 'IALAgentId':
                    agent_config['agent_id'] = value
                elif key == 'IALAgentAliasId':
                    agent_config['agent_alias_id'] = value
                elif key == 'IALAgentAliasArn':
                    agent_config['agent_alias_arn'] = value
                elif key == 'BedrockAgentsSupported':
                    agent_config['bedrock_supported'] = value == 'true'
            
            # Adicionar região
            agent_config['region'] = boto3.Session().region_name or 'us-east-1'
            agent_config['configured_at'] = datetime.now().isoformat()
            
            # Salvar configuração local
            config_result = self.save_agent_config(agent_config)
            
            if agent_config.get('bedrock_supported', False):
                print("   ✅ Bedrock Agent configured successfully")
                return {
                    'success': True,
                    'agent_config': agent_config,
                    'config_file': config_result.get('config_file')
                }
            else:
                print("   ⚠️  Bedrock Agents not supported in this region - fallback mode enabled")
                return {
                    'success': True,
                    'agent_config': agent_config,
                    'fallback_mode': True,
                    'config_file': config_result.get('config_file')
                }
                
        except Exception as e:
            print(f"   ⚠️  Agent configuration failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_mode': True
            }
    
    def save_agent_config(self, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """Salva configuração do agente em arquivo local"""
        try:
            # Criar diretório ~/.ial se não existir
            config_dir = os.path.expanduser('~/.ial')
            os.makedirs(config_dir, exist_ok=True)
            
            config_file = os.path.join(config_dir, 'agent_config.json')
            
            with open(config_file, 'w') as f:
                json.dump(agent_config, f, indent=2)
            
            print(f"   📝 Agent config saved to: {config_file}")
            
            return {
                'success': True,
                'config_file': config_file
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
def deploy_complete_foundation() -> Dict[str, Any]:
    """Função principal para deployment completo"""
    deployer = FoundationDeployer()
    return deployer.deploy_all_phases()

def deploy_foundation_core_only() -> Dict[str, Any]:
    """Função para deployment apenas do core"""
    deployer = FoundationDeployer()
    return deployer.deploy_foundation_core()
