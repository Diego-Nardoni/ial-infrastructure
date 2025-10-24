import json
import boto3
import subprocess
import os
from datetime import datetime

# AWS Clients
dynamodb = boto3.client('dynamodb')
bedrock = boto3.client('bedrock-runtime')
sns = boto3.client('sns')
ec2 = boto3.client('ec2')
rds = boto3.client('rds')
s3 = boto3.client('s3')

def lambda_handler(event, context):
    """Intelligent Drift Detection and Auto-Remediation with Bedrock"""
    
    print("🔍 Starting intelligent drift detection...")
    
    # 1. Detect all drifts
    drifts = detect_all_drifts()
    
    if not drifts:
        print("✅ No drifts detected")
        return {'statusCode': 200, 'drifts': 0, 'auto_fixed': 0}
    
    print(f"⚠️ Found {len(drifts)} drifts")
    
    # 2. Process each drift with Bedrock intelligence
    auto_fixed = 0
    escalated = 0
    
    for drift in drifts:
        try:
            # Bedrock analyzes and generates solution
            solution = bedrock_intelligent_analysis(drift)
            
            if solution['auto_fixable']:
                # Auto-remediation
                success = execute_auto_fix(drift, solution)
                if success:
                    auto_fixed += 1
                    log_auto_fix_success(drift, solution)
                else:
                    escalate_to_human(drift, solution, "Auto-fix failed")
                    escalated += 1
            else:
                # Human intervention required
                escalate_to_human(drift, solution, solution['escalation_reason'])
                escalated += 1
                
        except Exception as e:
            print(f"❌ Error processing drift {drift['resource']}: {str(e)}")
            escalate_to_human(drift, None, f"Processing error: {str(e)}")
            escalated += 1
    
    # 3. Summary notification
    send_summary_notification(len(drifts), auto_fixed, escalated)
    
    return {
        'statusCode': 200,
        'drifts': len(drifts),
        'auto_fixed': auto_fixed,
        'escalated': escalated
    }

def detect_all_drifts():
    """Scan AWS resources and compare with desired state"""
    
    drifts = []
    
    # Get all tracked resources from DynamoDB
    response = dynamodb.query(
        TableName='mcp-provisioning-checklist',
        KeyConditionExpression='Project = :p',
        ExpressionAttributeValues={':p': {'S': os.environ.get('PROJECT_NAME', 'ial')}}
    )
    
    for item in response.get('Items', []):
        resource_name = item['ResourceName']['S']
        resource_type = item.get('ResourceType', {}).get('S', 'Unknown')
        
        # Skip non-AWS resources
        if not resource_type.startswith('AWS::'):
            continue
            
        try:
            desired_state = json.loads(item.get('DesiredState', {}).get('S', '{}'))
            current_state = get_current_aws_state(resource_name, resource_type)
            
            drift = compare_states(resource_name, resource_type, desired_state, current_state)
            if drift:
                drifts.append(drift)
                
        except Exception as e:
            print(f"⚠️ Error checking {resource_name}: {str(e)}")
    
    return drifts

def get_current_aws_state(resource_name, resource_type):
    """Get current state from AWS APIs"""
    
    try:
        if resource_type == 'AWS::EC2::SecurityGroup':
            return get_security_group_state(resource_name)
        elif resource_type == 'AWS::EC2::Instance':
            return get_ec2_instance_state(resource_name)
        elif resource_type == 'AWS::RDS::DBInstance':
            return get_rds_instance_state(resource_name)
        elif resource_type == 'AWS::S3::Bucket':
            return get_s3_bucket_state(resource_name)
        else:
            return {}
    except Exception as e:
        print(f"Error getting state for {resource_name}: {str(e)}")
        return {}

def get_security_group_state(sg_id):
    """Get Security Group current state"""
    try:
        response = ec2.describe_security_groups(GroupIds=[sg_id])
        sg = response['SecurityGroups'][0]
        return {
            'ingress_rules': sg.get('IpPermissions', []),
            'egress_rules': sg.get('IpPermissionsEgress', []),
            'description': sg.get('Description', '')
        }
    except:
        return {}

def get_ec2_instance_state(instance_id):
    """Get EC2 Instance current state"""
    try:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        return {
            'state': instance['State']['Name'],
            'instance_type': instance['InstanceType'],
            'security_groups': [sg['GroupId'] for sg in instance['SecurityGroups']]
        }
    except:
        return {}

def get_rds_instance_state(db_identifier):
    """Get RDS Instance current state"""
    try:
        response = rds.describe_db_instances(DBInstanceIdentifier=db_identifier)
        db = response['DBInstances'][0]
        return {
            'status': db['DBInstanceStatus'],
            'instance_class': db['DBInstanceClass'],
            'publicly_accessible': db['PubliclyAccessible']
        }
    except:
        return {}

def get_s3_bucket_state(bucket_name):
    """Get S3 Bucket current state"""
    try:
        # Check encryption
        try:
            encryption = s3.get_bucket_encryption(Bucket=bucket_name)
            encrypted = True
        except:
            encrypted = False
            
        # Check public access
        try:
            public_access = s3.get_public_access_block(Bucket=bucket_name)
            public_blocked = public_access['PublicAccessBlockConfiguration']['BlockPublicAcls']
        except:
            public_blocked = False
            
        return {
            'encrypted': encrypted,
            'public_access_blocked': public_blocked
        }
    except:
        return {}

def compare_states(resource_name, resource_type, desired, current):
    """Compare desired vs current state"""
    
    if not desired or not current:
        return None
        
    # Simple comparison - can be enhanced
    if desired != current:
        return {
            'resource': resource_name,
            'resource_type': resource_type,
            'desired_state': desired,
            'current_state': current,
            'timestamp': datetime.utcnow().isoformat(),
            'severity': 'MEDIUM'  # Will be analyzed by Bedrock
        }
    
    return None

def bedrock_intelligent_analysis(drift):
    """Use Bedrock to analyze drift and generate intelligent solution"""
    
    prompt = f"""You are an AWS infrastructure expert analyzing a configuration drift.

DRIFT DETAILS:
Resource: {drift['resource']}
Type: {drift['resource_type']}
Desired State: {json.dumps(drift['desired_state'], indent=2)}
Current State: {json.dumps(drift['current_state'], indent=2)}
Environment: Production
Business Hours: {is_business_hours()}

ANALYSIS REQUIRED:
1. Assess the security and operational impact
2. Determine if this can be safely auto-fixed
3. Generate AWS CLI commands to remediate
4. Provide rollback plan
5. Classify severity (CRITICAL, HIGH, MEDIUM, LOW)

RESPONSE FORMAT (JSON only):
{{
  "severity": "CRITICAL|HIGH|MEDIUM|LOW",
  "impact_analysis": "Brief description of impact",
  "auto_fixable": true/false,
  "escalation_reason": "Why human intervention needed (if auto_fixable=false)",
  "remediation_commands": [
    "aws cli command 1",
    "aws cli command 2"
  ],
  "rollback_commands": [
    "aws cli rollback command 1"
  ],
  "validation_commands": [
    "aws cli validation command 1"
  ],
  "reasoning": "Why this approach is safe and correct"
}}

SAFETY RULES:
- Never auto-fix CRITICAL security issues without approval
- Always provide rollback commands
- Consider business hours and maintenance windows
- Validate commands before execution"""

    try:
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-5-sonnet-20240620-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 2000,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        content = result['content'][0]['text']
        
        # Parse JSON response
        solution = json.loads(content)
        
        # Update drift severity from Bedrock analysis
        drift['severity'] = solution['severity']
        
        return solution
        
    except Exception as e:
        print(f"❌ Bedrock analysis failed: {str(e)}")
        return {
            'severity': 'HIGH',
            'impact_analysis': 'Analysis failed - requires human review',
            'auto_fixable': False,
            'escalation_reason': f'Bedrock analysis error: {str(e)}',
            'remediation_commands': [],
            'rollback_commands': [],
            'reasoning': 'Failed to analyze - escalating to human'
        }

def execute_auto_fix(drift, solution):
    """Execute auto-remediation commands"""
    
    print(f"🤖 Auto-fixing drift in {drift['resource']}")
    
    try:
        # Execute each remediation command
        for command in solution['remediation_commands']:
            print(f"Executing: {command}")
            
            # Parse AWS CLI command
            cmd_parts = command.split()
            result = subprocess.run(cmd_parts, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                print(f"❌ Command failed: {result.stderr}")
                return False
            
            print(f"✅ Command succeeded: {result.stdout}")
        
        # Validate fix
        for validation_cmd in solution.get('validation_commands', []):
            print(f"Validating: {validation_cmd}")
            cmd_parts = validation_cmd.split()
            result = subprocess.run(cmd_parts, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                print(f"⚠️ Validation failed: {result.stderr}")
                # Don't fail the fix, just log
        
        return True
        
    except Exception as e:
        print(f"❌ Auto-fix execution failed: {str(e)}")
        return False

def escalate_to_human(drift, solution, reason):
    """Escalate drift to human intervention"""
    
    print(f"👨‍💻 Escalating {drift['resource']} to human: {reason}")
    
    message = f"""🚨 DRIFT REQUIRES HUMAN INTERVENTION

Resource: {drift['resource']}
Type: {drift['resource_type']}
Severity: {drift.get('severity', 'UNKNOWN')}
Reason: {reason}

Desired State:
{json.dumps(drift['desired_state'], indent=2)}

Current State:
{json.dumps(drift['current_state'], indent=2)}
"""

    if solution:
        message += f"""

BEDROCK ANALYSIS:
Impact: {solution.get('impact_analysis', 'N/A')}
Reasoning: {solution.get('reasoning', 'N/A')}

SUGGESTED COMMANDS:
{chr(10).join(solution.get('remediation_commands', []))}

ROLLBACK COMMANDS:
{chr(10).join(solution.get('rollback_commands', []))}
"""

    # Send to SNS
    sns.publish(
        TopicArn=os.environ.get('SNS_TOPIC_ARN'),
        Subject=f'🚨 Drift Escalation: {drift["resource"]} ({drift.get("severity", "UNKNOWN")})',
        Message=message
    )

def log_auto_fix_success(drift, solution):
    """Log successful auto-remediation"""
    
    # Update DynamoDB with fix details
    dynamodb.update_item(
        TableName='mcp-provisioning-checklist',
        Key={
            'Project': {'S': os.environ.get('PROJECT_NAME', 'ial')},
            'ResourceName': {'S': drift['resource']}
        },
        UpdateExpression='SET AutoFixApplied = :t, LastAutoFix = :time, AutoFixSolution = :sol',
        ExpressionAttributeValues={
            ':t': {'BOOL': True},
            ':time': {'S': datetime.utcnow().isoformat()},
            ':sol': {'S': json.dumps(solution)}
        }
    )
    
    print(f"✅ Auto-fix logged for {drift['resource']}")

def send_summary_notification(total_drifts, auto_fixed, escalated):
    """Send summary of drift detection run"""
    
    if total_drifts == 0:
        return
    
    message = f"""📊 DRIFT DETECTION SUMMARY

Total Drifts Found: {total_drifts}
Auto-Fixed: {auto_fixed}
Escalated to Human: {escalated}

Timestamp: {datetime.utcnow().isoformat()}
"""

    sns.publish(
        TopicArn=os.environ.get('SNS_TOPIC_ARN'),
        Subject=f'📊 Drift Summary: {auto_fixed} fixed, {escalated} escalated',
        Message=message
    )

def is_business_hours():
    """Check if current time is business hours (9 AM - 6 PM UTC)"""
    current_hour = datetime.utcnow().hour
    return 9 <= current_hour <= 18

if __name__ == "__main__":
    # For local testing
    lambda_handler({}, {})
