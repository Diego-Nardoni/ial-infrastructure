#!/usr/bin/env python3
"""
IAL Foundation Deployer
Cria toda infraestrutura AWS necessária para funcionamento do IAL
"""

import boto3
import json
import time
from typing import Dict, List, Optional
from pathlib import Path


class IALFoundationDeployer:
    """Deployer da infraestrutura foundation do IAL"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.cloudformation = boto3.client('cloudformation', region_name=region)
        self.iam = boto3.client('iam', region_name=region)
        self.dynamodb = boto3.client('dynamodb', region_name=region)
        self.stepfunctions = boto3.client('stepfunctions', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.events = boto3.client('events', region_name=region)
        self.kms = boto3.client('kms', region_name=region)
        self.logs = boto3.client('logs', region_name=region)
        self.bedrock = boto3.client('bedrock-runtime', region_name=region)
        self.sts = boto3.client('sts', region_name=region)
        
        self.account_id = None
        self.stack_name = "ial-foundation"
        
    async def deploy_complete_foundation(self) -> Dict:
        """Deploy completo da foundation"""
        
        print("🚀 IAL Foundation Deployment Starting...")
        print(f"📍 Region: {self.region}\n")
        
        steps = [
            ("Validating AWS credentials", self._validate_aws_credentials),
            ("Validating Bedrock access", self._validate_bedrock_access),
            ("Creating IAM roles", self._create_iam_roles),
            ("Creating DynamoDB tables", self._create_dynamodb_tables),
            ("Creating S3 buckets", self._create_s3_buckets),
            ("Creating KMS keys", self._create_kms_keys),
            ("Creating Lambda functions", self._create_lambda_functions),
            ("Creating Step Functions", self._create_step_functions),
            ("Creating CloudWatch resources", self._create_cloudwatch_resources),
            ("Creating EventBridge rules", self._create_eventbridge_rules),
            ("Creating SNS topics", self._create_sns_topics),
            ("Validating system health", self._validate_system_health)
        ]
        
        results = {}
        for step_name, step_func in steps:
            print(f"🔄 {step_name}...")
            
            try:
                result = await step_func()
                results[step_name] = {"status": "success", "result": result}
                print(f"✅ {step_name}: OK\n")
            except Exception as e:
                results[step_name] = {"status": "error", "error": str(e)}
                print(f"❌ {step_name}: {e}\n")
                return results
        
        return results
    
    async def _validate_aws_credentials(self) -> Dict:
        """Valida credenciais AWS"""
        try:
            identity = self.sts.get_caller_identity()
            self.account_id = identity['Account']
            return {
                "account_id": self.account_id,
                "user_arn": identity['Arn']
            }
        except Exception as e:
            raise Exception(f"Invalid AWS credentials: {e}")
    
    async def _validate_bedrock_access(self) -> Dict:
        """Valida acesso ao Bedrock"""
        try:
            # Teste simples de invocação
            response = self.bedrock.invoke_model(
                modelId='anthropic.claude-3-haiku-20240307-v1:0',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 10,
                    'messages': [{'role': 'user', 'content': 'test'}]
                })
            )
            return {"status": "accessible", "model": "claude-3-haiku"}
        except Exception as e:
            raise Exception(f"Bedrock not accessible: {e}")
    
    async def _create_iam_roles(self) -> Dict:
        """Cria IAM roles necessárias"""
        roles_created = []
        
        # IALExecutionRole
        try:
            self.iam.create_role(
                RoleName='IALExecutionRole',
                AssumeRolePolicyDocument=json.dumps({
                    'Version': '2012-10-17',
                    'Statement': [{
                        'Effect': 'Allow',
                        'Principal': {'Service': ['lambda.amazonaws.com', 'states.amazonaws.com']},
                        'Action': 'sts:AssumeRole'
                    }]
                })
            )
            
            # Attach policies
            policies = [
                'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
                'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
                'arn:aws:iam::aws:policy/CloudWatchFullAccess'
            ]
            
            for policy_arn in policies:
                self.iam.attach_role_policy(RoleName='IALExecutionRole', PolicyArn=policy_arn)
            
            # Bedrock inline policy
            self.iam.put_role_policy(
                RoleName='IALExecutionRole',
                PolicyName='BedrockAccess',
                PolicyDocument=json.dumps({
                    'Version': '2012-10-17',
                    'Statement': [{
                        'Effect': 'Allow',
                        'Action': ['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'],
                        'Resource': '*'
                    }]
                })
            )
            
            roles_created.append('IALExecutionRole')
        except self.iam.exceptions.EntityAlreadyExistsException:
            roles_created.append('IALExecutionRole (already exists)')
        
        # MCPServerRole
        try:
            self.iam.create_role(
                RoleName='MCPServerRole',
                AssumeRolePolicyDocument=json.dumps({
                    'Version': '2012-10-17',
                    'Statement': [{
                        'Effect': 'Allow',
                        'Principal': {'Service': 'lambda.amazonaws.com'},
                        'Action': 'sts:AssumeRole'
                    }]
                })
            )
            
            self.iam.attach_role_policy(
                RoleName='MCPServerRole',
                PolicyArn='arn:aws:iam::aws:policy/ReadOnlyAccess'
            )
            
            roles_created.append('MCPServerRole')
        except self.iam.exceptions.EntityAlreadyExistsException:
            roles_created.append('MCPServerRole (already exists)')
        
        return {"roles": roles_created}
    
    async def _create_dynamodb_tables(self) -> Dict:
        """Cria DynamoDB tables necessárias"""
        tables = [
            {
                'name': 'ial-conversation-history',
                'pk': 'user_id',
                'sk': 'timestamp',
                'ttl': 'ttl'
            },
            {
                'name': 'ial-user-sessions',
                'pk': 'user_id',
                'sk': 'session_id',
                'ttl': 'ttl'
            },
            {
                'name': 'ial-conversation-cache',
                'pk': 'user_id',
                'sk': 'content_hash',
                'ttl': 'ttl'
            },
            {
                'name': 'ial-state',
                'pk': 'system_id',
                'sk': 'component'
            },
            {
                'name': 'ial-resource-catalog',
                'pk': 'resource_type',
                'sk': 'resource_id'
            },
            {
                'name': 'ial-rollback-checkpoints',
                'pk': 'deployment_id',
                'sk': 'checkpoint_id'
            },
            {
                'name': 'ial-token-usage',
                'pk': 'user_id',
                'sk': 'date'
            },
            {
                'name': 'ial-knowledge-base',
                'pk': 'topic',
                'sk': 'document_id'
            },
            {
                'name': 'ial-feature-flags',
                'pk': 'flag_name',
                'sk': 'environment'
            },
            {
                'name': 'ial-dynamodb-tables',
                'pk': 'table_name',
                'sk': 'metadata_type'
            },
            {
                'name': 'mcp-provisioning-checklist',
                'pk': 'mcp_server',
                'sk': 'check_id'
            }
        ]
        
        tables_created = []
        
        for table_def in tables:
            try:
                params = {
                    'TableName': table_def['name'],
                    'BillingMode': 'PAY_PER_REQUEST',
                    'AttributeDefinitions': [
                        {'AttributeName': table_def['pk'], 'AttributeType': 'S'},
                        {'AttributeName': table_def['sk'], 'AttributeType': 'S'}
                    ],
                    'KeySchema': [
                        {'AttributeName': table_def['pk'], 'KeyType': 'HASH'},
                        {'AttributeName': table_def['sk'], 'KeyType': 'RANGE'}
                    ]
                }
                
                self.dynamodb.create_table(**params)
                
                # Enable TTL if specified
                if 'ttl' in table_def:
                    time.sleep(2)  # Wait for table creation
                    self.dynamodb.update_time_to_live(
                        TableName=table_def['name'],
                        TimeToLiveSpecification={
                            'Enabled': True,
                            'AttributeName': table_def['ttl']
                        }
                    )
                
                tables_created.append(table_def['name'])
            except self.dynamodb.exceptions.ResourceInUseException:
                tables_created.append(f"{table_def['name']} (already exists)")
        
        return {"tables": tables_created}
    
    async def _create_s3_buckets(self) -> Dict:
        """Cria S3 buckets necessários"""
        buckets = [
            f'ial-artifacts-{self.account_id}',
            f'ial-memory-{self.account_id}',
            f'ial-rag-store-{self.account_id}'
        ]
        
        buckets_created = []
        
        for bucket_name in buckets:
            try:
                if self.region == 'us-east-1':
                    self.s3.create_bucket(Bucket=bucket_name)
                else:
                    self.s3.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': self.region}
                    )
                
                # Enable versioning
                self.s3.put_bucket_versioning(
                    Bucket=bucket_name,
                    VersioningConfiguration={'Status': 'Enabled'}
                )
                
                buckets_created.append(bucket_name)
            except self.s3.exceptions.BucketAlreadyOwnedByYou:
                buckets_created.append(f"{bucket_name} (already exists)")
        
        return {"buckets": buckets_created}
    
    async def _create_kms_keys(self) -> Dict:
        """Cria KMS keys necessárias"""
        keys_created = []
        
        key_aliases = ['IAL-Master-Key', 'RAG-KMS-Key']
        
        for alias in key_aliases:
            try:
                # Create key
                key_response = self.kms.create_key(
                    Description=f'IAL {alias}',
                    KeyUsage='ENCRYPT_DECRYPT',
                    Origin='AWS_KMS'
                )
                
                key_id = key_response['KeyMetadata']['KeyId']
                
                # Create alias
                self.kms.create_alias(
                    AliasName=f'alias/{alias}',
                    TargetKeyId=key_id
                )
                
                keys_created.append(alias)
            except Exception as e:
                if 'AlreadyExistsException' in str(e):
                    keys_created.append(f"{alias} (already exists)")
                else:
                    raise
        
        return {"keys": keys_created}
    
    async def _create_lambda_functions(self) -> Dict:
        """Cria Lambda functions necessárias"""
        # Placeholder - Lambda functions serão criadas via CloudFormation
        return {"status": "Lambda functions will be created via Step Functions deployment"}
    
    async def _create_step_functions(self) -> Dict:
        """Cria Step Functions state machines"""
        # Placeholder - Step Functions serão criadas via arquivos ASL existentes
        return {"status": "Step Functions will be deployed from existing ASL definitions"}
    
    async def _create_cloudwatch_resources(self) -> Dict:
        """Cria CloudWatch log groups e alarms"""
        log_groups = [
            '/aws/lambda/ial-circuit-guard',
            '/aws/lambda/ial-plan',
            '/aws/lambda/ial-apply',
            '/aws/states/ial-phase-pipeline',
            '/ial/system'
        ]
        
        groups_created = []
        
        for log_group in log_groups:
            try:
                self.logs.create_log_group(logGroupName=log_group)
                self.logs.put_retention_policy(
                    logGroupName=log_group,
                    retentionInDays=30
                )
                groups_created.append(log_group)
            except self.logs.exceptions.ResourceAlreadyExistsException:
                groups_created.append(f"{log_group} (already exists)")
        
        return {"log_groups": groups_created}
    
    async def _create_eventbridge_rules(self) -> Dict:
        """Cria EventBridge rules"""
        rules = [
            {
                'name': 'ial-drift-check',
                'schedule': 'rate(1 hour)',
                'description': 'Drift detection check'
            },
            {
                'name': 'ial-cost-monitoring',
                'schedule': 'rate(6 hours)',
                'description': 'Cost monitoring check'
            },
            {
                'name': 'ial-health-check',
                'schedule': 'rate(30 minutes)',
                'description': 'System health check'
            }
        ]
        
        rules_created = []
        
        for rule in rules:
            try:
                self.events.put_rule(
                    Name=rule['name'],
                    ScheduleExpression=rule['schedule'],
                    State='ENABLED',
                    Description=rule['description']
                )
                rules_created.append(rule['name'])
            except Exception as e:
                if 'already exists' in str(e).lower():
                    rules_created.append(f"{rule['name']} (already exists)")
                else:
                    raise
        
        return {"rules": rules_created}
    
    async def _create_sns_topics(self) -> Dict:
        """Cria SNS topics"""
        topics = ['ial-notifications', 'ial-drift-alerts']
        
        topics_created = []
        
        for topic_name in topics:
            try:
                response = self.sns.create_topic(Name=topic_name)
                topics_created.append(topic_name)
            except Exception as e:
                if 'already exists' in str(e).lower():
                    topics_created.append(f"{topic_name} (already exists)")
                else:
                    raise
        
        return {"topics": topics_created}
    
    async def _validate_system_health(self) -> Dict:
        """Valida saúde do sistema"""
        checks = {
            "dynamodb_tables": len([t for t in await self._list_dynamodb_tables() if t.startswith('ial-')]) >= 11,
            "iam_roles": await self._check_iam_roles(),
            "s3_buckets": len([b for b in await self._list_s3_buckets() if b.startswith('ial-')]) >= 3,
            "kms_keys": len(await self._list_kms_aliases()) >= 2,
            "log_groups": len([lg for lg in await self._list_log_groups() if '/ial/' in lg or 'ial-' in lg]) >= 5
        }
        
        all_healthy = all(checks.values())
        
        return {
            "system_ready": all_healthy,
            "checks": checks
        }
    
    async def _list_dynamodb_tables(self) -> List[str]:
        """Lista DynamoDB tables"""
        try:
            response = self.dynamodb.list_tables()
            return response.get('TableNames', [])
        except:
            return []
    
    async def _check_iam_roles(self) -> bool:
        """Verifica IAM roles"""
        try:
            self.iam.get_role(RoleName='IALExecutionRole')
            self.iam.get_role(RoleName='MCPServerRole')
            return True
        except:
            return False
    
    async def _list_s3_buckets(self) -> List[str]:
        """Lista S3 buckets"""
        try:
            response = self.s3.list_buckets()
            return [b['Name'] for b in response.get('Buckets', [])]
        except:
            return []
    
    async def _list_kms_aliases(self) -> List[str]:
        """Lista KMS aliases"""
        try:
            response = self.kms.list_aliases()
            return [a['AliasName'] for a in response.get('Aliases', []) if 'IAL' in a['AliasName']]
        except:
            return []
    
    async def _list_log_groups(self) -> List[str]:
        """Lista CloudWatch log groups"""
        try:
            response = self.logs.describe_log_groups()
            return [lg['logGroupName'] for lg in response.get('logGroups', [])]
        except:
            return []


# Função auxiliar para uso síncrono
def deploy_foundation_sync(region: str = "us-east-1") -> Dict:
    """Versão síncrona do deploy"""
    import asyncio
    deployer = IALFoundationDeployer(region=region)
    return asyncio.run(deployer.deploy_complete_foundation())
