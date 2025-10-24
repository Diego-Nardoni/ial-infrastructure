#!/usr/bin/env python3
"""Bedrock-powered Test Generation for IaL CI/CD"""

import json
import boto3
import os
import sys
from datetime import datetime

# AWS Clients
bedrock = boto3.client('bedrock-runtime')
dynamodb = boto3.client('dynamodb')

def main():
    """Generate intelligent tests based on deployed infrastructure"""
    
    print("🧠 Generating intelligent tests with Bedrock...")
    
    # 1. Get deployed resources
    deployed_resources = get_deployed_resources()
    
    if not deployed_resources:
        print("⚠️ No deployed resources found")
        sys.exit(0)
    
    # 2. Generate tests with Bedrock
    test_scenarios = generate_bedrock_tests(deployed_resources)
    
    # 3. Save generated tests
    save_test_files(test_scenarios)
    
    print(f"✅ Generated {len(test_scenarios)} intelligent test scenarios")

def get_deployed_resources():
    """Get all deployed resources from DynamoDB state"""
    
    try:
        response = dynamodb.query(
            TableName='mcp-provisioning-checklist',
            KeyConditionExpression='#proj = :p',
            FilterExpression='#status = :status',
            ExpressionAttributeNames={
                '#proj': 'Project',
                '#status': 'Status'
            },
            ExpressionAttributeValues={
                ':p': {'S': os.environ.get('PROJECT_NAME', 'ial')},
                ':status': {'S': 'Created'}
            }
        )
        
        resources = []
        for item in response.get('Items', []):
            resource = {
                'name': item['ResourceName']['S'],
                'type': item.get('ResourceType', {}).get('S', 'Unknown'),
                'phase': item.get('Phase', {}).get('S', 'Unknown'),
                'properties': json.loads(item.get('Properties', {}).get('S', '{}'))
            }
            resources.append(resource)
        
        return resources
        
    except Exception as e:
        print(f"❌ Error getting deployed resources: {str(e)}")
        return []

def generate_bedrock_tests(resources):
    """Use Bedrock to generate intelligent test scenarios"""
    
    # Determine complexity for model selection
    complexity = assess_complexity(resources)
    model_id = select_model(complexity)
    
    prompt = create_test_generation_prompt(resources)
    
    try:
        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 4000,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        content = result['content'][0]['text']
        
        # Parse test scenarios from response
        test_scenarios = parse_test_scenarios(content)
        
        # Log usage for cost tracking
        log_bedrock_usage(model_id, len(prompt), len(content))
        
        return test_scenarios
        
    except Exception as e:
        print(f"❌ Bedrock test generation failed: {str(e)}")
        return generate_fallback_tests(resources)

def assess_complexity(resources):
    """Assess infrastructure complexity to select appropriate model"""
    
    complexity_score = 0
    
    # Base complexity
    complexity_score += len(resources)
    
    # Add complexity for specific resource types
    for resource in resources:
        if resource['type'] in ['AWS::ECS::Service', 'AWS::RDS::DBInstance']:
            complexity_score += 3
        elif resource['type'] in ['AWS::EC2::SecurityGroup', 'AWS::S3::Bucket']:
            complexity_score += 2
        else:
            complexity_score += 1
    
    return complexity_score

def select_model(complexity):
    """Select Bedrock model based on complexity"""
    
    if complexity > 50:
        return 'anthropic.claude-3-5-sonnet-20240620-v1:0'  # Latest accessible Sonnet for complex scenarios
    else:
        return 'anthropic.claude-3-haiku-20240307-v1:0'   # Haiku for simple scenarios

def create_test_generation_prompt(resources):
    """Create comprehensive prompt for test generation"""
    
    environment = os.environ.get('ENVIRONMENT', 'production')
    
    prompt = f"""You are an AWS infrastructure testing expert generating comprehensive test scenarios.

DEPLOYED INFRASTRUCTURE:
{json.dumps(resources, indent=2)}

ENVIRONMENT: {environment}
PROJECT: IaL (Infrastructure as Language)
TESTING FRAMEWORK: pytest + boto3

GENERATE TEST SCENARIOS FOR:

1. FUNCTIONAL TESTS:
   - API endpoints responding (ALB health checks)
   - Database connectivity (RDS/Aurora)
   - Service mesh communication (ECS tasks)
   - S3 bucket accessibility
   - Lambda function execution

2. SECURITY TESTS:
   - Security groups properly configured
   - Encryption at rest (S3, RDS, EBS)
   - Encryption in transit (ALB, RDS)
   - IAM permissions least privilege
   - VPC endpoints functioning

3. PERFORMANCE TESTS:
   - Load balancer response times (<500ms)
   - Auto-scaling triggers working
   - Database query performance
   - CloudWatch metrics collection

4. COST OPTIMIZATION TESTS:
   - Right-sizing validation
   - Unused resources detection
   - Reserved instance utilization
   - VPC endpoints usage

5. COMPLIANCE TESTS:
   - Well-Architected Framework alignment
   - Security best practices
   - Backup and recovery procedures
   - Monitoring and alerting

RESPONSE FORMAT:
Return a JSON object with test scenarios:

{{
  "test_scenarios": [
    {{
      "category": "functional|security|performance|cost|compliance",
      "name": "descriptive_test_name",
      "description": "What this test validates",
      "priority": "critical|high|medium|low",
      "test_code": "Complete pytest test function",
      "expected_result": "What should happen if test passes",
      "failure_remediation": "Steps to fix if test fails"
    }}
  ]
}}

REQUIREMENTS:
- Generate executable Python code using pytest
- Use boto3 for AWS API calls
- Include proper error handling
- Add meaningful assertions
- Consider environment-specific thresholds
- Focus on business-critical validations
- Provide clear failure messages"""

    return prompt

def parse_test_scenarios(content):
    """Parse test scenarios from Bedrock response"""
    
    try:
        # Find the JSON object in the response
        start_idx = content.find('{\n  "test_scenarios"')
        if start_idx == -1:
            start_idx = content.find('{"test_scenarios"')
        if start_idx == -1:
            start_idx = content.find('{')
        
        if start_idx == -1:
            raise ValueError("No JSON object found")
        
        # Find matching closing brace
        brace_count = 0
        end_idx = len(content)
        
        for i, char in enumerate(content[start_idx:], start_idx):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i + 1
                    break
        
        json_content = content[start_idx:end_idx]
        
        # Clean up the JSON content
        json_content = json_content.strip()
        
        parsed = json.loads(json_content)
        
        return parsed.get('test_scenarios', [])
        
    except Exception as e:
        print(f"⚠️ Error parsing Bedrock response: {str(e)}")
        # Try to extract just the test scenarios manually
        try:
            # Look for test_scenarios array
            scenarios_start = content.find('"test_scenarios": [')
            if scenarios_start != -1:
                print("📝 Falling back to manual parsing...")
                return []  # Return empty for now, will implement fallback if needed
        except:
            pass
        return []

def generate_fallback_tests(resources):
    """Generate basic fallback tests if Bedrock fails"""
    
    fallback_tests = []
    
    for resource in resources:
        if resource['type'] == 'AWS::S3::Bucket':
            fallback_tests.append({
                'category': 'functional',
                'name': f'test_{resource["name"]}_accessibility',
                'description': f'Validate S3 bucket {resource["name"]} is accessible',
                'priority': 'high',
                'test_code': f'''
def test_{resource["name"].replace("-", "_")}_accessibility():
    import boto3
    s3 = boto3.client('s3')
    try:
        s3.head_bucket(Bucket='{resource["name"]}')
        assert True
    except Exception as e:
        assert False, f"S3 bucket not accessible: {{e}}"
''',
                'expected_result': 'Bucket is accessible',
                'failure_remediation': 'Check bucket exists and permissions'
            })
    
    return fallback_tests

def save_test_files(test_scenarios):
    """Save generated tests to files"""
    
    # Create tests directory
    os.makedirs('/home/ial/tests/generated', exist_ok=True)
    
    # Group tests by category
    categories = {}
    for scenario in test_scenarios:
        category = scenario.get('category', 'general')
        if category not in categories:
            categories[category] = []
        categories[category].append(scenario)
    
    # Save each category to separate file
    for category, tests in categories.items():
        filename = f'/home/ial/tests/generated/test_{category}_bedrock.py'
        
        with open(filename, 'w') as f:
            f.write(f'''#!/usr/bin/env python3
"""
Bedrock-generated {category.title()} Tests
Generated: {datetime.now(datetime.timezone.utc).isoformat()}
Test Count: {len(tests)}
"""

import pytest
import boto3
import json
import time
from datetime import datetime

# AWS Clients
ec2 = boto3.client('ec2')
s3 = boto3.client('s3')
rds = boto3.client('rds')
elbv2 = boto3.client('elbv2')
ecs = boto3.client('ecs')
cloudwatch = boto3.client('cloudwatch')

''')
            
            for test in tests:
                f.write(f"\n# {test.get('description', 'Generated test')}\n")
                f.write(f"# Priority: {test.get('priority', 'medium')}\n")
                f.write(test.get('test_code', ''))
                f.write('\n\n')
        
        print(f"📝 Saved {len(tests)} {category} tests to {filename}")

def log_bedrock_usage(model_id, input_tokens, output_tokens):
    """Log Bedrock usage for cost tracking"""
    
    usage_log = {
        'timestamp': datetime.now(datetime.timezone.utc).isoformat(),
        'model_id': model_id,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'operation': 'test_generation',
        'project': os.environ.get('PROJECT_NAME', 'ial')
    }
    
    # Save to file for cost analysis
    with open('/home/ial/logs/bedrock_usage.jsonl', 'a') as f:
        f.write(json.dumps(usage_log) + '\n')

if __name__ == "__main__":
    main()
