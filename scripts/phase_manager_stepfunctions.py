#!/usr/bin/env python3
"""
Step Functions-based Phase Manager
Replaces manual DAG processing with AWS Step Functions
"""

import json
import boto3
import time
from pathlib import Path
from typing import Dict, List

class StepFunctionsPhaseManager:
    """Lightweight phase manager that delegates to Step Functions"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.stepfunctions = boto3.client('stepfunctions', region_name=region)
        self.state_machine_arn = f"arn:aws:states:{region}:{{account_id}}:stateMachine:ial-phase-manager"
        
    def execute_phases(self) -> Dict[str, any]:
        """Delegate phase execution to Step Functions"""
        
        correlation_id = f"phases-{int(time.time())}"
        
        execution_input = {
            "correlation_id": correlation_id
        }
        
        try:
            response = self.stepfunctions.start_execution(
                stateMachineArn=self.state_machine_arn,
                name=f"phases-{correlation_id}",
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

# Lambda functions
class PhaseDiscoverer:
    """Lambda to discover phases from filesystem"""
    
    def lambda_handler(self, event, context):
        PROJECT_ROOT = Path("/home/ial")
        PHASES_DIR = PROJECT_ROOT / 'phases'
        
        phases = {}
        
        for domain_dir in PHASES_DIR.iterdir():
            if not domain_dir.is_dir() or domain_dir.name.startswith('.'):
                continue
                
            domain_name = domain_dir.name
            phases[domain_name] = []
            
            for yaml_file in domain_dir.glob('*.yaml'):
                if yaml_file.name == 'domain-metadata.yaml':
                    continue
                    
                phases[domain_name].append({
                    'name': yaml_file.stem,
                    'file': str(yaml_file),
                    'domain': domain_name
                })
        
        return {"discovered_phases": phases}

class DependencyInferrer:
    """Lambda to infer dependencies using Bedrock"""
    
    def lambda_handler(self, event, context):
        import boto3
        
        phases = event.get("discovered_phases", {})
        bedrock = boto3.client('bedrock-runtime')
        
        # Simplified dependency inference
        dependencies = {}
        
        # Foundation phases always first
        foundation_phases = phases.get("00-foundation", [])
        for phase in foundation_phases:
            dependencies[phase["name"]] = []
        
        # Other phases depend on foundation
        foundation_names = [p["name"] for p in foundation_phases]
        
        for domain, domain_phases in phases.items():
            if domain == "00-foundation":
                continue
                
            for phase in domain_phases:
                dependencies[phase["name"]] = foundation_names.copy()
        
        return {"inferred_dependencies": dependencies}

class ExecutionPlanner:
    """Lambda to create execution plan"""
    
    def lambda_handler(self, event, context):
        import networkx as nx
        
        phases = event.get("discovered_phases", {})
        dependencies = event.get("inferred_dependencies", {})
        
        # Build execution graph
        graph = nx.DiGraph()
        
        # Add all phases
        all_phases = []
        for domain_phases in phases.values():
            all_phases.extend(domain_phases)
        
        for phase in all_phases:
            graph.add_node(phase["name"], **phase)
        
        # Add dependencies
        for phase_name, deps in dependencies.items():
            for dep in deps:
                if dep in graph.nodes:
                    graph.add_edge(dep, phase_name)
        
        # Get topological order
        try:
            execution_order = list(nx.topological_sort(graph))
            phase_details = []
            
            for phase_name in execution_order:
                phase_data = graph.nodes[phase_name]
                phase_details.append(phase_data)
            
            return {
                "execution_order": phase_details,
                "total_phases": len(phase_details)
            }
            
        except nx.NetworkXError as e:
            return {
                "error": f"Circular dependency detected: {str(e)}",
                "execution_order": []
            }

class PhaseExecutor:
    """Lambda to execute individual phase"""
    
    def lambda_handler(self, event, context):
        import subprocess
        import yaml
        
        phase = event.get("phase", {})
        phase_file = phase.get("file")
        
        if not phase_file or not Path(phase_file).exists():
            return {
                "success": False,
                "message": f"Phase file not found: {phase_file}"
            }
        
        try:
            # Execute CloudFormation deployment
            result = subprocess.run([
                "aws", "cloudformation", "deploy",
                "--template-file", phase_file,
                "--stack-name", f"ial-{phase['name']}",
                "--capabilities", "CAPABILITY_IAM"
            ], capture_output=True, text=True, timeout=300)
            
            return {
                "success": result.returncode == 0,
                "message": result.stdout if result.returncode == 0 else result.stderr,
                "phase_name": phase["name"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "phase_name": phase["name"]
            }
