#!/usr/bin/env python3
"""
Build RAG Index - Cria índice FAISS com docs AWS
"""

import os
import json

def build_basic_index():
    """Cria índice básico com snippets AWS"""
    
    # Criar diretório
    os.makedirs('.rag', exist_ok=True)
    
    # Snippets básicos (placeholder - depois integrar com docs reais)
    snippets = [
        {
            "text": "Amazon S3 bucket encryption: Use server-side encryption with AWS KMS (SSE-KMS) or S3-managed keys (SSE-S3). Enable default encryption on bucket.",
            "source": "s3-encryption-best-practices",
            "score": 0.95
        },
        {
            "text": "Amazon ECS task definition: Requires task role ARN, execution role ARN, network mode (awsvpc for Fargate), CPU and memory allocation.",
            "source": "ecs-task-definition",
            "score": 0.92
        },
        {
            "text": "VPC best practices: Use private subnets for compute resources, public subnets only for load balancers. Enable VPC Flow Logs for monitoring.",
            "source": "vpc-best-practices",
            "score": 0.90
        },
        {
            "text": "RDS encryption: Enable encryption at rest using AWS KMS. Cannot be enabled after database creation. Use encrypted snapshots for migration.",
            "source": "rds-encryption",
            "score": 0.88
        },
        {
            "text": "ElastiCache Redis: Use cluster mode for high availability. Enable encryption in-transit and at-rest. Configure automatic backups.",
            "source": "elasticache-redis-ha",
            "score": 0.87
        },
        {
            "text": "IAM least privilege: Grant minimum permissions required. Use managed policies when possible. Avoid wildcard (*) in production.",
            "source": "iam-least-privilege",
            "score": 0.85
        }
    ]
    
    # Salvar como JSON (placeholder para FAISS real)
    with open('.rag/index.json', 'w') as f:
        json.dump(snippets, f, indent=2)
    
    print(f"✅ RAG index criado: {len(snippets)} snippets")
    print("📁 Localização: .rag/index.json")

if __name__ == '__main__':
    build_basic_index()
