import os
import time
import yaml
import boto3
from typing import Dict, List, Optional, Any
from enum import Enum
from core.decision_ledger import DecisionLedger
from core.graph.dependency_graph import DependencyGraph

class ChaosMode(Enum):
    DISABLED = "disabled"
    GAME_DAY = "game_day"
    CONTINUOUS = "continuous"
    SIMULATION = "simulation"

class FailureType(Enum):
    # Application-level chaos (handled by Chaos Controller)
    CONFIGURATION_DRIFT = "configuration_drift"
    SERVICE_DEGRADATION = "service_degradation"
    
    # Infrastructure-level chaos (delegated to AWS FIS)
    INSTANCE_TERMINATION = "instance_termination"
    NETWORK_PARTITION = "network_partition"
    RESOURCE_EXHAUSTION = "resource_exhaustion"

class ChaosController:
    """
    Safe Chaos Engineering Controller - DISABLED BY DEFAULT
    
    This controller implements chaos engineering with multiple safety layers:
    - Disabled by default
    - Explicit enable required
    - Game day mode for organized testing
    - Blast radius controls
    - Automatic rollback
    - Safety monitoring
    """
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.decision_ledger = DecisionLedger()
        self.config = self._load_chaos_config()
        self.active_experiments: List[Dict] = []
        
        # AWS FIS integration for infrastructure chaos
        try:
            self.fis_client = boto3.client('fis', region_name=region)
        except Exception:
            self.fis_client = None
            print("⚠️  AWS FIS client not available - infrastructure chaos disabled")
        
        # Safety check on initialization
        if not self._is_chaos_explicitly_enabled():
            print("🔒 Chaos Engineering is DISABLED by default")
            print("   To enable: Set CHAOS_ENGINEERING_ENABLED=true and update config")
    
    def _load_chaos_config(self) -> Dict:
        """Load chaos engineering configuration"""
        
        config_path = "config/chaos/chaos_config.yaml"
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        
        # Default safe configuration
        return {
            "enabled": False,
            "require_explicit_enable": True,
            "mode": ChaosMode.DISABLED.value,
            "safety_checks": {
                "max_blast_radius": "minimal",
                "require_approval": True,
                "rollback_timeout": 300,
                "monitoring_required": True
            },
            "allowed_environments": ["development", "staging"],
            "blocked_environments": ["production"],
            "allowed_failure_types": [
                FailureType.CONFIGURATION_DRIFT.value,
                FailureType.SERVICE_DEGRADATION.value
            ]
        }
    
    def _is_chaos_explicitly_enabled(self) -> bool:
        """Check if chaos engineering is explicitly enabled"""
        
        # Multiple checks required for safety
        config_enabled = self.config.get("enabled", False)
        env_enabled = os.getenv("CHAOS_ENGINEERING_ENABLED", "false").lower() == "true"
        explicit_enable = not self.config.get("require_explicit_enable", True)
        
        return config_enabled and env_enabled and explicit_enable
    
    def is_chaos_allowed(self) -> Dict[str, Any]:
        """Check if chaos engineering is allowed in current context"""
        
        checks = {
            "enabled": self._is_chaos_explicitly_enabled(),
            "environment_allowed": self._is_environment_allowed(),
            "safety_checks_passed": self._safety_checks_passed(),
            "approval_required": self.config.get("safety_checks", {}).get("require_approval", True)
        }
        
        checks["overall_allowed"] = all([
            checks["enabled"],
            checks["environment_allowed"],
            checks["safety_checks_passed"]
        ])
        
        return checks
    
    def _is_environment_allowed(self) -> bool:
        """Check if current environment allows chaos engineering"""
        
        current_env = os.getenv("ENVIRONMENT", "production").lower()
        allowed_envs = self.config.get("allowed_environments", [])
        blocked_envs = self.config.get("blocked_environments", ["production"])
        
        return current_env in allowed_envs and current_env not in blocked_envs
    
    def _safety_checks_passed(self) -> bool:
        """Verify all safety checks are in place"""
        
        safety_config = self.config.get("safety_checks", {})
        
        # Check monitoring is available
        if safety_config.get("monitoring_required", True):
            if not self._is_monitoring_available():
                return False
        
        # Check rollback capability
        if not self._is_rollback_available():
            return False
        
        return True
    
    def _is_monitoring_available(self) -> bool:
        """Check if monitoring is available for chaos experiments"""
        
        # In real implementation, would check:
        # - CloudWatch metrics availability
        # - Application health endpoints
        # - Log aggregation systems
        
        return True  # Simplified for demo
    
    def _is_rollback_available(self) -> bool:
        """Check if rollback capability is available"""
        
        # In real implementation, would check:
        # - Infrastructure as Code state
        # - Backup availability
        # - Rollback procedures
        
        return True  # Simplified for demo
    
    def start_game_day_experiment(self, experiment_config: Dict) -> Dict[str, Any]:
        """Start a controlled chaos experiment for game day testing"""
        
        print("🎮 Starting Game Day Chaos Experiment...")
        
        # Verify chaos is allowed
        chaos_status = self.is_chaos_allowed()
        if not chaos_status["overall_allowed"]:
            return {
                "status": "blocked",
                "reason": "Chaos engineering not allowed",
                "checks": chaos_status
            }
        
        # Validate experiment configuration
        validation = self._validate_experiment_config(experiment_config)
        if not validation["valid"]:
            return {
                "status": "invalid_config",
                "reason": validation["reason"],
                "suggestions": validation.get("suggestions", [])
            }
        
        # Create experiment
        experiment = {
            "id": f"chaos-{int(time.time())}",
            "type": experiment_config["failure_type"],
            "target": experiment_config["target_resource"],
            "duration": experiment_config.get("duration", 300),
            "start_time": time.time(),
            "status": "running",
            "rollback_plan": self._create_rollback_plan(experiment_config),
            "monitoring": self._setup_experiment_monitoring(experiment_config)
        }
        
        # Log experiment start
        self.decision_ledger.log(
            phase="chaos-engineering",
            mcp="chaos-controller",
            tool="start_experiment",
            rationale=f"Started game day experiment: {experiment['type']} on {experiment['target']}",
            status="STARTED"
        )
        
        # Execute the chaos experiment
        execution_result = self._execute_chaos_experiment(experiment)
        
        # Add to active experiments
        self.active_experiments.append(experiment)
        
        return {
            "status": "started",
            "experiment_id": experiment["id"],
            "execution_result": execution_result,
            "monitoring_url": experiment["monitoring"].get("dashboard_url"),
            "estimated_duration": experiment["duration"]
        }
    
    def _validate_experiment_config(self, config: Dict) -> Dict[str, Any]:
        """Validate chaos experiment configuration"""
        
        validation = {"valid": True, "reason": "", "suggestions": []}
        
        # Check required fields
        required_fields = ["failure_type", "target_resource"]
        for field in required_fields:
            if field not in config:
                validation["valid"] = False
                validation["reason"] = f"Missing required field: {field}"
                return validation
        
        # Check failure type is allowed
        failure_type = config["failure_type"]
        allowed_types = self.config.get("allowed_failure_types", [])
        if failure_type not in allowed_types:
            validation["valid"] = False
            validation["reason"] = f"Failure type '{failure_type}' not allowed"
            validation["suggestions"] = [f"Allowed types: {', '.join(allowed_types)}"]
            return validation
        
        # Check blast radius
        blast_radius = config.get("blast_radius", "moderate")
        max_blast_radius = self.config.get("safety_checks", {}).get("max_blast_radius", "minimal")
        
        blast_radius_levels = ["minimal", "moderate", "high", "critical"]
        if blast_radius_levels.index(blast_radius) > blast_radius_levels.index(max_blast_radius):
            validation["valid"] = False
            validation["reason"] = f"Blast radius '{blast_radius}' exceeds maximum '{max_blast_radius}'"
            return validation
        
        return validation
    
    def _create_rollback_plan(self, experiment_config: Dict) -> Dict[str, Any]:
        """Create rollback plan for chaos experiment"""
        
        return {
            "type": "automatic",
            "timeout": self.config.get("safety_checks", {}).get("rollback_timeout", 300),
            "triggers": [
                "experiment_timeout",
                "critical_metric_breach",
                "manual_trigger"
            ],
            "steps": [
                "stop_failure_injection",
                "restore_original_state",
                "verify_system_health",
                "notify_stakeholders"
            ]
        }
    
    def _setup_experiment_monitoring(self, experiment_config: Dict) -> Dict[str, Any]:
        """Setup monitoring for chaos experiment"""
        
        return {
            "metrics": [
                "system_health",
                "error_rate",
                "response_time",
                "resource_utilization"
            ],
            "alerts": [
                "critical_error_rate",
                "system_unavailable",
                "cascade_failure_detected"
            ],
            "dashboard_url": f"https://console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name=chaos-experiment"
        }
    
    def _execute_chaos_experiment(self, experiment: Dict) -> Dict[str, Any]:
        """Execute the actual chaos experiment"""
        
        failure_type = experiment["type"]
        target_resource = experiment["target"]
        
        print(f"💥 Injecting failure: {failure_type} on {target_resource}")
        
        # Route to appropriate handler
        if failure_type == FailureType.CONFIGURATION_DRIFT.value:
            return self._inject_configuration_drift(target_resource)
        elif failure_type == FailureType.SERVICE_DEGRADATION.value:
            return self._inject_service_degradation(target_resource)
        elif failure_type in [FailureType.INSTANCE_TERMINATION.value, 
                             FailureType.NETWORK_PARTITION.value,
                             FailureType.RESOURCE_EXHAUSTION.value]:
            return self._delegate_to_fis(failure_type, target_resource)
        else:
            return {"status": "unsupported", "message": f"Failure type {failure_type} not implemented"}
    
    def _delegate_to_fis(self, failure_type: str, target_resource: str) -> Dict[str, Any]:
        """Delegate infrastructure chaos to AWS FIS"""
        
        if not self.fis_client:
            return {
                "status": "unavailable", 
                "message": "AWS FIS not available - infrastructure chaos disabled"
            }
        
        print(f"🔄 Delegating {failure_type} to AWS FIS for {target_resource}")
        
        # Map failure types to FIS experiment templates
        template_mapping = {
            FailureType.INSTANCE_TERMINATION.value: f"ial-instance-termination",
            FailureType.NETWORK_PARTITION.value: f"ial-network-latency", 
            FailureType.RESOURCE_EXHAUSTION.value: f"ial-ecs-task-termination"
        }
        
        template_id = template_mapping.get(failure_type)
        if not template_id:
            return {"status": "unsupported", "message": f"No FIS template for {failure_type}"}
        
        try:
            # In real implementation, would start FIS experiment
            return {
                "status": "delegated_to_fis",
                "fis_template": template_id,
                "target": target_resource,
                "message": f"Infrastructure chaos delegated to AWS FIS template: {template_id}"
            }
        except Exception as e:
            return {"status": "fis_error", "message": f"FIS delegation failed: {str(e)}"}
    
    def _inject_configuration_drift(self, target_resource: str) -> Dict[str, Any]:
        """Inject configuration drift as chaos experiment"""
        
        print(f"🔧 Injecting configuration drift on {target_resource}")
        
        # In real implementation, would:
        # - Modify resource configuration
        # - Trigger drift detection
        # - Monitor system response
        
        return {
            "status": "injected",
            "type": "configuration_drift",
            "target": target_resource,
            "changes": ["modified_security_group_rule", "changed_instance_type"],
            "expected_detection_time": "5-10 minutes"
        }
    
    def _inject_service_degradation(self, target_resource: str) -> Dict[str, Any]:
        """Inject service degradation as chaos experiment"""
        
        print(f"📉 Injecting service degradation on {target_resource}")
        
        # In real implementation, would:
        # - Introduce latency
        # - Reduce throughput
        # - Simulate partial failures
        
        return {
            "status": "injected",
            "type": "service_degradation",
            "target": target_resource,
            "degradation": ["increased_latency", "reduced_throughput"],
            "severity": "moderate"
        }
    
    def get_chaos_architecture_info(self) -> Dict[str, Any]:
        """Get information about chaos engineering architecture"""
        
        return {
            "architecture": "hybrid",
            "components": {
                "chaos_controller": {
                    "responsibility": "Application-level chaos + orchestration",
                    "failure_types": ["configuration_drift", "service_degradation"],
                    "features": ["dependency_graph_integration", "decision_ledger", "game_day_mode"]
                },
                "aws_fis": {
                    "responsibility": "Infrastructure-level chaos",
                    "failure_types": ["instance_termination", "network_partition", "resource_exhaustion"],
                    "features": ["native_aws_integration", "cloudwatch_alarms", "sns_notifications"]
                }
            },
            "integration": "chaos_controller_orchestrates_and_delegates_to_fis",
            "safety": "both_disabled_by_default_with_multiple_safety_layers"
        }
    
    def stop_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """Stop a running chaos experiment"""
        
        experiment = None
        for exp in self.active_experiments:
            if exp["id"] == experiment_id:
                experiment = exp
                break
        
        if not experiment:
            return {"status": "not_found", "message": f"Experiment {experiment_id} not found"}
        
        print(f"🛑 Stopping chaos experiment {experiment_id}")
        
        # Execute rollback plan
        rollback_result = self._execute_rollback(experiment)
        
        # Update experiment status
        experiment["status"] = "stopped"
        experiment["end_time"] = time.time()
        experiment["duration_actual"] = experiment["end_time"] - experiment["start_time"]
        
        # Log experiment stop
        self.decision_ledger.log(
            phase="chaos-engineering",
            mcp="chaos-controller",
            tool="stop_experiment",
            rationale=f"Stopped experiment {experiment_id}: {rollback_result['status']}",
            status="STOPPED"
        )
        
        return {
            "status": "stopped",
            "experiment_id": experiment_id,
            "rollback_result": rollback_result,
            "duration": experiment["duration_actual"]
        }
    
    def _execute_rollback(self, experiment: Dict) -> Dict[str, Any]:
        """Execute rollback plan for chaos experiment"""
        
        rollback_plan = experiment["rollback_plan"]
        
        print(f"🔄 Executing rollback for experiment {experiment['id']}")
        
        # Execute rollback steps
        for step in rollback_plan["steps"]:
            print(f"  - {step}")
            # In real implementation, would execute actual rollback actions
            time.sleep(0.5)  # Simulate rollback time
        
        return {
            "status": "completed",
            "steps_executed": rollback_plan["steps"],
            "rollback_time": time.time()
        }
    
    def get_experiment_status(self, experiment_id: str) -> Dict[str, Any]:
        """Get status of a chaos experiment"""
        
        experiment = None
        for exp in self.active_experiments:
            if exp["id"] == experiment_id:
                experiment = exp
                break
        
        if not experiment:
            return {"status": "not_found", "message": f"Experiment {experiment_id} not found"}
        
        current_time = time.time()
        elapsed_time = current_time - experiment["start_time"]
        
        return {
            "experiment_id": experiment_id,
            "status": experiment["status"],
            "type": experiment["type"],
            "target": experiment["target"],
            "elapsed_time": elapsed_time,
            "remaining_time": max(0, experiment["duration"] - elapsed_time),
            "monitoring": experiment["monitoring"]
        }
    
    def list_active_experiments(self) -> List[Dict[str, Any]]:
        """List all active chaos experiments"""
        
        active = [exp for exp in self.active_experiments if exp["status"] == "running"]
        
        return [
            {
                "experiment_id": exp["id"],
                "type": exp["type"],
                "target": exp["target"],
                "elapsed_time": time.time() - exp["start_time"],
                "status": exp["status"]
            }
            for exp in active
        ]
