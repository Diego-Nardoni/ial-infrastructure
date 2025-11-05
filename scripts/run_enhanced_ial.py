#!/usr/bin/env python3
"""
Script principal para executar IAL com melhorias completas
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

# Add core to path
sys.path.append(str(Path(__file__).parent.parent / 'core'))

from state_integrator import StateIntegrator

def main():
    parser = argparse.ArgumentParser(description='IAL Enhanced - Sistema completo com melhorias')
    parser.add_argument('--action', choices=['sync', 'validate', 'reconcile', 'report', 'full'], 
                       default='full', help='Ação a executar')
    parser.add_argument('--region', default='us-east-1', help='Região AWS')
    parser.add_argument('--verbose', '-v', action='store_true', help='Saída verbosa')
    
    args = parser.parse_args()
    
    print("🚀 IAL Enhanced v3.1 - Sistema Completo")
    print("=" * 50)
    print(f"⏰ Iniciado em: {datetime.utcnow().isoformat()}")
    print(f"🌍 Região: {args.region}")
    print(f"🎯 Ação: {args.action}")
    print()
    
    try:
        # Inicializar integrador
        integrator = StateIntegrator(region=args.region)
        
        if args.action == 'sync':
            print("🔄 Executando sincronização de desired state...")
            result = integrator.sync_desired_state_with_phases()
            
        elif args.action == 'validate':
            print("🔍 Executando validação de completude...")
            result = integrator.enhanced_completeness_validation()
            
        elif args.action == 'reconcile':
            print("🔄 Executando reconciliação...")
            result = integrator.enhanced_reconciliation()
            
        elif args.action == 'report':
            print("📊 Gerando relatório abrangente...")
            result = integrator.generate_comprehensive_report()
            
        elif args.action == 'full':
            print("🚀 Executando workflow completo...")
            result = integrator.full_sync_workflow()
        
        # Exibir resultado
        if args.verbose:
            import json
            print("\n📄 RESULTADO DETALHADO:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"\n📊 RESUMO:")
            print(f"  ✅ Sucesso: {result.get('success', False)}")
            if 'steps' in result:
                for step_name, step_result in result['steps'].items():
                    status = "✅" if step_result.get('success', False) else "❌"
                    print(f"  {status} {step_name}")
        
        # Código de saída baseado no sucesso
        exit_code = 0 if result.get('success', False) else 1
        
        if exit_code == 0:
            print(f"\n🎉 {args.action.upper()} executado com sucesso!")
        else:
            print(f"\n❌ {args.action.upper()} executado com erros.")
        
        return exit_code
        
    except Exception as e:
        print(f"\n💥 ERRO CRÍTICO: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
