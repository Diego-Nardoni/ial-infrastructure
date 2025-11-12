#!/usr/bin/env python3
"""
IALCTL Complete - CLI unificado com interface conversacional
Integra todos os engines: Query + Provisioning + Observabilidade + Segurança
"""

import asyncio
import argparse
import sys
from typing import Dict, Optional

class IALCTLComplete:
    """CLI completo do IAL com interface conversacional"""
    
    def __init__(self):
        self.master_engine = None
        self._initialize_master_engine()
    
    def _initialize_master_engine(self):
        """Inicializar Master Engine"""
        try:
            from core.ial_master_engine_complete import IALMasterEngineComplete
            self.master_engine = IALMasterEngineComplete()
            print("✅ IAL Master Engine inicializado")
        except ImportError as e:
            print(f"❌ Erro ao inicializar Master Engine: {e}")
            sys.exit(1)
    
    async def run_conversational_mode(self):
        """Executar modo conversacional (padrão)"""
        
        print("🤖 **IAL Assistant - Interface Conversacional**")
        print("Capacidades: Query + Provisioning + Observabilidade + Segurança")
        print("Digite 'help' para ajuda, 'quit' para sair\n")
        
        # Mostrar status inicial
        await self._show_initial_status()
        
        while True:
            try:
                user_input = input("IAL> ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'sair']:
                    print("👋 Até logo!")
                    break
                
                if user_input.lower() in ['help', 'ajuda']:
                    await self._show_help()
                    continue
                
                if user_input.lower() == 'status':
                    await self._show_system_status()
                    continue
                
                if user_input:
                    # Processar via Master Engine
                    response = await self.master_engine.process_user_input(user_input)
                    print(f"\n{response}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Até logo!")
                break
            except Exception as e:
                print(f"❌ Erro: {e}")
    
    async def _show_initial_status(self):
        """Mostrar status inicial do sistema"""
        
        status = self.master_engine.get_capabilities_status()
        active_engines = sum(1 for engine in status["engines_status"].values() if engine)
        active_orchestrators = sum(1 for orch in status["orchestrators_status"].values() if orch)
        
        print(f"📊 **Sistema:** {active_engines}/5 engines ativos, {active_orchestrators}/3 orquestradores")
        print("🚀 **Pronto para uso!**\n")
    
    async def _show_help(self):
        """Mostrar ajuda detalhada"""
        
        help_text = """
🤖 **IAL Assistant - Guia de Uso**

**📊 CONSULTAS (Query):**
• "liste todos os buckets" - Listar recursos S3
• "quantas EC2 eu tenho" - Contar instâncias EC2  
• "qual o custo atual" - Análise de custos
• "status dos recursos" - Visão geral

**🚀 PROVISIONING:**
• "quero ECS com Redis" - Criar infraestrutura
• "criar VPC privada" - Provisionar rede
• "deploy aplicação serverless" - Lambda + API Gateway

**📈 OBSERVABILIDADE:**
• "análise de performance" - Métricas CPU/memória
• "verificar logs de erro" - Análise de logs
• "métricas CloudWatch" - Monitoramento detalhado

**🛡️ SEGURANÇA:**
• "análise de login" - Segurança de autenticação
• "verificar ameaças" - Detecção de brute force
• "audit cloudtrail" - Análise de eventos

**🔍 TROUBLESHOOTING:**
• "por que está lento?" - Diagnóstico de performance
• "debug aplicação" - Análise de problemas
• "problema de conexão" - Troubleshooting de rede

**💰 OTIMIZAÇÃO DE CUSTOS:**
• "como reduzir custos?" - Recomendações de economia
• "otimizar recursos" - Rightsizing automático
• "anomalias de custo" - Detecção de picos

**⚙️ COMANDOS ESPECIAIS:**
• "status" - Status do sistema
• "help" - Esta ajuda
• "quit" - Sair

💡 **Dica:** Seja natural! O IAL entende linguagem conversacional.
"""
        print(help_text)
    
    async def _show_system_status(self):
        """Mostrar status detalhado do sistema"""
        
        status = self.master_engine.get_capabilities_status()
        
        print("\n📊 **Status Detalhado do Sistema:**")
        
        print("\n🔧 **Engines:**")
        engines = status["engines_status"]
        print(f"• Query Engine: {'✅ Ativo' if engines['query_engine'] else '❌ Inativo'}")
        print(f"• Conversational Engine: {'✅ Ativo' if engines['conversational_engine'] else '❌ Inativo'}")
        print(f"• CloudWatch Analyzer: {'✅ Ativo' if engines['cloudwatch_analyzer'] else '❌ Inativo'}")
        print(f"• Security Analyzer: {'✅ Ativo' if engines['security_analyzer'] else '❌ Inativo'}")
        print(f"• Response Formatter: {'✅ Ativo' if engines['response_formatter'] else '❌ Inativo'}")
        
        print("\n🔄 **Orquestradores:**")
        orchestrators = status["orchestrators_status"]
        print(f"• Step Functions: {'✅ Ativo' if orchestrators['stepfunctions'] else '❌ Inativo'}")
        print(f"• MCP-First: {'✅ Ativo' if orchestrators['mcp_first'] else '❌ Inativo'}")
        print(f"• Python: {'✅ Ativo' if orchestrators['python'] else '❌ Inativo'}")
        
        print("\n💬 **Contexto:**")
        print(f"• Conversation Context: {'✅ Ativo' if status['conversation_context'] else '❌ Inativo'}")
        
        print("\n🎯 **Capacidades Disponíveis:**")
        capabilities = status["capabilities"]
        for capability, active in capabilities.items():
            status_icon = "✅" if active else "❌"
            print(f"• {capability.replace('_', ' ').title()}: {status_icon}")

def main():
    """Função principal do CLI"""
    
    parser = argparse.ArgumentParser(
        description="IAL Complete - Interface conversacional para AWS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Modo interativo (padrão)
  python ialctl_complete.py

  # Query única
  python ialctl_complete.py query "liste todos os buckets"

  # Status do sistema
  python ialctl_complete.py status
        """
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="IAL Complete v1.0.0"
    )
    
    # Inicializar CLI
    cli = IALCTLComplete()
    
    # Executar modo interativo
    try:
        asyncio.run(cli.run_conversational_mode())
        return 0
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
