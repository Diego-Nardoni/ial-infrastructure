#!/usr/bin/env python3
"""
Lambda Handler: Cost Estimation
"""

import json
import sys
sys.path.append('/opt/python')

from cost_guardrails import CostGuardrails


def handler(event, context):
    """
    Input:
        {
            "nl_intent": "quero ECS privado com Redis",
            "correlation_id": "uuid",
            "monthly_budget": 500.0
        }
    
    Output:
        {
            "estimates": [...],
            "total_monthly_cost": float,
            "within_budget": bool,
            "alternatives": [...]
        }
    """
    
    nl_intent = event['nl_intent']
    monthly_budget = event.get('monthly_budget', 500.0)
    
    cost_guardrails = CostGuardrails(monthly_budget=monthly_budget)
    result = cost_guardrails.estimate_from_intent(nl_intent)
    
    return {
        "statusCode": 200,
        "body": result,
        "nl_intent": nl_intent,
        "correlation_id": event.get('correlation_id')
    }
