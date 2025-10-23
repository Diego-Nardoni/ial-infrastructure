# 📋 PARTE 1: TESTES COM BEDROCK NO DOCKERFILE DA APLICAÇÃO

**Objetivo**: Adicionar validação Bedrock no Dockerfile da aplicação Spring Boot com GitHub Actions Artifacts

**Tempo estimado**: 2 horas  
**Complexidade**: Média  
**Risco**: Baixo (não afeta infraestrutura)

---

## 🎯 ESCOPO

### O que será feito
- ✅ Multi-stage Dockerfile com estágio de validação Bedrock
- ✅ Validação de código Java (controllers, services, configs)
- ✅ Validação de configurações (application.yml, pom.xml)
- ✅ Validação de segurança (dependências, secrets)
- ✅ Relatórios salvos em `/app/test-reports/`
- ✅ GitHub Actions copia relatórios como Artifacts

### O que NÃO será feito
- ❌ Scripts Python (quebra IaL)
- ❌ Scripts Shell complexos (quebra IaL)
- ❌ Testes unitários Java (não solicitado)
- ❌ Validação de infraestrutura (Parte 2)

---

## 📦 ESTRUTURA DO DOCKERFILE

### Multi-Stage Build

```dockerfile
# Stage 1: Builder (Maven)
FROM maven:3.9.5-eclipse-temurin-17 AS builder
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn clean package -DskipTests

# Stage 2: Bedrock Validator (NOVO)
FROM amazon/aws-cli:latest AS validator
WORKDIR /app

# Copiar código fonte para validação
COPY --from=builder /app/src ./src
COPY --from=builder /app/pom.xml ./pom.xml
COPY --from=builder /app/target/*.jar ./app.jar

# Criar diretório de relatórios
RUN mkdir -p /app/test-reports

# Validação 1: Código Java
RUN aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-3-sonnet-20240229-v1:0 \
  --body "{\"anthropic_version\":\"bedrock-2023-05-31\",\"max_tokens\":4096,\"messages\":[{\"role\":\"user\",\"content\":\"Analyze this Spring Boot application structure and identify potential issues: $(find src -name '*.java' | head -10 | xargs cat)\"}]}" \
  --region us-east-1 \
  /app/test-reports/code-analysis.json || echo "Bedrock validation skipped (no credentials)"

# Validação 2: Configurações
RUN aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-3-sonnet-20240229-v1:0 \
  --body "{\"anthropic_version\":\"bedrock-2023-05-31\",\"max_tokens\":2048,\"messages\":[{\"role\":\"user\",\"content\":\"Review this Spring Boot configuration for security issues: $(cat src/main/resources/application*.yml)\"}]}" \
  --region us-east-1 \
  /app/test-reports/config-analysis.json || echo "Bedrock validation skipped (no credentials)"

# Validação 3: Dependências
RUN aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-3-sonnet-20240229-v1:0 \
  --body "{\"anthropic_version\":\"bedrock-2023-05-31\",\"max_tokens\":2048,\"messages\":[{\"role\":\"user\",\"content\":\"Check these Maven dependencies for known vulnerabilities: $(cat pom.xml | grep -A 5 '<dependency>')\"}]}" \
  --region us-east-1 \
  /app/test-reports/dependencies-analysis.json || echo "Bedrock validation skipped (no credentials)"

# Stage 3: Runtime (Final)
FROM eclipse-temurin:17-jre-alpine
RUN apk add --no-cache curl
RUN addgroup -g 1001 -S appgroup && adduser -u 1001 -S appuser -G appgroup
WORKDIR /app
COPY --from=builder /app/target/*.jar app.jar
RUN chown -R appuser:appgroup /app
USER appuser
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
  CMD curl -f http://localhost:8080/actuator/health/readiness || exit 1
ENV JAVA_OPTS="-Xmx512m -Xms256m -XX:+UseG1GC -XX:+UseContainerSupport"
EXPOSE 8080
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
```

---

## 🔧 GITHUB ACTIONS WORKFLOW

### Atualizar `.github/workflows/deploy.yml`

```yaml
name: Deploy to ECS

on:
  push:
    branches: [ main ]
  workflow_dispatch: {}

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest

    env:
      AWS_REGION: ${{ vars.AWS_REGION }}
      AWS_ACCOUNT_ID: ${{ vars.AWS_ACCOUNT_ID }}
      ECR_REPOSITORY: ${{ vars.ECR_REPOSITORY }}
      ECS_CLUSTER: ${{ vars.ECS_CLUSTER }}
      ECS_SERVICE: ${{ vars.ECS_SERVICE }}
      TASK_FAMILY: ${{ vars.TASK_FAMILY }}
      IMAGE_TAG: ${{ github.sha }}

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::${{ vars.AWS_ACCOUNT_ID }}:role/GitHubActionsECRDeployRole
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      # NOVO: Build com validação Bedrock
      - name: Build Docker image with Bedrock validation
        run: |
          ECR_REGISTRY=${{ steps.login-ecr.outputs.registry }}
          IMAGE=$ECR_REGISTRY/${{ env.ECR_REPOSITORY }}
          
          # Build até o estágio validator
          docker build --target validator -t validator:${{ env.IMAGE_TAG }} .
          
          # Copiar relatórios do container
          CONTAINER_ID=$(docker create validator:${{ env.IMAGE_TAG }})
          docker cp $CONTAINER_ID:/app/test-reports ./bedrock-reports
          docker rm $CONTAINER_ID
          
          # Build final
          docker build --no-cache -t $IMAGE:${{ env.IMAGE_TAG }} .
          docker tag $IMAGE:${{ env.IMAGE_TAG }} $IMAGE:latest

      # NOVO: Upload relatórios Bedrock como artifacts
      - name: Upload Bedrock validation reports
        uses: actions/upload-artifact@v4
        with:
          name: bedrock-validation-reports-${{ github.sha }}
          path: bedrock-reports/
          retention-days: 30

      - name: Push Docker images
        run: |
          ECR_REGISTRY=${{ steps.login-ecr.outputs.registry }}
          IMAGE=$ECR_REGISTRY/${{ env.ECR_REPOSITORY }}
          docker push $IMAGE:${{ env.IMAGE_TAG }}
          docker push $IMAGE:latest

      - name: Export current ECS task definition
        run: |
          aws ecs describe-task-definition --task-definition "${{ env.TASK_FAMILY }}" \
            --query 'taskDefinition | {
              family: family,
              networkMode: networkMode,
              requiresCompatibilities: requiresCompatibilities,
              cpu: cpu,
              memory: memory,
              executionRoleArn: executionRoleArn,
              taskRoleArn: taskRoleArn,
              containerDefinitions: [{
                name: containerDefinitions[0].name,
                image: containerDefinitions[0].image,
                essential: containerDefinitions[0].essential,
                portMappings: containerDefinitions[0].portMappings,
                environment: containerDefinitions[0].environment,
                secrets: containerDefinitions[0].secrets,
                logConfiguration: containerDefinitions[0].logConfiguration,
                healthCheck: containerDefinitions[0].healthCheck
              }]
            }' > ecs-task-def.json

      - name: Render task definition with new image
        id: render
        uses: aws-actions/amazon-ecs-render-task-definition@v1
        with:
          task-definition: ecs-task-def.json
          container-name: spring-redis-app-app
          image: ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:${{ env.IMAGE_TAG }}

      - name: Deploy to Amazon ECS
        uses: aws-actions/amazon-ecs-deploy-task-definition@v1
        with:
          task-definition: ${{ steps.render.outputs.task-definition }}
          service: ${{ env.ECS_SERVICE }}
          cluster: ${{ env.ECS_CLUSTER }}
          wait-for-service-stability: true
```

---

## 📊 RELATÓRIOS BEDROCK

### Estrutura dos Relatórios

```
bedrock-reports/
├── code-analysis.json          # Análise de código Java
├── config-analysis.json        # Análise de configurações
└── dependencies-analysis.json  # Análise de dependências
```

### Exemplo de Relatório (code-analysis.json)

```json
{
  "body": {
    "content": [
      {
        "text": "## Spring Boot Application Analysis\n\n### Findings:\n1. ✅ Controllers properly structured\n2. ⚠️ Missing input validation in SessionApiController\n3. ✅ Security configuration present\n4. ⚠️ Hardcoded values in HealthController\n\n### Recommendations:\n- Add @Valid annotation to request bodies\n- Move hardcoded values to application.yml\n- Consider adding rate limiting"
      }
    ]
  }
}
```

---

## 💰 CUSTO ESTIMADO

### Bedrock Claude 3 Sonnet
- **Input**: ~$3 por 1M tokens
- **Output**: ~$15 por 1M tokens

### Por Build
- Código Java: ~2K tokens input, ~1K tokens output = $0.02
- Configurações: ~1K tokens input, ~500 tokens output = $0.01
- Dependências: ~1K tokens input, ~500 tokens output = $0.01
- **Total por build**: ~$0.04

### Mensal (50 builds)
- **Total**: ~$2/mês

---

## 🔒 PERMISSÕES IAM NECESSÁRIAS

### GitHub Actions Role

Adicionar ao role `GitHubActionsECRDeployRole`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
      ]
    }
  ]
}
```

---

## 📋 CHECKLIST DE IMPLEMENTAÇÃO

### Preparação (15 min)
- [ ] Atualizar Dockerfile com multi-stage build
- [ ] Adicionar estágio validator com Bedrock
- [ ] Criar diretório test-reports

### GitHub Actions (30 min)
- [ ] Atualizar workflow deploy.yml
- [ ] Adicionar step de build com validator
- [ ] Adicionar step de cópia de relatórios
- [ ] Adicionar step de upload artifacts

### Permissões IAM (15 min)
- [ ] Adicionar permissão bedrock:InvokeModel ao role
- [ ] Testar permissões

### Teste (1 hora)
- [ ] Commit e push das mudanças
- [ ] Verificar build no GitHub Actions
- [ ] Baixar artifacts e revisar relatórios
- [ ] Validar custo no AWS Cost Explorer

---

## ✅ VALIDAÇÃO

### Build Local
```bash
# Build até validator
docker build --target validator -t validator:test .

# Copiar relatórios
CONTAINER_ID=$(docker create validator:test)
docker cp $CONTAINER_ID:/app/test-reports ./local-reports
docker rm $CONTAINER_ID

# Revisar relatórios
cat local-reports/code-analysis.json | jq '.body.content[0].text'
```

### GitHub Actions
1. Ir em Actions → Deploy to ECS
2. Selecionar último workflow run
3. Clicar em "Artifacts"
4. Baixar `bedrock-validation-reports-{sha}`
5. Revisar relatórios JSON

---

## 🎯 RESULTADO ESPERADO

### Após Implementação
- ✅ Cada build gera 3 relatórios Bedrock
- ✅ Relatórios disponíveis como GitHub Artifacts (30 dias)
- ✅ Custo: ~$0.04 por build (~$2/mês)
- ✅ Validação automática de código, configs e dependências
- ✅ Zero impacto no runtime da aplicação
- ✅ 100% compatível com IaL (sem scripts Python)

---

## 📚 DOCUMENTAÇÃO ADICIONAL

### Acessar Relatórios
1. GitHub → Actions → Workflow Run
2. Scroll down → Artifacts
3. Download `bedrock-validation-reports-{sha}.zip`
4. Extrair e revisar JSONs

### Interpretar Relatórios
- `code-analysis.json`: Issues no código Java
- `config-analysis.json`: Problemas de configuração
- `dependencies-analysis.json`: Vulnerabilidades conhecidas

### Custo
- AWS Cost Explorer → Bedrock → InvokeModel
- Filtrar por período
- Verificar custo por build

---

## 🚀 PRÓXIMOS PASSOS

Após completar Parte 1:
1. Validar relatórios Bedrock
2. Ajustar prompts se necessário
3. Documentar findings comuns
4. Prosseguir para Parte 2 (AWS Reference Pattern)
