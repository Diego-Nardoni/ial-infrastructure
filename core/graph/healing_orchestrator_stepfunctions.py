#!/usr/bin/env python3
"""
Step Functions-based Healing Orchestrator
Replaces manual orchestration with AWS Step Functions
"""

import json
import boto3
import time
from typing import Dict, List, Optional
from core.graph.dependency_graph import DependencyGraph

class StepFunctionsHealingOrchestrator:
    """Lightweight orchestrator that delegates to Step Functions"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.stepfunctions = boto3.client('stepfunctions', region_name=region)
        self.state_machine_arn = f"arn:aws:states:{region}:{{account_id}}:stateMachine:ial-healing-orchestrator"
        
    def orchestrate_healing(self, failed_resources: List[str] = None) -> Dict[str, any]:
        """Delegate healing to Step Functions"""
        
        correlation_id = f"healing-{int(time.time())}"
        
        execution_input = {
            "failed_resources": failed_resources or [],
            "region": self.region,
            "correlation_id": correlation_id
        }
        
        try:
            # Start Step Functions execution
            response = self.stepfunctions.start_execution(
                stateMachineArn=self.state_machine_arn,
                name=f"healing-{correlation_id}",
                input=json.dumps(execution_input)
            )
            
            return {
                "status": "started",
                "execution_arn": response["executionArn"],
                "correlation_id": correlation_id,
                "message": "Healing orchestration delegated to Step Functions"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to start Step Functions execution: {str(e)}",
                "correlation_id": correlation_id
            }
    
    def get_execution_status(self, execution_arn: str) -> Dict[str, any]:
        """Get Step Functions execution status"""
        try:
            response = self.stepfunctions.describe_execution(executionArn=execution_arn)
            return {
                "status": response["status"],
                "output": json.loads(response.get("output", "{}")),
                "start_date": response["startDate"].isoformat(),
                "stop_date": response.get("stopDate", {}).isoformat() if response.get("stopDate") else None
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

# Lambda functions for Step Functions
class HealingInitializer:
    """Lambda function to initialize healing plan"""
    
    def __init__(self, region: str = "us-east-1"):
        self.dependency_graph = DependencyGraph(region=region, enable_persistence=True)
    
    def lambda_handler(self, event, context):
        failed_resources = event.get("failed_resources", [])
        
        # Load resources into graph
        for resource_id in failed_resources:
            if resource_id not in self.dependency_graph.nodes:
                self.dependency_graph.load_resource_from_persistence(resource_id)
        
        # Get healing order
        healing_order = self.dependency_graph.get_healing_order()
        
        # Create batches (max 5 resources per batch)
        healing_batches = []
        batch_size = 5
        for i in range(0, len(healing_order), batch_size):
            batch = healing_order[i:i + batch_size]
            healing_batches.append(batch)
        
        return {
            "has_resources": len(healing_order) > 0,
            "healing_batches": healing_batches,
            "total_resources": len(healing_order)
        }

class ResourceHealer:
    """Lambda function to heal resource batch"""
    
    def lambda_handler(self, event, context):
        from core.drift.auto_healer import AutoHealer
        
        batch = event.get("batch", [])
        correlation_id = event.get("correlation_id")
        
        healer = AutoHealer()
        results = []
        
        for resource_id in batch:
            try:
                result = healer.heal_resource(resource_id)
                results.append({
                    "resource_id": resource_id,
                    "success": result.get("success", False),
                    "message": result.get("message", ""),
                    "correlation_id": correlation_id
                })
            except Exception as e:
                results.append({
                    "resource_id": resource_id,
                    "success": False,
                    "message": str(e),
                    "correlation_id": correlation_id
                })
        
        return {"batch_results": results}

class HealingAggregator:
    """Lambda function to aggregate healing results"""
    
    def lambda_handler(self, event, context):
        healing_results = event.get("healing_results", [])
        
        all_results = []
        success_count = 0
        
        for batch_result in healing_results:
            batch_data = batch_result.get("Payload", {}).get("batch_results", [])
            for result in batch_data:
                all_results.append(result)
                if result.get("success"):
                    success_count += 1
        
        return {
            "status": "completed",
            "total_resources": len(all_results),
            "successful_healings": success_count,
            "failed_healings": len(all_results) - success_count,
            "results": all_results
        }
