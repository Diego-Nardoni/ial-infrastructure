#!/usr/bin/env python3
"""
IaL Natural Language Processor v3.0
Complete system with all phases integrated
"""

import sys
import os
import uuid
import json
from typing import Dict, List, Optional

# Try to import Master Engine
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
    from ial_master_engine import IaLMasterEngine
    MASTER_ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Master Engine not available: {e}")
    MASTER_ENGINE_AVAILABLE = False

class IaLNaturalProcessor:
    def __init__(self):
        if MASTER_ENGINE_AVAILABLE:
            try:
                self.master_engine = IaLMasterEngine()
                self.advanced_mode = True
                print("🚀 IaL v3.0 - Advanced Mode: ALL SYSTEMS OPERATIONAL")
                print("✅ Bedrock Conversational AI")
                print("✅ Infrastructure Integration") 
                print("✅ Response Caching & Optimization")
                print("✅ Knowledge Base & RAG")
                print("✅ Cost Monitoring & Rate Limiting")
            except Exception as e:
                print(f"⚠️ Master Engine initialization failed: {e}")
                self.advanced_mode = False
                self.init_fallback_mode()
        else:
            self.advanced_mode = False
            self.init_fallback_mode()

    def init_fallback_mode(self):
        """Initialize fallback mode for basic functionality"""
        print("⚠️ IaL v3.0 - Fallback Mode: Basic functionality only")
        
        # Basic pattern matching for offline mode
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
        """Main processing function"""
        
        if not user_id:
            user_id = "anonymous-user"
        
        if self.advanced_mode:
            try:
                # Use Master Engine for full functionality
                result = self.master_engine.process_conversation(user_input, user_id, session_id)
                
                # Extract response and add metadata info if needed
                response = result.get('response', 'No response generated')
                
                # Add performance info for interactive mode
                if result.get('cached'):
                    response += f"\n\n💾 (Cached response - {result.get('processing_time', 0):.2f}s)"
                elif result.get('rag_used'):
                    response += f"\n\n🧠 (Knowledge base used - {result.get('knowledge_base_hits', 0)} sources)"
                elif result.get('infrastructure_action'):
                    response += f"\n\n🏗️ (Infrastructure action: {result.get('action_type', 'unknown')})"
                
                return response
                
            except Exception as e:
                print(f"Master Engine error: {e}")
                return self.fallback_processing(user_input)
        else:
            return self.fallback_processing(user_input)

    def fallback_processing(self, user_input: str) -> str:
        """Fallback processing when advanced features are unavailable"""
        
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
        """Generate fallback response when advanced features are unavailable"""
        
        action = intent.get('action')
        domain = intent.get('domain')
        dry_run = intent.get('dry_run')
        all_domains = intent.get('all_domains')
        
        if not action:
            return "🤔 I'm currently running in basic mode. Try saying something like 'deploy security' or 'show me the status'. For full conversational AI with Bedrock, infrastructure integration, and advanced features, please ensure all dependencies are installed."
        
        if action == 'deploy':
            if all_domains:
                return "🚀 I would deploy the complete infrastructure across all domains. This includes foundation, security, networking, compute, data, application, observability, AI/ML, and governance. This will take approximately 3 hours. (Note: Running in basic mode - full functionality available with Master Engine)"
            elif domain:
                domain_info = self.get_domain_info(domain)
                if dry_run:
                    return f"🔍 I would simulate deploying the {domain} infrastructure. This would include {domain_info['phases']} phases and take about {domain_info['duration']}. No actual resources would be created. (Basic mode)"
                else:
                    return f"🚀 I would deploy the {domain} infrastructure. This includes {domain_info['phases']} phases and will take about {domain_info['duration']}. (Basic mode - use Master Engine for real deployment)"
            else:
                return "🤔 What would you like me to deploy? You can say 'security', 'networking', 'compute', or 'everything'. (Basic mode)"
        
        elif action == 'status':
            if domain:
                return f"📊 I would check the {domain} infrastructure status... (Basic mode - enable Master Engine for real-time status)"
            else:
                return "📊 I would show you the overall infrastructure status... (Basic mode)"
        
        elif action == 'rollback':
            if domain:
                return f"🔄 I would rollback the {domain} infrastructure. This would safely remove all resources in reverse order. (Basic mode - Master Engine needed for execution)"
            else:
                return "🔄 What would you like me to rollback? Please specify the domain like 'rollback security' or 'rollback networking'. (Basic mode)"
        
        elif action == 'validate':
            if domain:
                return f"🔍 I would validate the {domain} infrastructure configuration and deployment... (Basic mode)"
            else:
                return "🔍 I would validate the complete infrastructure setup... (Basic mode)"
        
        return "🤔 I understand you want to perform an action, but I'm running in basic mode. For full conversational AI capabilities with Bedrock, infrastructure integration, caching, and knowledge base, please configure the Master Engine."

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

    def get_system_status(self) -> dict:
        """Get system status"""
        
        if self.advanced_mode and hasattr(self, 'master_engine'):
            return self.master_engine.get_system_status()
        else:
            return {
                'mode': 'basic',
                'advanced_features': False,
                'master_engine': 'unavailable',
                'fallback_mode': True
            }

    def get_usage_report(self, user_id: str) -> dict:
        """Get usage and cost report for a user"""
        
        if self.advanced_mode and hasattr(self, 'master_engine'):
            try:
                return self.master_engine.cost_monitor.get_monthly_usage(user_id)
            except Exception as e:
                return {'error': f"Unable to retrieve usage report: {e}"}
        else:
            return {'error': 'Usage reporting not available in basic mode'}

# Interactive CLI for testing
def interactive_mode():
    processor = IaLNaturalProcessor()
    user_id = input("Enter your user ID (or press Enter for anonymous): ").strip() or "anonymous-user"
    session_id = str(uuid.uuid4())
    
    print(f"\n🧠 IaL Natural Language Processor v3.0")
    
    system_status = processor.get_system_status()
    if processor.advanced_mode:
        print("✅ ADVANCED MODE: All systems operational")
        print("   🤖 Bedrock Conversational AI")
        print("   🏗️ Infrastructure Integration")
        print("   💾 Response Caching & Optimization")
        print("   🧠 Knowledge Base & RAG")
        print("   💰 Cost Monitoring & Rate Limiting")
    else:
        print("⚠️ BASIC MODE: Limited functionality")
        print("   📝 Pattern-based responses only")
    
    print(f"👤 User: {user_id}")
    print(f"🔗 Session: {session_id[:8]}...")
    print("=" * 60)
    print("Commands: 'quit' to exit, 'status' for system status, 'usage' for cost report")
    print("Ask me anything about infrastructure!")
    print()
    
    while True:
        try:
            user_input = input("👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye! Thanks for using IaL!")
                break
            
            if user_input.lower() == 'status':
                status = processor.get_system_status()
                print(f"📊 System Status: {json.dumps(status, indent=2)}")
                continue
            
            if user_input.lower() == 'usage':
                report = processor.get_usage_report(user_id)
                print(f"💰 Usage Report: {json.dumps(report, indent=2)}")
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
            "How do I secure my database?",
            "Rollback the compute changes from yesterday",
            "What's the best practice for networking?"
        ]
        
        print("🧠 IaL Natural Language Processor v3.0 Test")
        print("=" * 50)
        
        test_user_id = "test-user-123"
        for i, test_input in enumerate(test_inputs):
            print(f"\n👤 User: {test_input}")
            response = processor.process_command(test_input, test_user_id)
            print(f"🤖 IaL: {response}")
