"""
DynamoDB Construct
Creates all DynamoDB tables needed by IAL
"""

from aws_cdk import (
    aws_dynamodb as dynamodb,
    RemovalPolicy
)
from constructs import Construct

class DynamoDBConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str, project_name: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        
        # Main state table (01-dynamodb-state.yaml)
        self.state_table = dynamodb.Table(
            self, "StateTable",
            table_name=f"{project_name}-mcp-provisioning-checklist",
            partition_key=dynamodb.Attribute(
                name="Project",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="ResourceName", 
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
            time_to_live_attribute="TTL"
        )
        
        # Add GSI for status queries
        self.state_table.add_global_secondary_index(
            index_name="StatusIndex",
            partition_key=dynamodb.Attribute(
                name="Status",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="LastUpdated",
                type=dynamodb.AttributeType.STRING
            )
        )
        
        # Conversation memory table (07-conversation-memory.yaml)
        self.conversation_table = dynamodb.Table(
            self, "ConversationTable",
            table_name=f"{project_name}-conversation-history",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            time_to_live_attribute="expires_at"
        )
        
        # User sessions table
        self.sessions_table = dynamodb.Table(
            self, "SessionsTable", 
            table_name=f"{project_name}-user-sessions",
            partition_key=dynamodb.Attribute(
                name="session_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            time_to_live_attribute="expires_at"
        )
        
        # Feature flags table (18-ial-feature-flags.yaml)
        self.feature_flags_table = dynamodb.Table(
            self, "FeatureFlagsTable",
            table_name=f"{project_name}-feature-flags",
            partition_key=dynamodb.Attribute(
                name="flag_name",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN
        )
        
        # Circuit breaker tokens table (09-stepfunctions-orchestrator.yaml)
        self.circuit_breaker_table = dynamodb.Table(
            self, "CircuitBreakerTable",
            table_name=f"{project_name}-circuit-breaker-tokens",
            partition_key=dynamodb.Attribute(
                name="circuit_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            time_to_live_attribute="expires_at"
        )
