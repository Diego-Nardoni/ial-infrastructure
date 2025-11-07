#!/usr/bin/env python3
"""
Step Functions-based Audit Validator
Replaces manual validation with AWS Step Functions parallel processing
"""

import json
import boto3
import time
from typing import Dict, List, Optional

class StepFunctionsAuditValidator:
    """Lightweight audit validator that delegates to Step Functions"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.stepfunctions = boto3.client('stepfunctions', region_name=region)
        self.state_machine_arn = f"arn:aws:states:{region}:{{account_id}}:stateMachine:ial-audit-validator"
        
    def validate_completeness_with_enforcement(self, desired_spec_path: str = "reports/desired_spec.json") -> Dict:
        """Delegate audit validation to Step Functions"""
        
        correlation_id = f"audit-{int(time.time())}"
        
        execution_input = {
            "desired_spec_path": desired_spec_path,
            "correlation_id": correlation_id
        }
        
        try:
            response = self.stepfunctions.start_execution(
                stateMachineArn=self.state_machine_arn,
                name=f"audit-{correlation_id}",
                input=json.dumps(execution_input)
            )
            
            return {
                "status": "started",
                "execution_arn": response["executionArn"],
                "correlation_id": correlation_id
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "correlation_id": correlation_id
            }

# Lambda functions for Step Functions
class AuditInitializer:
    """Lambda to initialize audit configuration"""
    
    def lambda_handler(self, event, context):
        import json
        from pathlib import Path
        
        desired_spec_path = event.get("desired_spec_path", "reports/desired_spec.json")
        
        try:
            with open(desired_spec_path, 'r') as f:
                desired_spec = json.load(f)
            
            return {
                "desired_spec": desired_spec,
                "spec_path": desired_spec_path,
                "resource_count": len(desired_spec.get("resources", []))
            }
            
        except Exception as e:
            return {
                "error": f"Failed to load desired spec: {str(e)}",
                "desired_spec": {},
                "resource_count": 0
            }

class CloudFormationValidator:
    """Lambda to validate CloudFormation state"""
    
    def lambda_handler(self, event, context):
        import boto3
        
        audit_config = event.get("audit_config", {})
        desired_spec = audit_config.get("desired_spec", {})
        
        cloudformation = boto3.client('cloudformation')
        
        cf_resources = {}
        cf_stacks = []
        
        try:
            # Get all stacks
            paginator = cloudformation.get_paginator('list_stacks')
            for page in paginator.paginate():
                for stack in page['StackSummaries']:
                    if stack['StackStatus'] not in ['DELETE_COMPLETE']:
                        cf_stacks.append(stack['StackName'])
            
            # Get resources from stacks
            for stack_name in cf_stacks:
                try:
                    resources = cloudformation.list_stack_resources(StackName=stack_name)
                    for resource in resources['StackResourceSummaries']:
                        cf_resources[resource['PhysicalResourceId']] = {
                            'type': resource['ResourceType'],
                            'status': resource['ResourceStatus'],
                            'stack': stack_name
                        }
                except Exception:
                    continue
            
            return {
                "validation_type": "cloudformation",
                "resources_found": len(cf_resources),
                "stacks_found": len(cf_stacks),
                "resources": cf_resources
            }
            
        except Exception as e:
            return {
                "validation_type": "cloudformation",
                "error": str(e),
                "resources_found": 0,
                "resources": {}
            }

class AWSRealValidator:
    """Lambda to validate real AWS state"""
    
    def lambda_handler(self, event, context):
        from core.resource_catalog import ResourceCatalog
        
        audit_config = event.get("audit_config", {})
        
        try:
            catalog = ResourceCatalog()
            real_resources = catalog.get_all_resources()
            
            return {
                "validation_type": "aws_real",
                "resources_found": len(real_resources),
                "resources": real_resources
            }
            
        except Exception as e:
            return {
                "validation_type": "aws_real",
                "error": str(e),
                "resources_found": 0,
                "resources": {}
            }

class KnowledgeGraphValidator:
    """Lambda to validate Knowledge Graph state"""
    
    def lambda_handler(self, event, context):
        try:
            from core.graph.dependency_graph import DependencyGraph
            
            graph = DependencyGraph(enable_persistence=True)
            graph_resources = {}
            
            for node_id, node in graph.nodes.items():
                graph_resources[node_id] = {
                    'type': node.resource_type,
                    'state': node.state.value,
                    'dependencies': len(node.dependencies)
                }
            
            return {
                "validation_type": "knowledge_graph",
                "resources_found": len(graph_resources),
                "resources": graph_resources
            }
            
        except Exception as e:
            return {
                "validation_type": "knowledge_graph",
                "error": str(e),
                "resources_found": 0,
                "resources": {}
            }

class AuditAggregator:
    """Lambda to aggregate audit results"""
    
    def lambda_handler(self, event, context):
        validation_results = event.get("validation_results", [])
        
        # Extract results from parallel branches
        cf_result = validation_results[0].get("Payload", {})
        aws_result = validation_results[1].get("Payload", {})
        graph_result = validation_results[2].get("Payload", {})
        
        # Calculate completeness
        total_desired = cf_result.get("resources_found", 0)
        cf_found = cf_result.get("resources_found", 0)
        aws_found = aws_result.get("resources_found", 0)
        graph_found = graph_result.get("resources_found", 0)
        
        if total_desired > 0:
            completeness_percentage = min(100, (aws_found / total_desired) * 100)
        else:
            completeness_percentage = 0
        
        return {
            "completeness_percentage": completeness_percentage,
            "cloudformation_resources": cf_found,
            "aws_real_resources": aws_found,
            "knowledge_graph_resources": graph_found,
            "validation_summary": {
                "cloudformation": cf_result,
                "aws_real": aws_result,
                "knowledge_graph": graph_result
            }
        }

class ComplianceEnforcer:
    """Lambda to enforce compliance when audit fails"""
    
    def lambda_handler(self, event, context):
        import boto3
        
        audit_results = event.get("audit_results", {})
        completeness = audit_results.get("completeness_percentage", 0)
        
        # Send SNS notification
        try:
            sns = boto3.client('sns')
            message = f"""
            IAL AUDIT VALIDATION FAILED
            
            Completeness: {completeness}%
            Required: 100%
            
            Action Required: Manual intervention needed
            """
            
            sns.publish(
                TopicArn=f"arn:aws:sns:{os.environ.get('AWS_REGION', 'us-east-1')}:{os.environ.get('AWS_ACCOUNT_ID')}:{os.environ.get('PROJECT_NAME', 'ial')}-audit-alerts",
                Message=message,
                Subject="IAL Audit Validation Failed"
            )
            
        except Exception as e:
            print(f"Failed to send SNS notification: {e}")
        
        return {
            "enforcement_action": "notification_sent",
            "completeness_percentage": completeness,
            "status": "failed"
        }
