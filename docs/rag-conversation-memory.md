# 🧠 RAG + Conversation Memory

**Phase 17: Semantic search and conversation memory for Amazon Q**

---

## 🎯 Overview

This phase implements RAG (Retrieval Augmented Generation) using S3 Tables as vector store to give Amazon Q "memory" of previous conversations.

### Benefits

- 🧠 **Memory**: Amazon Q remembers previous conversations
- 🔍 **Semantic Search**: Find similar conversations by meaning
- 📊 **Context**: Better responses with historical context
- 💰 **Cost-Effective**: $5/month (vs $20+ with OpenSearch)

---

## 🏗️ Architecture

```
Amazon Q Conversation
    ↓
API Gateway (webhook)
    ↓
Lambda (capture + embed)
    ├─ Generate embedding (Bedrock Titan)
    ├─ Store in S3 Tables (vector store)
    └─ Store metadata in DynamoDB
    ↓
Bedrock Knowledge Base
    ↓
Amazon Q (enhanced context via RAG)
```

---

## 📦 Resources Created

| Resource | Purpose | Cost/month |
|----------|---------|------------|
| S3 Bucket (Tables) | Vector store | $2 |
| DynamoDB Table | Metadata index | $1 |
| Lambda Function | Capture conversations | $0.50 |
| Bedrock Knowledge Base | RAG engine | $1 |
| API Gateway | Webhook endpoint | $0.50 |
| **Total** | - | **$5** |

---

## 🚀 Usage

### 1. Capture Conversation

```bash
# Via API
curl -X POST https://YOUR_API_ENDPOINT/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "user": "diego",
    "text": "How do I add port 8443 to ALB security group?",
    "metadata": {
      "project": "ial-infrastructure",
      "phase": "10-alb"
    }
  }'

# Response
{
  "conversation_id": "uuid-here",
  "timestamp": 1729712345,
  "s3_key": "conversations/2025/10/23/uuid-here.json",
  "message": "Conversation stored successfully"
}
```

### 2. Search Conversations (Semantic)

```bash
# Search by meaning (not exact text)
aws bedrock-agent-runtime retrieve \
  --knowledge-base-id YOUR_KB_ID \
  --retrieval-query '{"text": "ALB port configuration"}' \
  --region us-east-1

# Returns similar conversations even if they used different words
```

### 3. Query Metadata

```bash
# Get conversation by ID
aws dynamodb get-item \
  --table-name ial-conversations-metadata \
  --key '{"ConversationId": {"S": "uuid-here"}}'

# Query by user
aws dynamodb query \
  --table-name ial-conversations-metadata \
  --index-name UserIndex \
  --key-condition-expression "User = :user" \
  --expression-attribute-values '{":user": {"S": "diego"}}'
```

---

## 🧠 How RAG Works

### 1. Conversation Capture

```python
# User asks Amazon Q
"How do I add port 8443 to ALB?"
    ↓
# Lambda captures and generates embedding
embedding = bedrock.invoke_model(
    modelId='amazon.titan-embed-text-v2:0',
    body={'inputText': conversation_text}
)
    ↓
# Stores in S3 Tables with vector
s3.put_object(
    Bucket='ial-conversations',
    Key='conversations/2025/10/23/uuid.json',
    Body=json.dumps({
        'text': conversation_text,
        'embedding': embedding,  # 1024-dim vector
        'metadata': {...}
    })
)
```

### 2. Semantic Search

```python
# User asks similar question
"How to open port 8443 on load balancer?"
    ↓
# Generate query embedding
query_embedding = generate_embedding(query)
    ↓
# S3 Tables vector search
results = s3_tables.vector_search(
    query_embedding,
    top_k=5,
    similarity='cosine'
)
    ↓
# Returns similar conversations
[
    {
        'text': 'How do I add port 8443 to ALB?',
        'similarity': 0.95,
        'metadata': {'phase': '10-alb'}
    },
    ...
]
```

### 3. Enhanced Response

```python
# Amazon Q uses retrieved context
context = "\n".join([r['text'] for r in results])

prompt = f"""
Context from previous conversations:
{context}

User question: {current_question}

Answer:
"""
    ↓
# Better response with historical context
```

---

## 💰 Cost Breakdown

### S3 Tables (Vector Store)
```
Storage: 20 GB × $0.023/GB = $0.46/month
Requests: 1M × $0.0004 = $0.40/month
Vector search: 1M × $0.001 = $1.00/month
Subtotal: $1.86/month
```

### DynamoDB (Metadata)
```
On-demand: ~$1/month (low usage)
```

### Lambda (Capture)
```
Invocations: 10k × $0.0000002 = $0.002/month
Duration: 10k × 1s × $0.0000166667 = $0.17/month
Subtotal: $0.17/month
```

### Bedrock (Embeddings)
```
Titan Embeddings: 1M tokens × $0.0001 = $1.00/month
```

### API Gateway
```
Requests: 10k × $0.000001 = $0.01/month
Data transfer: Minimal
Subtotal: $0.50/month
```

**Total: ~$5/month**

---

## 🔧 Configuration

### Environment Variables

```bash
# Lambda
S3_BUCKET=ial-conversations-221082174220
DYNAMODB_TABLE=ial-conversations-metadata
BEDROCK_MODEL=amazon.titan-embed-text-v2:0

# Bedrock Knowledge Base
KNOWLEDGE_BASE_ID=your-kb-id
EMBEDDING_MODEL=amazon.titan-embed-text-v2:0
```

### Retention Policy

```yaml
# S3 Lifecycle (90 days)
LifecycleConfiguration:
  Rules:
    - Id: "DeleteOldConversations"
      Status: "Enabled"
      ExpirationInDays: 90

# DynamoDB TTL (90 days)
TimeToLiveSpecification:
  Enabled: true
  AttributeName: "TTL"
```

---

## 📊 Monitoring

### CloudWatch Metrics

```bash
# Lambda invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=ial-conversation-capture \
  --start-time 2025-10-23T00:00:00Z \
  --end-time 2025-10-23T23:59:59Z \
  --period 3600 \
  --statistics Sum

# S3 requests
aws cloudwatch get-metric-statistics \
  --namespace AWS/S3 \
  --metric-name AllRequests \
  --dimensions Name=BucketName,Value=ial-conversations-221082174220 \
  --start-time 2025-10-23T00:00:00Z \
  --end-time 2025-10-23T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

### DynamoDB Metrics

```bash
# Item count
aws dynamodb describe-table \
  --table-name ial-conversations-metadata \
  --query 'Table.ItemCount'

# Storage size
aws dynamodb describe-table \
  --table-name ial-conversations-metadata \
  --query 'Table.TableSizeBytes'
```

---

## 🎯 Integration with Amazon Q

### Automatic Capture (Future)

```python
# Amazon Q MCP tool integration
@mcp_tool
def capture_conversation(conversation_text, metadata):
    """Automatically capture Amazon Q conversations"""
    response = requests.post(
        'https://api-endpoint/conversations',
        json={
            'user': os.environ['USER'],
            'text': conversation_text,
            'metadata': metadata
        }
    )
    return response.json()
```

### Enhanced Context (Future)

```python
# Amazon Q retrieves context before responding
@mcp_tool
def get_conversation_context(query):
    """Get relevant conversation history"""
    response = bedrock_agent.retrieve(
        knowledgeBaseId=KB_ID,
        retrievalQuery={'text': query}
    )
    return response['retrievalResults']
```

---

## 🚀 Deployment

### Deploy Phase 17

```bash
# Via Amazon Q
q chat "Deploy Phase 17: RAG with S3 Tables"

# Via manual
cd /home/ial
python scripts/reconcile.py --phase 17
```

### Verify Deployment

```bash
# Check S3 bucket
aws s3 ls s3://ial-conversations-221082174220/

# Check DynamoDB table
aws dynamodb describe-table --table-name ial-conversations-metadata

# Check Lambda function
aws lambda get-function --function-name ial-conversation-capture

# Check Bedrock Knowledge Base
aws bedrock-agent list-knowledge-bases
```

---

## 🎉 Benefits

### vs Traditional IaC

| Feature | IaC | IaL + RAG |
|---------|-----|-----------|
| Memory | ❌ None | ✅ 90 days |
| Context | ❌ None | ✅ Semantic |
| Learning | ❌ None | ✅ Continuous |
| Search | ❌ None | ✅ Vector |
| Cost | $0 | $5/month |

### vs OpenSearch

| Feature | OpenSearch | S3 Tables |
|---------|-----------|-----------|
| Cost | $15-20/month | $5/month |
| Latency | 10-50ms | 100-200ms |
| Setup | Complex | Simple |
| Scale | Limited | Unlimited |
| Maintenance | High | Low |

---

## 📚 References

- [AWS S3 Tables](https://docs.aws.amazon.com/s3/latest/userguide/s3-tables.html)
- [Bedrock Knowledge Bases](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)
- [Titan Embeddings](https://docs.aws.amazon.com/bedrock/latest/userguide/titan-embedding-models.html)
- [Vector Search](https://docs.aws.amazon.com/s3/latest/userguide/s3-tables-vector-search.html)

---

**Phase 17 = Amazon Q with Memory** 🧠🚀
