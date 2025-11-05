#!/usr/bin/env python3
"""MCP Tool: Setup IaL Infrastructure"""
import subprocess
import json
import sys
import time
import re

def get_aws_account():
    """Detecta AWS Account ID"""
    result = subprocess.run(['aws', 'sts', 'get-caller-identity', '--query', 'Account', '--output', 'text'],
                          capture_output=True, text=True)
    return result.stdout.strip()

def get_aws_region():
    """Detecta AWS Region"""
    result = subprocess.run(['aws', 'configure', 'get', 'region'],
                          capture_output=True, text=True)
    return result.stdout.strip() or 'us-east-1'

def get_github_user():
    """Detecta GitHub User"""
    result = subprocess.run(['gh', 'api', 'user', '--jq', '.login'],
                          capture_output=True, text=True)
    return result.stdout.strip()

def get_github_repo():
    """Detecta ou solicita nome do repositório GitHub"""
    # Tentar detectar do git remote
    result = subprocess.run(
        ['git', 'remote', 'get-url', 'origin'],
        capture_output=True, text=True, cwd='/home/ial'
    )
    
    if result.returncode == 0:
        url = result.stdout.strip()
        # Parse: https://github.com/user/repo.git ou git@github.com:user/repo.git
        match = re.search(r'github\.com[:/](.+)/(.+?)(?:\.git)?$', url)
        if match:
            user = match.group(1)
            repo = match.group(2)
            print(f"✅ Repositório detectado: {user}/{repo}")
            return f"{user}/{repo}"
    
    # Se não detectou, solicitar
    print("\n📝 Configuração do GitHub Actions:")
    print("   Para que o GitHub Actions funcione, precisamos do nome do repositório.")
    print("   Formato: usuario/repositorio (ex: Diego-Nardoni/ial-infrastructure)")
    
    while True:
        repo_full = input("\n   Digite o nome completo do repositório: ").strip()
        if '/' in repo_full and len(repo_full.split('/')) == 2:
            return repo_full
        print("   ❌ Formato inválido. Use: usuario/repositorio")

def wait_for_table(table_name, region, max_wait=60):
    """Aguarda tabela DynamoDB ficar ativa"""
    print(f"⏳ Aguardando tabela {table_name} ficar ativa...")
    for i in range(max_wait):
        result = subprocess.run(
            f'aws dynamodb describe-table --table-name {table_name} --region {region} --query "Table.TableStatus" --output text',
            shell=True, capture_output=True, text=True
        )
        status = result.stdout.strip()
        if status == 'ACTIVE':
            print(f"✅ Tabela ativa!")
            return True
        time.sleep(2)
    return False

def create_oidc_provider(account_id, region):
    """Cria OIDC Provider para GitHub Actions"""
    # Verificar se já existe
    check = subprocess.run(
        'aws iam list-open-id-connect-providers --query "OpenIDConnectProviderList[?contains(Arn, \'token.actions.githubusercontent.com\')].Arn" --output text',
        shell=True, capture_output=True, text=True
    )
    
    if check.stdout.strip():
        print(f"✅ OIDC Provider já existe")
        return check.stdout.strip()
    
    print("📦 Criando OIDC Provider para GitHub Actions...")
    
    result = subprocess.run("""aws iam create-open-id-connect-provider \
        --url https://token.actions.githubusercontent.com \
        --client-id-list sts.amazonaws.com \
        --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
        --query 'OpenIDConnectProviderArn' \
        --output text""", shell=True, capture_output=True, text=True, check=True)
    
    return result.stdout.strip()

def create_github_actions_role(account_id, region, github_repo):
    """Cria IAM Role para GitHub Actions"""
    role_name = "IaL-GitHubActionsRole"
    
    # Verificar se já existe
    check = subprocess.run(
        f'aws iam get-role --role-name {role_name}',
        shell=True, capture_output=True, text=True
    )
    
    if check.returncode == 0:
        print(f"✅ IAM role {role_name} já existe")
        # Atualizar trust policy se repo foi fornecido
        if github_repo:
            print(f"📦 Atualizando trust policy para repo: {github_repo}")
            trust_policy = {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {
                        "Federated": f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"
                    },
                    "Action": "sts:AssumeRoleWithWebIdentity",
                    "Condition": {
                        "StringEquals": {
                            "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                        },
                        "StringLike": {
                            "token.actions.githubusercontent.com:sub": f"repo:{github_repo}:*"
                        }
                    }
                }]
            }
            subprocess.run(f"""aws iam update-assume-role-policy \
                --role-name {role_name} \
                --policy-document '{json.dumps(trust_policy)}'""",
                shell=True, check=True)
        return role_name
    
    print(f"📦 Criando IAM role {role_name}...")
    
    # Trust policy específico para o repo
    if github_repo:
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {
                    "Federated": f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"
                },
                "Action": "sts:AssumeRoleWithWebIdentity",
                "Condition": {
                    "StringEquals": {
                        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                    },
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": f"repo:{github_repo}:*"
                    }
                }
            }]
        }
    else:
        # Trust policy genérico (temporário)
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {
                    "Federated": f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"
                },
                "Action": "sts:AssumeRoleWithWebIdentity",
                "Condition": {
                    "StringEquals": {
                        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                    },
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": "repo:*:*"
                    }
                }
            }]
        }
    
    # Criar role
    subprocess.run(f"""aws iam create-role \
        --role-name {role_name} \
        --assume-role-policy-document '{json.dumps(trust_policy)}'""",
        shell=True, check=True)
    
    # Attach managed policies
    policies = [
        "arn:aws:iam::aws:policy/AmazonEC2FullAccess",
        "arn:aws:iam::aws:policy/AmazonECS_FullAccess", 
        "arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess",
        "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
        "arn:aws:iam::aws:policy/AmazonSNSFullAccess",
        "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
    ]
    
    for policy in policies:
        subprocess.run(f"""aws iam attach-role-policy \
            --role-name {role_name} \
            --policy-arn {policy}""",
            shell=True, check=True)
    
    print(f"⏳ Aguardando role propagar (10s)...")
    time.sleep(10)
    
    return role_name

def create_lambda_execution_role(account_id, region):
    """Cria IAM role para Lambda - MOVIDO PARA PHASE 16"""
    # Esta função foi movida para Phase 16 (drift-detection.yaml)
    # Lambda drift-detector será criado junto com a VPC
    print("⚠️  create_lambda_execution_role() foi movido para Phase 16")
    return None
    
    # Verificar se já existe
    check = subprocess.run(
        f'aws iam get-role --role-name {role_name}',
        shell=True, capture_output=True, text=True
    )
    
    if check.returncode == 0:
        print(f"✅ IAM role {role_name} já existe")
        return role_name
    
    print(f"📦 Criando IAM role {role_name}...")
    
    # Trust policy para Lambda
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    
    # Criar role
    subprocess.run(f"""aws iam create-role \
        --role-name {role_name} \
        --assume-role-policy-document '{json.dumps(trust_policy)}'""",
        shell=True, check=True)
    
    # Attach managed policies
    policies = [
        "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
        "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
        "arn:aws:iam::aws:policy/AmazonSNSFullAccess"
    ]
    
    for policy in policies:
        subprocess.run(f"""aws iam attach-role-policy \
            --role-name {role_name} \
            --policy-arn {policy}""",
            shell=True, check=True)
    
    # Criar inline policy para Bedrock
    bedrock_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": ["bedrock:InvokeModel"],
            "Resource": f"arn:aws:bedrock:{region}::foundation-model/*"
        }]
    }
    
    subprocess.run(f"""aws iam put-role-policy \
        --role-name {role_name} \
        --policy-name BedrockAccess \
        --policy-document '{json.dumps(bedrock_policy)}'""",
        shell=True, check=True)
    
    print(f"⏳ Aguardando role propagar (10s)...")
    time.sleep(10)
    
    return role_name

def create_dynamodb_table(account_id, region):
    """Cria DynamoDB table"""
    table_name = "mcp-provisioning-checklist"
    
    # Verificar se já existe
    check = subprocess.run(
        f'aws dynamodb describe-table --table-name {table_name} --region {region}',
        shell=True, capture_output=True, text=True
    )
    
    if check.returncode == 0:
        print(f"✅ Tabela {table_name} já existe")
        status = json.loads(check.stdout)['Table']['TableStatus']
        if status != 'ACTIVE':
            wait_for_table(table_name, region)
    else:
        print(f"📦 Criando tabela {table_name}...")
        subprocess.run(f"""aws dynamodb create-table \
            --table-name {table_name} \
            --attribute-definitions \
                AttributeName=Project,AttributeType=S \
                AttributeName=ResourceName,AttributeType=S \
            --key-schema \
                AttributeName=Project,KeyType=HASH \
                AttributeName=ResourceName,KeyType=RANGE \
            --billing-mode PAY_PER_REQUEST \
            --region {region}""", shell=True, check=True)
        
        wait_for_table(table_name, region)
    
    # Habilitar TTL
    print("📦 Habilitando TTL...")
    subprocess.run(f"""aws dynamodb update-time-to-live \
        --table-name {table_name} \
        --time-to-live-specification Enabled=true,AttributeName=TTL \
        --region {region}""", shell=True, capture_output=True)

def create_lambda_function(account_id, region, role_name):
    """Cria Lambda drift-detector - MOVIDO PARA PHASE 16"""
    # Esta função foi movida para Phase 16 (drift-detection.yaml)
    # Lambda será criado na VPC junto com a arquitetura
    print("⚠️  create_lambda_function() foi movido para Phase 16")
    return None
    
    # Verificar se já existe
    check = subprocess.run(
        f'aws lambda get-function --function-name {function_name} --region {region}',
        shell=True, capture_output=True, text=True
    )
    
    if check.returncode == 0:
        print(f"✅ Lambda {function_name} já existe")
        return
    
    print(f"📦 Criando Lambda {function_name}...")
    print("⚠️  NOTA: Lambda será criado FORA da VPC (VPC ainda não existe)")
    print("   Será migrado para VPC na Phase 03 automaticamente")
    
    # Criar zip
    subprocess.run("""cd /home/ial/lambda/drift-detector && \
        zip -q -r function.zip .""",
        shell=True, check=True)
    
    # Criar function
    subprocess.run(f"""aws lambda create-function \
        --function-name {function_name} \
        --runtime python3.11 \
        --handler index.lambda_handler \
        --zip-file fileb:///home/ial/lambda/drift-detector/function.zip \
        --role arn:aws:iam::{account_id}:role/{role_name} \
        --timeout 300 \
        --memory-size 512 \
        --region {region}""", shell=True, check=True)

def create_eventbridge_rule(account_id, region):
    """Cria EventBridge rule - MOVIDO PARA PHASE 16"""
    # Esta função foi movida para Phase 16 (drift-detection.yaml)
    # EventBridge será criado junto com Lambda na VPC
    print("⚠️  create_eventbridge_rule() foi movido para Phase 16")
    return None
    function_name = "drift-detector"
    
    # Verificar se já existe
    check = subprocess.run(
        f'aws events describe-rule --name {rule_name} --region {region}',
        shell=True, capture_output=True, text=True
    )
    
    if check.returncode == 0:
        print(f"✅ EventBridge rule {rule_name} já existe")
        return
    
    print(f"📦 Criando EventBridge rule {rule_name}...")
    
    # Criar rule
    subprocess.run(f"""aws events put-rule \
        --name {rule_name} \
        --schedule-expression "rate(1 hour)" \
        --region {region}""", shell=True, check=True)
    
    # Adicionar permissão Lambda
    subprocess.run(f"""aws lambda add-permission \
        --function-name {function_name} \
        --statement-id EventBridgeInvoke \
        --action lambda:InvokeFunction \
        --principal events.amazonaws.com \
        --source-arn arn:aws:events:{region}:{account_id}:rule/{rule_name} \
        --region {region}""", shell=True, capture_output=True)
    
    # Adicionar target
    subprocess.run(f"""aws events put-targets \
        --rule {rule_name} \
        --targets "Id"="1","Arn"="arn:aws:lambda:{region}:{account_id}:function:{function_name}" \
        --region {region}""", shell=True, check=True)

def create_kms_key_ial_data(account_id, region):
    """Cria CMK com alias/ial-data para criptografia padrão"""
    alias_name = "alias/ial-data"
    
    # Verificar se alias já existe
    check = subprocess.run(
        f'aws kms describe-key --key-id {alias_name} --region {region}',
        shell=True, capture_output=True, text=True
    )
    
    if check.returncode == 0:
        key_info = json.loads(check.stdout)
        key_id = key_info['KeyMetadata']['KeyId']
        print(f"✅ CMK {alias_name} já existe: {key_id}")
        return key_id
    
    print(f"🔐 Criando CMK {alias_name}...")
    
    # Criar KMS key
    key_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "Enable IAM User Permissions",
                "Effect": "Allow",
                "Principal": {"AWS": f"arn:aws:iam::{account_id}:root"},
                "Action": "kms:*",
                "Resource": "*"
            },
            {
                "Sid": "Allow use of the key for IAL services",
                "Effect": "Allow",
                "Principal": {"Service": ["s3.amazonaws.com", "dynamodb.amazonaws.com", "secretsmanager.amazonaws.com"]},
                "Action": [
                    "kms:Encrypt",
                    "kms:Decrypt",
                    "kms:ReEncrypt*",
                    "kms:GenerateDataKey*",
                    "kms:DescribeKey"
                ],
                "Resource": "*"
            }
        ]
    }
    
    # Criar key
    result = subprocess.run(f"""aws kms create-key \
        --description "IAL Data Encryption Key" \
        --key-usage ENCRYPT_DECRYPT \
        --key-spec SYMMETRIC_DEFAULT \
        --origin AWS_KMS \
        --policy '{json.dumps(key_policy)}' \
        --region {region} \
        --query 'KeyMetadata.KeyId' \
        --output text""", shell=True, capture_output=True, text=True, check=True)
    
    key_id = result.stdout.strip()
    
    # Criar alias
    subprocess.run(f"""aws kms create-alias \
        --alias-name {alias_name} \
        --target-key-id {key_id} \
        --region {region}""", shell=True, check=True)
    
    # Habilitar rotação automática
    subprocess.run(f"""aws kms enable-key-rotation \
        --key-id {key_id} \
        --region {region}""", shell=True, check=True)
    
    print(f"🔐 CMK criado: {key_id}")
    print(f"🔄 Rotação automática habilitada")
    
    return key_id

def create_sns_topic(account_id, region):
    """Cria SNS topic para notificações"""
    topic_name = "ial-alerts-critical"
    
    # Verificar se já existe
    check = subprocess.run(
        f'aws sns list-topics --region {region} --query "Topics[?contains(TopicArn, \'{topic_name}\')].TopicArn" --output text',
        shell=True, capture_output=True, text=True
    )
    
    if check.stdout.strip():
        print(f"✅ SNS topic {topic_name} já existe")
        return check.stdout.strip()
    
    print(f"📦 Criando SNS topic {topic_name}...")
    
    result = subprocess.run(f"""aws sns create-topic \
        --name {topic_name} \
        --region {region} \
        --query 'TopicArn' \
        --output text""", shell=True, capture_output=True, text=True, check=True)
    
    topic_arn = result.stdout.strip()
    print(f"📧 SNS Topic criado: {topic_arn}")
    
    return topic_arn

def setup_ial():
    """Setup completo do IaL"""
    print("🚀 Iniciando setup do IaL...\n")
    
    # Detectar contexto
    account_id = get_aws_account()
    region = get_aws_region()
    github_user = get_github_user() or None
    
    print(f"✅ AWS Account: {account_id}")
    print(f"✅ AWS Region: {region}")
    if github_user:
        print(f"✅ GitHub User: {github_user}")
    else:
        print(f"⚠️  GitHub User: não configurado (execute: gh auth login)")
    
    # Detectar ou solicitar repositório
    github_repo = get_github_repo() if github_user else None
    
    # Criar recursos
    try:
        # 1. OIDC Provider (para GitHub Actions)
        oidc_arn = create_oidc_provider(account_id, region)
        
        # 2. IAM Role para GitHub Actions (com repo específico)
        github_role = create_github_actions_role(account_id, region, github_repo)
        
        # 3. KMS Key para criptografia padrão
        kms_key_id = create_kms_key_ial_data(account_id, region)
        
        # 4. DynamoDB State Table
        create_dynamodb_table(account_id, region)
        
        # 5. SNS Topic (para alertas)
        topic_arn = create_sns_topic(account_id, region)
        
        print("\n" + "="*60)
        print("✅ Setup inicial completo!")
        print("="*60)
        print(f"\n🎯 Próximos passos:")
        print(f"1. Subscrever email no SNS:")
        print(f"   aws sns subscribe --topic-arn {topic_arn} \\")
        print(f"     --protocol email --notification-endpoint seu-email@example.com")
        print(f"2. Confirmar email (check inbox)")
        print(f"3. Habilitar Bedrock model access (console AWS)")
        print(f"4. Fazer primeiro deploy via GitHub Actions")
        if github_repo:
            print(f"\n🚀 GitHub Actions configurado para: {github_repo}")
            print(f"   Role ARN: arn:aws:iam::{account_id}:role/{github_role}")
            print(f"   ✅ Workflows funcionarão automaticamente!")
            print(f"\n📝 NOTA: Lambda drift-detector será criado na Phase 16")
            print(f"   (junto com a VPC - arquitetura mais consistente)")
        else:
            print(f"\n⚠️  Configure GitHub depois:")
            print(f"   1. gh auth login")
            print(f"   2. Execute setup novamente para atualizar trust policy")
        
        return {
            'status': 'success',
            'account_id': account_id,
            'region': region,
            'github_user': github_user,
            'github_repo': github_repo,
            'github_role': github_role,
            'oidc_arn': oidc_arn,
            'kms_key_id': kms_key_id,
            'topic_arn': topic_arn
        }
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        return {
            'status': 'error',
            'message': str(e),
            'account_id': account_id,
            'region': region
        }

if __name__ == '__main__':
    try:
        result = setup_ial()
        print(f"\n{json.dumps(result, indent=2)}")
        sys.exit(0 if result['status'] == 'success' else 1)
    except Exception as e:
        print(json.dumps({'status': 'error', 'message': str(e)}))
        sys.exit(1)
