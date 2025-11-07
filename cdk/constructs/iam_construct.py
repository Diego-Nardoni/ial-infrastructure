"""
IAM Construct
Creates all IAM roles and policies needed by IAL
"""

from aws_cdk import (
    aws_iam as iam,
    aws_logs as logs
)
from constructs import Construct

class IAMConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str, 
                 project_name: str, github_user: str = None, 
                 github_repo: str = None, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        
        # Lambda execution role
        self.lambda_execution_role = iam.Role(
            self, "LambdaExecutionRole",
            role_name=f"{project_name}-lambda-execution-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ],
            inline_policies={
                "DynamoDBAccess": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:GetItem",
                                "dynamodb:PutItem", 
                                "dynamodb:UpdateItem",
                                "dynamodb:DeleteItem",
                                "dynamodb:Query",
                                "dynamodb:Scan"
                            ],
                            resources=[f"arn:aws:dynamodb:{scope.region}:{scope.account}:table/{project_name}-*"]
                        )
                    ]
                ),
                "BedrockAccess": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["bedrock:InvokeModel"],
                            resources=[f"arn:aws:bedrock:{scope.region}::foundation-model/*"]
                        )
                    ]
                ),
                "SNSPublish": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["sns:Publish"],
                            resources=[f"arn:aws:sns:{scope.region}:{scope.account}:{project_name}-*"]
                        )
                    ]
                )
            }
        )
        
        # Step Functions execution role
        self.step_functions_role = iam.Role(
            self, "StepFunctionsRole",
            role_name=f"{project_name}-stepfunctions-role",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com"),
            inline_policies={
                "LambdaInvoke": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["lambda:InvokeFunction"],
                            resources=[f"arn:aws:lambda:{scope.region}:{scope.account}:function:{project_name}-*"]
                        )
                    ]
                ),
                "LogsAccess": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream", 
                                "logs:PutLogEvents"
                            ],
                            resources=[f"arn:aws:logs:{scope.region}:{scope.account}:log-group:/aws/stepfunctions/{project_name}-*"]
                        )
                    ]
                )
            }
        )
        
        # GitHub OIDC Provider and Role (if GitHub integration enabled)
        if github_user and github_repo:
            self._create_github_integration(project_name, github_user, github_repo)
    
    def _create_github_integration(self, project_name: str, github_user: str, github_repo: str):
        """Create GitHub OIDC provider and role"""
        
        # GitHub OIDC Provider
        self.github_oidc_provider = iam.OpenIdConnectProvider(
            self, "GitHubOIDCProvider",
            url="https://token.actions.githubusercontent.com",
            client_ids=["sts.amazonaws.com"],
            thumbprints=["6938fd4d98bab03faadb97b34396831e3780aea1"]
        )
        
        # GitHub Actions Role
        self.github_actions_role = iam.Role(
            self, "GitHubActionsRole",
            role_name=f"{project_name}-github-actions-role",
            assumed_by=iam.WebIdentityPrincipal(
                identity_provider=self.github_oidc_provider.open_id_connect_provider_arn,
                conditions={
                    "StringEquals": {
                        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                    },
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": f"repo:{github_user}/ial-infrastructure:*"
                    }
                }
            ),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("PowerUserAccess")
            ],
            inline_policies={
                "BedrockAccess": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["bedrock:InvokeModel"],
                            resources=[f"arn:aws:bedrock:*::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"]
                        )
                    ]
                )
            }
        )
