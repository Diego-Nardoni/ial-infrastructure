#!/usr/bin/env python3
"""Enhanced Observability Integration for IaL"""

import boto3
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from .logger import get_logger

# AWS clients
cloudwatch = boto3.client('cloudwatch')
xray = boto3.client('xray')

logger = get_logger(__name__)

class IaLObservability:
    """Enhanced observability for IaL operations"""
    
    def __init__(self, project_name: str = "ial"):
        self.project_name = project_name
        self.namespace_operations = "IaL/Operations"
        self.namespace_performance = "IaL/Performance"
        self.namespace_resources = "IaL/Resources"
    
    def put_custom_metric(self, metric_name: str, value: float, unit: str = "Count", 
                         namespace: str = None, dimensions: Dict[str, str] = None):
        """Put custom metric to CloudWatch"""
        try:
            namespace = namespace or self.namespace_operations
            dimensions = dimensions or {"Project": self.project_name}
            
            # Convert dimensions to CloudWatch format
            cw_dimensions = [{"Name": k, "Value": v} for k, v in dimensions.items()]
            
            cloudwatch.put_metric_data(
                Namespace=namespace,
                MetricData=[
                    {
                        'MetricName': metric_name,
                        'Value': value,
                        'Unit': unit,
                        'Dimensions': cw_dimensions,
                        'Timestamp': datetime.now(timezone.utc)
                    }
                ]
            )
            
            logger.info(f"Custom metric sent: {metric_name}={value}", 
                       metric_name=metric_name, 
                       value=value, 
                       namespace=namespace)
                       
        except Exception as e:
            logger.error(f"Failed to send custom metric: {e}", 
                        metric_name=metric_name, 
                        error=str(e))
    
    def record_deployment_start(self, phase: str, resources_expected: int):
        """Record deployment start metrics"""
        self.put_custom_metric("DeploymentStarted", 1, dimensions={
            "Project": self.project_name,
            "Phase": phase
        })
        
        self.put_custom_metric("ResourcesExpected", resources_expected, 
                              namespace=self.namespace_resources,
                              dimensions={
                                  "Project": self.project_name,
                                  "Phase": phase
                              })
    
    def record_deployment_success(self, phase: str, duration: float, resources_created: int):
        """Record successful deployment metrics"""
        self.put_custom_metric("DeploymentSuccess", 1, dimensions={
            "Project": self.project_name,
            "Phase": phase
        })
        
        self.put_custom_metric("DeploymentDuration", duration, "Seconds",
                              namespace=self.namespace_performance,
                              dimensions={
                                  "Project": self.project_name,
                                  "Phase": phase
                              })
        
        self.put_custom_metric("ResourcesCreated", resources_created,
                              namespace=self.namespace_resources,
                              dimensions={
                                  "Project": self.project_name,
                                  "Phase": phase
                              })
    
    def record_deployment_failure(self, phase: str, duration: float, error: str):
        """Record deployment failure metrics"""
        self.put_custom_metric("DeploymentFailure", 1, dimensions={
            "Project": self.project_name,
            "Phase": phase,
            "ErrorType": self._classify_error(error)
        })
        
        self.put_custom_metric("DeploymentDuration", duration, "Seconds",
                              namespace=self.namespace_performance,
                              dimensions={
                                  "Project": self.project_name,
                                  "Phase": phase,
                                  "Status": "Failed"
                              })
    
    def record_validation_result(self, completion_rate: float, expected: int, 
                                created: int, missing: int):
        """Record validation results"""
        status = "Success" if completion_rate >= 100 else "Failure"
        
        self.put_custom_metric(f"Validation{status}", 1, dimensions={
            "Project": self.project_name
        })
        
        self.put_custom_metric("CompletionRate", completion_rate, "Percent",
                              dimensions={"Project": self.project_name})
        
        self.put_custom_metric("ResourcesExpectedTotal", expected,
                              namespace=self.namespace_resources,
                              dimensions={"Project": self.project_name})
        
        self.put_custom_metric("ResourcesCreatedTotal", created,
                              namespace=self.namespace_resources,
                              dimensions={"Project": self.project_name})
        
        if missing > 0:
            self.put_custom_metric("ResourcesMissing", missing,
                                  namespace=self.namespace_resources,
                                  dimensions={"Project": self.project_name})
    
    def record_rollback_event(self, checkpoint_id: str, reason: str, success: bool):
        """Record rollback events"""
        self.put_custom_metric("RollbackTriggered", 1, dimensions={
            "Project": self.project_name,
            "Reason": self._classify_rollback_reason(reason)
        })
        
        if success:
            self.put_custom_metric("RollbackSuccess", 1, dimensions={
                "Project": self.project_name
            })
        else:
            self.put_custom_metric("RollbackFailure", 1, dimensions={
                "Project": self.project_name
            })
    
    def record_chaos_test_result(self, test_type: str, success: bool, 
                                duration: float, impact_score: float):
        """Record chaos engineering test results"""
        status = "Success" if success else "Failure"
        
        self.put_custom_metric(f"ChaosTest{status}", 1, dimensions={
            "Project": self.project_name,
            "TestType": test_type
        })
        
        self.put_custom_metric("ChaosTestDuration", duration, "Seconds",
                              namespace=self.namespace_performance,
                              dimensions={
                                  "Project": self.project_name,
                                  "TestType": test_type
                              })
        
        self.put_custom_metric("ChaosImpactScore", impact_score, "None",
                              dimensions={
                                  "Project": self.project_name,
                                  "TestType": test_type
                              })
    
    def _classify_error(self, error: str) -> str:
        """Classify error type for better metrics"""
        error_lower = error.lower()
        
        if "timeout" in error_lower:
            return "Timeout"
        elif "permission" in error_lower or "access" in error_lower:
            return "Permission"
        elif "resource" in error_lower and "exist" in error_lower:
            return "ResourceNotFound"
        elif "limit" in error_lower or "quota" in error_lower:
            return "Limit"
        elif "network" in error_lower or "connection" in error_lower:
            return "Network"
        else:
            return "Other"
    
    def _classify_rollback_reason(self, reason: str) -> str:
        """Classify rollback reason for better metrics"""
        reason_lower = reason.lower()
        
        if "completion" in reason_lower or "incomplete" in reason_lower:
            return "LowCompletion"
        elif "validation" in reason_lower:
            return "ValidationFailure"
        elif "chaos" in reason_lower:
            return "ChaosTest"
        elif "manual" in reason_lower:
            return "Manual"
        else:
            return "Other"
    
    def create_x_ray_segment(self, name: str, operation: str):
        """Create X-Ray tracing segment"""
        try:
            segment = {
                "name": name,
                "id": self._generate_segment_id(),
                "start_time": time.time(),
                "trace_id": self._generate_trace_id(),
                "service": {
                    "name": f"ial-{operation}",
                    "version": "1.0"
                },
                "annotations": {
                    "project": self.project_name,
                    "operation": operation
                }
            }
            
            return segment
            
        except Exception as e:
            logger.error(f"Failed to create X-Ray segment: {e}")
            return None
    
    def _generate_segment_id(self) -> str:
        """Generate X-Ray segment ID"""
        import random
        return f"{random.randint(1000000000000000, 9999999999999999):016x}"
    
    def _generate_trace_id(self) -> str:
        """Generate X-Ray trace ID"""
        import random
        timestamp = int(time.time())
        random_part = f"{random.randint(100000000000000000000000, 999999999999999999999999):024x}"
        return f"1-{timestamp:08x}-{random_part}"

# Global observability instance
observability = IaLObservability()

# Convenience functions
def record_deployment_start(phase: str, resources_expected: int):
    """Record deployment start"""
    observability.record_deployment_start(phase, resources_expected)

def record_deployment_success(phase: str, duration: float, resources_created: int):
    """Record deployment success"""
    observability.record_deployment_success(phase, duration, resources_created)

def record_deployment_failure(phase: str, duration: float, error: str):
    """Record deployment failure"""
    observability.record_deployment_failure(phase, duration, error)

def record_validation_result(completion_rate: float, expected: int, created: int, missing: int):
    """Record validation result"""
    observability.record_validation_result(completion_rate, expected, created, missing)

def record_rollback_event(checkpoint_id: str, reason: str, success: bool):
    """Record rollback event"""
    observability.record_rollback_event(checkpoint_id, reason, success)

def put_custom_metric(metric_name: str, value: float, unit: str = "Count", 
                     namespace: str = None, dimensions: Dict[str, str] = None):
    """Put custom metric"""
    observability.put_custom_metric(metric_name, value, unit, namespace, dimensions)
