#!/usr/bin/env python3
import json
import os
import subprocess
import boto3

def handler(event, context):
    phase_payload = event['phase_result']['Payload']
    phase_result = phase_payload.get('body', phase_payload)
    
    phase_file = f"{phase_result['phase_number']:02d}-{phase_result['phase_name']}.yaml"
    yaml_path = f"/tmp/{phase_file}"
    
    with open(yaml_path, 'w') as f:
        f.write(phase_result['yaml_content'])
    
    return {
        "statusCode": 200,
        "body": {
            "phase_file": phase_file,
            "commit_sha": "mock-sha",
            "pr_url": "https://github.com/Diego-Nardoni/ial-infrastructure/pull/new/main",
            "message": "PR will be created by GitHub Actions"
        },
        "correlation_id": event.get('correlation_id')
    }
