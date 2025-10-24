#!/usr/bin/env python3
"""Conversational Infrastructure Orchestrator - Natural Language Intent Processing"""

from pathlib import Path
import yaml
import re
import subprocess
import sys
import os
from datetime import datetime
from time import time

# Import professional logging
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import get_logger
from utils.rollback_manager import rollback_manager

logger = get_logger(__name__)

def process_intent(user_input):
    """Process natural language intent and execute corresponding actions"""
    
    start_time = time()
    logger.info(f"Processing intent: {user_input}", 
                user_input=user_input, 
                event_type="intent_processing_started")
    
    # Load intent configuration
    config = load_intent_config()
    
    # Match intent
    matched_intent = match_intent(user_input, config)
    
    if not matched_intent:
        print("❓ Intent not recognized. Available intents:")
        show_available_intents(config)
        return False
    
    print(f"✅ Matched intent: {matched_intent['name']}")
    
    # Execute actions
    success = execute_intent_actions(matched_intent)
    
    # Run verification
    if success and matched_intent.get('verify'):
        print("🔍 Running verification...")
        verify_success = run_verification(matched_intent['verify'])
        if verify_success:
            print("✅ Verification passed")
        else:
            print("⚠️ Verification failed")
    
    return success

def load_intent_config():
    """Load intent configuration from main.mcp.yaml"""
    
    try:
        # Get project root dynamically
        project_root = Path(__file__).parent.parent
        config_path = project_root / 'orchestration' / 'main.mcp.yaml'
        
        # Import CloudFormation YAML loader
        sys.path.append(str(Path(__file__).parent))
        from cf_yaml_loader import load_cf_yaml
        
        config = load_cf_yaml(config_path)
        return config if config else {'intents': {}}
    except Exception as e:
        print(f"❌ Error loading intent config: {e}")
        return {'intents': {}}

def match_intent(user_input, config):
    """Match user input to configured intents"""
    
    user_input_lower = user_input.lower()
    
    for intent_name, intent_config in config.get('intents', {}).items():
        phrases = intent_config.get('phrases', [])
        
        for phrase in phrases:
            if phrase.lower() in user_input_lower:
                return {
                    'name': intent_name,
                    'config': intent_config,
                    'actions': intent_config.get('actions', []),
                    'verify': intent_config.get('verify', '')
                }
    
    return None

def execute_intent_actions(intent):
    """Execute actions for matched intent"""
    
    print(f"🔄 Executing actions for intent: {intent['name']}")
    
    success = True
    
    for action in intent['actions']:
        if 'phase' in action:
            # Phase deployment
            phase_success = deploy_phase(action['phase'])
            if not phase_success:
                success = False
                break
        elif 'script' in action:
            # Script execution
            script_success = run_script(action['script'])
            if not script_success:
                success = False
                break
    
    return success

def deploy_phase(phase_name):
    """Deploy a specific phase"""
    
    print(f"📋 Deploying phase: {phase_name}")
    
    # Get project root dynamically
    project_root = Path(__file__).parent.parent
    phase_file = project_root / 'phases' / f"{phase_name}.yaml"
    
    if not os.path.exists(phase_file):
        print(f"❌ Phase file not found: {phase_file}")
        return False
    
    try:
        # For now, just validate the phase exists and is readable
        with open(phase_file, 'r') as f:
            phase_content = yaml.safe_load(f)
        
        resource_count = phase_content.get('resource_count', 0)
        print(f"✅ Phase {phase_name} validated ({resource_count} resources)")
        
        # In a real implementation, this would deploy via CloudFormation
        # For now, we'll simulate successful deployment
        return True
        
    except Exception as e:
        print(f"❌ Error deploying phase {phase_name}: {e}")
        return False

def run_script(script_command):
    """Run a script command"""
    
    print(f"🔧 Running script: {script_command}")
    
    try:
        # Change to project root directory
        project_root = Path(__file__).parent.parent
        os.chdir(project_root)
        
        # Run the script
        result = subprocess.run(
            script_command.split(),
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print("✅ Script executed successfully")
            if result.stdout:
                print("📄 Output:")
                print(result.stdout[:500])  # Limit output
            return True
        else:
            print(f"❌ Script failed with exit code {result.returncode}")
            if result.stderr:
                print("📄 Error:")
                print(result.stderr[:500])
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Script timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Error running script: {e}")
        return False

def run_verification(verify_command):
    """Run verification command"""
    
    try:
        project_root = Path(__file__).parent.parent
        os.chdir(project_root)
        
        result = subprocess.run(
            verify_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

def show_available_intents(config):
    """Show available intents to user"""
    
    print("\n📋 Available intents:")
    
    for intent_name, intent_config in config.get('intents', {}).items():
        phrases = intent_config.get('phrases', [])
        print(f"\n🎯 {intent_name.title()}:")
        for phrase in phrases[:3]:  # Show first 3 phrases
            print(f"   • \"{phrase}\"")
        if len(phrases) > 3:
            print(f"   • ... and {len(phrases) - 3} more")

def show_help():
    """Show help information"""
    
    print("""
🗣️ Conversational Infrastructure Orchestrator

Usage:
  python3 scripts/conversational-orchestrator.py "your natural language request"

Examples:
  python3 scripts/conversational-orchestrator.py "provisionar segurança"
  python3 scripts/conversational-orchestrator.py "subir rede"
  python3 scripts/conversational-orchestrator.py "auditar estado"
  python3 scripts/conversational-orchestrator.py "descobrir recursos"
  python3 scripts/conversational-orchestrator.py "analisar custos"

The orchestrator will:
1. Parse your natural language input
2. Match it to configured intents
3. Execute the appropriate phases or scripts
4. Run verification checks
5. Provide feedback on success/failure
""")

def main():
    """Main function"""
    
    if len(sys.argv) < 2:
        show_help()
        return 1
    
    if sys.argv[1] in ['--help', '-h', 'help']:
        show_help()
        return 0
    
    user_input = ' '.join(sys.argv[1:])
    
    print("🚀 IaL Conversational Infrastructure Orchestrator")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    success = process_intent(user_input)
    
    print("-" * 60)
    if success:
        print("✅ Intent processed successfully")
        return 0
    else:
        print("❌ Intent processing failed")
        return 1

if __name__ == "__main__":
    exit(main())
