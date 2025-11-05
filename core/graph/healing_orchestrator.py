import time
from typing import Dict, List, Optional, Tuple
from core.graph.dependency_graph import DependencyGraph, ResourceState, ResourceNode
from core.drift.auto_healer import AutoHealer
from core.decision_ledger import DecisionLedger

class HealingResult:
    def __init__(self, resource_id: str, success: bool, message: str, duration: float):
        self.resource_id = resource_id
        self.success = success
        self.message = message
        self.duration = duration
        self.timestamp = time.time()

class GraphBasedHealingOrchestrator:
    """
    Intelligent healing orchestrator that uses dependency graph for safe healing
    """
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.auto_healer = AutoHealer(region)
        self.decision_ledger = DecisionLedger()
        self.healing_history: List[HealingResult] = []
        
        # Initialize dependency graph with persistence
        self.dependency_graph = DependencyGraph(region=region, enable_persistence=True)
        print("✅ HealingOrchestrator: Grafo persistente habilitado")
        
    def orchestrate_healing(self, failed_resources: List[str] = None) -> Dict[str, any]:
        """Orchestrate intelligent healing based on persistent dependency graph"""
        
        print("🔧 Starting graph-based healing orchestration...")
        start_time = time.time()
        
        # Load failed resources into graph if provided
        if failed_resources:
            for resource_id in failed_resources:
                # Load resource from persistence if not in memory
                if resource_id not in self.dependency_graph.nodes:
                    self.dependency_graph.load_resource_from_persistence(resource_id)
                
                # Mark as needing healing
                if resource_id in self.dependency_graph.nodes:
                    self.dependency_graph.nodes[resource_id].state = ResourceState.DRIFT
        
        # Get optimal healing order from persistent graph
        healing_order = self.dependency_graph.get_healing_order()
        
        if not healing_order:
            print("✅ No resources need healing")
            return {
                "status": "no_healing_needed",
                "resources_healed": 0,
                "duration": time.time() - start_time
            }
        
        print(f"📋 Healing order calculated: {len(healing_order)} resources")
        
        # Execute healing in dependency-aware order
        results = []
        successful_healings = 0
        failed_healings = 0
        
        for resource_id in healing_order:
            result = self._heal_resource_safely(graph, resource_id)
            results.append(result)
            
            if result.success:
                successful_healings += 1
                # Update graph state
                graph.nodes[resource_id].state = ResourceState.HEALTHY
            else:
                failed_healings += 1
                # Update graph state
                graph.nodes[resource_id].state = ResourceState.FAILED
                
                # Check if we should stop healing due to cascade risk
                if self._should_stop_healing(graph, resource_id, result):
                    print(f"🛑 Stopping healing due to cascade risk from {resource_id}")
                    break
        
        total_duration = time.time() - start_time
        
        # Log overall healing operation
        self.decision_ledger.log(
            phase="graph-healing",
            mcp="healing-orchestrator",
            tool="orchestrate_healing",
            rationale=f"Healed {successful_healings}/{len(healing_order)} resources in dependency order",
            status="COMPLETED" if failed_healings == 0 else "PARTIAL"
        )
        
        return {
            "status": "completed",
            "resources_healed": successful_healings,
            "resources_failed": failed_healings,
            "total_resources": len(healing_order),
            "healing_order": healing_order,
            "results": [{"resource_id": r.resource_id, "success": r.success, "message": r.message} for r in results],
            "duration": total_duration
        }
    
    def _heal_resource_safely(self, graph: DependencyGraph, resource_id: str) -> HealingResult:
        """Heal a single resource with safety checks"""
        
        start_time = time.time()
        node = graph.nodes[resource_id]
        
        print(f"🔧 Healing {resource_id} ({node.type})")
        
        # Pre-healing safety validation
        safety_check = graph.validate_healing_safety(resource_id)
        
        if not safety_check["safe"]:
            message = f"Healing blocked: {', '.join(safety_check['blockers'])}"
            print(f"🚫 {message}")
            
            result = HealingResult(resource_id, False, message, time.time() - start_time)
            self.healing_history.append(result)
            return result
        
        # Log warnings
        for warning in safety_check["warnings"]:
            print(f"⚠️ {warning}")
        
        # Verify dependencies are healthy
        unhealthy_deps = self._check_dependencies_health(graph, resource_id)
        if unhealthy_deps:
            # Try to heal dependencies first
            for dep_id in unhealthy_deps:
                if graph.nodes[dep_id].state == ResourceState.DRIFT:
                    print(f"🔄 Healing dependency {dep_id} first")
                    dep_result = self._heal_resource_safely(graph, dep_id)
                    if not dep_result.success:
                        message = f"Failed to heal dependency {dep_id}: {dep_result.message}"
                        result = HealingResult(resource_id, False, message, time.time() - start_time)
                        self.healing_history.append(result)
                        return result
        
        # Perform the actual healing
        try:
            # Update state to healing
            graph.nodes[resource_id].state = ResourceState.HEALING
            
            # Create drift item for auto healer
            drift_item = {
                "resource_id": resource_id,
                "drift_type": "configuration_drift",
                "desired": {"state": "healthy"},
                "current": {"state": "drift"},
                "severity": "medium"
            }
            
            # Use existing auto healer
            heal_result = self.auto_healer.heal_drift(drift_item)
            
            if heal_result.get("status") == "updated":
                # Verify healing didn't break dependents
                broken_dependents = self._verify_dependents_health(graph, resource_id)
                
                if broken_dependents:
                    # Rollback healing
                    print(f"🔄 Rolling back {resource_id} due to broken dependents: {broken_dependents}")
                    self._rollback_healing(graph, resource_id)
                    
                    message = f"Healing rolled back - broke dependents: {broken_dependents}"
                    result = HealingResult(resource_id, False, message, time.time() - start_time)
                else:
                    message = f"Successfully healed {resource_id}"
                    result = HealingResult(resource_id, True, message, time.time() - start_time)
            else:
                message = f"Healing failed: {heal_result.get('error', 'Unknown error')}"
                result = HealingResult(resource_id, False, message, time.time() - start_time)
        
        except Exception as e:
            message = f"Healing exception: {str(e)}"
            result = HealingResult(resource_id, False, message, time.time() - start_time)
        
        # Log individual healing result
        self.decision_ledger.log(
            phase="graph-healing",
            mcp="healing-orchestrator",
            tool="heal_resource",
            rationale=f"Healing {resource_id}: {result.message}",
            status="SUCCESS" if result.success else "FAILED"
        )
        
        self.healing_history.append(result)
        print(f"{'✅' if result.success else '❌'} {result.message}")
        
        return result
    
    def _check_dependencies_health(self, graph: DependencyGraph, resource_id: str) -> List[str]:
        """Check if all dependencies are healthy"""
        
        unhealthy_deps = []
        node = graph.nodes[resource_id]
        
        for dep_id in node.dependencies:
            dep_node = graph.nodes[dep_id]
            if dep_node.state != ResourceState.HEALTHY:
                unhealthy_deps.append(dep_id)
        
        return unhealthy_deps
    
    def _verify_dependents_health(self, graph: DependencyGraph, resource_id: str) -> List[str]:
        """Verify that healing didn't break dependent resources"""
        
        # In a real implementation, this would check actual resource health
        # For now, we'll simulate health checks
        
        broken_dependents = []
        node = graph.nodes[resource_id]
        
        for dependent_id in node.dependents:
            # Simulate health check (in real implementation, would check actual resource)
            if self._simulate_health_check(dependent_id):
                # Resource is healthy
                continue
            else:
                # Resource is broken
                broken_dependents.append(dependent_id)
                graph.nodes[dependent_id].state = ResourceState.FAILED
        
        return broken_dependents
    
    def _simulate_health_check(self, resource_id: str) -> bool:
        """Simulate health check for a resource"""
        
        # In real implementation, this would:
        # - Check CloudWatch metrics
        # - Verify resource configuration
        # - Test connectivity/functionality
        # - Check dependent service health
        
        # For simulation, assume 95% success rate
        import random
        return random.random() > 0.05
    
    def _rollback_healing(self, graph: DependencyGraph, resource_id: str):
        """Rollback healing for a resource"""
        
        print(f"🔄 Rolling back healing for {resource_id}")
        
        # In real implementation, this would:
        # - Revert configuration changes
        # - Restore previous state
        # - Update CloudFormation stack if needed
        
        # Update graph state
        graph.nodes[resource_id].state = ResourceState.DRIFT
        
        # Log rollback
        self.decision_ledger.log(
            phase="graph-healing",
            mcp="healing-orchestrator",
            tool="rollback_healing",
            rationale=f"Rolled back healing for {resource_id}",
            status="ROLLBACK"
        )
    
    def _should_stop_healing(self, graph: DependencyGraph, failed_resource_id: str, result: HealingResult) -> bool:
        """Determine if healing should stop due to cascade risk"""
        
        node = graph.nodes[failed_resource_id]
        
        # Stop if critical resource failed
        if node.healing_priority == 1:
            return True
        
        # Stop if high blast radius resource failed
        if node.blast_radius.value in ["high", "critical"]:
            return True
        
        # Stop if too many dependents would be affected
        if len(node.dependents) > 5:
            return True
        
        return False
    
    def get_healing_summary(self) -> Dict[str, any]:
        """Get summary of recent healing operations"""
        
        if not self.healing_history:
            return {"message": "No healing operations performed"}
        
        recent_healings = self.healing_history[-10:]  # Last 10 operations
        
        successful = len([h for h in recent_healings if h.success])
        failed = len([h for h in recent_healings if not h.success])
        avg_duration = sum(h.duration for h in recent_healings) / len(recent_healings)
        
        return {
            "total_operations": len(recent_healings),
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / len(recent_healings)) * 100,
            "average_duration": avg_duration,
            "recent_operations": [
                {
                    "resource_id": h.resource_id,
                    "success": h.success,
                    "message": h.message,
                    "duration": h.duration
                }
                for h in recent_healings
            ]
        }
