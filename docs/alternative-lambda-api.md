# Opção Alternativa: API Lambda para Linguagem Natural

**Status:** 📋 Documentação (não implementado)  
**Recomendação:** Use Amazon Q + MCP Server (Opção 1)

---

## 🎯 Visão Geral

Esta é uma **arquitetura alternativa** para interface de linguagem natural com a infraestrutura IaL. A implementação padrão usa **Amazon Q + MCP Server** (mais simples e já disponível).

Use esta opção apenas se você precisar de:
- API REST pública
- Interface web
- Integração com Slack/Teams
- Acesso fora do terminal

---

## 🏗️ Arquitetura Lambda API

```
┌─────────────────────────────────────────────────────────────┐
│  Cliente (qualquer interface)                               │
│  - Web UI                                                    │
│  - Mobile app                                                │
│  - Slack bot                                                 │
│  - curl/Postman                                              │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  API Gateway                                                 │
│  - POST /ial/command                                         │
│  - Authentication (API Key ou Cognito)                       │
│  - Rate limiting                                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Lambda: natural-language-processor                          │
│                                                              │
│  1. Parse comando (Bedrock)                                 │
│  2. Atualizar YAML (S3)                                     │
│  3. Git commit + push (CodeCommit ou GitHub API)            │
│  4. Trigger reconciliation                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  GitHub Actions (CI/CD)                                      │
│  - Detecta push                                              │
│  - Executa reconciliation                                    │
│  - Aplica mudanças na AWS                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Componentes Necessários

### **1. Lambda Function**

```python
# lambda/natural-language/index.py
import boto3
import json
import yaml
from github import Github

bedrock = boto3.client('bedrock-runtime')
s3 = boto3.client('s3')

def lambda_handler(event, context):
    """Process natural language infrastructure commands"""
    
    # Parse request
    body = json.loads(event['body'])
    command = body['command']
    
    # Parse with Bedrock
    intent = parse_command_with_bedrock(command)
    
    # Update YAML
    update_yaml_in_s3(intent)
    
    # Git commit + push
    commit_to_github(intent)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f"✅ {intent['explanation']}",
            'intent': intent
        })
    }

def parse_command_with_bedrock(command):
    """Use Bedrock to parse natural language"""
    
    prompt = f"""
    Parse this infrastructure command:
    "{command}"
    
    Return JSON:
    {{
      "action": "ADD|REMOVE|MODIFY",
      "resource": "security_group|alb|ecs|...",
      "file": "phases/XX-resource.yaml",
      "yaml_path": "path.to.field",
      "change": {{"field": "value"}},
      "explanation": "what will be done"
    }}
    """
    
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        body=json.dumps({
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 2000,
            'messages': [{'role': 'user', 'content': prompt}]
        })
    )
    
    result = json.loads(response['body'].read())
    return json.loads(result['content'][0]['text'])

def update_yaml_in_s3(intent):
    """Update YAML file in S3"""
    
    # Download YAML from S3
    obj = s3.get_object(
        Bucket='ial-infrastructure',
        Key=intent['file']
    )
    data = yaml.safe_load(obj['Body'].read())
    
    # Apply change
    keys = intent['yaml_path'].split('.')
    current = data
    for key in keys[:-1]:
        current = current[key]
    current[keys[-1]] = intent['change']
    
    # Upload back to S3
    s3.put_object(
        Bucket='ial-infrastructure',
        Key=intent['file'],
        Body=yaml.dump(data)
    )

def commit_to_github(intent):
    """Commit changes to GitHub"""
    
    g = Github(os.environ['GITHUB_TOKEN'])
    repo = g.get_repo(os.environ['GITHUB_REPO'])
    
    # Get file content
    file = repo.get_contents(intent['file'])
    
    # Update file
    repo.update_file(
        path=intent['file'],
        message=f"Update via API: {intent['explanation']}",
        content=file.decoded_content,
        sha=file.sha
    )
```

---

### **2. API Gateway**

```yaml
# cloudformation/api-gateway.yaml
Resources:
  IaLAPI:
    Type: AWS::ApiGatewayV2::Api
    Properties:
      Name: ial-natural-language-api
      ProtocolType: HTTP
      CorsConfiguration:
        AllowOrigins:
          - '*'
        AllowMethods:
          - POST
        AllowHeaders:
          - Content-Type
          - Authorization
  
  IaLRoute:
    Type: AWS::ApiGatewayV2::Route
    Properties:
      ApiId: !Ref IaLAPI
      RouteKey: POST /ial/command
      Target: !Sub integrations/${IaLIntegration}
      AuthorizationType: AWS_IAM
  
  IaLIntegration:
    Type: AWS::ApiGatewayV2::Integration
    Properties:
      ApiId: !Ref IaLAPI
      IntegrationType: AWS_PROXY
      IntegrationUri: !GetAtt NaturalLanguageLambda.Arn
      PayloadFormatVersion: '2.0'
```

---

### **3. IAM Permissions**

```yaml
LambdaExecutionRole:
  Type: AWS::IAM::Role
  Properties:
    AssumeRolePolicyDocument:
      Version: '2012-10-17'
      Statement:
        - Effect: Allow
          Principal:
            Service: lambda.amazonaws.com
          Action: sts:AssumeRole
    ManagedPolicyArns:
      - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    Policies:
      - PolicyName: BedrockAccess
        PolicyDocument:
          Version: '2012-10-17'
          Statement:
            - Effect: Allow
              Action:
                - bedrock:InvokeModel
              Resource: '*'
      
      - PolicyName: S3Access
        PolicyDocument:
          Version: '2012-10-17'
          Statement:
            - Effect: Allow
              Action:
                - s3:GetObject
                - s3:PutObject
              Resource: arn:aws:s3:::ial-infrastructure/*
      
      - PolicyName: DynamoDBAccess
        PolicyDocument:
          Version: '2012-10-17'
          Statement:
            - Effect: Allow
              Action:
                - dynamodb:PutItem
                - dynamodb:GetItem
                - dynamodb:UpdateItem
              Resource: arn:aws:dynamodb:*:*:table/mcp-provisioning-checklist
```

---

## 🚀 Uso da API

### **Exemplo 1: Adicionar Porta**

```bash
curl -X POST https://api.example.com/ial/command \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "command": "Adicione porta 8443 no security group do ALB"
  }'

# Response:
{
  "message": "✅ Porta 8443 adicionada ao Security Group ALB",
  "intent": {
    "action": "ADD",
    "resource": "security_group",
    "file": "phases/03-networking.yaml",
    "change": {"port": 8443, "cidr": "0.0.0.0/0"}
  }
}
```

---

### **Exemplo 2: Escalar ECS**

```bash
curl -X POST https://api.example.com/ial/command \
  -H "Content-Type: application/json" \
  -d '{
    "command": "Aumente o número mínimo de tasks ECS para 5"
  }'

# Response:
{
  "message": "✅ ECS Service escalado para 5 tasks mínimas",
  "intent": {
    "action": "MODIFY",
    "resource": "ecs_service",
    "file": "phases/08-ecs-task-service.yaml",
    "change": {"desired_count": 5}
  }
}
```

---

### **Exemplo 3: Rollback**

```bash
curl -X POST https://api.example.com/ial/command \
  -H "Content-Type: application/json" \
  -d '{
    "command": "Desfaça a última mudança"
  }'

# Response:
{
  "message": "✅ Rollback completo - porta 8443 removida",
  "intent": {
    "action": "ROLLBACK",
    "target_commit": "abc123",
    "changes_reverted": ["Add port 8443"]
  }
}
```

---

## 💰 Custo Estimado

```
Lambda:
- Invocações: 50/mês
- Duração: 10s × 256MB
- Custo: ~$0.20/mês

API Gateway:
- Requests: 50/mês
- Custo: ~$0.05/mês

Bedrock:
- Invocações: 50 × $0.015
- Custo: ~$0.75/mês

S3:
- Storage: 1MB
- Requests: 100/mês
- Custo: ~$0.01/mês

TOTAL: ~$1/mês
```

---

## 📊 Comparação: Amazon Q vs Lambda API

| Aspecto | Amazon Q + MCP | Lambda API |
|---------|----------------|------------|
| **Interface** | Terminal | REST API |
| **Setup** | Zero (já existe) | Precisa criar |
| **Custo** | $0 | ~$1/mês |
| **Complexidade** | Baixa | Média |
| **Acesso** | Terminal only | Qualquer lugar |
| **Web UI** | ❌ Não | ✅ Possível |
| **Slack bot** | ❌ Não | ✅ Possível |
| **Mobile** | ❌ Não | ✅ Possível |
| **Recomendado** | ✅ **SIM** | ⚠️ Só se precisar API |

---

## ⚠️ Quando Usar Lambda API

Use esta opção se você precisa de:

1. ✅ **Interface Web** - Dashboard para gerenciar infraestrutura
2. ✅ **Slack/Teams Bot** - Comandos via chat corporativo
3. ✅ **Mobile App** - Gerenciar infra do celular
4. ✅ **API Pública** - Permitir acesso externo
5. ✅ **Multi-usuário** - Vários usuários sem acesso ao terminal

**Caso contrário:** Use Amazon Q + MCP Server (mais simples)

---

## 🔧 Implementação

Se você decidir implementar esta opção:

### **Fase 1: Lambda Function (2 horas)**
- Criar função Lambda
- Implementar parse com Bedrock
- Implementar update YAML
- Implementar Git integration

### **Fase 2: API Gateway (1 hora)**
- Criar API Gateway
- Configurar rotas
- Configurar autenticação
- Configurar CORS

### **Fase 3: Integração (1 hora)**
- Conectar Lambda + API Gateway
- Testar endpoints
- Configurar monitoring
- Documentar API

**Total:** 4 horas

---

## 📚 Recursos Adicionais

- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)
- [Bedrock Runtime API](https://docs.aws.amazon.com/bedrock/latest/userguide/api-methods-run.html)
- [GitHub API Documentation](https://docs.github.com/en/rest)

---

## ✅ Conclusão

Esta é uma **opção válida** mas **não recomendada** para a maioria dos casos.

**Use Amazon Q + MCP Server** (Opção 1) a menos que você tenha um caso de uso específico que exija API REST.

**Benefício:** Documentado para referência futura se precisar escalar para interface web/mobile.
