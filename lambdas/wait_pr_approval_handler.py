#!/usr/bin/env python3
"""
Lambda Handler: Wait for PR Approval (simplified)
"""

import json


def handler(event, context):
    """
    Simula aprovação automática do PR para teste
    Em produção, seria integrado com GitHub Actions
    """
    
    # Extrair body do Payload (Step Functions invoke retorna Payload)
    git_payload = event['git_result']['Payload']
    git_result = git_payload.get('body', git_payload)
    pr_url = git_result['pr_url']
    
    # Simular aprovação automática para teste
    return {
        "statusCode": 200,
        "body": {
            "pr_approved": True,
            "pr_url": pr_url,
            "approved_by": "auto-approval-test",
            "approved_at": "2025-11-14T12:18:00Z",
            "message": "PR aprovado automaticamente para teste"
        }
    }
