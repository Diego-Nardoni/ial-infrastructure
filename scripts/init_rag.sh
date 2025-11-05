#!/bin/bash

echo "🚀 Inicializando RAG System para IAL..."

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &>/dev/null; then
    echo "❌ AWS credentials not configured"
    exit 1
fi

# Create S3 bucket for knowledge base (if not exists)
BUCKET_NAME="ial-knowledge-base-$(date +%s)"
echo "📦 Creating S3 bucket: $BUCKET_NAME"

aws s3 mb s3://$BUCKET_NAME 2>/dev/null || echo "Bucket may already exist"

# Index existing documents
echo "🔍 Indexing IAL documents..."
cd /home/ial
python3 rag/rag_cli.py index

echo "✅ RAG System initialized successfully!"
echo "💡 Try: python3 rag/rag_cli.py query 'How to deploy security phase?'"
