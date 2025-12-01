#!/usr/bin/env python3
"""
Setup Bedrock Agent Core for IAL
Creates agent, deploys Lambda, and configures tools
"""

import sys
import os
import boto3
import json
from typing import Dict, Any

sys.path.insert(0, '/home/ial')

def main():
    """Setup Bedrock Agent Core"""
    print("🧠 Setting up IAL Bedrock Agent Core...")
    
    try:
        # Step 1: Deploy Lambda function
        print("1️⃣ Deploying Agent Tools Lambda...")
        lambda_result = deploy_agent_lambda()
        if not lambda_result.get('success'):
            print(f"❌ Lambda deployment failed: {lambda_result.get('error')}")
            return 1
        
        lambda_arn = lambda_result.get('lambda_arn')
        print(f"✅ Lambda deployed: {lambda_arn}")
        
        # Step 2: Create Bedrock Agent
        print("2️⃣ Creating Bedrock Agent...")
        agent_result = create_bedrock_agent(lambda_arn)
        if not agent_result.get('success'):
            print(f"❌ Agent creation failed: {agent_result.get('error')}")
            return 1
        
        agent_id = agent_result.get('agent_id')
        agent_alias_id = agent_result.get('agent_alias_id')
        print(f"✅ Agent created: {agent_id}")
        print(f"✅ Agent alias: {agent_alias_id}")
        
        # Step 3: Update Lambda with agent ARN
        print("3️⃣ Updating Lambda configuration...")
        update_result = update_lambda_config(lambda_arn, agent_id)
        if not update_result.get('success'):
            print(f"⚠️ Lambda update warning: {update_result.get('error')}")
        
        # Step 4: Test integration
        print("4️⃣ Testing integration...")
        test_result = test_agent_integration(agent_id, agent_alias_id)
        if test_result.get('success'):
            print("✅ Integration test passed")
        else:
            print(f"⚠️ Integration test warning: {test_result.get('error')}")
        
        print("\n🎉 Bedrock Agent Core setup complete!")
        print(f"🆔 Agent ID: {agent_id}")
        print(f"🔗 Agent Alias: {agent_alias_id}")
        print(f"⚡ Lambda ARN: {lambda_arn}")
        print("\n🚀 You can now use: python3 ialctl_agent_enhanced.py")
        
        return 0
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return 1

def deploy_agent_lambda():
    """Deploy Agent Tools Lambda via CloudFormation"""
    try:
        from core.foundation_deployer import FoundationDeployer
        
        deployer = FoundationDeployer()
        
        # Deploy the agent lambda template
        result = deployer.deploy_template(
            template_path='phases/00-foundation/43-bedrock-agent-lambda.yaml',
            stack_name='ial-bedrock-agent-lambda'
        )
        
        if result.get('success'):
            # Get Lambda ARN from stack outputs
            cf_client = boto3.client('cloudformation')
            stack_info = cf_client.describe_stacks(StackName='ial-bedrock-agent-lambda')
            
            outputs = stack_info['Stacks'][0].get('Outputs', [])
            lambda_arn = None
            
            for output in outputs:
                if output['OutputKey'] == 'AgentToolsLambdaArn':
                    lambda_arn = output['OutputValue']
                    break
            
            if lambda_arn:
                return {'success': True, 'lambda_arn': lambda_arn}
            else:
                return {'success': False, 'error': 'Lambda ARN not found in outputs'}
        else:
            return {'success': False, 'error': result.get('error', 'Unknown deployment error')}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

def create_bedrock_agent(lambda_arn):
    """Create Bedrock Agent with tools"""
    try:
        from core.bedrock_agent_core import BedrockAgentCore
        
        agent_core = BedrockAgentCore()
        
        # Update lambda ARN in agent core
        agent_core.lambda_arn = lambda_arn
        
        result = agent_core.create_agent()
        return result
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def update_lambda_config(lambda_arn, agent_id):
    """Update Lambda with agent configuration"""
    try:
        lambda_client = boto3.client('lambda')
        
        # Update environment variables
        lambda_client.update_function_configuration(
            FunctionName=lambda_arn,
            Environment={
                'Variables': {
                    'IAL_AGENT_ID': agent_id,
                    'IAL_PROJECT_NAME': 'ial',
                    'IAL_REGION': boto3.Session().region_name or 'us-east-1'
                }
            }
        )
        
        return {'success': True}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def test_agent_integration(agent_id, agent_alias_id):
    """Test agent integration"""
    try:
        from core.ialctl_agent_integration import IALCTLAgentIntegration
        
        integration = IALCTLAgentIntegration()
        
        # Test simple message
        result = integration.process_message("Hello, can you help me with AWS infrastructure?")
        
        if result.get('success'):
            return {'success': True, 'response': result.get('response')}
        else:
            return {'success': False, 'error': result.get('error')}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

if __name__ == '__main__':
    sys.exit(main())
