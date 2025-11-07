"""
Lambda Construct
Creates all Lambda functions needed by IAL
"""

from aws_cdk import (
    aws_lambda as _lambda,
    aws_dynamodb as dynamodb,
    Duration,
    BundlingOptions
)
from constructs import Construct
import os

class LambdaConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str, 
                 project_name: str, dynamodb_table: dynamodb.Table,
                 iam_roles, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        
        # Common Lambda configuration
        common_env = {
            "PROJECT_NAME": project_name,
            "DYNAMODB_TABLE": dynamodb_table.table_name,
            "IAL_AWS_REGION": scope.region  # Renamed to avoid conflict
        }
        
        # Drift Detector Lambda (13-ial-drift-detection.yaml)
        self.drift_detector = _lambda.Function(
            self, "DriftDetector",
            function_name=f"{project_name}-drift-detector",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="index.lambda_handler",
            code=_lambda.Code.from_asset(
                "/home/ial/lambda/drift-detector",
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_11.bundling_image,
                    command=[
                        "bash", "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ]
                )
            ),
            timeout=Duration.minutes(5),
            memory_size=256,
            environment={
                **common_env,
                "SNS_TOPIC_ARN": f"arn:aws:sns:{scope.region}:{scope.account}:{project_name}-alerts-critical"
            },
            role=iam_roles.lambda_execution_role
        )
        
        # Reconciliation Engine Lambda (03-reconciliation-engine.yaml)
        self.reconciliation_engine = _lambda.Function(
            self, "ReconciliationEngine",
            function_name=f"{project_name}-reconciliation-engine",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="index.lambda_handler",
            code=_lambda.Code.from_asset(
                "/home/ial/lambda/reconciliation-engine",
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_11.bundling_image,
                    command=[
                        "bash", "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ]
                )
            ),
            timeout=Duration.minutes(15),
            memory_size=512,
            environment=common_env,
            role=iam_roles.lambda_execution_role
        )
        
        # Audit Validator Lambda
        self.audit_validator = _lambda.Function(
            self, "AuditValidator",
            function_name=f"{project_name}-audit-validator",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="index.lambda_handler",
            code=_lambda.Code.from_asset(
                "/home/ial/lambda/audit-validator",
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_11.bundling_image,
                    command=[
                        "bash", "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ]
                )
            ),
            timeout=Duration.minutes(10),
            memory_size=256,
            environment={
                **common_env,
                "SNS_TOPIC_ARN": f"arn:aws:sns:{scope.region}:{scope.account}:{project_name}-audit-alerts"
            },
            role=iam_roles.lambda_execution_role
        )
        
        # Feature Flag Manager Lambda (18-ial-feature-flags.yaml)
        self.feature_flag_manager = _lambda.Function(
            self, "FeatureFlagManager",
            function_name=f"{project_name}-feature-flag-manager",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="index.lambda_handler",
            code=_lambda.Code.from_inline("""
import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['FEATURE_FLAGS_TABLE'])

def lambda_handler(event, context):
    method = event['httpMethod']
    
    if method == 'GET':
        # Get all feature flags
        response = table.scan()
        return {
            'statusCode': 200,
            'body': json.dumps(response['Items'])
        }
    elif method == 'POST':
        # Update feature flag
        body = json.loads(event['body'])
        table.put_item(Item=body)
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Feature flag updated'})
        }
    
    return {
        'statusCode': 405,
        'body': json.dumps({'error': 'Method not allowed'})
    }
            """),
            timeout=Duration.seconds(30),
            memory_size=128,
            environment={
                **common_env,
                "FEATURE_FLAGS_TABLE": f"{project_name}-feature-flags"
            },
            role=iam_roles.lambda_execution_role
        )
        
        # Grant DynamoDB permissions
        dynamodb_table.grant_read_write_data(self.drift_detector)
        dynamodb_table.grant_read_write_data(self.reconciliation_engine)
        dynamodb_table.grant_read_write_data(self.audit_validator)
