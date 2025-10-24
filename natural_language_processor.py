#!/usr/bin/env python3
"""
IaL Natural Language Processor v2.0
Enhanced with Bedrock Conversational AI
"""

import sys
import os
import uuid
import json
from typing import Dict, List, Optional

# Try to import Bedrock modules
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
    from bedrock_conversation_engine import BedrockConversationEngine
    from bedrock_cost_monitor import BedrockCostMonitor
    BEDROCK_AVAILABLE = True
except ImportError:
    BEDROCK_AVAILABLE = False
    print("⚠️ Bedrock modules not available - running in offline mode")

class IaLNaturalProcessor:
    def __init__(self):
        if BEDROCK_AVAILABLE:
            try:
                self.bedrock_engine = BedrockConversationEngine()
                self.cost_monitor = BedrockCostMonitor()
                self.bedrock_enabled = True
                print("🧠 Bedrock AI enabled")
            except Exception as e:
                print(f"⚠️ Bedrock initialization failed: {e}")
                self.bedrock_enabled = False
        else:
            self.bedrock_enabled = False
        
        # Fallback simple patterns for offline mode
        self.domain_mapping = {
            'security': ['security', 'kms', 'iam', 'secrets', 'waf', 'encryption'],
            'networking': ['network', 'vpc', 'subnet', 'routing', 'flow logs'],
            'compute': ['compute', 'ecs', 'container', 'cluster', 'scaling'],
            'data': ['database', 'rds', 'dynamodb', 'redis', 'storage', 's3'],
            'application': ['lambda', 'function', 'step functions', 'sns', 'api'],
            'observability': ['monitoring', 'cloudwatch', 'logs', 'metrics', 'alerts'],
            'ai-ml': ['bedrock', 'ai', 'ml', 'rag', 'machine learning'],
            'governance': ['budget', 'cost', 'compliance', 'well-architected']
        }
        
        self.action_mapping = {
            'deploy': ['deploy', 'create', 'setup', 'build', 'provision', 'install'],
            'status': ['status', 'show', 'check', 'list', 'display', 'what'],
            'rollback': ['rollback', 'undo', 'revert', 'remove', 'delete', 'destroy'],
            'validate': ['validate', 'test', 'verify', 'check', 'ensure']
        }

    def process_command(self, user_input: str, user_id: str = None, session_id: str = None) -> str:
        """Main processing function with Bedrock integration"""
        
        if not user_id:
            user_id = "anonymous-user"
        
        if self.bedrock_enabled:
            try:
                # Use Bedrock for intelligent conversation
                result = self.bedrock_engine.process_conversation(user_input, user_id, session_id)
                
                # Track costs
                if result.get('usage') and hasattr(self, 'cost_monitor'):
                    usage = result['usage']
                    model_id = self.bedrock_engine.models.get(result.get('model_used', 'haiku'))
                    
                    self.cost_monitor.track_token_usage(
                        user_id=user_id,
                        model_id=model_id,
                        input_tokens=usage.get('input_tokens', 0),
                        output_tokens=usage.get('output_tokens', 0)
                    )
                
                return result['response']
                
            except Exception as e:
                print(f"Bedrock error: {e}")
                # Fallback to simple pattern matching
                return self.fallback_processing(user_input)
        else:
            # Use fallback processing
            return self.fallback_processing(user_input)

    def fallback_processing(self, user_input: str) -> str:
        """Fallback processing when Bedrock is unavailable"""
        
        intent = self.extract_intent(user_input)
        return self.generate_fallback_response(intent)

    def extract_intent(self, user_input: str) -> dict:
        """Extract intent from natural language input (fallback)"""
        user_input = user_input.lower()
        
        # Extract action
        action = None
        for act, keywords in self.action_mapping.items():
            if any(keyword in user_input for keyword in keywords):
                action = act
                break
        
        # Extract domain
        domain = None
        for dom, keywords in self.domain_mapping.items():
            if any(keyword in user_input for keyword in keywords):
                domain = dom
                break
        
        # Extract modifiers
        dry_run = any(word in user_input for word in ['dry run', 'test', 'simulate', 'preview'])
        all_domains = any(word in user_input for word in ['everything', 'all', 'complete', 'full'])
        
        return {
            'action': action,
            'domain': domain,
            'dry_run': dry_run,
            'all_domains': all_domains,
            'original_input': user_input
        }

    def generate_fallback_response(self, intent: dict) -> str:
        """Generate fallback response when Bedrock is unavailable"""
        
        action = intent.get('action')
        domain = intent.get('domain')
        dry_run = intent.get('dry_run')
        all_domains = intent.get('all_domains')
        
        if not action:
            return "🤔 I'm currently running in offline mode. Try saying something like 'deploy security' or 'show me the status'. For full conversational AI, please ensure Bedrock access is configured."
        
        if action == 'deploy':
            if all_domains:
                return "🚀 I would deploy the complete infrastructure across all domains. This includes foundation, security, networking, compute, data, application, observability, AI/ML, and governance. This will take approximately 3 hours. (Note: Running in offline mode - full conversation available with Bedrock)"
            elif domain:
                domain_info = self.get_domain_info(domain)
                if dry_run:
                    return f"🔍 I would simulate deploying the {domain} infrastructure. This would include {domain_info['phases']} phases and take about {domain_info['duration']}. No actual resources would be created. (Offline mode)"
                else:
                    return f"🚀 I would deploy the {domain} infrastructure. This includes {domain_info['phases']} phases and will take about {domain_info['duration']}. (Offline mode - use Bedrock for full conversation)"
            else:
                return "🤔 What would you like me to deploy? You can say 'security', 'networking', 'compute', or 'everything'. (Offline mode)"
        
        elif action == 'status':
            if domain:
                return f"📊 I would check the {domain} infrastructure status... (Offline mode - enable Bedrock for real-time status)"
            else:
                return "📊 I would show you the overall infrastructure status... (Offline mode)"
        
        elif action == 'rollback':
            if domain:
                return f"🔄 I would rollback the {domain} infrastructure. This would safely remove all resources in reverse order. (Offline mode - Bedrock needed for confirmation)"
            else:
                return "🔄 What would you like me to rollback? Please specify the domain like 'rollback security' or 'rollback networking'. (Offline mode)"
        
        elif action == 'validate':
            if domain:
                return f"🔍 I would validate the {domain} infrastructure configuration and deployment... (Offline mode)"
            else:
                return "🔍 I would validate the complete infrastructure setup... (Offline mode)"
        
        return "🤔 I understand you want to perform an action, but I'm running in offline mode. For full conversational AI capabilities, please configure Bedrock access."

    def get_domain_info(self, domain: str) -> dict:
        """Get information about a domain"""
        domain_details = {
            'security': {'phases': 6, 'duration': '30 minutes'},
            'networking': {'phases': 2, 'duration': '20 minutes'},
            'compute': {'phases': 5, 'duration': '35 minutes'},
            'data': {'phases': 5, 'duration': '40 minutes'},
            'application': {'phases': 4, 'duration': '25 minutes'},
            'observability': {'phases': 3, 'duration': '20 minutes'},
            'ai-ml': {'phases': 1, 'duration': '15 minutes'},
            'governance': {'phases': 4, 'duration': '15 minutes'}
        }
        
        return domain_details.get(domain, {'phases': 'several', 'duration': 'some time'})

    def get_usage_report(self, user_id: str) -> dict:
        """Get usage and cost report for a user"""
        
        if not self.bedrock_enabled or not hasattr(self, 'cost_monitor'):
            return {'error': 'Cost monitoring not available in offline mode'}
        
        try:
            daily_usage = self.cost_monitor.get_daily_usage(user_id)
            monthly_usage = self.cost_monitor.get_monthly_usage(user_id)
            suggestions = self.cost_monitor.get_cost_optimization_suggestions(user_id)
            
            return {
                'daily_usage': daily_usage,
                'monthly_usage': monthly_usage,
                'optimization_suggestions': suggestions
            }
        except Exception as e:
            return {'error': f"Unable to retrieve usage report: {e}"}

# Interactive CLI for testing
def interactive_mode():
    processor = IaLNaturalProcessor()
    user_id = input("Enter your user ID (or press Enter for anonymous): ").strip() or "anonymous-user"
    session_id = str(uuid.uuid4())
    
    print(f"\n🧠 IaL Natural Language Processor v2.0")
    if processor.bedrock_enabled:
        print("✅ Bedrock AI: ENABLED")
    else:
        print("⚠️ Bedrock AI: OFFLINE MODE")
    print(f"👤 User: {user_id}")
    print(f"🔗 Session: {session_id[:8]}...")
    print("=" * 60)
    print("Type 'quit' to exit, 'usage' for cost report, or ask me anything about infrastructure!")
    print()
    
    while True:
        try:
            user_input = input("👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye! Thanks for using IaL!")
                break
            
            if user_input.lower() == 'usage':
                report = processor.get_usage_report(user_id)
                print(f"📊 Usage Report: {json.dumps(report, indent=2)}")
                continue
            
            if not user_input:
                continue
            
            response = processor.process_command(user_input, user_id, session_id)
            print(f"🤖 IaL: {response}")
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

# Example usage and testing
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'interactive':
        interactive_mode()
    else:
        processor = IaLNaturalProcessor()
        
        # Test examples
        test_inputs = [
            "Hello, I need help with my infrastructure",
            "Deploy the security infrastructure for production",
            "Show me the current status of all deployments",
            "What's the cost of my Bedrock usage this month?",
            "Rollback the compute changes from yesterday",
            "I want to set up monitoring for my application"
        ]
        
        print("🧠 IaL Natural Language Processor v2.0 Test")
        print("=" * 50)
        
        test_user_id = "test-user-123"
        for i, test_input in enumerate(test_inputs):
            print(f"\n👤 User: {test_input}")
            response = processor.process_command(test_input, test_user_id)
            print(f"🤖 IaL: {response}")
