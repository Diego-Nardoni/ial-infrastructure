#!/usr/bin/env python3
"""
IaL Bootstrap Assistant
Instala e configura o sistema via linguagem natural
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime

class IaLBootstrapAssistant:
    def __init__(self):
        self.aws_configured = False
        self.bedrock_available = False
        self.dynamodb_ready = False
        self.github_configured = False
        self.environment_type = 'development'
        
    def start_conversation(self):
        """Inicia conversa de instalação"""
        print("🚀 Olá! Sou o assistente de instalação do IaL")
        print("Vou configurar tudo para você usar linguagem natural com sua infraestrutura AWS")
        print()
        
        while True:
            user_input = input("👤 Você: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['sair', 'quit', 'exit']:
                print("👋 Instalação cancelada. Execute novamente quando quiser configurar!")
                break
                
            response = self.process_setup_request(user_input)
            print(f"🤖 IaL Setup: {response}")
            print()
            
            # Se instalação completa, transfere para sistema principal
            if self.is_setup_complete():
                print("✅ Instalação completa! Transferindo para o sistema principal...")
                print("=" * 60)
                self.start_main_system()
                break

    def process_setup_request(self, user_input):
        """Processa solicitações de instalação"""
        
        user_lower = user_input.lower()
        
        # Intenções de instalação
        if any(word in user_lower for word in ['instalar', 'configurar', 'setup', 'começar', 'iniciar']):
            return self.start_installation()
            
        elif any(word in user_lower for word in ['aws', 'credenciais', 'configure']):
            return self.check_aws_setup()
            
        elif any(word in user_lower for word in ['bedrock', 'ai', 'modelos']):
            return self.setup_bedrock()
            
        elif any(word in user_lower for word in ['tabelas', 'dynamodb', 'banco']):
            return self.setup_dynamodb()
            
        elif any(word in user_lower for word in ['testar', 'verificar', 'status']):
            return self.check_system_status()
            
        elif any(word in user_lower for word in ['sim', 'yes', 'ok', 'pode', 'prosseguir']):
            return self.continue_installation()
            
        elif any(word in user_lower for word in ['não', 'no', 'cancelar', 'parar']):
            return "Instalação pausada. Me diga quando quiser continuar!"
            
        else:
            return self.provide_setup_guidance(user_input)

    def start_installation(self):
        """Inicia processo de instalação"""
        
        print("\n🔍 Verificando seu ambiente...")
        
        # Detecta tipo de ambiente
        self.detect_environment()
        
        # Verifica dependências
        checks = self.run_environment_checks()
        
        response = f"📊 Análise do ambiente:\n"
        response += f"   Tipo: {self.environment_type}\n"
        
        for check, status in checks.items():
            emoji = "✅" if status else "❌"
            response += f"   {emoji} {check}\n"
        
        if all(checks.values()):
            response += "\n🎉 Tudo pronto! Sistema já configurado."
            return response
        
        response += "\n🚀 Vou configurar o que está faltando. Posso prosseguir?"
        return response

    def detect_environment(self):
        """Detecta tipo de ambiente"""
        
        # Verifica se está em repositório Git
        if os.path.exists('.git'):
            self.github_configured = True
            
            # Verifica se tem GitHub Actions
            if os.path.exists('.github/workflows'):
                self.environment_type = 'production'
            else:
                self.environment_type = 'development'
        else:
            self.environment_type = 'local'

    def run_environment_checks(self):
        """Executa verificações do ambiente"""
        
        checks = {}
        
        # Verifica Python
        checks['Python 3.11+'] = sys.version_info >= (3, 11)
        
        # Verifica AWS CLI
        try:
            result = subprocess.run(['aws', '--version'], capture_output=True, text=True)
            checks['AWS CLI'] = result.returncode == 0
        except:
            checks['AWS CLI'] = False
        
        # Verifica credenciais AWS
        try:
            result = subprocess.run(['aws', 'sts', 'get-caller-identity'], capture_output=True, text=True)
            self.aws_configured = result.returncode == 0
            checks['AWS Credenciais'] = self.aws_configured
        except:
            checks['AWS Credenciais'] = False
        
        # Verifica Bedrock
        if self.aws_configured:
            try:
                result = subprocess.run(['aws', 'bedrock', 'list-foundation-models', '--max-items', '1'], 
                                      capture_output=True, text=True)
                self.bedrock_available = result.returncode == 0
                checks['Bedrock Access'] = self.bedrock_available
            except:
                checks['Bedrock Access'] = False
        else:
            checks['Bedrock Access'] = False
        
        # Verifica DynamoDB tables
        if self.aws_configured:
            try:
                result = subprocess.run(['aws', 'dynamodb', 'describe-table', 
                                       '--table-name', 'ial-conversation-history'], 
                                      capture_output=True, text=True)
                self.dynamodb_ready = result.returncode == 0
                checks['DynamoDB Tables'] = self.dynamodb_ready
            except:
                checks['DynamoDB Tables'] = False
        else:
            checks['DynamoDB Tables'] = False
        
        return checks

    def continue_installation(self):
        """Continua instalação automática"""
        
        steps_completed = []
        
        # 1. Instalar dependências Python
        if not self.check_python_dependencies():
            print("📦 Instalando dependências Python...")
            if self.install_python_dependencies():
                steps_completed.append("✅ Dependências Python instaladas")
            else:
                return "❌ Erro ao instalar dependências Python. Verifique pip install boto3"
        
        # 2. Configurar AWS se necessário
        if not self.aws_configured:
            return "⚠️ AWS CLI não configurado. Execute 'aws configure' primeiro e me chame novamente."
        
        # 3. Deploy DynamoDB tables
        if not self.dynamodb_ready:
            print("🗄️ Criando tabelas DynamoDB...")
            if self.deploy_dynamodb_tables():
                steps_completed.append("✅ Tabelas DynamoDB criadas")
                self.dynamodb_ready = True
            else:
                return "❌ Erro ao criar tabelas DynamoDB. Verifique permissões."
        
        # 4. Configurar Bedrock
        if not self.bedrock_available:
            bedrock_result = self.setup_bedrock_models()
            steps_completed.append(bedrock_result)
        
        response = "🎉 Configuração concluída!\n\n"
        for step in steps_completed:
            response += f"{step}\n"
        
        response += "\n✅ Sistema IaL pronto para uso!"
        return response

    def check_python_dependencies(self):
        """Verifica dependências Python"""
        try:
            import boto3
            return True
        except ImportError:
            return False

    def install_python_dependencies(self):
        """Instala dependências Python"""
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'boto3'], check=True)
            return True
        except:
            return False

    def deploy_dynamodb_tables(self):
        """Deploy das tabelas DynamoDB"""
        try:
            result = subprocess.run([
                'aws', 'cloudformation', 'deploy',
                '--template-file', 'phases/00-foundation/07-conversation-memory.yaml',
                '--stack-name', 'ial-conversation-memory',
                '--capabilities', 'CAPABILITY_IAM'
            ], capture_output=True, text=True, timeout=300)
            
            return result.returncode == 0
        except:
            return False

    def setup_bedrock_models(self):
        """Configura modelos Bedrock"""
        try:
            # Tenta listar modelos para verificar acesso
            result = subprocess.run(['aws', 'bedrock', 'list-foundation-models'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.bedrock_available = True
                return "✅ Bedrock configurado e acessível"
            else:
                return "⚠️ Bedrock: Acesse AWS Console → Bedrock → Model access → Habilite Claude 3.5 Sonnet e Haiku"
        except:
            return "⚠️ Bedrock não disponível na região. Verifique se está em us-east-1 ou us-west-2"

    def check_system_status(self):
        """Verifica status do sistema"""
        checks = self.run_environment_checks()
        
        response = "📊 Status do Sistema IaL:\n"
        for check, status in checks.items():
            emoji = "✅" if status else "❌"
            response += f"   {emoji} {check}\n"
        
        if all(checks.values()):
            response += "\n🎉 Sistema totalmente operacional!"
        else:
            response += "\n⚠️ Algumas configurações precisam ser ajustadas."
        
        return response

    def provide_setup_guidance(self, user_input):
        """Fornece orientação baseada na entrada do usuário"""
        
        if 'help' in user_input.lower() or 'ajuda' in user_input.lower():
            return """🤖 Posso ajudar você a configurar o IaL! Diga:
            
• "Instalar tudo" - Configuro automaticamente
• "Verificar status" - Mostro o que está funcionando  
• "Configurar AWS" - Ajudo com credenciais
• "Configurar Bedrock" - Ajudo com modelos AI
• "Criar tabelas" - Configuro banco de dados
            
O que você gostaria de fazer?"""
        
        return "🤔 Não entendi. Diga 'instalar tudo' para começar ou 'ajuda' para ver opções."

    def is_setup_complete(self):
        """Verifica se setup está completo"""
        checks = self.run_environment_checks()
        # Bedrock é opcional, então não bloqueia
        required_checks = ['Python 3.11+', 'AWS CLI', 'AWS Credenciais', 'DynamoDB Tables']
        return all(checks.get(check, False) for check in required_checks)

    def start_main_system(self):
        """Inicia sistema principal"""
        try:
            from natural_language_processor import IaLNaturalProcessor
            
            processor = IaLNaturalProcessor()
            print("🧠 Sistema IaL carregado com sucesso!")
            print("Agora você pode conversar naturalmente sobre sua infraestrutura.")
            print("Digite 'sair' para encerrar.\n")
            
            while True:
                user_input = input("👤 Você: ").strip()
                
                if user_input.lower() in ['sair', 'quit', 'exit']:
                    print("👋 Obrigado por usar o IaL!")
                    break
                
                if not user_input:
                    continue
                
                response = processor.process_command(user_input, "setup-user")
                print(f"🤖 IaL: {response}")
                print()
                
        except Exception as e:
            print(f"❌ Erro ao iniciar sistema principal: {e}")
            print("Execute: python3 natural_language_processor.py interactive")

if __name__ == "__main__":
    print("🚀 IaL - Infrastructure as Language")
    print("Assistente de Instalação Inteligente")
    print("=" * 50)
    
    assistant = IaLBootstrapAssistant()
    assistant.start_conversation()
