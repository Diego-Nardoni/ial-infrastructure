#!/usr/bin/env python3
"""
IAL Destroy Commands - Remove specific resources
"""

import boto3
import sys
import argparse
from botocore.exceptions import ClientError

class SecurityServicesDestroyer:
    def __init__(self):
        self.cloudformation = boto3.client('cloudformation')
        self.guardduty = boto3.client('guardduty')
        self.securityhub = boto3.client('securityhub')
        
    def destroy_security_services(self, confirm: bool = False):
        """Destroy security services to stop billing"""
        
        if not confirm:
            print("⚠️  WARNING: This will remove ALL security services")
            print("   💰 Will stop ~$24/month billing")
            print("   🔒 Services to remove:")
            print("      - GuardDuty Detector")
            print("      - Security Hub")
            print("      - Inspector Assessments")
            print("      - Access Analyzer")
            print("      - Macie (if configured)")
            print("")
            print("   📊 Historical security data will be lost")
            print("   🚨 Your AWS account will have reduced security monitoring")
            print("")
            
            confirm_input = input("Type 'DELETE' to confirm removal: ")
            if confirm_input != 'DELETE':
                print("❌ Cancelled - Security services preserved")
                return False
        
        print("🔄 Removing security services...")
        
        # 1. Remove CloudFormation stack if exists
        try:
            stack_name = "ial-50-security-services"
            print(f"   📦 Removing CloudFormation stack: {stack_name}")
            
            self.cloudformation.delete_stack(StackName=stack_name)
            print(f"   ✅ Stack deletion initiated")
            
        except ClientError as e:
            if 'does not exist' in str(e):
                print(f"   ⏭️  Stack {stack_name} not found")
            else:
                print(f"   ⚠️  Error removing stack: {e}")
        
        # 2. Disable GuardDuty manually (if stack deletion fails)
        try:
            detectors = self.guardduty.list_detectors()
            for detector_id in detectors.get('DetectorIds', []):
                print(f"   🔒 Disabling GuardDuty detector: {detector_id}")
                self.guardduty.delete_detector(DetectorId=detector_id)
                print(f"   ✅ GuardDuty disabled")
                
        except ClientError as e:
            print(f"   ⚠️  GuardDuty cleanup: {e}")
        
        # 3. Disable Security Hub manually (if stack deletion fails)
        try:
            print(f"   🛡️  Disabling Security Hub")
            self.securityhub.disable_security_hub()
            print(f"   ✅ Security Hub disabled")
            
        except ClientError as e:
            if 'not subscribed' in str(e).lower():
                print(f"   ⏭️  Security Hub not enabled")
            else:
                print(f"   ⚠️  Security Hub cleanup: {e}")
        
        print("")
        print("✅ Security services removal completed")
        print("💰 Billing for security services should stop within 24 hours")
        print("🔒 To re-enable: ialctl config set SECURITY_SERVICES_ENABLED=true")
        
        return True

def handle_destroy_command(args):
    """Handle ialctl destroy commands"""
    
    if args.resource == 'security-services':
        destroyer = SecurityServicesDestroyer()
        destroyer.destroy_security_services(confirm=args.force)
    else:
        print(f"❌ Unknown resource: {args.resource}")
        print("Available resources: security-services")

def main():
    parser = argparse.ArgumentParser(description='IAL Resource Destroyer')
    parser.add_argument('resource', help='Resource to destroy (security-services)')
    parser.add_argument('--force', action='store_true', help='Skip confirmation')
    
    args = parser.parse_args()
    handle_destroy_command(args)

if __name__ == '__main__':
    main()
