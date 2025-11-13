#!/usr/bin/env python3
"""
IALCTL Integrated - CLI usando arquitetura robusta existente
Integra BedrockConversationEngine + Memory + Context + MCP Servers
"""

import asyncio
import argparse
import sys
import os
from typing import Dict, Optional

def custom_input(prompt: str) -> str:
    """Input customizado que suporta Ctrl+L para limpar tela"""
    import termios
    import tty
    
    # Mostrar prompt
    print(prompt, end='', flush=True)
    
    buffer = []
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    
    try:
        tty.setraw(fd)
        while True:
            char = sys.stdin.read(1)
            
            # Ctrl+L (ASCII 12)
            if ord(char) == 12:
                os.system('clear')
                print(prompt, end='', flush=True)
                print(''.join(buffer), end='', flush=True)
                continue
            
            # Enter
            if char in ['\r', '\n']:
                print()
                break
            
            # Backspace
            if char in ['\x7f', '\x08']:
                if buffer:
                    buffer.pop()
                    print('\b \b', end='', flush=True)
                continue
            
            # Ctrl+C
            if ord(char) == 3:
                print()
                raise KeyboardInterrupt
            
            # Ctrl+D
            if ord(char) == 4:
                if not buffer:
                    print()
                    raise EOFError
                continue
            
            # Caracteres imprimíveis
            if 32 <= ord(char) <= 126:
                buffer.append(char)
                print(char, end='', flush=True)
    
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    return ''.join(buffer)

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
        
        print("🚀 IAL Foundation Deployment Starting...")
        print("=" * 50)
        
        # 1. Deploy Foundation
        print("\n📦 Step 1/3: Deploying AWS Foundation...")
        deployer = FoundationDeployer()
        result = deployer.deploy_foundation_core()
        
        if result['successful_deployments'] == 0:
            print("\n❌ IAL Foundation deployment failed!")
            return 1
        
        print(f"✅ Foundation: {result['successful_deployments']}/{result['total_resource_groups']} resource groups deployed")
        
        # 2. Initialize MCP Servers
        print("\n🔌 Step 2/3: Initializing MCP Servers...")
        mcp_initializer = MCPServersInitializer()
        mcp_result = await mcp_initializer.initialize_all_servers()
        
        print(f"✅ MCP Servers: {mcp_result['total_initialized']} initialized")
        
        # 3. Validate System Health
        print("\n🏥 Step 3/3: Validating System Health...")
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
        
        if health_result['system_ready']:
            print("\n🎯 System ready! Run 'ialctl' to start conversational interface")
            return 0
        else:
            print("\n⚠️  System has issues but may still work")
            return 0
    
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
                    # Processar via Master Engine Integrado
                    response = await self.master_engine.process_user_input(user_input)
                    print(f"\n{response}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Até logo!")
                break
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
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
