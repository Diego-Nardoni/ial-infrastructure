#!/usr/bin/env python3
"""
Lambda Handler: Phase Builder
"""

import json
import sys
sys.path.append('/opt/python')

from intelligent_phase_builder import IntelligentPhaseBuilder


def handler(event, context):
    """
    Input:
        {
            "nl_intent": "quero ECS privado com Redis",
            "ias_result": {"Payload": {"statusCode": 200, "body": {...}}},
            "cost_result": {"Payload": {"statusCode": 200, "body": {...}}},
            "correlation_id": "uuid"
        }
    
    Output:
        {
            "phase_number": int,
            "phase_name": str,
            "yaml_content": str,
            "dependencies": [...],
            "estimated_cost": float
        }
    """
    
    nl_intent = event['nl_intent']
    
    # Extrair body do Payload (Step Functions invoke retorna Payload)
    ias_payload = event['ias_result']['Payload']
    cost_payload = event['cost_result']['Payload']
    
    ias_result = ias_payload.get('body', ias_payload)
    cost_result = cost_payload.get('body', cost_payload)
    
    builder = IntelligentPhaseBuilder()
    result = builder.build_phase_from_intent(
        nl_intent,
        ias_result,
        cost_result
    )
    
    return {
        "statusCode": 200,
        "body": result,
        "nl_intent": nl_intent,
        "correlation_id": event.get('correlation_id')
    }
