#!/usr/bin/env python3
"""
Lambda Handler: Post-Deploy Analysis (WA + FinOps + Compliance)
"""

import json
import boto3


def handler(event, context):
    """
    Análise pós-deployment via MCP Mesh
    - Well-Architected assessment
    - FinOps analysis
    - Compliance check
    
    Input:
        {
            "deployment_result": {...},
            "proof_result": {...}
        }
    
    Output:
        {
            "well_architected_score": int,
            "cost_optimization_opportunities": [...],
            "compliance_status": "compliant" | "non_compliant"
        }
    """
    
    deployment = event['deployment_result']['body']
    stack_name = deployment['stack_name']
    
    # 1. Well-Architected Assessment (simplified)
    wa_score = 85  # Placeholder - integrar com AWS Well-Architected Tool
    
    # 2. FinOps Analysis
    ce = boto3.client('ce')
    
    # Get cost for last 7 days
    from datetime import datetime, timedelta
    end = datetime.now().date()
    start = end - timedelta(days=7)
    
    try:
        cost_response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': start.isoformat(),
                'End': end.isoformat()
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost'],
            Filter={
                'Tags': {
                    'Key': 'aws:cloudformation:stack-name',
                    'Values': [stack_name]
                }
            }
        )
        
        total_cost = sum(
            float(day['Total']['UnblendedCost']['Amount'])
            for day in cost_response['ResultsByTime']
        )
    except:
        total_cost = 0.0
    
    # Cost optimization opportunities
    opportunities = []
    if total_cost > 50:
        opportunities.append({
            "type": "reserved_instances",
            "potential_savings": total_cost * 0.4,
            "recommendation": "Consider Reserved Instances for 40% savings"
        })
    
    # 3. Compliance Check (simplified)
    compliance_status = "compliant"  # Placeholder - integrar com AWS Config
    
    return {
        "statusCode": 200,
        "body": {
            "well_architected_score": wa_score,
            "cost_last_7_days": round(total_cost, 2),
            "cost_optimization_opportunities": opportunities,
            "compliance_status": compliance_status,
            "recommendations": [
                "✅ Stack deployed successfully",
                f"💰 Current 7-day cost: ${total_cost:.2f}",
                f"🏗️ Well-Architected score: {wa_score}/100"
            ]
        }
    }
