#!/usr/bin/env python3
"""
Teste do Ctrl+L para limpar tela
"""

import os
import readline

def clear_screen():
    """Clear the terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')

# Set up readline key bindings
readline.parse_and_bind('Control-l: clear-screen')

print("🧪 Teste do Ctrl+L")
print("Digite 'clear' ou pressione Ctrl+L para limpar a tela")
print("Digite 'quit' para sair")
print()

while True:
    try:
        user_input = input("👤 Teste: ").strip()
        
        if user_input.lower() in ['quit', 'exit']:
            print("👋 Teste finalizado!")
            break
        
        if user_input.lower() in ['clear', 'cls']:
            clear_screen()
            print("🧪 Teste do Ctrl+L")
            print("Digite 'clear' ou pressione Ctrl+L para limpar a tela")
            print("Digite 'quit' para sair")
            print()
            continue
        
        print(f"Você digitou: {user_input}")
        
    except KeyboardInterrupt:
        print("\n👋 Teste finalizado!")
        break
