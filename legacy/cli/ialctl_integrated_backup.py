#!/usr/bin/env python3
"""
IALCTL Enhanced - Baseado no natural_language_processor funcional
Mantém todas as funcionalidades originais + interface conversacional
"""

import sys
import os
import argparse
import asyncio

# Adicionar diretório do IAL ao path
sys.path.insert(0, '/home/ial')

# Importar o processador funcional
from natural_language_processor import NaturalLanguageProcessor

class IALCTLEnhanced:
    def __init__(self):
        self.processor = NaturalLanguageProcessor()
        
    async def run_start_command(self):
        """Executar comando 'start' - deploy da foundation"""
        from core.foundation_deployer import FoundationDeployer
        
        print("🚀 IAL Foundation Deployment Starting (Enhanced)...")
        print("=" * 50)
        
        # Usar foundation deployer existente
        deployer = FoundationDeployer()
        try:
            result = await deployer.deploy_all_phases()
            if result.get('success'):
                print("✅ Foundation deployment completed successfully!")
                return 0
            else:
                print(f"❌ Foundation deployment failed: {result.get('error')}")
                return 1
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            return 1

    def run_conversational_interface(self):
        """Executar interface conversacional usando o processador funcional"""
        import readline
        
        # Configurar readline
        def clear_screen():
            os.system('clear' if os.name == 'posix' else 'cls')
        
        readline.parse_and_bind('Control-l: clear-screen')
        
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
                
                # Usar o processador funcional original
                response = self.processor.process_command(user_input)
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
        
        return 0

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="IALCTL Enhanced - IAL Infrastructure Assistant")
    parser.add_argument(
        "command",
        nargs="?",
        choices=["start"],
        help="Comando a executar: 'start' para deploy da foundation"
    )
    
    args = parser.parse_args()
    
    cli = IALCTLEnhanced()
    
    try:
        if args.command == "start":
            return asyncio.run(cli.run_start_command())
        else:
            # Abrir interface conversacional
            return cli.run_conversational_interface()
    except KeyboardInterrupt:
        print("\n⚠️  Operação cancelada pelo usuário")
        return 1
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
