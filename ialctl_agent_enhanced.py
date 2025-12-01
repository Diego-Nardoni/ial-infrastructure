#!/usr/bin/env python3
"""
IALCTL Enhanced with Bedrock Agent Core
Maintains full compatibility with existing system
"""

import sys
import os
import argparse

# Add IAL path
sys.path.insert(0, '/home/ial')

def main():
    """Main IALCTL entry point with Agent Core integration"""
    
    parser = argparse.ArgumentParser(description='IAL Infrastructure Assistant')
    parser.add_argument('command', nargs='?', help='Command or natural language input')
    parser.add_argument('--offline', action='store_true', help='Use offline NLP mode')
    parser.add_argument('--setup-agent', action='store_true', help='Setup Bedrock Agent')
    parser.add_argument('--status', action='store_true', help='Show system status')
    
    args = parser.parse_args()
    
    # Initialize agent integration
    try:
        from core.ialctl_agent_integration import IALCTLAgentIntegration
        integration = IALCTLAgentIntegration()
    except Exception as e:
        print(f"❌ Failed to initialize integration: {e}")
        return 1
    
    # Handle setup
    if args.setup_agent:
        print("🔧 Setting up Bedrock Agent...")
        result = integration.setup_agent()
        if result.get('success'):
            print(f"✅ Agent created: {result.get('agent_id')}")
        else:
            print(f"❌ Agent setup failed: {result.get('error')}")
        return 0
    
    # Handle status
    if args.status:
        status = integration.get_status()
        print("📊 IAL System Status:")
        print(f"🧠 Agent Core: {'✅' if status['agent_core_available'] else '❌'}")
        print(f"🔄 Fallback NLP: {'✅' if status['fallback_available'] else '❌'}")
        print(f"📴 Offline Mode: {'✅' if status['offline_mode'] else '❌'}")
        if status.get('agent_info'):
            info = status['agent_info']
            print(f"🆔 Agent ID: {info.get('agent_id', 'N/A')}")
            print(f"🔗 Session: {info.get('session_id', 'N/A')}")
        return 0
    
    # Handle special commands (preserve existing functionality)
    if args.command:
        if args.command == 'start':
            return handle_foundation_deploy(integration, args.offline)
        elif args.command.startswith('deploy'):
            return handle_deploy_command(args.command, integration, args.offline)
        elif args.command in ['drift', 'check-drift']:
            return handle_drift_command(integration, args.offline)
        else:
            # Natural language processing
            return handle_conversational_mode(args.command, integration, args.offline)
    else:
        # Interactive mode
        return interactive_mode(integration, args.offline)

def handle_foundation_deploy(integration, offline=False):
    """Handle foundation deployment (preserve existing)"""
    print("🏗️ Foundation deployment via Agent Core...")
    
    result = integration.process_message("Deploy foundation infrastructure", offline)
    
    if result.get('success'):
        print(f"✅ Foundation deployment initiated via {result.get('source')}")
        return 0
    else:
        print(f"❌ Foundation deployment failed: {result.get('error')}")
        return 1

def handle_deploy_command(command, integration, offline=False):
    """Handle deploy commands"""
    print(f"🚀 Processing deploy command: {command}")
    
    result = integration.process_message(command, offline)
    
    if result.get('success'):
        print(f"✅ Deploy command processed via {result.get('source')}")
        return 0
    else:
        print(f"❌ Deploy command failed: {result.get('error')}")
        return 1

def handle_drift_command(integration, offline=False):
    """Handle drift commands"""
    print("🔍 Checking infrastructure drift...")
    
    result = integration.process_message("Check infrastructure drift", offline)
    
    if result.get('success'):
        print(f"✅ Drift check completed via {result.get('source')}")
        return 0
    else:
        print(f"❌ Drift check failed: {result.get('error')}")
        return 1

def handle_conversational_mode(message, integration, offline=False):
    """Handle single conversational message"""
    print(f"🧠 Processing: {message}")
    
    result = integration.process_message(message, offline)
    
    if result.get('success'):
        response = result.get('response', '')
        source = result.get('source', 'unknown')
        
        print(f"\n🤖 IAL ({source}):")
        if isinstance(response, dict):
            # Format structured response
            if response.get('status') == 'needs_clarification':
                print(f"❓ {response.get('question')}")
            elif response.get('status') == 'preview_ready':
                print("🔍 PREVIEW GENERATED:")
                print(f"📊 Phases: {len(response.get('predicted_phases', []))}")
                print(f"💰 Cost: ${response.get('cost_estimate', {}).get('monthly_cost', 0)}/month")
                print(f"⚠️ Risk: {response.get('risk_assessment', {}).get('risk_level', 'unknown')}")
            else:
                print(response)
        else:
            print(response)
        
        return 0
    else:
        print(f"❌ Processing failed: {result.get('error')}")
        return 1

def interactive_mode(integration, offline=False):
    """Interactive conversational mode"""
    print("🤖 IAL Conversational Assistant")
    print("=" * 50)
    
    if offline:
        print("📴 OFFLINE MODE - Using local NLP")
    else:
        status = integration.get_status()
        if status['agent_core_available']:
            print("🧠 AGENT MODE - Using Bedrock Agent Core")
        else:
            print("🔄 FALLBACK MODE - Using local NLP")
    
    print("💬 Type your infrastructure requests or 'quit' to exit")
    print("🔧 Commands: 'start' (foundation), 'drift' (check drift), '--offline' (switch mode)")
    print()
    
    while True:
        try:
            user_input = input("💭 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'sair']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Handle mode switching
            if user_input == '--offline':
                integration.set_offline_mode(True)
                continue
            elif user_input == '--online':
                integration.set_offline_mode(False)
                continue
            
            # Process message
            result = integration.process_message(user_input, offline)
            
            if result.get('success'):
                response = result.get('response', '')
                source = result.get('source', 'unknown')
                
                print(f"\n🤖 IAL ({source}):")
                if isinstance(response, dict):
                    # Format structured response
                    if response.get('status') == 'needs_clarification':
                        print(f"❓ {response.get('question')}")
                    elif response.get('status') == 'preview_ready':
                        print("🔍 PREVIEW GENERATED:")
                        print(f"📊 Phases: {len(response.get('predicted_phases', []))}")
                        print(f"💰 Cost: ${response.get('cost_estimate', {}).get('monthly_cost', 0)}/month")
                        print(f"⚠️ Risk: {response.get('risk_assessment', {}).get('risk_level', 'unknown')}")
                    else:
                        print(response)
                else:
                    print(response)
            else:
                print(f"❌ Error: {result.get('error')}")
            
            print()  # Blank line
            
        except KeyboardInterrupt:
            print("\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
