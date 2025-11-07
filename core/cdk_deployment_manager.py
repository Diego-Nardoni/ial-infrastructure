#!/usr/bin/env python3
"""
CDK Deployment Manager
Manages CDK deployment for IAL Foundation
"""

import os
import sys
import json
import subprocess
import boto3
from typing import Dict, Optional
from pathlib import Path

class CDKDeploymentManager:
    def __init__(self, config: Dict):
        self.config = config
        
        # Detectar se está executando como binário PyInstaller ou script
        if hasattr(sys, '_MEIPASS'):
            # Executando como binário - usar recursos empacotados
            self.cdk_app_path = os.path.join(sys._MEIPASS, 'cdk')
        else:
            # Executando como script - usar diretório do projeto
            project_root = os.path.dirname(os.path.dirname(__file__))
            self.cdk_app_path = os.path.join(project_root, 'cdk')
            
        self.project_name = config.get('PROJECT_NAME', 'ial')
        self.aws_region = config.get('AWS_REGION', 'us-east-1')
        self.aws_account = config.get('AWS_ACCOUNT_ID')
        
    def deploy_foundation(self) -> Dict:
        """Deploy IAL Foundation via CDK"""
        try:
            print("🚀 Iniciando deploy da infraestrutura IAL via CDK...")
            
            # 1. Prepare CDK environment
            self._prepare_cdk_environment()
            
            # 2. Bootstrap CDK (if needed)
            bootstrap_result = self._bootstrap_cdk()
            if not bootstrap_result['success']:
                return bootstrap_result
            
            # 3. Deploy CDK stack
            deploy_result = self._deploy_cdk_stack()
            if not deploy_result['success']:
                return deploy_result
            
            # 4. Get stack outputs
            outputs = self._get_stack_outputs()
            
            # 5. Update local configuration
            self._update_local_config(outputs)
            
            # 6. Test connectivity
            test_result = self._test_connectivity(outputs)
            
            return {
                'success': True,
                'message': '✅ IAL Foundation deployed successfully!',
                'outputs': outputs,
                'connectivity_test': test_result
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'❌ Deploy failed: {str(e)}',
                'error': str(e)
            }
    
    def _prepare_cdk_environment(self):
        """Prepare CDK environment and install dependencies"""
        print("📦 Preparando ambiente CDK...")
        
        # Change to CDK directory
        os.chdir(self.cdk_app_path)
        
        # Use venv python for CDK operations
        self.python_path = "/home/ial/venv/bin/python"
        self.pip_path = "/home/ial/venv/bin/pip"
        
        # Install Python dependencies in venv
        subprocess.run([
            self.pip_path, "install", "-r", "requirements.txt"
        ], check=True, capture_output=True)
        
        print("✅ Ambiente CDK preparado")
    
    def _bootstrap_cdk(self) -> Dict:
        """Bootstrap CDK in the target account/region"""
        print("🔧 Verificando bootstrap CDK...")
        
        try:
            # Check if already bootstrapped
            cf_client = boto3.client('cloudformation', region_name=self.aws_region)
            
            try:
                cf_client.describe_stacks(StackName='CDKToolkit')
                print("✅ CDK já está bootstrapped")
                return {'success': True}
            except cf_client.exceptions.ClientError:
                # Need to bootstrap
                print("🚀 Executando CDK bootstrap...")
                
                result = subprocess.run([
                    "cdk", "bootstrap", 
                    f"aws://{self.aws_account}/{self.aws_region}"
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    return {
                        'success': False,
                        'message': f'CDK bootstrap failed: {result.stderr}'
                    }
                
                print("✅ CDK bootstrap concluído")
                return {'success': True}
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Bootstrap error: {str(e)}'
            }
    
    def _deploy_cdk_stack(self) -> Dict:
        """Deploy the CDK stack"""
        print("🚀 Deployando stack IAL Foundation...")
        
        try:
            # Set CDK context variables
            context_args = [
                "-c", f"project_name={self.project_name}",
                "-c", f"aws_account={self.aws_account}",
                "-c", f"aws_region={self.aws_region}",
                "-c", f"executor_name={self.config.get('EXECUTOR_NAME', 'IAL-User')}"
            ]
            
            # Add GitHub context if available
            if self.config.get('GITHUB_USER'):
                context_args.extend([
                    "-c", f"github_user={self.config['GITHUB_USER']}",
                    "-c", f"github_repo={self.config.get('GITHUB_REPOSITORY', '')}"
                ])
            
            # Execute CDK deploy with venv python
            env = os.environ.copy()
            env['PYTHONPATH'] = '/home/ial/cdk'
            
            result = subprocess.run([
                "cdk", "deploy", f"{self.project_name}-foundation",
                "--require-approval", "never",
                "--outputs-file", "outputs.json",
                "--app", f"{self.python_path} app.py"
            ] + context_args, capture_output=True, text=True, env=env)
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'message': f'CDK deploy failed: {result.stderr}'
                }
            
            print("✅ Stack deployado com sucesso")
            return {'success': True}
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Deploy error: {str(e)}'
            }
    
    def _get_stack_outputs(self) -> Dict:
        """Get CloudFormation stack outputs"""
        print("📋 Coletando outputs do stack...")
        
        try:
            # Read outputs from CDK outputs file
            outputs_file = Path(self.cdk_app_path) / "outputs.json"
            if outputs_file.exists():
                with open(outputs_file, 'r') as f:
                    outputs_data = json.load(f)
                    stack_name = f"{self.project_name}-foundation"
                    return outputs_data.get(stack_name, {})
            
            # Fallback: get from CloudFormation directly
            cf_client = boto3.client('cloudformation', region_name=self.aws_region)
            response = cf_client.describe_stacks(
                StackName=f"{self.project_name}-foundation"
            )
            
            outputs = {}
            if response['Stacks']:
                stack_outputs = response['Stacks'][0].get('Outputs', [])
                for output in stack_outputs:
                    outputs[output['OutputKey']] = output['OutputValue']
            
            return outputs
            
        except Exception as e:
            print(f"⚠️ Erro coletando outputs: {e}")
            return {}
    
    def _update_local_config(self, outputs: Dict):
        """Update local parameters.env with stack outputs"""
        print("⚙️ Atualizando configuração local...")
        
        config_path = "/etc/ial/parameters.env"
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Read existing config
        existing_config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        existing_config[key] = value
        
        # Add CDK outputs
        existing_config.update({
            'IAL_MODE': 'aws',
            'DYNAMODB_STATE_TABLE': outputs.get('DynamoDBStateTable', ''),
            'API_GATEWAY_ENDPOINT': outputs.get('APIGatewayEndpoint', ''),
            'STEP_FUNCTIONS_PIPELINE_ARN': outputs.get('StepFunctionsPipelineArn', ''),
            'DRIFT_DETECTOR_ARN': outputs.get('DriftDetectorArn', ''),
            'ALERTS_TOPIC_ARN': outputs.get('AlertsTopicArn', ''),
            'GITHUB_OIDC_ROLE_ARN': outputs.get('GitHubOIDCRoleArn', '')
        })
        
        # Write updated config
        with open(config_path, 'w') as f:
            f.write("# IAL Configuration - Updated by CDK Deploy\n")
            for key, value in existing_config.items():
                f.write(f"{key}={value}\n")
        
        print("✅ Configuração local atualizada")
    
    def _test_connectivity(self, outputs: Dict) -> Dict:
        """Test connectivity to deployed resources"""
        print("🔍 Testando conectividade...")
        
        tests = {}
        
        # Test DynamoDB access
        if outputs.get('DynamoDBStateTable'):
            try:
                dynamodb = boto3.client('dynamodb', region_name=self.aws_region)
                dynamodb.describe_table(TableName=outputs['DynamoDBStateTable'])
                tests['dynamodb'] = '✅ Conectado'
            except Exception as e:
                tests['dynamodb'] = f'❌ Erro: {str(e)}'
        
        # Test API Gateway
        if outputs.get('APIGatewayEndpoint'):
            try:
                import requests
                response = requests.get(f"{outputs['APIGatewayEndpoint']}/health", timeout=10)
                if response.status_code == 200:
                    tests['api_gateway'] = '✅ Conectado'
                else:
                    tests['api_gateway'] = f'⚠️ Status: {response.status_code}'
            except Exception as e:
                tests['api_gateway'] = f'❌ Erro: {str(e)}'
        
        return tests
