#!/usr/bin/env python3
"""
Lambda Handler: Drift Detection
"""

import json
import boto3


def handler(event, context):
    """
    Detecta drift entre AWS real e Git desired state
    
    Input:
        {
            "deployment_result": {...}
        }
    
    Output:
        {
            "drift_detected": bool,
            "drift_type": "safe" | "risky",
            "drifted_resources": [...]
        }
    """
    
    deployment = event['deployment_result']['body']
    stack_name = deployment['stack_name']
    
    cfn = boto3.client('cloudformation')
    
    # Iniciar drift detection
    try:
        cfn.detect_stack_drift(StackName=stack_name)
        
        # Aguardar resultado (simplified - deveria usar waiter)
        import time
        time.sleep(5)
        
        # Get drift status
        drift_response = cfn.describe_stack_drift_detection_status(
            StackDriftDetectionId=cfn.detect_stack_drift(StackName=stack_name)['StackDriftDetectionId']
        )
        
        drift_status = drift_response['StackDriftStatus']
        
        if drift_status == 'DRIFTED':
            # Get drifted resources
            drifted = cfn.describe_stack_resource_drifts(
                StackName=stack_name,
                StackResourceDriftStatusFilters=['MODIFIED', 'DELETED']
            )
            
            # Classify drift as safe or risky
            risky_types = ['AWS::IAM::Role', 'AWS::IAM::Policy', 'AWS::EC2::SecurityGroup']
            
            drift_type = "risky" if any(
                r['ResourceType'] in risky_types
                for r in drifted['StackResourceDrifts']
            ) else "safe"
            
            return {
                "statusCode": 200,
                "body": {
                    "drift_detected": True,
                    "drift_type": drift_type,
                    "drifted_resources": [
                        {
                            "resource_id": r['LogicalResourceId'],
                            "resource_type": r['ResourceType'],
                            "drift_status": r['StackResourceDriftStatus']
                        }
                        for r in drifted['StackResourceDrifts']
                    ]
                }
            }
        
        return {
            "statusCode": 200,
            "body": {
                "drift_detected": False,
                "drift_type": None,
                "drifted_resources": []
            }
        }
    
    except Exception as e:
        return {
            "statusCode": 500,
            "body": {
                "error": str(e),
                "drift_detected": False
            }
        }
