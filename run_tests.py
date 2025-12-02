#!/usr/bin/env python3
"""
Script para executar testes do IAL
"""
import subprocess
import sys
import os
import argparse

def run_command(cmd, description):
    """Executa comando e mostra resultado"""
    print(f"\n🔄 {description}")
    print(f"Comando: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        if result.returncode == 0:
            print(f"✅ {description} - SUCESSO")
        else:
            print(f"❌ {description} - FALHOU (código: {result.returncode})")
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT")
        return False
    except Exception as e:
        print(f"💥 {description} - ERRO: {e}")
        return False

def install_pytest():
    """Instala pytest se não estiver disponível"""
    try:
        import pytest
        print("✅ pytest já instalado")
        return True
    except ImportError:
        print("📦 Instalando pytest...")
        return run_command([sys.executable, "-m", "pip", "install", "pytest", "pytest-cov"], "Instalação do pytest")

def main():
    parser = argparse.ArgumentParser(description="Executar testes do IAL")
    parser.add_argument("category", nargs="?", default="all", 
                       choices=["all", "unit", "integration", "e2e", "quick"],
                       help="Categoria de testes para executar")
    parser.add_argument("--coverage", action="store_true", help="Executar com cobertura")
    parser.add_argument("--verbose", "-v", action="store_true", help="Modo verboso")
    
    args = parser.parse_args()
    
    # Verificar se estamos no diretório correto
    if not os.path.exists("tests"):
        print("❌ Diretório 'tests' não encontrado. Execute no diretório raiz do IAL.")
        sys.exit(1)
    
    # Instalar pytest
    if not install_pytest():
        print("❌ Falha ao instalar pytest")
        sys.exit(1)
    
    success_count = 0
    total_count = 0
    
    # Configurar comandos pytest
    base_cmd = [sys.executable, "-m", "pytest"]
    if args.verbose:
        base_cmd.append("-v")
    if args.coverage:
        base_cmd.extend(["--cov=.", "--cov-report=term-missing"])
    
    # Executar testes baseado na categoria
    if args.category == "all":
        tests_to_run = [
            ("tests/unit/", "Testes Unitários"),
            ("tests/integration/", "Testes de Integração"),
            ("tests/e2e/", "Testes End-to-End")
        ]
    elif args.category == "quick":
        tests_to_run = [
            ("tests/unit/", "Testes Unitários (Quick)")
        ]
    else:
        tests_to_run = [
            (f"tests/{args.category}/", f"Testes {args.category.title()}")
        ]
    
    # Executar cada categoria de teste
    for test_path, description in tests_to_run:
        if os.path.exists(test_path):
            cmd = base_cmd + [test_path]
            if run_command(cmd, description):
                success_count += 1
            total_count += 1
        else:
            print(f"⚠️ Diretório {test_path} não encontrado, pulando...")
    
    # Resumo final
    print("\n" + "=" * 60)
    print(f"📊 RESUMO DOS TESTES")
    print(f"✅ Sucessos: {success_count}")
    print(f"❌ Falhas: {total_count - success_count}")
    print(f"📈 Taxa de sucesso: {(success_count/total_count)*100:.1f}%" if total_count > 0 else "N/A")
    
    if success_count == total_count:
        print("🎉 TODOS OS TESTES PASSARAM!")
        sys.exit(0)
    else:
        print("💥 ALGUNS TESTES FALHARAM!")
        sys.exit(1)

if __name__ == "__main__":
    main()
