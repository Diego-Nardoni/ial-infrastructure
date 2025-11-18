"""
Phase Parser - Deploy automatizado de templates CloudFormation
"""

import os
import sys
import boto3
import time
import yaml
import tempfile
import re
from typing import Dict, List, Any, Optional

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class PhaseParser:
    def __init__(self, phases_dir: str = None):
        if phases_dir is None:
            phases_dir = get_resource_path("phases")
        self.phases_dir = phases_dir
        self.session = boto3.Session()
        self.cf_client = self.session.client('cloudformation')

    def _create_or_update_stack_idempotent(self, stack_name, template_body, parameters, project_name):
        """Create stack if not exists, skip if exists and complete"""
        stack_id = None
        try:
            response = self.cf_client.describe_stacks(StackName=stack_name)
            stack_status = response["Stacks"][0]["StackStatus"]
            stack_id = response["Stacks"][0]["StackId"]
            
            if stack_status in ["CREATE_COMPLETE", "UPDATE_COMPLETE"]:
                return {"success": True, "action": "skipped", "stack_name": stack_name}
            
            elif stack_status in ["ROLLBACK_COMPLETE", "CREATE_FAILED", "UPDATE_ROLLBACK_COMPLETE", "ROLLBACK_FAILED", "DELETE_FAILED"]:
                print(f"🔄 Stack {stack_name} in failed state ({stack_status}), creating with unique name...")
                
                # Para DELETE_FAILED, criar com nome único
                if stack_status == "DELETE_FAILED":
                    timestamp = int(time.time())
                    new_stack_name = f"{stack_name}-fixed-{timestamp}"
                    print(f"📦 Creating new stack: {new_stack_name}")
                    return {"success": True, "action": "create_new", "stack_name": new_stack_name}
                
                # Cleanup órfãos primeiro
                self._cleanup_orphaned_stacks(stack_name)
                
                # Deletar stack atual
                self.cf_client.delete_stack(StackName=stack_name)
                waiter = self.cf_client.get_waiter("stack_delete_complete")
                try:
                    waiter.wait(StackName=stack_id, WaiterConfig={"Delay": 10, "MaxAttempts": 30})
                except Exception as e:
                    print(f"⚠️ Delete waiter failed: {e}, continuing...")
                
            else:
                return {"success": False, "action": "failed", "error": f"Stack in {stack_status} state"}
        except self.cf_client.exceptions.ClientError as e:
            if "does not exist" in str(e):
                print(f"📦 Creating new stack: {stack_name}")
            else:
                return {"success": False, "action": "failed", "error": str(e)}
        
        # Cleanup órfãos antes de criar
        self._cleanup_orphaned_stacks(stack_name)
        
        create_args = {
            "StackName": stack_name,
            "TemplateBody": template_body,
            "Capabilities": ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"],
            "Tags": [
                {"Key": "Project", "Value": project_name},
                {"Key": "Component", "Value": "IAL-Foundation"},
                {"Key": "DeployedBy", "Value": "IAL-MCP-System"},
                {"Key": "Idempotent", "Value": "true"}
            ]
        }
        if parameters:
            create_args["Parameters"] = parameters
        try:
            response = self.cf_client.create_stack(**create_args)
            return {"success": True, "action": "created", "stack_id": response["StackId"], "stack_name": stack_name}
        except Exception as e:
            return {"success": False, "action": "failed", "error": str(e)}

    def _cleanup_orphaned_stacks(self, base_stack_name):
        """Remove stacks órfãos com timestamps"""
        try:
            stacks = self.cf_client.list_stacks()
            orphaned = [s for s in stacks['StackSummaries'] 
                       if s['StackName'].startswith(f"{base_stack_name}-v") 
                       and s['StackStatus'] in ['ROLLBACK_COMPLETE', 'CREATE_FAILED', 'DELETE_FAILED']]
            
            for stack in orphaned:
                print(f"🧹 Removing orphaned stack: {stack['StackName']}")
                try:
                    self.cf_client.delete_stack(StackName=stack['StackName'])
                except:
                    pass  # Ignore errors during cleanup
        except:
            pass  # Ignore cleanup errors
    
    def list_phase_files(self, phase: str = "00-foundation") -> List[str]:
        """Lista arquivos YAML de uma fase"""
        phase_path = os.path.join(self.phases_dir, phase)
        if not os.path.exists(phase_path):
            return []
        
        yaml_files = []
        for file in os.listdir(phase_path):
            if file.endswith('.yaml'):
                yaml_files.append(os.path.join(phase_path, file))
        
        return sorted(yaml_files)
    
    def deploy_cloudformation_stack(self, file_path: str, project_name: str = "ial-fork") -> Dict[str, Any]:
        """Deploy real via CloudFormation com idempotência"""
        try:
            file_name = os.path.basename(file_path).replace('.yaml', '')
            stack_name = f"{project_name}-{file_name}"
            
            # Ler template
            with open(file_path, 'r') as f:
                template_body = f.read()
            
            # Verificar se template tem parâmetros
            import yaml
            try:
                template_dict = yaml.safe_load(template_body)
                has_parameters = 'Parameters' in template_dict and template_dict['Parameters']
            except:
                has_parameters = False
            
            # Parâmetros padrão apenas se template os requer
            parameters = []
            if has_parameters:
                parameters = [
                    {'ParameterKey': 'ProjectName', 'ParameterValue': project_name},
                    {"ParameterKey": "Environment", "ParameterValue": "prod"}
                ]
            
            # Usar deployment idempotente
            deployment_result = self._create_or_update_stack_idempotent(
                stack_name, template_body, parameters, project_name
            )
            
            # Usar nome do stack retornado pela função idempotente
            actual_stack_name = deployment_result.get('stack_name', stack_name)
            
            if deployment_result.get('action') == 'create_new':
                # Usar novo nome para DELETE_FAILED
                stack_name = actual_stack_name
            
            if deployment_result['action'] == 'skipped':
                print(f"✅ Stack {stack_name} already exists and is complete")
                return {'success': True, 'stack_name': stack_name, 'action': 'skipped'}
            elif deployment_result['action'] == 'failed':
                print(f"❌ Stack {stack_name} deployment failed: {deployment_result.get('error', 'Unknown error')}")
                return {'success': False, 'error': deployment_result.get('error', 'Deployment failed')}
            
            response = {'StackId': deployment_result.get('stack_id', stack_name)}
            
            stack_id = response['StackId']
            
            # Aguardar criação (timeout 5 minutos)
            print(f"⏳ Aguardando criação do stack {actual_stack_name}...")
            
            waiter = self.cf_client.get_waiter('stack_create_complete')
            try:
                waiter.wait(
                    StackName=deployment_result.get("stack_id", actual_stack_name),
                    WaiterConfig={'Delay': 10, 'MaxAttempts': 30}
                )
                
                # Verificar status final
                stack_info = self.cf_client.describe_stacks(StackName=actual_stack_name)
                stack_status = stack_info['Stacks'][0]['StackStatus']
                
                if stack_status == 'CREATE_COMPLETE':
                    print(f"✅ Stack {actual_stack_name} criado com sucesso")
                    return {
                        'success': True,
                        'stack_name': actual_stack_name,
                        'file_path': file_path,
                        'action': 'created',
                        'idempotent': True
                    }
                else:
                    return {
                        'success': False,
                        'stack_name': actual_stack_name,
                        'error': f'Stack creation failed with status: {stack_status}',
                        'file_path': file_path,
                        'idempotent': True
                    }
                    
            except Exception as wait_error:
                return {
                    'success': False,
                    'stack_name': actual_stack_name,
                    'error': f'Timeout waiting for stack creation: {wait_error}',
                    'file_path': file_path,
                    'idempotent': True
                }
        except Exception as e:
            return {
                'success': False,
                'stack_name': stack_name,
                'error': str(e),
                'file_path': file_path,
                'idempotent': True
            }
                
    def is_ial_metadata(self, file_path: str) -> bool:
        """Detecta se arquivo é metadado IAL ou CloudFormation direto"""
        try:
            with open(file_path, 'r') as f:
                content = yaml.safe_load(f)
            
            # Se tem 'resources' com 'mcp_workflow', é metadado IAL
            if isinstance(content, dict) and 'resources' in content:
                resources = content['resources']
                if isinstance(resources, dict):
                    for resource in resources.values():
                        if isinstance(resource, dict) and 'mcp_workflow' in resource:
                            return True
            
            # Se tem estrutura de workflow (formato antigo), também é IAL
            if isinstance(content, dict):
                for key, value in content.items():
                    if isinstance(value, dict) and 'workflow' in value:
                        return True
            
            return False
        except:
            return False
    
    def convert_ial_to_cloudformation(self, file_path: str) -> Optional[str]:
        """Converte metadado IAL para template CloudFormation"""
        try:
            with open(file_path, 'r') as f:
                ial_metadata = yaml.safe_load(f)
            
            # Template CloudFormation básico
            cf_template = {
                'AWSTemplateFormatVersion': '2010-09-09',
                'Description': f"Generated from IAL metadata: {ial_metadata.get('description', 'IAL Phase')}",
                'Parameters': {
                    'ProjectName': {
                        'Type': 'String',
                        'Default': 'ial-project',
                        'Description': 'Project name for resource naming'
                    },
                    'Environment': {
                        'Type': 'String',
                        'Default': 'dev',
                        'Description': 'Environment name'
                    }
                },
                'Resources': {}
            }
            
            # Processar recursos IAL
            if 'resources' in ial_metadata:
                for resource_key, resource_config in ial_metadata['resources'].items():
                    if isinstance(resource_config, dict):
                        # Processar recursos com mcp_workflow (formato completo)
                        if 'mcp_workflow' in resource_config:
                            mcp_config = resource_config['mcp_workflow']
                            if 'generate_code' in mcp_config:
                                gen_config = mcp_config['generate_code']
                                if 'parameters' in gen_config:
                                    params = gen_config['parameters']
                                    properties = params.get('properties', {})
                                    resource_type = params.get('resource_type', 'AWS::CloudFormation::WaitConditionHandle')
                        
                        # Processar recursos IAL simples (sem mcp_workflow)
                        elif 'type' in resource_config:
                            properties = resource_config.get('properties', {})
                            resource_type = resource_config.get('type', 'AWS::CloudFormation::WaitConditionHandle')
                        
                        else:
                            continue  # Pular recursos sem type
                        
                        # Processar placeholders recursivamente como objetos
                        def process_placeholders(obj):
                            if isinstance(obj, dict):
                                return {k: process_placeholders(v) for k, v in obj.items()}
                            elif isinstance(obj, list):
                                return [process_placeholders(item) for item in obj]
                            elif isinstance(obj, str):
                                if '{{PROJECT_NAME}}' in obj:
                                    if obj == '{{PROJECT_NAME}}':
                                        return {'Ref': 'ProjectName'}
                                    else:
                                        # Substituição com !Sub para concatenação
                                        new_str = obj.replace('{{PROJECT_NAME}}', '${ProjectName}')
                                        new_str = new_str.replace('{{AWS_REGION}}', '${AWS::Region}')
                                        return {'Fn::Sub': new_str}
                                elif '{{AWS_REGION}}' in obj:
                                    if obj == '{{AWS_REGION}}':
                                        return {'Ref': 'AWS::Region'}
                                    else:
                                        new_str = obj.replace('{{AWS_REGION}}', '${AWS::Region}')
                                        return {'Fn::Sub': new_str}
                                # Placeholders de referência entre recursos
                                elif obj == '[VPC_ID]':
                                    return {'Ref': 'Resource03vpc'}
                                elif obj == '[IGW_ID]':
                                    return {'Ref': 'Resource03igw'}
                                elif obj == '[PUBLIC_RT_ID]':
                                    return {'Ref': 'Resource03publicrt'}
                                elif obj == '[PRIVATE_RT_ID]':
                                    return {'Ref': 'Resource03privatert'}
                                elif obj == '[SG_APP_ID]':
                                    return {'Ref': 'Resource03sgapp'}
                                elif obj == '[SG_ALB_ID]':
                                    return {'Ref': 'Resource03sgalb'}
                                elif obj == '[SG_ENDPOINTS_ID]':
                                    return {'Ref': 'Resource03sgendpoints'}
                                elif obj == '[SG_LAMBDA_ID]':
                                    return {'Ref': 'Resource03sglambda'}
                                elif obj == '[PUBLIC_SUBNET_1A_ID]':
                                    return {'Ref': 'Resource03publicsubnet1a'}
                                elif obj == '[PUBLIC_SUBNET_1B_ID]':
                                    return {'Ref': 'Resource03publicsubnet1b'}
                                elif obj == '[PUBLIC_SUBNET_1C_ID]':
                                    return {'Ref': 'Resource03publicsubnet1c'}
                                elif obj == '[PRIVATE_SUBNET_1A_ID]':
                                    return {'Ref': 'Resource03privatesubnet1a'}
                                elif obj == '[PRIVATE_SUBNET_1B_ID]':
                                    return {'Ref': 'Resource03privatesubnet1b'}
                                elif obj == '[PRIVATE_SUBNET_1C_ID]':
                                    return {'Ref': 'Resource03privatesubnet1c'}
                                return obj
                            else:
                                return obj
                        
                        processed_properties = process_placeholders(properties)
                        
                        cf_resource = {
                            'Type': resource_type,
                            'Properties': processed_properties
                        }
                        
                        # Adicionar DependsOn para quebrar dependências circulares
                        if resource_type == 'AWS::EC2::VPCEndpoint':
                            cf_resource['DependsOn'] = ['Resource03vpc']
                        elif 'SecurityGroup' in resource_type and 'endpoints' in resource_key.lower():
                            # Security groups de endpoints não dependem de VPC endpoints
                            pass
                        
                        # Usar resource_name se disponível, senão usar key
                        resource_name = resource_config.get('resource_name', resource_key.replace('-', '').replace('_', ''))
                        # Garantir que nome é alfanumérico
                        resource_name = re.sub(r'[^a-zA-Z0-9]', '', resource_name)
                        # Garantir que nome começa com letra
                        if not resource_name or not resource_name[0].isalpha():
                            resource_name = 'Resource' + resource_name
                            
                        cf_template['Resources'][resource_name] = cf_resource
            
            # Processar formato workflow (formato antigo)
            else:
                for resource_key, resource_config in ial_metadata.items():
                    if isinstance(resource_config, dict) and 'workflow' in resource_config:
                        workflow = resource_config['workflow']
                        
                        # Procurar step com generate_infrastructure_code
                        resource_type = 'AWS::CloudFormation::WaitConditionHandle'
                        properties = {}
                        
                        for step_key, step_config in workflow.items():
                            if isinstance(step_config, dict) and step_config.get('action') == 'generate_infrastructure_code':
                                resource_type = step_config.get('resource_type', resource_type)
                                properties = step_config.get('properties', {})
                                break
                        
                        # Processar placeholders
                        def process_placeholders(obj):
                            if isinstance(obj, dict):
                                return {k: process_placeholders(v) for k, v in obj.items()}
                            elif isinstance(obj, list):
                                return [process_placeholders(item) for item in obj]
                            elif isinstance(obj, str):
                                if '{{PROJECT_NAME}}' in obj:
                                    return {'Fn::Sub': obj.replace('{{PROJECT_NAME}}', '${ProjectName}')}
                                elif '{{AWS_REGION}}' in obj:
                                    return {'Fn::Sub': obj.replace('{{AWS_REGION}}', '${AWS::Region}')}
                                return obj
                            else:
                                return obj
                        
                        processed_properties = process_placeholders(properties)
                        
                        cf_resource = {
                            'Type': resource_type,
                            'Properties': processed_properties
                        }
                        
                        # Nome do recurso
                        resource_name = re.sub(r'[^a-zA-Z0-9]', '', resource_key)
                        if not resource_name or not resource_name[0].isalpha():
                            resource_name = 'Resource' + resource_name
                            
                        cf_template['Resources'][resource_name] = cf_resource
            
            # Se não tem recursos, criar um placeholder
            if not cf_template['Resources']:
                cf_template['Resources']['PlaceholderResource'] = {
                    'Type': 'AWS::CloudFormation::WaitConditionHandle',
                    'Properties': {}
                }
                
            return yaml.dump(cf_template, default_flow_style=False)
            
        except Exception as e:
            print(f"❌ Error converting IAL metadata: {e}")
            return None
    
    def deploy_cloudformation_from_template(self, template_content: str, file_name: str) -> Dict[str, Any]:
        """Deploy CloudFormation a partir de template string"""
        try:
            # Criar arquivo temporário com nome válido
            import tempfile
            import re
            
            # Gerar nome de stack válido baseado no arquivo
            base_name = re.sub(r'[^a-zA-Z0-9-]', '', file_name.replace('.yaml', '').replace('.yml', ''))
            if not base_name:
                base_name = 'converted'
            # Garantir que não termina com hífen
            base_name = base_name.rstrip('-')
            stack_suffix = f"ial-{base_name}-temp"
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
                temp_file.write(template_content)
                temp_file_path = temp_file.name
            
            # Deploy usando método existente
            result = self.deploy_cloudformation_stack(temp_file_path)
            
            # Limpar arquivo temporário
            os.unlink(temp_file_path)
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error deploying from template: {str(e)}'
            }

def deploy_phase_resources(phase: str = "00-foundation") -> Dict[str, Any]:
    """Deploy todos os recursos de uma fase"""
    parser = PhaseParser()
    
    # Listar todos os arquivos da fase
    phase_files = parser.list_phase_files(phase)
    
    if not phase_files:
        return {
            'success': False,
            'error': f'No YAML files found in phase {phase}',
            'total_resources': 0,
            'successful': 0,
            'results': []
        }
    
    print(f"📦 Found {len(phase_files)} templates in phase {phase}")
    
    results = []
    successful = 0
    
    for file_path in phase_files:
        file_name = os.path.basename(file_path)
        print(f"🔄 Deploying {file_name}...")
        
        try:
            # OPÇÃO 3: Detectar se é metadado IAL e converter para CloudFormation
            if parser.is_ial_metadata(file_path):
                print(f"🔧 Converting IAL metadata to CloudFormation...")
                cf_template = parser.convert_ial_to_cloudformation(file_path)
                if cf_template:
                    result = parser.deploy_cloudformation_from_template(cf_template, file_name)
                else:
                    result = {'success': False, 'error': 'Failed to convert IAL metadata to CloudFormation'}
            else:
                # CloudFormation template direto
                result = parser.deploy_cloudformation_stack(file_path)
            
            if result.get('success', False):
                successful += 1
                print(f"✅ {file_name} deployed successfully")
            else:
                print(f"❌ {file_name} deployment failed: {result.get('error', 'Unknown error')}")
            
            results.append({
                'name': file_name,
                'success': result.get('success', False),
                'error': result.get('error'),
                'type': 'CloudFormation Stack'
            })
            
        except Exception as e:
            print(f"❌ Error deploying {file_name}: {str(e)}")
            results.append({
                'name': file_name,
                'success': False,
                'error': str(e),
                'type': 'CloudFormation Stack'
            })
    
    return {
        'success': successful == len(phase_files),
        'total_resources': len(phase_files),
        'successful': successful,
        'results': results
    }
