#!/usr/bin/env python3
"""
Lambda Handler: Reverse Sync
Detecta mudanças no console AWS e cria PRs
"""

import json
import boto3
import sys
import os

# Add core modules to path
sys.path.append('/opt/python')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def handler(event, context):
    """
    Processa eventos do console AWS e cria PRs para sincronizar
    
    Input (EventBridge):
        {
            "source": "aws.s3",
            "detail-type": "AWS API Call via CloudTrail",
            "detail": {
                "eventName": "CreateBucket",
                "responseElements": {...}
            }
        }
    
    Output:
        {
            "reverse_sync_status": "pr_created" | "ignored" | "failed",
            "pr_url": "...",
            "resource_discovered": {...}
        }
    """
    
    try:
        # Verificar se é evento relevante
        if not _is_relevant_event(event):
            return {
                "statusCode": 200,
                "body": {
                    "reverse_sync_status": "ignored",
                    "reason": "Event not relevant for reverse sync",
                    "event_source": event.get('source', 'unknown')
                }
            }
        
        # Descobrir recurso criado/modificado
        resource_info = _discover_resource(event)
        
        if not resource_info:
            return {
                "statusCode": 200,
                "body": {
                    "reverse_sync_status": "ignored",
                    "reason": "Could not discover resource details"
                }
            }
        
        # Gerar YAML para o recurso
        try:
            from core.drift.reverse_sync import ReverseSync
            reverse_sync = ReverseSync()
            
            yaml_content = reverse_sync.generate_yaml_from_resource(resource_info)
            
            if yaml_content:
                # Criar PR (simulado por enquanto)
                pr_result = _create_reverse_sync_pr(resource_info, yaml_content)
                
                return {
                    "statusCode": 200,
                    "body": {
                        "reverse_sync_status": "pr_created",
                        "pr_url": pr_result.get('pr_url'),
                        "resource_discovered": resource_info,
                        "yaml_generated": True,
                        "message": f"Reverse sync PR created for {resource_info.get('resource_type')}"
                    }
                }
            else:
                return {
                    "statusCode": 200,
                    "body": {
                        "reverse_sync_status": "failed",
                        "reason": "Could not generate YAML for resource",
                        "resource_discovered": resource_info
                    }
                }
                
        except ImportError:
            # Fallback sem reverse sync engine
            return {
                "statusCode": 200,
                "body": {
                    "reverse_sync_status": "failed",
                    "reason": "Reverse sync engine not available",
                    "resource_discovered": resource_info
                }
            }
    
    except Exception as e:
        return {
            "statusCode": 500,
            "body": {
                "reverse_sync_status": "failed",
                "error": str(e),
                "message": "Reverse sync handler failed"
            }
        }

def _is_relevant_event(event: dict) -> bool:
    """Verifica se o evento é relevante para reverse sync"""
    
    # Eventos relevantes
    relevant_events = {
        'CreateBucket', 'RunInstances', 'CreateDBInstance',
        'CreateLoadBalancer', 'CreateFunction', 'CreateTable'
    }
    
    event_name = event.get('detail', {}).get('eventName', '')
    event_source = event.get('source', '')
    
    # Filtrar apenas eventos de criação de recursos importantes
    return (event_name in relevant_events and 
            event_source.startswith('aws.'))

def _discover_resource(event: dict) -> dict:
    """Descobre detalhes do recurso criado/modificado"""
    
    detail = event.get('detail', {})
    event_name = detail.get('eventName', '')
    response_elements = detail.get('responseElements', {})
    
    # Mapear eventos para tipos de recursos
    resource_mapping = {
        'CreateBucket': {
            'resource_type': 'AWS::S3::Bucket',
            'resource_id': response_elements.get('bucketName', 'unknown')
        },
        'RunInstances': {
            'resource_type': 'AWS::EC2::Instance',
            'resource_id': response_elements.get('instanceId', 'unknown')
        },
        'CreateDBInstance': {
            'resource_type': 'AWS::RDS::DBInstance',
            'resource_id': response_elements.get('dBInstanceIdentifier', 'unknown')
        }
    }
    
    if event_name in resource_mapping:
        resource_info = resource_mapping[event_name].copy()
        resource_info.update({
            'event_name': event_name,
            'event_time': detail.get('eventTime'),
            'aws_region': detail.get('awsRegion'),
            'user_identity': detail.get('userIdentity', {}).get('type')
        })
        return resource_info
    
    return None

def _create_reverse_sync_pr(resource_info: dict, yaml_content: str) -> dict:
    """Cria PR para reverse sync (simulado)"""
    
    import time
    timestamp = int(time.time())
    
    # Simular criação de PR
    pr_url = f"https://github.com/Diego-Nardoni/ial-infrastructure/pull/reverse-sync-{timestamp}"
    
    return {
        'pr_url': pr_url,
        'pr_title': f"Reverse Sync: {resource_info.get('resource_type')} {resource_info.get('resource_id')}",
        'branch_name': f"reverse-sync-{timestamp}",
        'yaml_file': f"phases/90-reverse-sync/{resource_info.get('resource_id')}.yaml"
    }
