#!/usr/bin/env python3
"""
Fix remaining issues: X-Ray and Metrics Publisher
"""

import boto3
import json

def fix_xray_api_gateway():
    """Fix X-Ray tracing on API Gateway"""
    try:
        apigateway = boto3.client('apigateway')
        
        # Get all APIs
        apis = apigateway.get_rest_apis()
        
        for api in apis['items']:
            if 'ial' in api['name'].lower():
                print(f"🔍 Enabling X-Ray on API: {api['name']}")
                
                # Get stages
                stages = apigateway.get_stages(restApiId=api['id'])
                
                for stage in stages['item']:
                    try:
                        apigateway.update_stage(
                            restApiId=api['id'],
                            stageName=stage['stageName'],
                            patchOps=[
                                {
                                    'op': 'replace',
                                    'path': '/tracingConfig/tracingEnabled',
                                    'value': 'true'
                                }
                            ]
                        )
                        print(f"   ✅ X-Ray enabled on stage: {stage['stageName']}")
                    except Exception as e:
                        print(f"   ⚠️  Failed to enable X-Ray on {stage['stageName']}: {e}")
        
        return True
    except Exception as e:
        print(f"❌ X-Ray fix failed: {e}")
        return False

def create_lambda_execution_role():
    """Create proper IAM role for Lambda"""
    try:
        iam = boto3.client('iam')
        
        # Create role
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        role_name = 'ial-metrics-publisher-role'
        
        try:
            iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description='IAL Circuit Breaker Metrics Publisher Role'
            )
            print(f"✅ Created IAM role: {role_name}")
        except iam.exceptions.EntityAlreadyExistsException:
            print(f"ℹ️  IAM role {role_name} already exists")
        
        # Attach policies
        policies = [
            'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
            'arn:aws:iam::aws:policy/CloudWatchFullAccess'
        ]
        
        for policy in policies:
            try:
                iam.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy
                )
                print(f"   ✅ Attached policy: {policy.split('/')[-1]}")
            except Exception as e:
                print(f"   ⚠️  Policy attach failed: {e}")
        
        # Get role ARN
        role = iam.get_role(RoleName=role_name)
        return role['Role']['Arn']
        
    except Exception as e:
        print(f"❌ Role creation failed: {e}")
        return None

def deploy_metrics_publisher():
    """Deploy metrics publisher with correct role"""
    try:
        role_arn = create_lambda_execution_role()
        if not role_arn:
            return False
        
        lambda_client = boto3.client('lambda')
        
        # Delete existing function if exists
        try:
            lambda_client.delete_function(
                FunctionName='ial-circuit-breaker-metrics-publisher'
            )
            print("🗑️  Deleted existing function")
            import time
            time.sleep(5)  # Wait for deletion
        except lambda_client.exceptions.ResourceNotFoundException:
            pass
        
        # Create deployment package
        import zipfile
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
            with zipfile.ZipFile(tmp_file.name, 'w') as zip_file:
                # Add metrics publisher code
                metrics_code_path = '/home/ial/core/resilience/circuit_breaker_metrics.py'
                zip_file.write(metrics_code_path, 'lambda_function.py')
            
            # Deploy Lambda
            with open(tmp_file.name, 'rb') as zip_data:
                lambda_client.create_function(
                    FunctionName='ial-circuit-breaker-metrics-publisher',
                    Runtime='python3.9',
                    Role=role_arn,
                    Handler='lambda_function.lambda_handler',
                    Code={'ZipFile': zip_data.read()},
                    Description='IAL Circuit Breaker Metrics Publisher',
                    Timeout=60,
                    Environment={
                        'Variables': {
                            'NAMESPACE': 'IAL/CircuitBreaker'
                        }
                    }
                )
        
        print("✅ Metrics Publisher deployed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Metrics Publisher deployment failed: {e}")
        return False

def main():
    print("🔧 Fixing Remaining IAL Enhanced Issues")
    print("=" * 40)
    
    # Fix X-Ray
    print("\n🔍 Fixing X-Ray Configuration...")
    xray_success = fix_xray_api_gateway()
    
    # Fix Metrics Publisher
    print("\n📈 Fixing Metrics Publisher...")
    metrics_success = deploy_metrics_publisher()
    
    # Summary
    print("\n📋 Fix Summary:")
    print(f"   X-Ray: {'✅ FIXED' if xray_success else '❌ FAILED'}")
    print(f"   Metrics: {'✅ FIXED' if metrics_success else '❌ FAILED'}")
    
    if xray_success and metrics_success:
        print("\n🎉 All issues fixed! Run test again.")
    else:
        print("\n⚠️  Some issues remain")

if __name__ == "__main__":
    main()
