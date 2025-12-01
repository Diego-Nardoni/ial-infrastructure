#!/usr/bin/env python3
"""
Utilitário para verificar status do Bedrock Agent
"""

import sys
import os
import json

sys.path.insert(0, '/home/ial')

def check_agent_status():
    """Verifica status completo do Bedrock Agent"""
    
    print("🔍 IAL Bedrock Agent Status Check")
    print("=" * 40)
    
    # 1. Verificar arquivo de configuração
    config_file = os.path.expanduser('~/.ial/agent_config.json')
    
    if os.path.exists(config_file):
        print("✅ Agent config file exists")
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            print(f"   📝 Config file: {config_file}")
            print(f"   🌍 Region: {config.get('region', 'unknown')}")
            print(f"   🧠 Bedrock supported: {config.get('bedrock_supported', False)}")
            print(f"   🆔 Agent ID: {config.get('agent_id', 'not-set')}")
            print(f"   🏷️  Alias ID: {config.get('agent_alias_id', 'not-set')}")
            print(f"   ⏰ Configured at: {config.get('configured_at', 'unknown')}")
            
        except Exception as e:
            print(f"❌ Error reading config: {e}")
            return False
    else:
        print("❌ Agent config file not found")
        print("   💡 Run 'ialctl start' to configure the agent")
        return False
    
    # 2. Verificar BedrockAgentCore
    try:
        from core.bedrock_agent_core import BedrockAgentCore
        agent = BedrockAgentCore()
        
        status = agent.get_status()
        
        print(f"\n🧠 Bedrock Agent Core Status:")
        print(f"   Available: {status['agent_available']}")
        print(f"   Agent ID: {status['agent_id']}")
        print(f"   Alias ID: {status['agent_alias_id']}")
        print(f"   Region: {status['region']}")
        
        return status['agent_available']
        
    except Exception as e:
        print(f"❌ BedrockAgentCore error: {e}")
        return False

if __name__ == "__main__":
    success = check_agent_status()
    
    if success:
        print("\n🎉 Bedrock Agent is properly configured!")
    else:
        print("\n⚠️  Bedrock Agent needs configuration")
        print("   Run: ialctl start")
    
    sys.exit(0 if success else 1)
