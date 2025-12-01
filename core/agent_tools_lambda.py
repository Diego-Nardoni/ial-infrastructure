#!/usr/bin/env python3
"""
Lambda Function for Bedrock Agent Tools
Executes IAL operations as agent tools
"""

import json
import sys
import os

# Add IAL path
sys.path.append('/opt/ial')

def lambda_handler(event, context):
    """Handle agent tool invocations"""
    
    try:
        # Parse agent request
        action_group = event.get('actionGroup', '')
        api_path = event.get('apiPath', '')
        parameters = event.get('parameters', [])
        
        # Convert parameters to dict
        params = {}
        for param in parameters:
            params[param['name']] = param['value']
        
        # Route to appropriate tool
        if api_path == '/get_aws_docs':
            result = tool_get_aws_docs(params)
        elif api_path == '/estimate_cost':
            result = tool_estimate_cost(params)
        elif api_path == '/risk_validation':
            result = tool_risk_validation(params)
        elif api_path == '/generate_phases':
            result = tool_generate_phases(params)
        elif api_path == '/apply_phase':
            result = tool_apply_phase(params)
        elif api_path == '/check_drift':
            result = tool_check_drift(params)
        elif api_path == '/reverse_sync':
            result = tool_reverse_sync(params)
        else:
            result = {'error': f'Unknown tool: {api_path}'}
        
        # Return agent response format
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action_group,
                'apiPath': api_path,
                'httpMethod': 'POST',
                'httpStatusCode': 200,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps(result)
                    }
                }
            }
        }
        
    except Exception as e:
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action_group,
                'apiPath': api_path,
                'httpMethod': 'POST',
                'httpStatusCode': 500,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps({'error': str(e)})
                    }
                }
            }
        }

def tool_get_aws_docs(params):
    """Tool: Get AWS documentation via MCP"""
    try:
        from mcp_orchestrator import MCPOrchestrator
        
        orchestrator = MCPOrchestrator()
        query = params.get('query', '')
        
        # Execute MCP AWS Official
        result = orchestrator.execute_mcp_group('MCP_AWS_OFFICIAL', query)
        
        return {
            'success': True,
            'documentation': result.get('documentation', ''),
            'query': query
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def tool_estimate_cost(params):
    """Tool: Estimate infrastructure costs"""
    try:
        from core.intent_cost_guardrails import IntentCostGuardrails
        
        cost_guardrails = IntentCostGuardrails()
        intent = params.get('intent', '')
        
        result = cost_guardrails.validate_cost(intent)
        
        return {
            'success': True,
            'cost_estimate': result.get('cost_estimate', {}),
            'monthly_cost': result.get('monthly_cost', 0),
            'risk_level': result.get('risk_level', 'unknown')
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def tool_risk_validation(params):
    """Tool: Validate infrastructure risks"""
    try:
        from core.validation_system import IALValidationSystem
        
        validator = IALValidationSystem()
        intent = params.get('intent', '')
        
        # Use validation system to assess risks
        result = validator.validate_complete_deployment()
        
        return {
            'success': True,
            'risk_level': 'medium',  # Default assessment
            'validation_result': result,
            'recommendations': ['Review security groups', 'Check IAM policies']
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def tool_generate_phases(params):
    """Tool: Generate infrastructure phases"""
    try:
        from core.desired_state import DesiredStateBuilder
        
        phase_builder = DesiredStateBuilder()
        intent = params.get('intent', '')
        
        result = phase_builder.build_desired_spec([intent])
        
        return {
            'success': True,
            'phases': result.get('phases', []),
            'dag': result.get('dag', {}),
            'preview': True  # Always preview first
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def tool_apply_phase(params):
    """Tool: Apply infrastructure phase"""
    try:
        from core.foundation_deployer import FoundationDeployer
        
        deployer = FoundationDeployer()
        phase = params.get('phase', '')
        
        result = deployer.deploy_phase(phase)
        
        return {
            'success': True,
            'phase': phase,
            'deployment_result': result.get('deployment_result', {}),
            'stack_status': result.get('stack_status', 'unknown')
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def tool_check_drift(params):
    """Tool: Check infrastructure drift"""
    try:
        from core.drift.drift_detector import DriftDetector
        
        drift_detector = DriftDetector()
        result = drift_detector.detect_drift()
        
        return {
            'success': True,
            'drift_items': result,
            'drift_count': len(result),
            'has_drift': len(result) > 0
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def tool_reverse_sync(params):
    """Tool: Perform reverse sync"""
    try:
        from core.drift.reverse_sync import ReverseSync
        
        reverse_sync = ReverseSync()
        result = reverse_sync.sync_from_aws()
        
        return {
            'success': True,
            'sync_result': result.get('sync_result', {}),
            'changes_made': result.get('changes_made', [])
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}
