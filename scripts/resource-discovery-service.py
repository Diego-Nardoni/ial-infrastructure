#!/usr/bin/env python3
"""Resource Discovery Service - Continuous Monitoring"""

import boto3
import json
import time
import schedule
from datetime import datetime
from auto_resource_tracker import discover_existing_resources, get_tracked_resources

def continuous_discovery():
    """Continuously discover and track new resources"""
    
    print(f"🔍 [{datetime.now()}] Running resource discovery...")
    
    try:
        # Discover untracked resources
        untracked = discover_existing_resources()
        
        if untracked:
            print(f"📝 Discovered and tracked {len(untracked)} new resources")
            
            # Send notification
            send_discovery_notification(untracked)
        else:
            print("✅ No new resources discovered")
    
    except Exception as e:
        print(f"❌ Discovery error: {e}")

def send_discovery_notification(resources):
    """Send notification about discovered resources"""
    
    try:
        sns = boto3.client('sns')
        topic_arn = f"arn:aws:sns:{boto3.Session().region_name}:{boto3.client('sts').get_caller_identity()['Account']}:ial-alerts-critical"
        
        message = f"""🔍 AUTO-DISCOVERY ALERT

Discovered {len(resources)} untracked resources:

"""
        
        for resource in resources[:10]:  # Limit to first 10
            message += f"- {resource['type']}: {resource['name']} (Phase: {resource['phase']})\n"
        
        if len(resources) > 10:
            message += f"... and {len(resources) - 10} more resources\n"
        
        message += f"""
All resources have been automatically:
✅ Registered in DynamoDB
✅ Added to appropriate phases
✅ Committed to Git

No action required - resources are now fully managed.
        """
        
        sns.publish(
            TopicArn=topic_arn,
            Subject=f"IaL Auto-Discovery: {len(resources)} Resources Found",
            Message=message.strip()
        )
        
        print("📧 Discovery notification sent")
        
    except Exception as e:
        print(f"⚠️ Could not send notification: {e}")

def run_discovery_service():
    """Run discovery service with scheduling"""
    
    print("🚀 Starting Resource Discovery Service...")
    
    # Schedule discovery every 30 minutes
    schedule.every(30).minutes.do(continuous_discovery)
    
    # Run initial discovery
    continuous_discovery()
    
    print("⏰ Scheduled discovery every 30 minutes")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n🛑 Discovery service stopped")

def run_one_time_discovery():
    """Run one-time discovery for immediate results"""
    
    print("🔍 Running one-time resource discovery...")
    continuous_discovery()
    print("✅ One-time discovery complete")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        run_one_time_discovery()
    else:
        run_discovery_service()
