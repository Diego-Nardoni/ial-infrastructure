#!/usr/bin/env python3
"""
Lambda Handler: Wait for PR Approval (callback pattern)
"""

import json
import os
import boto3


def handler(event, context):
    """
    Envia callback token para GitHub Actions
    GitHub Actions chamará SendTaskSuccess quando PR for aprovado
    
    Input:
        {
            "git_result": {...},
            "TaskToken": "..." (Step Functions callback token)
        }
    """
    
    task_token = event['TaskToken']
    pr_url = event['git_result']['body']['pr_url']
    
    # Salvar task token no DynamoDB para GitHub Actions recuperar
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('ial-pr-callbacks')
    
    table.put_item(Item={
        'pr_url': pr_url,
        'task_token': task_token,
        'status': 'waiting_approval'
    })
    
    return {
        "statusCode": 200,
        "message": f"Aguardando aprovação do PR: {pr_url}",
        "task_token_saved": True
    }
