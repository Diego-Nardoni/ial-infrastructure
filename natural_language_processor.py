#!/usr/bin/env python3
"""
IaL Natural Language Processor
Processes natural language commands for infrastructure deployment
"""

import re
import json
from typing import Dict, List, Optional

class IaLNaturalProcessor:
    def __init__(self):
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
    
    def extract_intent(self, user_input: str) -> Dict:
        """Extract intent from natural language input"""
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
    
    def generate_response(self, intent: Dict) -> str:
        """Generate natural language response"""
        action = intent.get('action')
        domain = intent.get('domain')
        dry_run = intent.get('dry_run')
        all_domains = intent.get('all_domains')
        
        if not action:
            return "🤔 I'm not sure what you'd like me to do. Try saying something like 'deploy security' or 'show me the status'."
        
        if action == 'deploy':
            if all_domains:
                return "🚀 I'll deploy the complete infrastructure across all domains. This includes foundation, security, networking, compute, data, application, observability, AI/ML, and governance. This will take approximately 3 hours. Shall I proceed?"
            elif domain:
                domain_info = self.get_domain_info(domain)
                if dry_run:
                    return f"🔍 I'll simulate deploying the {domain} infrastructure. This would include {domain_info['phases']} phases and take about {domain_info['duration']}. No actual resources will be created."
                else:
                    return f"🚀 I'll deploy the {domain} infrastructure. This includes {domain_info['phases']} phases and will take about {domain_info['duration']}. Shall I proceed?"
            else:
                return "🤔 What would you like me to deploy? You can say 'security', 'networking', 'compute', or 'everything'."
        
        elif action == 'status':
            if domain:
                return f"📊 Let me check the {domain} infrastructure status..."
            else:
                return "📊 Let me show you the overall infrastructure status..."
        
        elif action == 'rollback':
            if domain:
                return f"🔄 I'll rollback the {domain} infrastructure. This will safely remove all resources in reverse order. Are you sure you want to proceed?"
            else:
                return "🔄 What would you like me to rollback? Please specify the domain like 'rollback security' or 'rollback networking'."
        
        elif action == 'validate':
            if domain:
                return f"🔍 I'll validate the {domain} infrastructure configuration and deployment..."
            else:
                return "🔍 I'll validate the complete infrastructure setup..."
        
        return "🤔 I understand you want to perform an action, but I need more details. Try being more specific about what you'd like to do."
    
    def get_domain_info(self, domain: str) -> Dict:
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
    
    def process_command(self, user_input: str) -> str:
        """Main processing function"""
        intent = self.extract_intent(user_input)
        response = self.generate_response(intent)
        
        return response

# Example usage and testing
if __name__ == "__main__":
    processor = IaLNaturalProcessor()
    
    # Test examples
    test_inputs = [
        "Deploy the security infrastructure",
        "Show me the networking status",
        "Create everything for production",
        "Rollback the compute changes",
        "Test the database setup",
        "What's the current status?",
        "I need to set up monitoring",
        "Remove the AI services"
    ]
    
    print("🧠 IaL Natural Language Processor Test")
    print("=" * 50)
    
    for test_input in test_inputs:
        print(f"\n👤 User: {test_input}")
        response = processor.process_command(test_input)
        print(f"🤖 IaL: {response}")
