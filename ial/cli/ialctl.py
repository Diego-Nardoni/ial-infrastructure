#!/usr/bin/env python3
"""
IALCTL - Infrastructure Assistant Layer CLI
Versão consolidada oficial do IAL CLI
"""

import sys
import os
import asyncio
from pathlib import Path

# Adicionar diretório raiz do IAL ao path
IAL_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(IAL_ROOT))

async def run_foundation_deploy():
    """Executar deploy usando CognitiveEngine completo"""
    try:
        from core.cognitive_engine import CognitiveEngine
        
        print("🧠 IAL Cognitive Engine Starting...")
        print("=" * 50)
        
        engine = CognitiveEngine()
        result = engine.process_intent("Deploy foundation infrastructure")
        
        if result.get('status') == 'success':
            print(f"✅ Foundation deployment completed via Cognitive Engine!")
            print("🔧 Full pipeline: IAS → Cost Guardrails → Phase Builder → GitOps")
            return 0
        else:
            print(f"❌ Foundation deployment failed: {result.get('error', 'Unknown error')}")
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
        result = engine.process_intent(f"Deploy phase {phase}")
        
        if result.get('success'):
            print(f"✅ Phase {phase} deployed successfully!")
            return 0
        else:
            print(f"❌ Phase {phase} deployment failed")
            return 1
            
    except Exception as e:
        print(f"❌ Erro no deploy da fase {phase}: {e}")
        return 1

def main():
    """Função principal do CLI"""
    if len(sys.argv) < 2:
        print("Usage: ialctl [start|plan|phase <number>|--offline]")
        return 1
    
    command = sys.argv[1]
    
    # Verificar modo offline
    offline_mode = '--offline' in sys.argv or os.getenv('IAL_MODE') == 'offline'
    if offline_mode:
        print("🔒 IAL running in OFFLINE mode")
    
    if command == "start":
        return asyncio.run(run_foundation_deploy())
    elif command == "plan":
        print("🔍 IAL Plan mode - showing what would be deployed")
        # TODO: Implementar plan mode
        return 0
    elif command == "phase" and len(sys.argv) > 2:
        phase = sys.argv[2]
        return deploy_specific_phase(phase)
    else:
        print(f"❌ Unknown command: {command}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
