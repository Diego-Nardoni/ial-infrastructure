"""
Step Functions Construct
Creates Step Functions workflows for IAL orchestration
"""

from aws_cdk import (
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_logs as logs,
    Duration
)
from constructs import Construct

class StepFunctionsConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str,
                 project_name: str, lambda_functions=None, iam_roles=None, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        
        # Log group for Step Functions
        self.log_group = logs.LogGroup(
            self, "StepFunctionsLogGroup",
            log_group_name=f"/aws/stepfunctions/{project_name}",
            retention=logs.RetentionDays.TWO_WEEKS
        )
        
        # Phase Pipeline State Machine (09-stepfunctions-orchestrator.yaml)
        self.phase_pipeline = self._create_phase_pipeline(
            project_name, lambda_functions, iam_roles
        )
        
        # Drift Auto-Heal State Machine
        self.drift_autoheal = self._create_drift_autoheal(
            project_name, lambda_functions, iam_roles
        )
    
    def _create_phase_pipeline(self, project_name: str, lambda_functions, iam_roles):
        """Create phase pipeline state machine"""
        
        # Define tasks
        validate_task = tasks.LambdaInvoke(
            self, "ValidatePhase",
            lambda_function=lambda_functions.audit_validator,
            payload=sfn.TaskInput.from_object({
                "phase": sfn.JsonPath.string_at("$.phase"),
                "resources": sfn.JsonPath.string_at("$.resources")
            })
        )
        
        reconcile_task = tasks.LambdaInvoke(
            self, "ReconcileState",
            lambda_function=lambda_functions.reconciliation_engine,
            payload=sfn.TaskInput.from_object({
                "phase": sfn.JsonPath.string_at("$.phase"),
                "desired_state": sfn.JsonPath.string_at("$.desired_state")
            })
        )
        
        # Define workflow
        definition = validate_task.next(
            sfn.Choice(self, "ValidationChoice")
            .when(
                sfn.Condition.string_equals("$.validation_result", "PASS"),
                reconcile_task
            )
            .otherwise(
                sfn.Fail(self, "ValidationFailed",
                        cause="Phase validation failed")
            )
        )
        
        return sfn.StateMachine(
            self, "PhasePipeline",
            state_machine_name=f"{project_name}-phase-pipeline",
            definition=definition,
            role=iam_roles.step_functions_role,
            logs=sfn.LogOptions(
                destination=self.log_group,
                level=sfn.LogLevel.ALL
            ),
            timeout=Duration.hours(1)
        )
    
    def _create_drift_autoheal(self, project_name: str, lambda_functions, iam_roles):
        """Create drift auto-heal state machine"""
        
        # Drift detection task
        detect_drift_task = tasks.LambdaInvoke(
            self, "DetectDrift",
            lambda_function=lambda_functions.drift_detector,
            payload=sfn.TaskInput.from_object({
                "scan_type": "full",
                "resources": sfn.JsonPath.string_at("$.resources")
            })
        )
        
        # Auto-heal task
        heal_drift_task = tasks.LambdaInvoke(
            self, "HealDrift",
            lambda_function=lambda_functions.reconciliation_engine,
            payload=sfn.TaskInput.from_object({
                "action": "heal_drift",
                "drift_items": sfn.JsonPath.string_at("$.drift_items")
            })
        )
        
        # Define workflow
        definition = detect_drift_task.next(
            sfn.Choice(self, "DriftChoice")
            .when(
                sfn.Condition.number_greater_than("$.drift_count", 0),
                heal_drift_task
            )
            .otherwise(
                sfn.Succeed(self, "NoDriftDetected")
            )
        )
        
        return sfn.StateMachine(
            self, "DriftAutoHeal",
            state_machine_name=f"{project_name}-drift-autoheal",
            state_machine_type=sfn.StateMachineType.EXPRESS,
            definition=definition,
            role=iam_roles.step_functions_role,
            logs=sfn.LogOptions(
                destination=self.log_group,
                level=sfn.LogLevel.ERROR
            ),
            timeout=Duration.minutes(15)
        )
