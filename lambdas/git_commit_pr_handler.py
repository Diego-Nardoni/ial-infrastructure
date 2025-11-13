#!/usr/bin/env python3
"""
Lambda Handler: Git Commit & Create PR
"""

import json
import os
import subprocess
import boto3


def handler(event, context):
    """
    Input:
        {
            "phase_result": {
                "phase_number": 30,
                "phase_name": "ecs-cache",
                "yaml_content": "...",
                "estimated_cost": 150.0
            },
            "correlation_id": "uuid"
        }
    
    Output:
        {
            "phase_file": "30-ecs-cache.yaml",
            "commit_sha": "abc123",
            "pr_url": "https://github.com/..."
        }
    """
    
    phase_result = event['phase_result']['body']
    
    # 1. Salvar YAML em /tmp
    phase_file = f"{phase_result['phase_number']:02d}-{phase_result['phase_name']}.yaml"
    yaml_path = f"/tmp/{phase_file}"
    
    with open(yaml_path, 'w') as f:
        f.write(phase_result['yaml_content'])
    
    # 2. Clone repo (usando CodeCommit ou GitHub)
    repo_url = os.environ.get('REPO_URL', 'https://github.com/Diego-Nardoni/ial-infrastructure.git')
    repo_dir = '/tmp/ial-repo'
    
    # Clone
    subprocess.run(['git', 'clone', repo_url, repo_dir], check=True)
    
    # Copy YAML
    subprocess.run(['cp', yaml_path, f"{repo_dir}/phases/{phase_file}"], check=True)
    
    # Git commit
    subprocess.run(['git', 'add', f"phases/{phase_file}"], cwd=repo_dir, check=True)
    subprocess.run([
        'git', 'commit', '-m',
        f'feat: Add {phase_result["phase_name"]} phase\n\nGenerated via IAL NL Intent Pipeline\nCost: ${phase_result["estimated_cost"]:.2f}/month'
    ], cwd=repo_dir, check=True)
    
    # Get commit SHA
    commit_sha = subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'],
        cwd=repo_dir
    ).decode().strip()
    
    # Push
    subprocess.run(['git', 'push', 'origin', 'main'], cwd=repo_dir, check=True)
    
    # 3. Create PR via GitHub API (will be done by GitHub Actions)
    pr_url = f"https://github.com/Diego-Nardoni/ial-infrastructure/pull/new/main"
    
    return {
        "statusCode": 200,
        "body": {
            "phase_file": phase_file,
            "commit_sha": commit_sha,
            "pr_url": pr_url,
            "message": "PR will be created by GitHub Actions"
        },
        "correlation_id": event.get('correlation_id')
    }
