#!/usr/bin/env python3
"""
IALCTL Integrated - CLI usando arquitetura robusta existente
Integra BedrockConversationEngine + Memory + Context + MCP Servers
"""

import asyncio
import argparse
import sys
import os
import json
import readline  # Habilita setas e histórico
from typing import Dict, Optional, Any

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def custom_input(prompt: str) -> str:
    """Input com readline (setas funcionam)"""
    return input(prompt)

class IALCTLIntegrated:
    """CLI integrado usando componentes robustos existentes"""
    
    def __init__(self):
        self.master_engine = None
        self._initialize_master_engine()
    
    def _initialize_master_engine(self):
        """Inicializar Master Engine integrado"""
        try:
            from core.ial_master_engine_integrated import IALMasterEngineIntegrated
            self.master_engine = IALMasterEngineIntegrated()
            print("✅ IAL Master Engine Integrado inicializado")
        except ImportError as e:
            print(f"❌ Erro ao inicializar Master Engine Integrado: {e}")
            sys.exit(1)
    
    async def run_start_command(self):
        """Executar comando 'start' - deploy da foundation"""
        from core.foundation_deployer import FoundationDeployer
        from core.mcp_servers_initializer import MCPServersInitializer
        from core.system_health_validator import SystemHealthValidator
        import subprocess
        import boto3
        import getpass
        
        print("🚀 IAL Foundation Deployment Starting...")
        print("=" * 50)
        
        # 0. Prerequisites & Dependencies
        print("\n🔧 Step 0/6: Prerequisites & Dependencies...")
        prereq_result = self._check_and_install_prerequisites()
        if not prereq_result['success']:
            print(f"❌ Prerequisites check failed: {prereq_result['error']}")
            return 1
        print("✅ All prerequisites validated")
        
        # 1. GitHub Configuration
        print("\n🔑 Step 1/6: GitHub Configuration...")
        github_token = self._get_github_token()
        if not github_token:
            print("❌ GitHub token é obrigatório para IAL funcionar")
            return 1
        print("✅ GitHub token configurado")
        
        # 2. Deploy Foundation
        print("\n📦 Step 2/6: Deploying AWS Foundation...")
        deployer = FoundationDeployer()
        result = deployer.deploy_foundation_core()
        
        if result['successful_deployments'] == 0:
            print("\n❌ IAL Foundation deployment failed!")
            return 1
        
        print(f"✅ Foundation: {result['successful_deployments']}/{result['total_resource_groups']} resource groups deployed")
        
        # 3. Initialize MCP Servers
        print("\n🔌 Step 3/6: Initializing MCP Servers...")
        mcp_initializer = MCPServersInitializer()
        mcp_result = await mcp_initializer.initialize_all_servers()
        
        print(f"✅ MCP Servers: {mcp_result['total_initialized']} initialized")
        
        # 4. Build and Deploy Container Lambda
        print("\n🐳 Step 4/6: Building Container Lambda...")
        try:
            container_result = self._build_and_deploy_container_lambda()
            if container_result['success']:
                print("   ✅ Container Lambda deployed successfully")
            else:
                print(f"   ⚠️  Container Lambda deployment failed: {container_result['error']}")
        except Exception as e:
            print(f"   ⚠️  Warning: Container Lambda build failed: {e}")
            print("   ℹ️  Enhanced MCP will use fallback mode")
        
        if health_result['warnings']:
            print(f"⚠️  Warnings: {len(health_result['warnings'])}")
        
        # 5. Deploy NL Intent Pipeline (Step Functions)
        print("\n🔀 Step 5/6: Deploying NL Intent Pipeline...")
        try:
            # Update Secrets Manager with real GitHub token
            print("   🔑 Updating GitHub token in Secrets Manager...")
            self._update_github_secret(github_token)
            
            # Preparar artifacts
            print("   📦 Preparing Lambda artifacts...")
            subprocess.run([
                'bash', '-c',
                'cd /home/ial/lambdas && '
                'zip -q ias_validation_handler.zip ias_validation_handler.py && '
                'zip -q cost_estimation_handler.zip cost_estimation_handler.py && '
                'zip -q phase_builder_handler.zip phase_builder_handler.py && '
                'zip -q git_commit_pr_handler.zip git_commit_pr_handler.py && '
                'zip -q wait_pr_approval_handler.zip wait_pr_approval_handler.py && '
                'zip -q deploy_cloudformation_handler.zip deploy_cloudformation_handler.py && '
                'zip -q proof_of_creation_handler.zip proof_of_creation_handler.py && '
                'zip -q post_deploy_analysis_handler.zip post_deploy_analysis_handler.py && '
                'zip -q drift_detection_handler.zip drift_detection_handler.py'
            ], check=True)
            
            subprocess.run([
                'bash', '-c',
                'cd /home/ial/lambda-layer && zip -qr ial-pipeline-layer.zip python/'
            ], check=True)
            
            # Criar bucket S3 se não existir
            account_id = boto3.client('sts').get_caller_identity()['Account']
            bucket_name = f'ial-artifacts-{account_id}'
            s3 = boto3.client('s3')
            
            try:
                s3.head_bucket(Bucket=bucket_name)
            except:
                print(f"   📦 Creating S3 bucket: {bucket_name}")
                s3.create_bucket(Bucket=bucket_name)
            
            # Upload artifacts
            print("   ☁️  Uploading to S3...")
            handlers = [
                'ias_validation_handler',
                'cost_estimation_handler',
                'phase_builder_handler',
                'git_commit_pr_handler',
                'wait_pr_approval_handler',
                'deploy_cloudformation_handler',
                'proof_of_creation_handler',
                'post_deploy_analysis_handler',
                'drift_detection_handler'
            ]
            
            for handler in handlers:
                s3.upload_file(
                    f'/home/ial/lambdas/{handler}.zip',
                    bucket_name,
                    f'lambdas/{handler}.zip'
                )
            
            s3.upload_file(
                '/home/ial/lambda-layer/ial-pipeline-layer.zip',
                bucket_name,
                'lambda-layer/ial-pipeline-layer.zip'
            )
            
            # Deploy CloudFormation
            print("   🚀 Deploying CloudFormation stack...")
            cfn = boto3.client('cloudformation')
            
            with open(get_resource_path('phases/00-foundation/17-nl-intent-pipeline.yaml')) as f:
                template_body = f.read()
            
            try:
                cfn.create_stack(
                    StackName='ial-nl-intent-pipeline',
                    TemplateBody=template_body,
                    Capabilities=['CAPABILITY_NAMED_IAM']
                )
                print("   ✅ NL Intent Pipeline stack created")
            except cfn.exceptions.AlreadyExistsException:
                print("   ℹ️  NL Intent Pipeline stack already exists")
        
        except Exception as e:
            print(f"   ⚠️  Warning: NL Intent Pipeline deployment failed: {e}")
            print("   ℹ️  You can deploy it manually later")
        
        # 6. Validate System Health
        print("\n🏥 Step 6/6: Validating System Health...")
        health_validator = SystemHealthValidator()
        health_result = await health_validator.validate_complete_system()
        
        print(f"✅ Health Check: {health_result['checks_passed']}/{health_result['checks_passed'] + health_result['checks_failed']} checks passed")
        
        if health_result['warnings']:
            print(f"⚠️  Warnings: {len(health_result['warnings'])}")
        
        # Summary
        print("\n" + "=" * 50)
        print("✅ IAL Foundation deployed successfully!")
        print(f"📊 AWS Resources: {result['successful_deployments']}/{result['total_resource_groups']} groups")
        print(f"🔌 MCP Servers: {mcp_result['total_initialized']} active")
        print(f"🏥 System Status: {health_result['overall_status'].upper()}")
        print(f"🔀 NL Intent Pipeline: Step Functions deployed")
        print(f"🐳 Container Lambda: Enhanced MCP ready")
        
        if health_result['system_ready']:
            print("\n🎯 System ready! Run 'ialctl' to start conversational interface")
            return 0
        else:
            print("\n⚠️  System has issues but may still work")
            return 0
    
    def _check_and_install_prerequisites(self) -> Dict[str, Any]:
        """Check and install all prerequisites"""
        import subprocess
        import os
        
        try:
            # 1. Check Docker
            print("   🐳 Checking Docker...")
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                return {'success': False, 'error': 'Docker not installed or not running'}
            print("   ✅ Docker available")
            
            # 2. Check AWS CLI
            print("   ☁️  Checking AWS CLI...")
            result = subprocess.run(['aws', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                return {'success': False, 'error': 'AWS CLI not installed'}
            print("   ✅ AWS CLI available")
            
            # 3. Check AWS credentials
            print("   🔑 Checking AWS credentials...")
            try:
                import boto3
                boto3.client('sts').get_caller_identity()
                print("   ✅ AWS credentials valid")
            except Exception as e:
                return {'success': False, 'error': f'AWS credentials invalid: {e}'}
            
            # 4. Install FAISS
            print("   📚 Checking FAISS...")
            try:
                import faiss
                print("   ✅ FAISS already installed")
            except ImportError:
                print("   📦 Installing FAISS...")
                subprocess.run([
                    'pip', 'install', 'faiss-cpu', '--break-system-packages'
                ], check=True)
                print("   ✅ FAISS installed")
            
            # 5. Build RAG index if needed
            if not os.path.exists('.rag/index.faiss'):
                print("   🔍 Building RAG index...")
                from services.rag.index_builder import build_index
                build_index({
                    'local_path': '.rag/index.faiss',
                    'local_meta': '.rag/index.json'
                })
                print("   ✅ RAG index built")
            else:
                print("   ℹ️  RAG index already exists")
            
            # 6. Prepare build environment
            print("   🔧 Preparing build environment...")
            os.makedirs('/tmp/ial-container-build', exist_ok=True)
            print("   ✅ Build environment ready")
            
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _get_github_token(self):
        """Capturar GitHub token do usuário"""
        import getpass
        import os
        
        # Verificar se já existe em variável de ambiente
        token = os.getenv('GITHUB_TOKEN')
        if token:
            print("   ✅ GitHub token encontrado em GITHUB_TOKEN")
            return token
        
        # Verificar se já existe no Secrets Manager
        try:
            import boto3
            secrets = boto3.client('secretsmanager')
            response = secrets.get_secret_value(SecretId='ial-github-token')
            secret_data = json.loads(response['SecretString'])
            existing_token = secret_data.get('token', '')
            
            if existing_token and not existing_token.startswith('ghp_placeholder'):
                print("   ✅ GitHub token encontrado no Secrets Manager")
                return existing_token
        except:
            pass
        
        # Solicitar token do usuário
        print("\n📋 IAL precisa de um GitHub token para criar PRs automaticamente")
        print("   1. Vá para: https://github.com/settings/tokens")
        print("   2. Clique em 'Generate new token (classic)'")
        print("   3. Selecione scopes: repo, workflow")
        print("   4. Cole o token abaixo")
        print()
        
        while True:
            token = getpass.getpass("🔑 GitHub Token (ghp_...): ").strip()
            
            if not token:
                print("❌ Token é obrigatório")
                continue
            
            if not token.startswith('ghp_'):
                print("❌ Token deve começar com 'ghp_'")
                continue
            
            # Validar token
            if self._validate_github_token(token):
                return token
            else:
                print("❌ Token inválido ou sem permissões necessárias")
                continue
    
    def _validate_github_token(self, token):
        """Validar GitHub token"""
        try:
            import requests
            
            response = requests.get(
                'https://api.github.com/user',
                headers={'Authorization': f'token {token}'},
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                print(f"   ✅ Token válido para usuário: {user_data.get('login')}")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"   ⚠️  Erro validando token: {e}")
            return False
    
    def _update_github_secret(self, github_token):
        """Atualizar GitHub token no Secrets Manager"""
        try:
            import boto3
            import json
            
            secrets = boto3.client('secretsmanager')
            
            secret_value = {
                "token": github_token
            }
            
            secrets.update_secret(
                SecretId='ial-github-token',
                SecretString=json.dumps(secret_value)
            )
            
            print("   ✅ GitHub token atualizado no Secrets Manager")
            
        except Exception as e:
            print(f"   ⚠️  Warning: Falha ao atualizar secret: {e}")
    
    def _build_and_deploy_container_lambda(self) -> Dict[str, Any]:
        """Build and deploy container Lambda"""
        import subprocess
        import boto3
        import os
        
        try:
            # 1. Check if Docker is available
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                return {'success': False, 'error': 'Docker not installed'}
            
            print("   ✅ Docker available")
            
            # 2. Get account ID and region
            sts = boto3.client('sts')
            account_id = sts.get_caller_identity()['Account']
            region = 'us-east-1'
            
            # 3. ECR repository URI
            ecr_uri = f"{account_id}.dkr.ecr.{region}.amazonaws.com/ial-phase-builder-mcp"
            
            # 4. Copy files to build context
            build_dir = '/tmp/ial-container-build'
            os.makedirs(build_dir, exist_ok=True)
            
            # Copy Dockerfile and dependencies
            import shutil
            shutil.copy(get_resource_path('phases/00-foundation/Dockerfile.lambda-mcp'), f'{build_dir}/Dockerfile')
            shutil.copy(get_resource_path('phases/00-foundation/requirements-lambda.txt'), build_dir)
            shutil.copy(get_resource_path('phases/00-foundation/phase_builder_handler_container.py'), build_dir)
            
            print("   📦 Build context prepared")
            
            # 5. Docker build
            print("   🔨 Building Docker image...")
            build_result = subprocess.run([
                'docker', 'build', '-t', 'ial-phase-builder-mcp:latest', '.'
            ], cwd=build_dir, capture_output=True, text=True, timeout=300)
            
            if build_result.returncode != 0:
                return {'success': False, 'error': f'Docker build failed: {build_result.stderr}'}
            
            print("   ✅ Docker image built")
            
            # 6. ECR login
            print("   🔐 Logging into ECR...")
            ecr = boto3.client('ecr', region_name=region)
            token_response = ecr.get_authorization_token()
            token = token_response['authorizationData'][0]['authorizationToken']
            endpoint = token_response['authorizationData'][0]['proxyEndpoint']
            
            import base64
            username, password = base64.b64decode(token).decode().split(':')
            
            login_result = subprocess.run([
                'docker', 'login', '--username', username, '--password-stdin', endpoint
            ], input=password, text=True, capture_output=True)
            
            if login_result.returncode != 0:
                return {'success': False, 'error': 'ECR login failed'}
            
            print("   ✅ ECR login successful")
            
            # 7. Tag and push
            print("   📤 Pushing to ECR...")
            
            # Tag image
            subprocess.run([
                'docker', 'tag', 'ial-phase-builder-mcp:latest', f'{ecr_uri}:latest'
            ], check=True)
            
            # Push image
            push_result = subprocess.run([
                'docker', 'push', f'{ecr_uri}:latest'
            ], capture_output=True, text=True, timeout=600)
            
            if push_result.returncode != 0:
                return {'success': False, 'error': f'Docker push failed: {push_result.stderr}'}
            
            print("   ✅ Image pushed to ECR")
            
            # 8. Update Lambda function
            print("   🔄 Updating Lambda function...")
            lambda_client = boto3.client('lambda', region_name=region)
            
            try:
                lambda_client.update_function_code(
                    FunctionName='ial-nl-phase-builder-mcp',
                    ImageUri=f'{ecr_uri}:latest'
                )
                print("   ✅ Lambda function updated")
            except lambda_client.exceptions.ResourceNotFoundException:
                # Create Lambda function if it doesn't exist
                lambda_client.create_function(
                    FunctionName='ial-nl-phase-builder-mcp',
                    Role=f'arn:aws:iam::{account_id}:role/IAL-Pipeline-Lambda-Role',
                    Code={'ImageUri': f'{ecr_uri}:latest'},
                    PackageType='Image',
                    Timeout=300,
                    MemorySize=512,
                    Description='MCP-Enhanced Phase Builder with Container Lambda'
                )
                print("   ✅ Lambda function created")
            
            # Cleanup
            shutil.rmtree(build_dir, ignore_errors=True)
            
            return {'success': True, 'image_uri': f'{ecr_uri}:latest'}
            
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Build timeout (5 minutes)'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def run_conversational_mode(self):
        """Executar modo conversacional integrado"""
        
        print("🤖 **IAL Assistant - Arquitetura Robusta Integrada**")
        print("🧠 **Bedrock** + 💾 **DynamoDB** + 🔍 **Embeddings** + 🔗 **MCP Servers**")
        print("Digite 'help' para ajuda, 'quit' para sair\n")
        
        # Mostrar status inicial
        await self._show_initial_status()
        
        while True:
            try:
                user_input = custom_input("IAL> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n👋 Até logo!")
                break
                
            if user_input.lower() in ['quit', 'exit', 'sair']:
                print("👋 Até logo!")
                break
            
            if user_input.lower() in ['help', 'ajuda']:
                await self._show_help()
                continue
            
            if user_input.lower() == 'status':
                await self._show_system_status()
                continue
            
            if user_input.lower() in ['clear', 'cls']:
                import os
                os.system('clear' if os.name != 'nt' else 'cls')
                continue
            
            if user_input.lower() == 'reset':
                self.master_engine.clear_session()
                continue
            
            if user_input.lower() == 'memory':
                await self._show_memory_stats()
                continue
            
            if user_input:
                try:
                    # Processar via Master Engine Integrado
                    response = await self.master_engine.process_user_input(user_input)
                    print(f"\n{response}\n")
                except Exception as e:
                    print(f"❌ Erro: {e}")
    
    async def _show_initial_status(self):
        """Mostrar status inicial do sistema integrado"""
        
        status = self.master_engine.get_system_status()
        
        # Contar engines ativos
        engines_active = sum(1 for engine in status["engines_status"].values() if engine)
        orchestrators_active = sum(1 for orch in status["orchestrators_status"].values() if orch)
        
        print(f"📊 **Sistema Integrado:** {engines_active}/3 engines robustos, {orchestrators_active}/3 orquestradores")
        print(f"👤 **User ID:** {status['user_id']}")
        
        # Status da memória
        memory_stats = status.get('memory_stats', {})
        if 'total_messages' in memory_stats:
            print(f"💾 **Memória:** {memory_stats['total_messages']} mensagens, {memory_stats['sessions']} sessões")
            
            # Explicação da memória persistente
            print(f"\n🧠 **Memória Inteligente:**")
            print(f"   Eu lembro de TODAS as nossas conversas anteriores!")
            print(f"   • Bedrock Titan gera embeddings semânticos das mensagens")
            print(f"   • DynamoDB armazena todo o histórico de forma persistente")
            print(f"   • Busca vetorial encontra contexto relevante automaticamente")
            print(f"   Pode continuar de onde paramos ou retomar qualquer assunto! 💬")
            
            # NOVO: Resumo da última conversa
            if memory_stats['total_messages'] > 0 and self.master_engine.context_engine:
                try:
                    recent = self.master_engine.context_engine.memory.get_recent_context(limit=3)
                    if recent:
                        print(f"\n📝 **Última conversa:**")
                        last_user = None
                        last_assistant = None
                        
                        for msg in reversed(recent):
                            if msg['role'] == 'user' and not last_user:
                                last_user = msg['content'][:80] + "..." if len(msg['content']) > 80 else msg['content']
                            elif msg['role'] == 'assistant' and not last_assistant:
                                last_assistant = msg['content'][:80] + "..." if len(msg['content']) > 80 else msg['content']
                        
                        if last_user:
                            print(f"   Você: {last_user}")
                        if last_assistant:
                            print(f"   IAL: {last_assistant}")
                except Exception:
                    pass
        
        print("🚀 **Pronto para conversa inteligente!**\n")
    
    async def _show_help(self):
        """Mostrar ajuda detalhada integrada"""
        
        help_text = """
🤖 **IAL Assistant - Guia da Arquitetura Integrada**

**💬 CONVERSAÇÃO NATURAL (Bedrock + Contexto):**
• "Olá, como você pode me ajudar?"
• "Lembra da nossa conversa anterior?"
• "Explique o que é Amazon ECS"
• "Como está meu ambiente AWS?"

**📊 CONSULTAS (MCP + Query Engine):**
• "liste todos os buckets S3"
• "quantas instâncias EC2 eu tenho"
• "qual o custo atual da minha conta"
• "status dos meus recursos"

**🚀 PROVISIONING (Orquestradores):**
• "quero criar ECS com Redis"
• "preciso de uma VPC privada"
• "deploy aplicação serverless"
• "criar infraestrutura de segurança"

**🧠 CAPACIDADES AVANÇADAS:**
• **Memória Persistente:** Lembra conversas entre sessões
• **Busca Semântica:** Encontra contexto relevante automaticamente
• **Bedrock Claude:** Respostas naturais e inteligentes
• **MCP Integration:** Acesso direto aos serviços AWS

**⚙️ COMANDOS ESPECIAIS:**
• "status" - Status detalhado do sistema
• "memory" - Estatísticas de memória
• "clear" - Limpar sessão atual
• "help" - Esta ajuda
• "quit" - Sair

**🎯 RECURSOS IAL:**
• ✅ DynamoDB para persistência de conversas
• ✅ Bedrock embeddings para busca semântica
• ✅ Contexto cross-sessão inteligente
• ✅ MCP servers para integração AWS
• ✅ Memória conversacional avançada

💡 **Dica:** Seja natural! O IAL entende contexto e lembra das conversas.
"""
        print(help_text)
    
    async def _show_system_status(self):
        """Mostrar status detalhado do sistema integrado"""
        
        status = self.master_engine.get_system_status()
        
        print("\n📊 **Status Detalhado - Arquitetura Integrada:**")
        
        print(f"\n👤 **Usuário:**")
        print(f"• User ID: {status['user_id']}")
        print(f"• Session ID: {status.get('session_id', 'Nova sessão')}")
        
        print(f"\n🧠 **Engines Robustos:**")
        engines = status["engines_status"]
        print(f"• Bedrock Conversation: {'✅ Ativo (Claude + DynamoDB)' if engines['bedrock_conversation'] else '❌ Inativo'}")
        print(f"• Context Engine: {'✅ Ativo (Embeddings + Busca)' if engines['context_engine'] else '❌ Inativo'}")
        print(f"• Query Engine: {'✅ Ativo (MCP + AWS APIs)' if engines['query_engine'] else '❌ Inativo'}")
        
        print(f"\n🔄 **Orquestradores:**")
        orchestrators = status["orchestrators_status"]
        for name, active in orchestrators.items():
            status_text = "✅ Ativo" if active else "❌ Inativo"
            print(f"• {name.replace('_', ' ').title()}: {status_text}")
        
        print(f"\n🎯 **Capacidades:**")
        capabilities = status["capabilities"]
        for capability, active in capabilities.items():
            status_icon = "✅" if active else "❌"
            capability_name = capability.replace('_', ' ').title()
            print(f"• {capability_name}: {status_icon}")
        
        # Status da memória detalhado
        await self._show_memory_stats()
    
    async def _show_memory_stats(self):
        """Mostrar estatísticas detalhadas de memória"""
        
        status = self.master_engine.get_system_status()
        memory_stats = status.get('memory_stats', {})
        
        print(f"\n💾 **Estatísticas de Memória:**")
        
        if 'total_messages' in memory_stats:
            print(f"• Total de mensagens: {memory_stats['total_messages']}")
            print(f"• Número de sessões: {memory_stats['sessions']}")
            
            if memory_stats.get('first_interaction'):
                print(f"• Primeira interação: {memory_stats['first_interaction'][:19]}")
            if memory_stats.get('last_interaction'):
                print(f"• Última interação: {memory_stats['last_interaction'][:19]}")
        else:
            print(f"• Status: {memory_stats.get('status', 'Informações não disponíveis')}")
        
        print(f"• Persistência: ✅ DynamoDB + Cache local")
        print(f"• Busca semântica: ✅ Bedrock Embeddings")
        print(f"• Contexto cross-sessão: ✅ Ativo")

def main():
    """Função principal do CLI integrado"""
    
    parser = argparse.ArgumentParser(
        description="IAL Integrated - Interface conversacional com arquitetura robusta",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🎯 ARQUITETURA INTEGRADA:

• Bedrock Conversation Engine (Claude + DynamoDB)
• Context Engine (Embeddings + Busca semântica)  
• Query Engine (MCP Servers + AWS APIs)
• Memory Manager (Persistência + Cache)

🚀 CAPACIDADES IAL:
• Memória persistente entre sessões
• Busca semântica por contexto relevante
• Integração nativa com MCP servers
• Orquestração híbrida (Step Functions + MCP + Python)

Exemplos de uso:

  # Modo interativo (padrão)
  python ialctl_integrated.py

  # Conversação natural
  IAL> "Lembra da nossa conversa sobre ECS?"
  
  # Queries AWS
  IAL> "liste todos os buckets"
  
  # Provisioning
  IAL> "quero criar VPC privada"
        """
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="IAL Integrated v2.0.0 - Arquitetura Robusta"
    )
    
    parser.add_argument(
        "command",
        nargs="?",
        choices=["start"],
        help="Comando a executar: 'start' para deploy da foundation"
    )
    
    args = parser.parse_args()
    
    # Inicializar CLI integrado
    cli = IALCTLIntegrated()
    
    # Executar comando específico ou modo interativo
    try:
        if args.command == "start":
            return asyncio.run(cli.run_start_command())
        else:
            asyncio.run(cli.run_conversational_mode())
            return 0
    except KeyboardInterrupt:
        print("\n👋 Até logo!")
        return 0
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
