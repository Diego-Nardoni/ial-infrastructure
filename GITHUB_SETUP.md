# Configuração GitHub Actions - IAL GitOps

## ✅ Permissões IAM Configuradas

O role `IaL-GitHubActionsRole` agora tem todas as permissões necessárias:

- ✅ CloudFormation Full Access (criar/atualizar stacks)
- ✅ S3 Full Access (state files e artifacts)
- ✅ IAM Limited (criar roles para recursos)
- ✅ CloudWatch Logs Full Access (logging)
- ✅ VPC Full Access (networking)
- ✅ EC2 Full Access (compute)
- ✅ ECS Full Access (containers)
- ✅ ELB Full Access (load balancers)
- ✅ DynamoDB Full Access (state management)
- ✅ SNS Full Access (notifications)

## 🔧 Configurar Secret no GitHub

### Passo 1: Acessar Settings
1. Vá para: https://github.com/diegonardoni/ial-infrastructure
2. Clique em **Settings** (aba superior)
3. No menu lateral esquerdo, clique em **Secrets and variables** → **Actions**

### Passo 2: Criar Secret
1. Clique em **New repository secret**
2. Preencha:
   - **Name:** `AWS_ROLE_ARN`
   - **Value:** `arn:aws:iam::221082174220:role/IaL-GitHubActionsRole`
3. Clique em **Add secret**

### Passo 3: Verificar
Execute workflow manualmente:
1. Vá em **Actions** → **Deploy Infrastructure**
2. Clique em **Run workflow**
3. Selecione branch `main`
4. Clique em **Run workflow**

Se aparecer erro de autenticação, verifique se o secret foi criado corretamente.

## 🚀 Fluxo GitOps Completo

### Teste 1: Criar S3 Bucket
```bash
# No servidor Ubuntu com IAL instalado
ialctl

IAL> crie um bucket S3 privado chamado ial-test-bucket
```

**O que acontece:**
1. ✅ IAL gera `phases/XX-s3-bucket.yaml`
2. ✅ Git commit + push para branch `feature/s3-bucket`
3. ✅ GitHub Actions autentica via OIDC
4. ✅ Workflow valida CloudFormation template
5. ✅ Abre Pull Request automaticamente
6. ✅ Você aprova e faz merge
7. ✅ Workflow executa `aws cloudformation create-stack`
8. ✅ Bucket criado na AWS!

### Teste 2: Criar EKS Cluster
```bash
IAL> crie um cluster EKS chamado ial-production
```

**Agora funciona porque tem:**
- ✅ CloudFormation (criar stack)
- ✅ IAM (criar role do EKS)
- ✅ VPC (criar subnets)
- ✅ EC2 (criar node groups)

## 📋 Checklist Final

- [x] OIDC Provider criado
- [x] IAM Role `IaL-GitHubActionsRole` criado
- [x] Trust Policy configurado para `diegonardoni/ial-infrastructure`
- [x] 10 permissões AWS anexadas ao role
- [ ] **Secret `AWS_ROLE_ARN` configurado no GitHub** ← VOCÊ PRECISA FAZER
- [x] Workflows existem em `.github/workflows/`

## 🎯 Próximos Passos

1. Configure o secret `AWS_ROLE_ARN` no GitHub (instruções acima)
2. Teste criando um recurso simples: `ialctl` → "crie um bucket S3"
3. Verifique o PR aberto automaticamente
4. Aprove e faça merge
5. Veja o recurso sendo criado via GitHub Actions

## 🔍 Troubleshooting

**Erro: "role-to-assume not found"**
- Secret `AWS_ROLE_ARN` não foi configurado no GitHub

**Erro: "not authorized to perform cloudformation:CreateStack"**
- Permissões foram adicionadas agora, deve funcionar

**Erro: "trust policy violation"**
- Verifique se o repositório é `diegonardoni/ial-infrastructure`
- Trust policy está configurado para esse repo específico

## 📞 Suporte

Se encontrar problemas:
1. Verifique logs em: Actions → Deploy Infrastructure → Último run
2. Verifique CloudTrail para erros de permissão
3. Confirme que o secret está configurado corretamente
