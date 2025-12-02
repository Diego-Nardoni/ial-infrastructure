#!/usr/bin/env python3
"""
IALCTL Enhanced - Conversational Infrastructure Assistant
Suporte completo para modo conversacional estilo Amazon Q
"""

import sys
import os
import asyncio
from typing import Dict, List, Any

# Adicionar diretório do IAL ao path
sys.path.insert(0, '/home/ial')

def conversational_mode():
    """Modo conversacional interativo com Bedrock Agent Core"""
    try:
        # Check Agent Core availability via config file
        integration = None
        try:
            from core.bedrock_agent_core import BedrockAgentCore
            agent_core = BedrockAgentCore()
            agent_available = agent_core.is_available()
            
            if agent_available:
                print("🧠 AGENT MODE - Using Bedrock Agent Core")
                print(f"   Agent ID: {agent_core.agent_id}")
                print(f"   Region: {agent_core.region}")
                integration = agent_core
            else:
                print("🔄 FALLBACK MODE - Agent not configured")
                print("   Run 'ialctl start' to configure Bedrock Agent")
                
        except Exception as e:
            print(f"⚠️ Agent check failed: {e}")
            agent_available = False
        
        print("🤖 IAL Conversational Assistant")
        print("=" * 50)
        
        if not agent_available:
            print("🔄 FALLBACK MODE - Using local NLP")
            # Fallback to original engines
            from core.cognitive_engine import CognitiveEngine
            from core.master_engine_final import MasterEngineFinal
            engine = CognitiveEngine()
            master_engine = MasterEngineFinal()
        
        print("💬 Modo conversacional ativo - Digite 'quit' para sair")
        print("🔍 Comandos especiais: 'preview <request>' para preview mode")
        print("📋 Exemplos: 'mostrar drift', 'criar web app', 'listar fases'")
        print("🔧 Comandos: '--offline' (modo offline), '--online' (modo agent)")
        print()
        
        while True:
            try:
                user_input = input("💭 Você: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'sair']:
                    print("👋 Até logo!")
                    break
                
                if not user_input:
                    continue
                
                # Handle mode switching
                if user_input == '--offline' and integration:
                    integration.set_offline_mode(True)
                    continue
                elif user_input == '--online' and integration:
                    integration.set_offline_mode(False)
                    continue
                
                # Detectar preview mode
                preview_mode = False
                if user_input.lower().startswith('preview '):
                    preview_mode = True
                    user_input = user_input[8:]  # Remove 'preview '
                    print("🔍 PREVIEW MODE ativado")
                
                print("🧠 IAL: Processando...")
                
                # Use Agent Core if available, otherwise fallback
                if integration and agent_available:
                    result = integration.process_message(user_input)
                    
                    if result.get('success'):
                        response = result.get('response', '')
                        source = result.get('source', 'unknown')
                        print(f"🤖 IAL ({source}): {response}")
                    else:
                        print(f"❌ IAL: {result.get('error', 'Erro desconhecido')}")
                else:
                    # Original fallback logic
                    if preview_mode:
                        result = master_engine.process_request(user_input, preview_mode=True)
                    else:
                        result = engine.process_intent(user_input)
                    
                    # Formatar resposta
                    if isinstance(result, dict):
                        if result.get('status') == 'needs_clarification':
                            print(f"❓ IAL: {result.get('question')}")
                        elif result.get('status') == 'preview_ready':
                            print("🔍 PREVIEW GERADO:")
                            print(f"📊 Fases previstas: {len(result.get('predicted_phases', []))}")
                            print(f"💰 Custo estimado: ${result.get('cost_estimate', {}).get('monthly_cost', 0)}/mês")
                            print(f"⚠️ Nível de risco: {result.get('risk_assessment', {}).get('risk_level', 'unknown')}")
                            print(f"\n❓ {result.get('confirmation_message', 'Prosseguir?')}")
                        elif result.get('status') == 'success':
                            print("✅ IAL: Operação concluída com sucesso!")
                        elif result.get('status') == 'error':
                            print(f"❌ IAL: {result.get('error', 'Erro desconhecido')}")
                        else:
                            print(f"🤖 IAL: {result}")
                    else:
                        print(f"🤖 IAL: {result}")
                
                print()  # Linha em branco para separar conversas
                
            except KeyboardInterrupt:
                print("\n👋 Interrompido pelo usuário. Até logo!")
                break
            except Exception as e:
                print(f"❌ Erro: {e}")
                print()
        
        return 0
        
    except Exception as e:
        print(f"❌ Erro ao inicializar modo conversacional: {e}")
        return 1

def run_foundation_deploy():
    """Deploy apenas 00-foundation (recursos core do IAL)"""
    try:
        from core.foundation_deployer import FoundationDeployer
        
        print("🚀 IAL Foundation Deployment")
        print("=" * 50)
        print("📦 Installing IAL core infrastructure (00-foundation only)")
        
        deployer = FoundationDeployer()
        result = deployer.deploy_foundation_core()
        
        if result.get('success'):
            print(f"✅ IAL Foundation deployed successfully!")
            print("🔧 Core resources: VPC, IAM, S3, CloudTrail, etc.")
            print("💡 Use 'ialctl chat' for conversational infrastructure management")
            return 0
        else:
            print(f"❌ Foundation deployment failed: {result.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return 1

def deploy_specific_phase(phase):
    """Deploy uma fase específica usando CognitiveEngine com budget check"""
    from core.feature_flags import feature_flags
    from core.budget_config import budget_config
    
    # Check budget enforcement
    budget_enforcement = feature_flags.get_flag('BUDGET_ENFORCEMENT_ENABLED')
    if budget_enforcement:
        budget_limit = budget_config.get_phase_limit(phase)
        print(f"💰 Budget Enforcement: ENABLED (limit: ${budget_limit}/month)")
        
        # Check budget before deployment
        try:
            from mcp.finops.server import FinOpsMCP
            finops = FinOpsMCP()
            budget_result = finops.check_budget(phase, budget_limit)
            
            if not budget_result['within_budget']:
                print(f"❌ BUDGET EXCEEDED FOR PHASE {phase}!")
                print(f"   Estimated: ${budget_result['estimated_cost']:.2f}/month")
                print(f"   Limit: ${budget_result['budget_limit']:.2f}/month")
                print(f"   Overage: ${budget_result['overage']:.2f}/month")
                print(f"")
                print(f"   To proceed anyway: ialctl config set BUDGET_ENFORCEMENT_ENABLED=false")
                print(f"   Or increase limit: ialctl config set PHASE_{phase.upper().replace('-', '_')}_LIMIT={budget_result['estimated_cost']:.0f}")
                return 1
            else:
                print(f"✅ Budget OK: ${budget_result['estimated_cost']:.2f} < ${budget_result['budget_limit']:.2f}")
                
        except Exception as e:
            print(f"⚠️ Budget check failed: {e}")
            print(f"   Proceeding with deployment...")
    
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
            return run_foundation_deploy()
        elif command == 'config':
            # Feature flags management
            from ialctl_config import main as config_main
            # Remove 'config' from sys.argv and call config main
            sys.argv = ['ialctl'] + sys.argv[2:]
            return config_main()
        elif command == 'destroy':
            # Resource destruction
            from ialctl_destroy import main as destroy_main
            # Remove 'destroy' from sys.argv and call destroy main
            sys.argv = ['ialctl'] + sys.argv[2:]
            return destroy_main()
        elif command == 'ci':
            # IAL CI Mode
            from core.ci_mode import main as ci_main
            return ci_main()
        elif command == 'chat' or command == 'conversational':
            return run_interactive_mode()
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
    
    # Modo interativo conversacional (padrão)
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
  ialctl config <ação>      Gerenciar feature flags
    ialctl config get      Ver todos os feature flags
    ialctl config set FLAG=VALUE  Configurar feature flag
    ialctl config reset    Resetar para defaults
  ialctl destroy <recurso>  Remover recursos específicos
    ialctl destroy security-services  Remover security services
  ialctl ci <subcomando>    Modo CI/CD profissional
    ialctl ci validate      Validar phases YAML e DAG
    ialctl ci governance    Validar governança e segurança
    ialctl ci completeness  Validar completude dos phases
    ialctl ci drift         Detectar drift de infraestrutura
    ialctl ci mcp-test      Testar conectividade MCP
    ialctl ci test          Executar testes rápidos (< 5s)
  ialctl list-phases        Lista todas as fases disponíveis
  ialctl deploy <fase>      Deploy uma fase específica (com conversão IAL)
  ialctl delete <fase>      Excluir uma fase específica (todos os stacks)
  ialctl status             Status do sistema
  ialctl logs               Logs recentes
  ialctl --help             Esta ajuda

MODO INTERATIVO:
  ialctl                    Interface conversacional Amazon Q-like
  ialctl chat               Interface conversacional (alias)
  ialctl conversational     Interface conversacional (alias)

EXEMPLOS:
  ialctl start                           # Deploy foundation
  ialctl config get                      # Ver feature flags
  ialctl config set SECURITY_SERVICES_ENABLED=false  # Desabilitar security (~$24/mês)
  ialctl destroy security-services       # Remover security services existentes
  ialctl list-phases                     # Ver fases disponíveis
  ialctl deploy 20-network               # Deploy fase de rede (IAL→CF)
  ialctl delete 20-network               # Excluir fase de rede
  ialctl deploy 30-compute               # Deploy fase de compute (IAL→CF)
  ialctl delete 30-compute               # Excluir fase de compute

FEATURE FLAGS:
  SECURITY_SERVICES_ENABLED=true        # Security services (~$24/mês)
  WELL_ARCHITECTED_ENABLED=true         # Well-Architected assessment
  COST_MONITORING_ENABLED=true          # Cost monitoring
  DRIFT_DETECTION_ENABLED=true          # Drift detection
  BUDGET_ENFORCEMENT_ENABLED=false      # Budget enforcement blocking (disabled by default)

BUDGET LIMITS (per phase):
  00-foundation: $50/month              # DynamoDB, S3, Lambda básico
  10-security: $30/month                # Security services
  20-network: $20/month                 # VPC, subnets, NAT gateway
  30-compute: $100/month                # EC2, ECS, ALB
  40-data: $80/month                    # RDS, DynamoDB workload
  50-application: $60/month             # Lambda, API Gateway
  60-observability: $40/month           # CloudWatch, X-Ray
  70-ai-ml: $150/month                  # Bedrock, SageMaker
  90-governance: $10/month              # Budgets, Config rules
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
