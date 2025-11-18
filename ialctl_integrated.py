#!/usr/bin/env python3
"""
IALCTL Enhanced - Wrapper mínimo para o natural_language_processor funcional
Mantém TODAS as funcionalidades existentes sem modificações
"""

import sys
import os
import argparse

# Adicionar diretório do IAL ao path
sys.path.insert(0, '/home/ial')

def main():
    """Main entry point - wrapper para o natural_language_processor"""
    
    # Se comando 'start', usar o natural_language_processor com 'start'
    if len(sys.argv) > 1 and sys.argv[1] == 'start':
        # Importar e executar o processador com comando start
        from natural_language_processor import main as nlp_main
        # Modificar sys.argv temporariamente
        original_argv = sys.argv[:]
        sys.argv = ['natural_language_processor.py', 'start']
        try:
            nlp_main()
        finally:
            sys.argv = original_argv
        return
    
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
    main()
