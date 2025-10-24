#!/usr/bin/env python3
"""Setup Enhanced Observability for IaL"""

import boto3
import json
import sys
from pathlib import Path

# Import professional logging
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import get_logger

logger = get_logger(__name__)

def setup_container_insights():
    """Enable Container Insights for ECS cluster"""
    try:
        ecs = boto3.client('ecs')
        
        # Enable Container Insights for IaL cluster
        response = ecs.put_cluster_capacity_providers(
            cluster='ial-cluster',
            capacityProviders=['FARGATE', 'FARGATE_SPOT'],
            defaultCapacityProviderStrategy=[
                {
                    'capacityProvider': 'FARGATE',
                    'weight': 1,
                    'base': 0
                }
            ]
        )
        
        # Update cluster settings for Container Insights
        ecs.update_cluster_settings(
            cluster='ial-cluster',
            settings=[
                {
                    'name': 'containerInsights',
                    'value': 'enabled'
                }
            ]
        )
        
        logger.info("Container Insights enabled for ial-cluster")
        return True
        
    except Exception as e:
        logger.error(f"Failed to enable Container Insights: {e}")
        return False

def create_sns_subscription(topic_arn: str, email: str):
    """Create email subscription for SNS alerts"""
    try:
        sns = boto3.client('sns')
        
        response = sns.subscribe(
            TopicArn=topic_arn,
            Protocol='email',
            Endpoint=email
        )
        
        logger.info(f"SNS subscription created for {email}")
        print(f"📧 Check your email ({email}) to confirm the subscription")
        return response['SubscriptionArn']
        
    except Exception as e:
        logger.error(f"Failed to create SNS subscription: {e}")
        return None

def test_custom_metrics():
    """Test custom metrics functionality"""
    try:
        from utils.observability import put_custom_metric
        
        # Test metrics
        put_custom_metric("TestMetric", 1.0, "Count")
        put_custom_metric("TestPerformance", 150.5, "Milliseconds", 
                         namespace="IaL/Performance")
        
        logger.info("Test metrics sent successfully")
        print("✅ Test metrics sent to CloudWatch")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send test metrics: {e}")
        return False

def verify_x_ray_setup():
    """Verify X-Ray tracing setup"""
    try:
        xray = boto3.client('xray')
        
        # Get sampling rules
        response = xray.get_sampling_rules()
        
        ial_rules = [rule for rule in response['SamplingRuleRecords'] 
                    if 'ial' in rule['SamplingRule']['ServiceName'].lower()]
        
        if ial_rules:
            logger.info(f"Found {len(ial_rules)} X-Ray sampling rules for IaL")
            print(f"✅ X-Ray tracing configured with {len(ial_rules)} rules")
            return True
        else:
            logger.warning("No X-Ray sampling rules found for IaL")
            print("⚠️ X-Ray rules not found - deploy 00c-enhanced-observability.yaml first")
            return False
            
    except Exception as e:
        logger.error(f"Failed to verify X-Ray setup: {e}")
        return False

def main():
    """Setup enhanced observability"""
    
    logger.info("Setting up enhanced observability")
    print("🔧 Setting up Enhanced Observability for IaL...")
    
    success_count = 0
    total_checks = 4
    
    # 1. Setup Container Insights
    print("\n1. Setting up Container Insights...")
    if setup_container_insights():
        print("✅ Container Insights enabled")
        success_count += 1
    else:
        print("❌ Container Insights setup failed")
    
    # 2. Test custom metrics
    print("\n2. Testing custom metrics...")
    if test_custom_metrics():
        success_count += 1
    else:
        print("❌ Custom metrics test failed")
    
    # 3. Verify X-Ray setup
    print("\n3. Verifying X-Ray tracing...")
    if verify_x_ray_setup():
        success_count += 1
    else:
        print("❌ X-Ray verification failed")
    
    # 4. SNS subscription (optional)
    print("\n4. SNS Alert Subscription (optional)...")
    email = input("Enter email for alerts (or press Enter to skip): ").strip()
    
    if email:
        try:
            # Get SNS topic ARN from CloudFormation
            cf = boto3.client('cloudformation')
            response = cf.describe_stacks(StackName='ial-00c-enhanced-observability')
            
            topic_arn = None
            for output in response['Stacks'][0]['Outputs']:
                if output['OutputKey'] == 'AlertsTopicArn':
                    topic_arn = output['OutputValue']
                    break
            
            if topic_arn and create_sns_subscription(topic_arn, email):
                print("✅ SNS subscription created")
                success_count += 1
            else:
                print("❌ SNS subscription failed")
                
        except Exception as e:
            print(f"❌ SNS subscription failed: {e}")
    else:
        print("⏭️ SNS subscription skipped")
        success_count += 1  # Count as success since it's optional
    
    # Summary
    print(f"\n📊 Setup Summary: {success_count}/{total_checks} successful")
    
    if success_count == total_checks:
        print("🎉 Enhanced Observability setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Check CloudWatch Dashboard: IaL-Enhanced-Operations")
        print("2. Run a deployment to see metrics in action")
        print("3. Monitor alerts and adjust thresholds as needed")
        
        logger.info("Enhanced observability setup completed successfully")
        return True
    else:
        print("⚠️ Some components failed to setup. Check logs for details.")
        logger.warning(f"Enhanced observability setup partially failed: {success_count}/{total_checks}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
