#!/usr/bin/env python3
"""
Bedrock Agent Core - Cérebro Cognitivo Principal do IAL
Integra com infraestrutura existente via tools
"""

import boto3
import json
import uuid
import os
from typing import Dict, Any, Optional
from datetime import datetime

class BedrockAgentCore:
    def __init__(self, region: str = None):
        self.region = region or boto3.Session().region_name or 'us-east-1'
        self.bedrock_agent = boto3.client('bedrock-agent-runtime', region_name=self.region)
        self.bedrock_agent_mgmt = boto3.client('bedrock-agent', region_name=self.region)
        
        # Load agent configuration from local file
        self.agent_config = self._load_agent_config()
        
        # Agent configuration
        self.agent_id = self.agent_config.get('agent_id')
        self.agent_alias_id = self.agent_config.get('agent_alias_id')
        self.session_id = str(uuid.uuid4())
        
        # Initialize tools
        self._init_tools()
        
    def _load_agent_config(self) -> Dict[str, Any]:
        """Load agent configuration from local file"""
        try:
            config_file = os.path.expanduser('~/.ial/agent_config.json')
            
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                # Validate configuration
                if config.get('bedrock_supported', False) and config.get('agent_id'):
                    return config
                else:
                    print("⚠️ Bedrock Agent not supported or not configured")
                    return {'bedrock_supported': False}
            else:
                print("⚠️ Agent config file not found - run 'ialctl start' first")
                return {'bedrock_supported': False}
                
        except Exception as e:
            print(f"⚠️ Error loading agent config: {e}")
            return {'bedrock_supported': False}
    
    def is_available(self) -> bool:
        """Check if Bedrock Agent is available and configured"""
        return (
            self.agent_config.get('bedrock_supported', False) and
            self.agent_id is not None and
            self.agent_alias_id is not None
        )
    
    def invoke_agent(self, user_input: str, session_id: str = None) -> Dict[str, Any]:
        """Invoke the Bedrock Agent with user input"""
        if not self.is_available():
            raise Exception("Bedrock Agent not available - falling back to NLP")
        
        try:
            session_id = session_id or self.session_id
            
            response = self.bedrock_agent.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=user_input
            )
            
            # Process streaming response
            result_text = ""
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        result_text += chunk['bytes'].decode('utf-8')
            
            return {
                'success': True,
                'response': result_text,
                'session_id': session_id,
                'agent_id': self.agent_id
            }
            
        except Exception as e:
            raise Exception(f"Agent invocation failed: {str(e)}")
        
    def _init_tools(self):
        """Initialize IAL tools for the agent"""
        try:
            from mcp_orchestrator import MCPOrchestrator
            from core.intent_cost_guardrails import IntentCostGuardrails
            from core.validation_system import IALValidationSystem
            from core.desired_state import DesiredStateBuilder
            from core.foundation_deployer import FoundationDeployer
            from core.drift.drift_detector import DriftDetector
            from core.drift.reverse_sync import ReverseSync
            
            self.mcp_orchestrator = MCPOrchestrator()
            self.cost_guardrails = IntentCostGuardrails()
            self.validation_system = IALValidationSystem()
            self.phase_builder = DesiredStateBuilder()
            self.foundation_deployer = FoundationDeployer()
            self.drift_detector = DriftDetector()
            self.reverse_sync = ReverseSync()
            
        except ImportError as e:
            print(f"⚠️ Tool initialization warning: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status and configuration"""
        return {
            'agent_available': self.is_available(),
            'agent_id': self.agent_id,
            'agent_alias_id': self.agent_alias_id,
            'region': self.region,
            'bedrock_supported': self.agent_config.get('bedrock_supported', False),
            'config_file_exists': os.path.exists(os.path.expanduser('~/.ial/agent_config.json')),
            'configured_at': self.agent_config.get('configured_at')
        }
        try:
            # Agent instruction
            instruction = """You are IALCoreBrain, the cognitive core of the Infrastructure Assistant Layer (IAL).

Your role is to help users manage AWS infrastructure through natural conversation.

CAPABILITIES:
- Consult AWS documentation via get_aws_docs
- Estimate costs via estimate_cost  
- Validate risks via risk_validation
- Generate infrastructure phases via generate_phases
- Apply phases via apply_phase
- Check drift via check_drift
- Perform reverse sync via reverse_sync

BEHAVIOR:
- Always validate costs and risks before applying changes
- Ask for confirmation before destructive operations
- Provide clear explanations of what will be deployed
- Use existing IAL infrastructure (Step Functions, Lambdas, CloudFormation)
- Maintain conversation context and memory

WORKFLOW:
1. Understand user intent
2. Consult documentation if needed
3. Validate costs and risks
4. Generate phases preview
5. Ask for confirmation
6. Apply if confirmed
7. Monitor and validate deployment
"""

            # Create agent
            response = self.bedrock_agent_mgmt.create_agent(
                agentName='IALCoreBrain',
                description='Cognitive core for Infrastructure Assistant Layer',
                instruction=instruction,
                foundationModel='anthropic.claude-3-5-sonnet-20241022-v2:0',
                idleSessionTTLInSeconds=3600
            )
            
            self.agent_id = response['agent']['agentId']
            
            # Create agent action groups (tools)
            self._create_action_groups()
            
            # Prepare agent
            self.bedrock_agent_mgmt.prepare_agent(agentId=self.agent_id)
            
            # Create alias
            alias_response = self.bedrock_agent_mgmt.create_agent_alias(
                agentId=self.agent_id,
                agentAliasName='DRAFT'
            )
            
            self.agent_alias_id = alias_response['agentAlias']['agentAliasId']
            
            return {
                'success': True,
                'agent_id': self.agent_id,
                'agent_alias_id': self.agent_alias_id
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _create_action_groups(self):
        """Create action groups for IAL tools"""
        
        # Tool schemas
        tools_schema = {
            "openapi": "3.0.0",
            "info": {"title": "IAL Tools", "version": "1.0.0"},
            "paths": {
                "/get_aws_docs": {
                    "post": {
                        "description": "Get AWS documentation via MCP",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Documentation query"}
                            },
                            "required": ["query"]
                        }
                    }
                },
                "/estimate_cost": {
                    "post": {
                        "description": "Estimate infrastructure costs",
                        "parameters": {
                            "type": "object", 
                            "properties": {
                                "intent": {"type": "string", "description": "Infrastructure intent"}
                            },
                            "required": ["intent"]
                        }
                    }
                },
                "/risk_validation": {
                    "post": {
                        "description": "Validate infrastructure risks",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "intent": {"type": "string", "description": "Infrastructure intent"}
                            },
                            "required": ["intent"]
                        }
                    }
                },
                "/generate_phases": {
                    "post": {
                        "description": "Generate infrastructure phases",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "intent": {"type": "string", "description": "Infrastructure intent"}
                            },
                            "required": ["intent"]
                        }
                    }
                },
                "/apply_phase": {
                    "post": {
                        "description": "Apply infrastructure phase",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "phase": {"type": "string", "description": "Phase to apply"}
                            },
                            "required": ["phase"]
                        }
                    }
                },
                "/check_drift": {
                    "post": {
                        "description": "Check infrastructure drift",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                },
                "/reverse_sync": {
                    "post": {
                        "description": "Perform reverse sync",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                }
            }
        }
        
        # Create action group
        self.bedrock_agent_mgmt.create_agent_action_group(
            agentId=self.agent_id,
            agentVersion='DRAFT',
            actionGroupName='IALTools',
            description='IAL infrastructure tools',
            actionGroupExecutor={
                'lambda': 'arn:aws:lambda:us-east-1:123456789012:function:ial-agent-tools'
            },
            apiSchema={
                'payload': json.dumps(tools_schema)
            }
        )
    
    def invoke_agent(self, message: str) -> Dict[str, Any]:
        """Invoke agent with user message"""
        try:
            response = self.bedrock_agent.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=self.session_id,
                inputText=message
            )
            
            # Process response stream
            result = ""
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        result += chunk['bytes'].decode('utf-8')
            
            return {
                'success': True,
                'response': result,
                'session_id': self.session_id
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            'agent_id': self.agent_id,
            'agent_alias_id': self.agent_alias_id,
            'session_id': self.session_id,
            'region': self.region
        }
