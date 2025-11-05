#!/usr/bin/env python3
"""
Deploy Step Functions State Machines
"""

import boto3
import json
from pathlib import Path

class StepFunctionsDeployer:
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.stepfunctions = boto3.client('stepfunctions', region_name=region)
        self.iam = boto3.client('iam', region_name=region)
        
    def create_execution_role(self) -> str:
        """Create IAM role for Step Functions execution"""
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "states.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "lambda:InvokeFunction",
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        role_name = "ial-stepfunctions-execution-role"
        
        try:
            # Create role
            self.iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="IAL Step Functions execution role"
            )
            
            # Attach policy
            self.iam.put_role_policy(
                RoleName=role_name,
                PolicyName="ial-stepfunctions-policy",
                PolicyDocument=json.dumps(policy_document)
            )
            
            print(f"✅ Created IAM role: {role_name}")
            
        except Exception as e:
            if "EntityAlreadyExists" not in str(e):
                print(f"❌ Failed to create IAM role: {e}")
                raise
        
        return f"arn:aws:iam::{self._get_account_id()}:role/{role_name}"
    
    def _get_account_id(self) -> str:
        """Get AWS account ID"""
        sts = boto3.client('sts')
        return sts.get_caller_identity()['Account']
    
    def deploy_state_machine(self, name: str, definition_file: str) -> str:
        """Deploy a Step Functions state machine"""
        
        definition_path = Path(__file__).parent / definition_file
        
        with open(definition_path, 'r') as f:
            definition = f.read()
        
        # Replace account ID placeholder
        account_id = self._get_account_id()
        definition = definition.replace("{account_id}", account_id)
        
        role_arn = self.create_execution_role()
        
        try:
            # Try to update existing state machine
            response = self.stepfunctions.update_state_machine(
                stateMachineArn=f"arn:aws:states:{self.region}:{account_id}:stateMachine:{name}",
                definition=definition,
                roleArn=role_arn
            )
            print(f"✅ Updated state machine: {name}")
            
        except Exception:
            # Create new state machine
            try:
                response = self.stepfunctions.create_state_machine(
                    name=name,
                    definition=definition,
                    roleArn=role_arn,
                    type='STANDARD'
                )
                print(f"✅ Created state machine: {name}")
                
            except Exception as e:
                print(f"❌ Failed to deploy state machine {name}: {e}")
                raise
        
        return response['stateMachineArn']
    
    def deploy_all(self):
        """Deploy all IAL Step Functions state machines"""
        
        state_machines = [
            ("ial-healing-orchestrator", "healing_orchestrator_definition.json"),
            ("ial-phase-manager", "phase_manager_definition.json"),
            ("ial-audit-validator", "audit_validator_definition.json")
        ]
        
        deployed_arns = {}
        
        for name, definition_file in state_machines:
            try:
                arn = self.deploy_state_machine(name, definition_file)
                deployed_arns[name] = arn
            except Exception as e:
                print(f"❌ Failed to deploy {name}: {e}")
        
        return deployed_arns

if __name__ == "__main__":
    deployer = StepFunctionsDeployer()
    arns = deployer.deploy_all()
    
    print("\n🚀 Deployment Summary:")
    for name, arn in arns.items():
        print(f"  {name}: {arn}")
