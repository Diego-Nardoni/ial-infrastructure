#!/usr/bin/env python3
"""
Lambda Handler: IAS Validation
"""

import json
import sys
sys.path.append('/opt/python')

from ias_sandbox import IASandbox


def handler(event, context):
    """
    Input:
        {
            "nl_intent": "quero ECS privado com Redis",
            "correlation_id": "uuid"
        }
    
    Output:
        {
            "safe": bool,
            "risks": [...],
            "severity_score": int,
            "recommendation": str
        }
    """
    
    nl_intent = event['nl_intent']
    
    ias = IASandbox()
    result = ias.validate_intent(nl_intent)
    
    return {
        "statusCode": 200,
        "body": result,
        "nl_intent": nl_intent,
        "correlation_id": event.get('correlation_id')
    }
