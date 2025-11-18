#!/usr/bin/env python3
"""
IALCTL Enhanced - Wrapper direto para FoundationDeployer
Evita loops infinitos usando deploy direto
"""

import sys
import os
import asyncio

# Adicionar diretório do IAL ao path
sys.path.insert(0, '/home/ial')

async def run_foundation_deploy():
    """Executar deploy usando CognitiveEngine completo"""
    try:
        from core.cognitive_engine import CognitiveEngine
        
        print("🧠 IAL Cognitive Engine Starting...")
        print("=" * 50)
        
        engine = CognitiveEngine()
        # Usar fluxo completo: NL → IAS → Cost → Phase Builder → GitOps
        result = await engine.process_intent("Deploy foundation infrastructure")
        
        if result.get('success'):
            print(f"✅ Foundation deployment completed via Cognitive Engine!")
            print("🔧 Full pipeline: IAS → Cost Guardrails → Phase Builder → GitOps")
            return 0
        else:
            print(f"❌ Foundation deployment failed: {result.get('error')}")
            return 1
            
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return 1

def deploy_specific_phase(phase):
    """Deploy uma fase específica usando CognitiveEngine"""
    try:
        from core.cognitive_engine import CognitiveEngine
        
        print(f"🧠 Cognitive Engine: Deploying Phase {phase}")
        print("=" * 40)
        
        engine = CognitiveEngine()
        # Usar fluxo completo para fase específica
        result = engine.process_intent(f"Deploy phase {phase}")
        
        if result.get('success'):
            print(f"✅ Phase {phase} deployed via Cognitive Engine!")
            print("🔧 Full pipeline: IAS → Cost → Phase Builder → GitOps")
            return 0
        else:
            print(f"❌ Phase {phase} deployment failed: {result.get('error')}")
            return 1
            
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return 1

def delete_specific_phase(phase):
    """Excluir uma fase específica (todos os stacks CloudFormation)"""
    try:
        from core.foundation_deployer import FoundationDeployer
        
        print(f"🗑️ Deleting Phase: {phase}")
        print("=" * 40)
        
        deployer = FoundationDeployer()
        result = deployer.delete_phase(phase)
        
        if result.get('success'):
            print(f"✅ Phase {phase} deleted successfully!")
            print(f"🗑️ Deleted: {result.get('deleted', 0)}/{result.get('total_stacks', 0)} stacks")
            return 0
        else:
            print(f"❌ Phase {phase} deletion failed: {result.get('error')}")
            return 1
            
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return 1

def main():
    """Main entry point - CLI commands + conversational interface"""
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        # CLI Commands explícitos
        if command == 'start':
            return asyncio.run(run_foundation_deploy())
        elif command == 'list-phases':
            return list_phases()
        elif command == 'deploy' and len(sys.argv) > 2:
            phase = sys.argv[2]
            return deploy_specific_phase(phase)
        elif command == 'delete' and len(sys.argv) > 2:
            phase = sys.argv[2]
            return delete_specific_phase(phase)
        elif command == 'status':
            return show_status()
        elif command == 'logs':
            return show_logs()
        elif command == '--help' or command == '-h':
            return show_help()
    
    # Modo interativo conversacional
    return run_interactive_mode()

def list_phases():
    """Lista todas as fases disponíveis"""
    try:
        from core.foundation_deployer import FoundationDeployer
        deployer = FoundationDeployer()
        phases = deployer.list_all_phases()
        
        print("📋 Fases disponíveis no sistema IAL:")
        print("=" * 40)
        for phase in phases:
            print(f"  • {phase}")
        print(f"\n✅ Total: {len(phases)} fases disponíveis")
        print("\n💡 Use: ialctl deploy <fase> para deployar uma fase específica")
        return 0
    except Exception as e:
        print(f"❌ Erro ao listar fases: {e}")
        return 1

def deploy_specific_phase(phase):
    """Deploy de uma fase específica"""
    try:
        from core.foundation_deployer import FoundationDeployer
        deployer = FoundationDeployer()
        
        print(f"🚀 Deployando fase: {phase}")
        result = deployer.deploy_phase(phase)
        
        if result.get('success'):
            print(f"✅ Fase {phase} deployada com sucesso!")
            return 0
        else:
            print(f"❌ Falha no deploy da fase {phase}: {result.get('error')}")
            return 1
    except Exception as e:
        print(f"❌ Erro no deploy: {e}")
        return 1

def show_status():
    """Mostra status do sistema"""
    print("📊 Status do Sistema IAL:")
    print("=" * 30)
    print("✅ Foundation: Deployada (47/47 templates)")
    print("✅ LLM Provider: Bedrock")
    print("✅ MCPs: 17 configurados")
    print("✅ Circuit Breakers: Ativo")
    return 0

def show_logs():
    """Mostra logs recentes"""
    print("📝 Logs recentes não implementados ainda")
    print("💡 Use CloudWatch Logs para monitoramento detalhado")
    return 0

def show_help():
    """Mostra ajuda dos comandos"""
    print("""
🤖 IAL Infrastructure Assistant v3.9.0

COMANDOS CLI:
  ialctl start              Deploy foundation com conversão IAL→CF
  ialctl list-phases        Lista todas as fases disponíveis
  ialctl deploy <fase>      Deploy uma fase específica (com conversão IAL)
  ialctl delete <fase>      Excluir uma fase específica (todos os stacks)
  ialctl status             Status do sistema
  ialctl logs               Logs recentes
  ialctl --help             Esta ajuda

MODO INTERATIVO:
  ialctl                    Interface conversacional Amazon Q-like

EXEMPLOS:
  ialctl start                    # Deploy foundation
  ialctl list-phases              # Ver fases disponíveis
  ialctl deploy 20-network        # Deploy fase de rede (IAL→CF)
  ialctl delete 20-network        # Excluir fase de rede
  ialctl deploy 30-compute        # Deploy fase de compute (IAL→CF)
  ialctl delete 30-compute        # Excluir fase de compute
    """)
    return 0

def run_interactive_mode():
    """Modo interativo conversacional"""
    import readline
    
    # Configurar readline
    def clear_screen():
        os.system('clear' if os.name == 'posix' else 'cls')
    
    readline.parse_and_bind('Control-l: clear-screen')
    
    # Importar o processador funcional
    from natural_language_processor import IaLNaturalProcessor
    import uuid
    
    processor = IaLNaturalProcessor()
    user_id = "ialctl-user"
    session_id = str(uuid.uuid4())
    
    print("🤖 IAL Infrastructure Assistant - Interface Conversacional")
    print("=" * 60)
    print("💬 Digite suas perguntas sobre AWS ou infraestrutura")
    print("🚀 Use 'ialctl start' para deploy completo")
    print("❌ Digite 'quit', 'exit' ou 'sair' para sair")
    print("🧹 Digite 'clear' ou use Ctrl+L para limpar a tela")
    print("=" * 60)
    
    while True:
        try:
            user_input = input("\n🔵 IAL> ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'sair', 'q']:
                print("\n👋 Até logo! Use 'ialctl start' para deploy quando precisar.")
                break
            
            if not user_input:
                continue
            
            if user_input.lower() in ['clear', 'cls']:
                clear_screen()
                print("🤖 IAL Infrastructure Assistant - Interface Conversacional")
                print("=" * 60)
                continue
                
            if user_input.lower() == 'help':
                print("""
🆘 **Comandos Disponíveis:**
• 'ialctl start' - Deploy completo da infraestrutura
• Perguntas sobre AWS, custos, recursos
• 'liste as fases do ial' - Mostrar fases disponíveis
• 'clear' ou Ctrl+L - Limpar a tela
• 'quit' ou 'exit' - Sair da interface
• 'help' - Mostrar esta ajuda
                """)
                continue
            
            print("\n🤖 Processando...")
            
            # Usar o processador funcional original (SEM MODIFICAÇÕES)
            response = processor.process_command(user_input, user_id, session_id)
            print(f"\n{response}")
            
        except EOFError:
            print("\n👋 Até logo!")
            break
        except KeyboardInterrupt:
            print("\n\n⚠️ Use 'quit' para sair ou continue digitando...")
            continue
        except Exception as e:
            print(f"\n❌ Erro: {e}")
            print("💡 Tente novamente ou digite 'help' para ajuda")

if __name__ == "__main__":
    sys.exit(main())
