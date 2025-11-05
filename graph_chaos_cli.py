#!/usr/bin/env python3
"""
Graph-based Chaos Engineering CLI
Unified interface for intelligent chaos experiments with dependency awareness
"""

import argparse
import json
import sys
from typing import Dict, Any, Optional
from core.chaos.chaos_controller import ChaosController, FailureType
from core.graph.dependency_graph import DependencyGraph

class GraphChaosCLI:
    """Unified CLI for graph-based chaos engineering"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.chaos_controller = ChaosController(region)
        self.dependency_graph = DependencyGraph()
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate chaos engineering configuration for conflicts"""
        
        validation = {
            "status": "valid",
            "architecture": "hybrid_specialized",
            "components": {
                "chaos_controller": {
                    "enabled": self.chaos_controller._is_chaos_explicitly_enabled(),
                    "responsibility": "application_level_chaos",
                    "failure_types": ["configuration_drift", "service_degradation"]
                },
                "aws_fis": {
                    "available": self.chaos_controller.fis_client is not None,
                    "responsibility": "infrastructure_level_chaos", 
                    "failure_types": ["instance_termination", "network_partition", "resource_exhaustion"]
                }
            },
            "conflicts": [],
            "recommendations": []
        }
        
        # Check for conflicts (should be none after refactoring)
        controller_types = set(self.chaos_controller.config.get("allowed_failure_types", []))
        fis_types = {"instance_termination", "network_partition", "resource_exhaustion"}
        
        overlap = controller_types.intersection(fis_types)
        if overlap:
            validation["conflicts"].append(f"Overlapping failure types: {list(overlap)}")
            validation["status"] = "conflict_detected"
        
        # Add recommendations
        if not validation["components"]["chaos_controller"]["enabled"]:
            validation["recommendations"].append("Chaos Controller is disabled - safe default")
        
        if not validation["components"]["aws_fis"]["available"]:
            validation["recommendations"].append("AWS FIS not available - infrastructure chaos limited")
        
        return validation
    
    def start_experiment(self, failure_type: str, target_resource: str, **kwargs) -> Dict[str, Any]:
        """Start chaos experiment with intelligent routing"""
        
        print(f"🎯 Starting chaos experiment: {failure_type} on {target_resource}")
        
        # Route based on failure type
        if failure_type in ["configuration_drift", "service_degradation"]:
            return self._start_application_chaos(failure_type, target_resource, **kwargs)
        elif failure_type in ["instance_termination", "network_partition", "resource_exhaustion"]:
            return self._start_infrastructure_chaos(failure_type, target_resource, **kwargs)
        else:
            return {
                "status": "unsupported",
                "message": f"Unknown failure type: {failure_type}",
                "supported_types": {
                    "application": ["configuration_drift", "service_degradation"],
                    "infrastructure": ["instance_termination", "network_partition", "resource_exhaustion"]
                }
            }
    
    def _start_application_chaos(self, failure_type: str, target_resource: str, **kwargs) -> Dict[str, Any]:
        """Start application-level chaos via Chaos Controller"""
        
        print(f"📱 Routing to Chaos Controller for application chaos")
        
        # Build experiment config
        experiment_config = {
            "failure_type": failure_type,
            "target_resource": target_resource,
            "blast_radius": kwargs.get("blast_radius", "minimal"),
            "duration": kwargs.get("duration", 300)
        }
        
        # Use dependency graph for intelligent targeting
        if hasattr(self.dependency_graph, 'analyze_impact'):
            impact_analysis = self.dependency_graph.analyze_impact(target_resource)
            experiment_config["dependency_analysis"] = impact_analysis
        
        return self.chaos_controller.start_game_day_experiment(experiment_config)
    
    def _start_infrastructure_chaos(self, failure_type: str, target_resource: str, **kwargs) -> Dict[str, Any]:
        """Start infrastructure-level chaos via AWS FIS delegation"""
        
        print(f"🏗️  Routing to AWS FIS for infrastructure chaos")
        
        if not self.chaos_controller.fis_client:
            return {
                "status": "unavailable",
                "message": "AWS FIS not available - infrastructure chaos disabled",
                "alternative": "Use application-level chaos types instead"
            }
        
        # Create experiment that will be delegated to FIS
        experiment_config = {
            "failure_type": failure_type,
            "target_resource": target_resource,
            "blast_radius": kwargs.get("blast_radius", "minimal"),
            "duration": kwargs.get("duration", 300)
        }
        
        return self.chaos_controller.start_game_day_experiment(experiment_config)
    
    def list_experiments(self) -> Dict[str, Any]:
        """List active chaos experiments"""
        
        active_experiments = self.chaos_controller.list_active_experiments()
        
        return {
            "active_experiments": active_experiments,
            "total_active": len(active_experiments),
            "architecture_info": self.chaos_controller.get_chaos_architecture_info()
        }
    
    def stop_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """Stop a running chaos experiment"""
        
        return self.chaos_controller.stop_experiment(experiment_id)
    
    def get_experiment_status(self, experiment_id: str) -> Dict[str, Any]:
        """Get status of a chaos experiment"""
        
        return self.chaos_controller.get_experiment_status(experiment_id)

def main():
    parser = argparse.ArgumentParser(description='Graph-based Chaos Engineering CLI')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Validate config
    validate_parser = subparsers.add_parser('validate-config', help='Validate chaos configuration')
    
    # Start experiment
    start_parser = subparsers.add_parser('start', help='Start chaos experiment')
    start_parser.add_argument('--type', required=True, help='Failure type')
    start_parser.add_argument('--target', required=True, help='Target resource')
    start_parser.add_argument('--blast-radius', default='minimal', help='Blast radius')
    start_parser.add_argument('--duration', type=int, default=300, help='Duration in seconds')
    
    # List experiments
    list_parser = subparsers.add_parser('list', help='List active experiments')
    
    # Stop experiment
    stop_parser = subparsers.add_parser('stop', help='Stop experiment')
    stop_parser.add_argument('--experiment-id', required=True, help='Experiment ID')
    
    # Get status
    status_parser = subparsers.add_parser('status', help='Get experiment status')
    status_parser.add_argument('--experiment-id', required=True, help='Experiment ID')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = GraphChaosCLI(args.region)
    
    try:
        if args.command == 'validate-config':
            result = cli.validate_config()
        elif args.command == 'start':
            result = cli.start_experiment(
                args.type, 
                args.target,
                blast_radius=args.blast_radius,
                duration=args.duration
            )
        elif args.command == 'list':
            result = cli.list_experiments()
        elif args.command == 'stop':
            result = cli.stop_experiment(args.experiment_id)
        elif args.command == 'status':
            result = cli.get_experiment_status(args.experiment_id)
        else:
            result = {"error": f"Unknown command: {args.command}"}
        
        print(json.dumps(result, indent=2, default=str))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()
