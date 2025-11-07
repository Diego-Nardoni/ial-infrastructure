"""
API Gateway Construct
Creates API Gateway for IAL external interface
"""

from aws_cdk import (
    aws_apigateway as apigateway,
    aws_lambda as _lambda
)
from constructs import Construct

class APIGatewayConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str,
                 project_name: str, lambda_functions=None, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        
        # Main API Gateway (18-ial-feature-flags.yaml)
        self.api = apigateway.RestApi(
            self, "IALAPI",
            rest_api_name=f"{project_name}-api",
            description=f"IAL API for {project_name}",
            endpoint_configuration=apigateway.EndpointConfiguration(
                types=[apigateway.EndpointType.REGIONAL]
            ),
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"]
            )
        )
        
        # Health check endpoint
        health_resource = self.api.root.add_resource("health")
        health_resource.add_method(
            "GET",
            apigateway.MockIntegration(
                integration_responses=[
                    apigateway.IntegrationResponse(
                        status_code="200",
                        response_templates={
                            "application/json": '{"status": "healthy", "service": "ial-api"}'
                        }
                    )
                ],
                request_templates={
                    "application/json": '{"statusCode": 200}'
                }
            ),
            method_responses=[
                apigateway.MethodResponse(status_code="200")
            ]
        )
        
        # Feature flags endpoints (if lambda functions available)
        if lambda_functions and hasattr(lambda_functions, 'feature_flag_manager'):
            flags_resource = self.api.root.add_resource("flags")
            
            # GET /flags - List all feature flags
            flags_resource.add_method(
                "GET",
                apigateway.LambdaIntegration(lambda_functions.feature_flag_manager)
            )
            
            # POST /flags - Update feature flag
            flags_resource.add_method(
                "POST", 
                apigateway.LambdaIntegration(lambda_functions.feature_flag_manager)
            )
        
        # API Key for external access
        self.api_key = apigateway.ApiKey(
            self, "IALAPIKey",
            api_key_name=f"{project_name}-api-key",
            description=f"API Key for {project_name} IAL"
        )
        
        # Usage plan
        self.usage_plan = apigateway.UsagePlan(
            self, "IALUsagePlan",
            name=f"{project_name}-usage-plan",
            description=f"Usage plan for {project_name} IAL API",
            throttle=apigateway.ThrottleSettings(
                rate_limit=100,
                burst_limit=200
            ),
            quota=apigateway.QuotaSettings(
                limit=10000,
                period=apigateway.Period.DAY
            ),
            api_stages=[
                apigateway.UsagePlanPerApiStage(
                    api=self.api,
                    stage=self.api.deployment_stage
                )
            ]
        )
        
        # Associate API key with usage plan
        self.usage_plan.add_api_key(self.api_key)
