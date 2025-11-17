#!/usr/bin/env python3
"""
Teste da integração da Phase Discovery Tool com IAL Master Engine
"""

import asyncio
import sys
import os

# Adicionar path do projeto
sys.path.append('/home/ial')

async def test_phase_discovery_integration():
    """Testa a integração completa da descoberta de fases"""
    
    print("🧪 Testando integração da Phase Discovery Tool...")
    
    try:
        # 1. Importar e inicializar IAL Master Engine
        from core.ial_master_engine_integrated import IALMasterEngineIntegrated
        
        print("📦 Inicializando IAL Master Engine...")
        engine = IALMasterEngineIntegrated()
        
        # 2. Testar inicialização da descoberta de fases
        print("\n🔍 Testando inicialização da descoberta de fases...")
        discovery_success = await engine.initialize_phase_discovery()
        
        if discovery_success:
            print(f"✅ Descoberta inicializada com sucesso!")
            print(f"   - Fases encontradas: {len(engine.available_phases)}")
            print(f"   - Templates totais: {sum(p['template_count'] for p in engine.available_phases)}")
        else:
            print("⚠️ Descoberta falhou - testando fallback...")
        
        # 3. Testar comandos de fase via process_user_input
        test_commands = [
            "list phases",
            "show phases", 
            "fases disponíveis",
            "deployment order",
            "show phase 00-foundation",
            "describe phase 01-security"
        ]
        
        print("\n🎯 Testando comandos de fase...")
        for command in test_commands:
            print(f"\n📝 Comando: '{command}'")
            try:
                response = await engine.process_user_input(command)
                print(f"✅ Resposta: {response[:200]}{'...' if len(response) > 200 else ''}")
            except Exception as e:
                print(f"❌ Erro: {e}")
        
        # 4. Testar descoberta standalone
        print("\n🔧 Testando Phase Discovery Tool standalone...")
        from phase_discovery_tool import PhaseDiscoveryTool
        
        standalone_tool = PhaseDiscoveryTool()
        phases = await standalone_tool.discover_phases()
        
        if phases:
            print(f"✅ Descoberta standalone: {len(phases)} fases")
            for phase in phases[:3]:  # Mostrar apenas primeiras 3
                print(f"   - {phase['phase_id']}: {phase['template_count']} templates")
        else:
            print("⚠️ Descoberta standalone falhou")
        
        print("\n🎉 Teste de integração concluído!")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()

async def test_mcp_github_server_connection():
    """Testa conexão com MCP GitHub Server"""
    
    print("\n🔗 Testando conexão com MCP GitHub Server...")
    
    try:
        from core.mcp_client import MCPClient
        
        mcp_client = MCPClient()
        
        # Testar listagem de conteúdo do repositório
        result = await mcp_client.call_tool("list_repository_contents", {
            "path": "phases",
            "type": "dir"
        })
        
        if result and result.get("contents"):
            print(f"✅ MCP GitHub Server conectado!")
            print(f"   - Encontrados {len(result['contents'])} itens no diretório phases")
            
            # Mostrar alguns itens
            for item in result['contents'][:5]:
                print(f"   - {item.get('type', 'unknown')}: {item.get('name', 'unnamed')}")
        else:
            print("⚠️ MCP GitHub Server não retornou dados esperados")
            
    except Exception as e:
        print(f"❌ Erro na conexão MCP: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando testes da Phase Discovery Integration...")
    
    # Executar testes
    asyncio.run(test_mcp_github_server_connection())
    asyncio.run(test_phase_discovery_integration())
    
    print("\n✨ Testes concluídos!")
