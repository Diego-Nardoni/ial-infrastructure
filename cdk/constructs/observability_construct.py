"""
Observability Construct
Creates SNS topics, CloudWatch dashboards and alarms
"""

from aws_cdk import (
    aws_sns as sns,
    aws_cloudwatch as cloudwatch,
    aws_logs as logs
)
from constructs import Construct

class ObservabilityConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str,
                 project_name: str, lambda_functions=None,
                 step_functions=None, api_gateway=None, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        
        # SNS Topics for alerts (24-ial-sns-topics.yaml)
        self.alerts_topic = sns.Topic(
            self, "AlertsTopic",
            topic_name=f"{project_name}-alerts-critical",
            display_name="IAL Critical Alerts"
        )
        
        self.audit_alerts_topic = sns.Topic(
            self, "AuditAlertsTopic", 
            topic_name=f"{project_name}-audit-alerts",
            display_name="IAL Audit Alerts"
        )
        
        # CloudWatch Log Groups
        self.ial_log_group = logs.LogGroup(
            self, "IALLogGroup",
            log_group_name=f"/aws/ial/{project_name}",
            retention=logs.RetentionDays.TWO_WEEKS
        )
        
        # CloudWatch Dashboard
        self.dashboard = cloudwatch.Dashboard(
            self, "IALDashboard",
            dashboard_name=f"{project_name}-ial-operations"
        )
        
        # Add widgets to dashboard
        if lambda_functions:
            self._add_lambda_widgets(lambda_functions)
        
        if step_functions:
            self._add_stepfunctions_widgets(step_functions)
        
        if api_gateway:
            self._add_apigateway_widgets(api_gateway)
    
    def _add_lambda_widgets(self, lambda_functions):
        """Add Lambda monitoring widgets"""
        
        # Lambda errors widget
        self.dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Lambda Function Errors",
                left=[
                    lambda_functions.drift_detector.metric_errors(),
                    lambda_functions.reconciliation_engine.metric_errors(),
                    lambda_functions.audit_validator.metric_errors()
                ],
                width=12
            )
        )
        
        # Lambda duration widget  
        self.dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Lambda Function Duration",
                left=[
                    lambda_functions.drift_detector.metric_duration(),
                    lambda_functions.reconciliation_engine.metric_duration(),
                    lambda_functions.audit_validator.metric_duration()
                ],
                width=12
            )
        )
    
    def _add_stepfunctions_widgets(self, step_functions):
        """Add Step Functions monitoring widgets"""
        
        self.dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Step Functions Executions",
                left=[
                    step_functions.phase_pipeline.metric("ExecutionsSucceeded"),
                    step_functions.phase_pipeline.metric("ExecutionsFailed")
                ],
                width=12
            )
        )
    
    def _add_apigateway_widgets(self, api_gateway):
        """Add API Gateway monitoring widgets"""
        
        self.dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="API Gateway Requests",
                left=[
                    api_gateway.api.metric_count(),
                    api_gateway.api.metric_client_error(),
                    api_gateway.api.metric_server_error()
                ],
                width=12
            )
        )
