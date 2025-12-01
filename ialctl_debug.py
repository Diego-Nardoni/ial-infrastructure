#!/usr/bin/env python3
"""
IALCTL Debug Mode
Enhanced CLI with debug capabilities and telemetry
"""

import sys
import os
import argparse
import json
from datetime import datetime

sys.path.insert(0, '/home/ial')

def main():
    """Main IALCTL with debug mode"""
    
    parser = argparse.ArgumentParser(description='IAL Infrastructure Assistant - Debug Mode')
    parser.add_argument('command', nargs='?', help='Command or natural language input')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--offline', action='store_true', help='Force offline NLP mode')
    parser.add_argument('--sandbox', action='store_true', help='Sandbox mode (no AWS operations)')
    parser.add_argument('--telemetry', action='store_true', help='Show telemetry logs')
    
    args = parser.parse_args()
    
    # Setup environment
    if args.sandbox:
        os.environ['IAL_MODE'] = 'sandbox'
    
    # Initialize enhanced fallback system
    try:
        from core.enhanced_fallback_system import EnhancedFallbackSystem, ProcessingMode
        fallback_system = EnhancedFallbackSystem()
    except Exception as e:
        print(f"❌ Failed to initialize enhanced system: {e}")
        return 1
    
    # Handle commands
    if args.command:
        return handle_single_command(args, fallback_system)
    else:
        return interactive_debug_mode(args, fallback_system)

def handle_single_command(args, fallback_system):
    """Handle single command with debug info"""
    
    # Determine processing mode
    mode = None
    if args.sandbox:
        mode = ProcessingMode.SANDBOX
    elif args.offline:
        mode = ProcessingMode.FALLBACK_NLP
    
    if args.debug:
        print("🐛 DEBUG MODE ENABLED")
        print(f"📝 Command: {args.command}")
        print(f"🔧 Mode: {mode.value if mode else 'auto'}")
        print(f"⏰ Timestamp: {datetime.now().isoformat()}")
        print("=" * 50)
    
    # Process command
    result = fallback_system.process_with_fallback(args.command, mode)
    
    if args.debug:
        print("\n🔍 DEBUG RESULTS:")
        print(f"✅ Success: {result.get('success')}")
        print(f"🎯 Source: {result.get('source')}")
        print(f"🆔 Request ID: {result.get('request_id')}")
        if result.get('error'):
            print(f"❌ Error: {result.get('error')}")
        print("=" * 50)
    
    # Show response
    if result.get('success'):
        response = result.get('response', '')
        if isinstance(response, dict):
            print(f"🤖 IAL ({result.get('source')}): {json.dumps(response, indent=2)}")
        else:
            print(f"🤖 IAL ({result.get('source')}): {response}")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    # Show telemetry if requested
    if args.telemetry:
        show_telemetry_logs()
    
    return 0 if result.get('success') else 1

def interactive_debug_mode(args, fallback_system):
    """Interactive mode with debug capabilities"""
    
    print("🐛 IAL Debug Mode")
    print("=" * 50)
    print(f"🔧 Debug: {'✅' if args.debug else '❌'}")
    print(f"📴 Offline: {'✅' if args.offline else '❌'}")
    print(f"🏖️ Sandbox: {'✅' if args.sandbox else '❌'}")
    print(f"📊 Telemetry: {'✅' if args.telemetry else '❌'}")
    print()
    print("💬 Commands:")
    print("  /debug    - Toggle debug mode")
    print("  /sandbox  - Toggle sandbox mode")
    print("  /offline  - Toggle offline mode")
    print("  /telemetry - Show telemetry logs")
    print("  /status   - Show system status")
    print("  quit      - Exit")
    print()
    
    while True:
        try:
            user_input = input("🐛 Debug> ").strip()
            
            if user_input.lower() in ['quit', 'exit']:
                print("👋 Debug session ended!")
                break
            
            if not user_input:
                continue
            
            # Handle debug commands
            if user_input == '/debug':
                args.debug = not args.debug
                print(f"🐛 Debug mode: {'✅' if args.debug else '❌'}")
                continue
            elif user_input == '/sandbox':
                args.sandbox = not args.sandbox
                if args.sandbox:
                    os.environ['IAL_MODE'] = 'sandbox'
                else:
                    os.environ.pop('IAL_MODE', None)
                print(f"🏖️ Sandbox mode: {'✅' if args.sandbox else '❌'}")
                continue
            elif user_input == '/offline':
                args.offline = not args.offline
                print(f"📴 Offline mode: {'✅' if args.offline else '❌'}")
                continue
            elif user_input == '/telemetry':
                show_telemetry_logs()
                continue
            elif user_input == '/status':
                show_system_status()
                continue
            
            # Process regular input
            mode = None
            if args.sandbox:
                mode = ProcessingMode.SANDBOX
            elif args.offline:
                mode = ProcessingMode.FALLBACK_NLP
            
            if args.debug:
                print(f"\n🐛 Processing: {user_input}")
                print(f"🔧 Mode: {mode.value if mode else 'auto'}")
            
            result = fallback_system.process_with_fallback(user_input, mode)
            
            if args.debug:
                print(f"🎯 Source: {result.get('source')}")
                print(f"🆔 Request ID: {result.get('request_id')}")
            
            # Show response
            if result.get('success'):
                response = result.get('response', '')
                if isinstance(response, dict):
                    print(f"\n🤖 IAL: {json.dumps(response, indent=2)}")
                else:
                    print(f"\n🤖 IAL: {response}")
            else:
                print(f"\n❌ Error: {result.get('error')}")
            
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Debug session interrupted!")
            break
        except Exception as e:
            print(f"❌ Debug error: {e}")
    
    return 0

def show_telemetry_logs():
    """Show recent telemetry logs"""
    try:
        log_file = '/home/ial/logs/ial_telemetry.log'
        if os.path.exists(log_file):
            print("\n📊 Recent Telemetry Logs:")
            print("=" * 50)
            with open(log_file, 'r') as f:
                lines = f.readlines()[-10:]  # Last 10 lines
                for line in lines:
                    try:
                        log_entry = json.loads(line.strip())
                        print(f"⏰ {log_entry['timestamp']}")
                        print(f"🎯 {log_entry['event_type']}")
                        print(f"🆔 {log_entry['request_id']}")
                        print(f"📝 {json.dumps(log_entry['data'], indent=2)}")
                        print("-" * 30)
                    except:
                        print(line.strip())
        else:
            print("📊 No telemetry logs found")
    except Exception as e:
        print(f"❌ Error reading telemetry: {e}")

def show_system_status():
    """Show system status"""
    print("\n📊 IAL System Status:")
    print("=" * 50)
    
    # Check Agent Core
    try:
        from core.ialctl_agent_integration import IALCTLAgentIntegration
        integration = IALCTLAgentIntegration()
        status = integration.get_status()
        print(f"🧠 Agent Core: {'✅' if status['agent_core_available'] else '❌'}")
        print(f"🔄 Fallback NLP: {'✅' if status['fallback_available'] else '❌'}")
    except Exception as e:
        print(f"🧠 Agent Core: ❌ ({e})")
    
    # Check environment
    print(f"🏖️ Sandbox Mode: {'✅' if os.environ.get('IAL_MODE') == 'sandbox' else '❌'}")
    print(f"📁 Log Directory: {'/home/ial/logs'}")
    print(f"📁 Sandbox Outputs: {'/home/ial/sandbox_outputs'}")

if __name__ == '__main__':
    sys.exit(main())
