#!/usr/bin/env python3
"""
IaL Bedrock Conversation Engine
Real conversational AI for infrastructure management
"""

import boto3
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class BedrockConversationEngine:
    def __init__(self, region='us-east-1'):
        self.bedrock = boto3.client('bedrock-runtime', region_name=region)
        self.dynamodb = boto3.client('dynamodb', region_name=region)
        
        # Model configuration
        self.models = {
            'sonnet': 'anthropic.claude-3-5-sonnet-20241022-v2:0',
            'haiku': 'anthropic.claude-3-haiku-20240307-v1:0'
        }
        
        # Cost optimization
        self.token_limits = {
            'sonnet': 4000,  # Max tokens for complex tasks
            'haiku': 2000    # Max tokens for simple tasks
        }
        
        # Infrastructure domain knowledge
        self.system_prompt = """You are IaL (Infrastructure as Language), an AI assistant that manages AWS infrastructure through natural conversation.

CORE CAPABILITIES:
- Deploy infrastructure domains: security, networking, compute, data, application, observability, ai-ml, governance
- Show deployment status and health
- Rollback changes safely
- Validate configurations
- Provide infrastructure guidance

CONVERSATION STYLE:
- Natural, friendly, and professional
- Use emojis appropriately (🚀 for deploy, 📊 for status, 🔄 for rollback)
- Ask for confirmation before destructive actions
- Provide clear next steps
- Remember conversation context

INFRASTRUCTURE DOMAINS:
- security: KMS, IAM, secrets, WAF (6 phases, ~30min)
- networking: VPC, subnets, flow logs (2 phases, ~20min)  
- compute: ECS, ECR, ALB, scaling (5 phases, ~35min)
- data: RDS, DynamoDB, Redis, S3 (5 phases, ~40min)
- application: Lambda, Step Functions, SNS (4 phases, ~25min)
- observability: CloudWatch, X-Ray, monitoring (3 phases, ~20min)
- ai-ml: Bedrock, RAG integration (1 phase, ~15min)
- governance: Budgets, compliance, Well-Architected (4 phases, ~15min)

Always maintain context and provide helpful, actionable responses."""

    def select_model(self, user_input: str, conversation_length: int) -> str:
        """Select optimal model based on complexity and cost"""
        
        # Use Sonnet for complex tasks
        complex_indicators = [
            'deploy everything', 'complete infrastructure', 'production',
            'rollback', 'troubleshoot', 'error', 'failed', 'issue'
        ]
        
        # Use Haiku for simple tasks
        simple_indicators = [
            'status', 'show', 'list', 'what', 'hello', 'hi', 'help'
        ]
        
        user_lower = user_input.lower()
        
        if any(indicator in user_lower for indicator in complex_indicators):
            return 'sonnet'
        elif any(indicator in user_lower for indicator in simple_indicators):
            return 'haiku'
        elif conversation_length > 5:  # Long conversations need context
            return 'sonnet'
        else:
            return 'haiku'  # Default to cost-effective option

    def invoke_bedrock(self, messages: List[Dict], model_type: str = 'haiku') -> Tuple[str, Dict]:
        """Invoke Bedrock with conversation messages"""
        
        model_id = self.models[model_type]
        max_tokens = self.token_limits[model_type]
        
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "system": self.system_prompt,
            "messages": messages,
            "temperature": 0.7
        }
        
        try:
            response = self.bedrock.invoke_model(
                modelId=model_id,
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            
            # Extract usage metrics
            usage = {
                'input_tokens': response_body.get('usage', {}).get('input_tokens', 0),
                'output_tokens': response_body.get('usage', {}).get('output_tokens', 0),
                'model': model_type,
                'timestamp': datetime.now().isoformat()
            }
            
            content = response_body['content'][0]['text']
            return content, usage
            
        except Exception as e:
            return f"❌ I'm having trouble processing your request: {str(e)}", {}

    def process_conversation(self, user_input: str, user_id: str, session_id: str = None) -> Dict:
        """Process a conversation turn with context awareness"""
        
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Get conversation history
        conversation_history = self.get_conversation_history(user_id, session_id)
        
        # Build messages for Bedrock
        messages = []
        
        # Add conversation history (last 10 turns for context)
        for turn in conversation_history[-10:]:
            messages.append({"role": "user", "content": turn.get('user_message', '')})
            if turn.get('assistant_response'):
                messages.append({"role": "assistant", "content": turn.get('assistant_response', '')})
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        # Select optimal model
        model_type = self.select_model(user_input, len(conversation_history))
        
        # Get response from Bedrock
        response, usage = self.invoke_bedrock(messages, model_type)
        
        # Store conversation turn
        conversation_data = {
            'user_id': user_id,
            'session_id': session_id,
            'user_message': user_input,
            'assistant_response': response,
            'model_used': model_type,
            'usage': usage,
            'timestamp': datetime.now().isoformat()
        }
        
        self.store_conversation_turn(conversation_data)
        
        return {
            'response': response,
            'session_id': session_id,
            'model_used': model_type,
            'usage': usage
        }

    def get_conversation_history(self, user_id: str, session_id: str, limit: int = 20) -> List[Dict]:
        """Retrieve conversation history from DynamoDB"""
        
        try:
            response = self.dynamodb.query(
                TableName='ial-conversation-history',
                KeyConditionExpression='user_id = :user_id AND begins_with(sort_key, :session)',
                ExpressionAttributeValues={
                    ':user_id': {'S': user_id},
                    ':session': {'S': f"SESSION#{session_id}"}
                },
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            
            history = []
            for item in reversed(response.get('Items', [])):  # Reverse to chronological order
                history.append({
                    'user_message': item.get('user_message', {}).get('S', ''),
                    'assistant_response': item.get('assistant_response', {}).get('S', ''),
                    'timestamp': item.get('timestamp', {}).get('S', ''),
                    'model_used': item.get('model_used', {}).get('S', ''),
                    'usage': json.loads(item.get('usage', {}).get('S', '{}'))
                })
            
            return history
            
        except Exception as e:
            print(f"Error retrieving conversation history: {e}")
            return []

    def store_conversation_turn(self, conversation_data: Dict):
        """Store conversation turn in DynamoDB"""
        
        try:
            item = {
                'user_id': {'S': conversation_data['user_id']},
                'sort_key': {'S': f"SESSION#{conversation_data['session_id']}#{conversation_data['timestamp']}"},
                'session_id': {'S': conversation_data['session_id']},
                'user_message': {'S': conversation_data['user_message']},
                'assistant_response': {'S': conversation_data['assistant_response']},
                'model_used': {'S': conversation_data['model_used']},
                'usage': {'S': json.dumps(conversation_data['usage'])},
                'timestamp': {'S': conversation_data['timestamp']},
                'ttl': {'N': str(int(datetime.now().timestamp()) + 86400 * 30)}  # 30 days TTL
            }
            
            self.dynamodb.put_item(
                TableName='ial-conversation-history',
                Item=item
            )
            
        except Exception as e:
            print(f"Error storing conversation: {e}")

    def get_session_context(self, user_id: str, session_id: str) -> Dict:
        """Get current session context and state"""
        
        try:
            response = self.dynamodb.get_item(
                TableName='ial-user-sessions',
                Key={
                    'user_id': {'S': user_id},
                    'session_id': {'S': session_id}
                }
            )
            
            if 'Item' in response:
                item = response['Item']
                return {
                    'current_domain': item.get('current_domain', {}).get('S', ''),
                    'last_action': item.get('last_action', {}).get('S', ''),
                    'deployment_state': json.loads(item.get('deployment_state', {}).get('S', '{}')),
                    'created_at': item.get('created_at', {}).get('S', ''),
                    'updated_at': item.get('updated_at', {}).get('S', '')
                }
            
            return {}
            
        except Exception as e:
            print(f"Error getting session context: {e}")
            return {}

    def update_session_context(self, user_id: str, session_id: str, context: Dict):
        """Update session context"""
        
        try:
            item = {
                'user_id': {'S': user_id},
                'session_id': {'S': session_id},
                'current_domain': {'S': context.get('current_domain', '')},
                'last_action': {'S': context.get('last_action', '')},
                'deployment_state': {'S': json.dumps(context.get('deployment_state', {}))},
                'updated_at': {'S': datetime.now().isoformat()},
                'ttl': {'N': str(int(datetime.now().timestamp()) + 86400 * 7)}  # 7 days TTL
            }
            
            # Add created_at if new session
            existing_context = self.get_session_context(user_id, session_id)
            if not existing_context:
                item['created_at'] = {'S': datetime.now().isoformat()}
            
            self.dynamodb.put_item(
                TableName='ial-user-sessions',
                Item=item
            )
            
        except Exception as e:
            print(f"Error updating session context: {e}")

# Example usage and testing
if __name__ == "__main__":
    engine = BedrockConversationEngine()
    
    # Test conversation
    test_user_id = "test-user-123"
    
    print("🧠 IaL Bedrock Conversation Engine Test")
    print("=" * 50)
    
    # Test inputs
    test_conversations = [
        "Hello, I need help with my infrastructure",
        "Deploy security for my production environment",
        "What's the current status of my deployments?",
        "Show me the networking configuration",
        "I want to rollback the compute changes"
    ]
    
    session_id = None
    for i, user_input in enumerate(test_conversations):
        print(f"\n👤 User: {user_input}")
        
        result = engine.process_conversation(user_input, test_user_id, session_id)
        session_id = result['session_id']  # Maintain session
        
        print(f"🤖 IaL: {result['response']}")
        print(f"📊 Model: {result['model_used']}, Tokens: {result['usage'].get('input_tokens', 0)}+{result['usage'].get('output_tokens', 0)}")
