#!/usr/bin/env python3
"""
IAL CLI Unificado - Interface de linha de comando seguindo arquitetura completa
Implementa comando: ialctl plan "intenção"
"""

import sys
import os
import argparse
from typing import Dict, Any

# Add core path
sys.path.append(os.path.dirname(__file__))

try:
    from core.ial_orchestrator import IALOrchestrator
except ImportError:
    IALOrchestrator = None

try:
    from core.master_engine_final import MasterEngineFinal
except ImportError:
    MasterEngineFinal = None

class IALCLIUnified:
    """CLI unificado seguindo arquitetura IAL"""
    
    def __init__(self):
        # Inicializar componentes disponíveis
        if IALOrchestrator:
            try:
                self.orchestrator = IALOrchestrator()
                self.orchestrator_available = True
            except Exception as e:
                print(f"⚠️ Orchestrator não disponível: {e}")
                self.orchestrator = None
                self.orchestrator_available = False
        else:
            self.orchestrator = None
            self.orchestrator_available = False
            
        if MasterEngineFinal:
            try:
                self.master_engine = MasterEngineFinal()
                self.master_engine_available = True
            except Exception as e:
                print(f"⚠️ Master Engine não disponível: {e}")
                self.master_engine = None
                self.master_engine_available = False
        else:
            self.master_engine = None
            self.master_engine_available = False
    
    def main(self):
        """Entry point principal"""
        parser = argparse.ArgumentParser(
            description='IAL Infrastructure Assistant - Unified CLI',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Exemplos:
  ialctl plan "Quero um ECS privado com Redis e DNS público"
  ialctl query "liste meus buckets s3"
  ialctl chat "como otimizar custos?"
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')
        
        # Comando PLAN - Arquitetura completa
        plan_parser = subparsers.add_parser('plan', help='Planejar infraestrutura')
        plan_parser.add_argument('intent', help='Intenção de infraestrutura em linguagem natural')
        
        # Comando QUERY - Consultas rápidas
        query_parser = subparsers.add_parser('query', help='Consultar recursos existentes')
        query_parser.add_argument('query', help='Consulta em linguagem natural')
        
        # Comando CHAT - Conversacional
        chat_parser = subparsers.add_parser('chat', help='Conversa casual')
        chat_parser.add_argument('message', help='Mensagem conversacional')
        
        # Comando STATUS - Status do sistema
        status_parser = subparsers.add_parser('status', help='Status dos componentes')
        
        # Parse arguments
        if len(sys.argv) == 1:
            parser.print_help()
            return
            
        args = parser.parse_args()
        
        # Roteamento de comandos
        if args.command == 'plan':
            self.handle_plan_command(args.intent)
        elif args.command == 'query':
            self.handle_query_command(args.query)
        elif args.command == 'chat':
            self.handle_chat_command(args.message)
        elif args.command == 'status':
            self.handle_status_command()
        else:
            parser.print_help()
    
    def handle_plan_command(self, intent: str):
        """Comando PLAN - Arquitetura completa IAL"""
        print("🧠 interpretando intenção...")
        
        try:
            if self.orchestrator_available:
                # Usar orquestrador completo para infraestrutura
                result = self.orchestrator.process_nl_intent(intent)
                
                if result.get('status') == 'success':
                    print(result.get('response', 'Processado com sucesso'))
                else:
                    print(f"❌ Erro: {result.get('response', 'Erro desconhecido')}")
            
            elif self.master_engine_available:
                # Fallback para master engine
                print("🔄 Usando Master Engine (fallback)")
                result = self.master_engine.process_request(intent)
                response = result.get('response', 'Processado com sucesso')
                print(response)
            
            else:
                print("❌ Nenhum engine disponível")
                
        except Exception as e:
            print(f"❌ Erro no processamento: {e}")
    
    def handle_query_command(self, query: str):
        """Comando QUERY - Consultas rápidas via master engine"""
        try:
            if self.master_engine_available:
                # Usar master engine para consultas rápidas
                result = self.master_engine.process_request(query)
                response = result.get('response', 'Processado com sucesso')
                print(response)
            else:
                print("❌ Master Engine não disponível para consultas")
                
        except Exception as e:
            print(f"❌ Erro na consulta: {e}")
    
    def handle_chat_command(self, message: str):
        """Comando CHAT - Conversacional via master engine"""
        try:
            if self.master_engine_available:
                # Usar master engine para conversas
                result = self.master_engine.process_conversation(
                    message, 
                    user_id="cli_user", 
                    session_id="cli_session"
                )
                response = result.get('response', 'Processado com sucesso')
                print(response)
            else:
                print("❌ Master Engine não disponível para conversas")
                
        except Exception as e:
            print(f"❌ Erro na conversa: {e}")
    
    def handle_status_command(self):
        """Comando STATUS - Status dos componentes"""
        print("📊 Status dos Componentes IAL")
        print("=" * 40)
        
        # Status do Orchestrator
        if self.orchestrator_available:
            print("✅ IAL Orchestrator: Disponível")
            if hasattr(self.orchestrator, 'ias_available'):
                print(f"  ├─ IAS: {'✅ OK' if self.orchestrator.ias_available else '❌ Indisponível'}")
            if hasattr(self.orchestrator, 'cost_available'):
                print(f"  ├─ Cost Guardrails: {'✅ OK' if self.orchestrator.cost_available else '❌ Indisponível'}")
            if hasattr(self.orchestrator, 'phase_available'):
                print(f"  ├─ Phase Builder: {'✅ OK' if self.orchestrator.phase_available else '❌ Indisponível'}")
            if hasattr(self.orchestrator, 'github_available'):
                print(f"  ├─ GitHub Integration: {'✅ OK' if self.orchestrator.github_available else '❌ Indisponível'}")
            if hasattr(self.orchestrator, 'drift_available'):
                print(f"  └─ Drift Detection: {'✅ OK' if self.orchestrator.drift_available else '❌ Indisponível'}")
        else:
            print("❌ IAL Orchestrator: Indisponível")
        
        # Status do Master Engine
        if self.master_engine_available:
            print("✅ Master Engine: Disponível (fallback)")
        else:
            print("❌ Master Engine: Indisponível")
        
        print("=" * 40)

def main():
    """Entry point para ialctl"""
    cli = IALCLIUnified()
    cli.main()

if __name__ == "__main__":
    main()
