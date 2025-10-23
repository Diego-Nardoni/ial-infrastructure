#!/usr/bin/env python3
"""MCP Tool: Setup IaL Infrastructure"""
import subprocess
import json
import sys
import time

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

def create_github_actions_role(account_id, region, github_user):
    """Cria IAM Role para GitHub Actions"""
    role_name = "IaL-GitHubActionsRole"
    
    # Verificar se já existe
    check = subprocess.run(
        f'aws iam get-role --role-name {role_name}',
        shell=True, capture_output=True, text=True
    )
    
    if check.returncode == 0:
        print(f"✅ IAM role {role_name} já existe")
        return role_name
    
    print(f"📦 Criando IAM role {role_name}...")
    
    # Trust policy para GitHub Actions
    if github_user and github_user != "not-configured":
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
                        "token.actions.githubusercontent.com:sub": f"repo:{github_user}/ial-infrastructure:*"
                    }
                }
            }]
        }
    else:
        # Trust policy genérico (aceita qualquer repo - usuário restringe depois)
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
        "arn:aws:iam::aws:policy/AmazonSNSFullAccess"
    ]
    
    for policy in policies:
        subprocess.run(f"""aws iam attach-role-policy \
            --role-name {role_name} \
            --policy-arn {policy}""",
            shell=True, check=True)
    
    # Inline policy para Bedrock
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

def create_lambda_execution_role(account_id, region):
    """Cria IAM role para Lambda"""
    role_name = "IaL-LambdaExecutionRole"
    
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
    """Cria Lambda drift-detector"""
    function_name = "drift-detector"
    
    # Verificar se já existe
    check = subprocess.run(
        f'aws lambda get-function --function-name {function_name} --region {region}',
        shell=True, capture_output=True, text=True
    )
    
    if check.returncode == 0:
        print(f"✅ Lambda {function_name} já existe")
        return
    
    print(f"📦 Criando Lambda {function_name}...")
    
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
    """Cria EventBridge rule"""
    rule_name = "drift-detection-scheduled"
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
    github_user = get_github_user() or "not-configured"
    
    print(f"✅ AWS Account: {account_id}")
    print(f"✅ AWS Region: {region}")
    print(f"✅ GitHub User: {github_user}\n")
    
    # Criar recursos
    try:
        # 1. OIDC Provider (para GitHub Actions)
        oidc_arn = create_oidc_provider(account_id, region)
        
        # 2. IAM Role para GitHub Actions
        github_role = create_github_actions_role(account_id, region, github_user)
        
        # 3. IAM Role para Lambda
        lambda_role = create_lambda_execution_role(account_id, region)
        
        # 4. DynamoDB
        create_dynamodb_table(account_id, region)
        
        # 5. SNS Topic
        topic_arn = create_sns_topic(account_id, region)
        
        # 6. Lambda
        create_lambda_function(account_id, region, lambda_role)
        
        # 7. EventBridge
        create_eventbridge_rule(account_id, region)
        
        print("\n" + "="*60)
        print("✅ Setup completo!")
        print("="*60)
        print(f"\n🎯 Próximos passos:")
        print(f"1. Subscrever email no SNS:")
        print(f"   aws sns subscribe --topic-arn {topic_arn} \\")
        print(f"     --protocol email --notification-endpoint seu-email@example.com")
        print(f"2. Confirmar email (check inbox)")
        print(f"3. Habilitar Bedrock model access (console AWS)")
        if github_user == "not-configured":
            print(f"4. Configurar GitHub: gh auth login")
            print(f"5. Atualizar trust policy do role {github_role} com seu repo")
        print(f"\n🚀 GitHub Actions configurado!")
        print(f"   Role ARN: arn:aws:iam::{account_id}:role/{github_role}")
        
        return {
            'status': 'success',
            'account_id': account_id,
            'region': region,
            'github_user': github_user,
            'lambda_role': lambda_role,
            'github_role': github_role,
            'oidc_arn': oidc_arn,
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
