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
    """Executar deploy APENAS da foundation (00-foundation)"""
    try:
        from core.foundation_deployer import FoundationDeployer
        
        print("🚀 IAL Foundation Deployment Starting...")
        print("=" * 50)
        
        deployer = FoundationDeployer()
        # Deploy APENAS a fase 00-foundation
        result = deployer.deploy_phase("00-foundation")
        
        if result.get('success'):
            print(f"✅ Foundation deployment completed successfully!")
            print(f"📊 Deployed: {result.get('successful', 0)}/{result.get('total_resources', 0)} templates")
            print("\n💡 Para outras fases, use comandos de linguagem natural:")
            print("   • 'criar rede VPC privada' → fase 20-network")
            print("   • 'provisionar ECS cluster' → fase 30-compute") 
            print("   • 'configurar RDS Aurora' → fase 40-data")
            return 0
        else:
            print(f"❌ Foundation deployment failed: {result.get('error')}")
            return 1
            
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return 1

def main():
    """Main entry point - deploy direto sem loops"""
    
    # Se comando 'start', usar FoundationDeployer diretamente
    if len(sys.argv) > 1 and sys.argv[1] == 'start':
        return asyncio.run(run_foundation_deploy())
    
    # Caso contrário, modo interativo
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
