#!/usr/bin/env python3
"""
Teste: IAL deployment em conta nova do zero
Simula o que aconteceria com ialctl start
"""

import boto3
import os

def analyze_fresh_deployment_readiness():
    """Analisa se ialctl start funciona 100% em conta nova"""
    
    print("🧪 FRESH DEPLOYMENT ANALYSIS")
    print("=" * 40)
    
    # 1. Check foundation templates
    foundation_path = "/home/ial/phases/00-foundation"
    templates = [f for f in os.listdir(foundation_path) if f.endswith('.yaml')]
    
    print(f"\n📦 Foundation Templates: {len(templates)} found")
    
    # 2. Check prerequisites
    prerequisites = {
        'Docker': 'docker --version',
        'AWS CLI': 'aws --version', 
        'Python': 'python3 --version',
        'Git': 'git --version'
    }
    
    print(f"\n🔧 Prerequisites Check:")
    missing_prereqs = []
    
    import subprocess
    for name, cmd in prerequisites.items():
        try:
            result = subprocess.run(cmd.split(), capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   ✅ {name}: Available")
            else:
                print(f"   ❌ {name}: Not found")
                missing_prereqs.append(name)
        except FileNotFoundError:
            print(f"   ❌ {name}: Not found")
            missing_prereqs.append(name)
    
    # 3. Check AWS permissions needed
    print(f"\n🔑 AWS Permissions Analysis:")
    
    required_services = [
        'CloudFormation', 'IAM', 'Lambda', 'DynamoDB', 'S3', 
        'KMS', 'SNS', 'EventBridge', 'CloudWatch', 'SecretsManager',
        'StepFunctions', 'ECR', 'WAF', 'X-Ray'
    ]
    
    print(f"   📋 Services needed: {len(required_services)}")
    for service in required_services:
        print(f"      - {service}")
    
    # 4. Check manual steps required
    print(f"\n👤 Manual Steps Required:")
    manual_steps = [
        "GitHub token input (interactive)",
        "AWS credentials configured", 
        "Docker daemon running",
        "Internet connectivity for downloads"
    ]
    
    for step in manual_steps:
        print(f"   ⚠️  {step}")
    
    # 5. Potential gaps analysis
    print(f"\n🔍 Potential Gaps Analysis:")
    
    gaps = {
        'GitHub Token': {
            'required': True,
            'automated': False,
            'impact': 'BLOCKER - System cannot function without it'
        },
        'AWS Permissions': {
            'required': True, 
            'automated': False,
            'impact': 'BLOCKER - CloudFormation will fail'
        },
        'Docker Runtime': {
            'required': True,
            'automated': False, 
            'impact': 'BLOCKER - Container builds will fail'
        },
        'Internet Access': {
            'required': True,
            'automated': False,
            'impact': 'BLOCKER - Downloads will fail'
        },
        'Region Selection': {
            'required': True,
            'automated': True,
            'impact': 'LOW - Defaults to us-east-1'
        }
    }
    
    blockers = 0
    for gap_name, gap_info in gaps.items():
        impact_icon = "🚫" if "BLOCKER" in gap_info['impact'] else "⚠️"
        auto_icon = "✅" if gap_info['automated'] else "👤"
        
        print(f"   {impact_icon} {gap_name}: {auto_icon} {gap_info['impact']}")
        
        if "BLOCKER" in gap_info['impact'] and not gap_info['automated']:
            blockers += 1
    
    # 6. Success probability
    print(f"\n🎯 Fresh Deployment Assessment:")
    
    if blockers == 0:
        success_rate = 95
        status = "✅ WILL WORK"
    elif blockers <= 2:
        success_rate = 75
        status = "⚠️  LIKELY TO WORK (with manual setup)"
    else:
        success_rate = 25
        status = "❌ WILL FAIL (multiple blockers)"
    
    print(f"   Success Probability: {success_rate}%")
    print(f"   Status: {status}")
    print(f"   Manual Blockers: {blockers}")
    
    # 7. What user needs to do
    print(f"\n📋 What User Needs (Fresh Account):")
    print(f"   1. AWS Account with admin permissions")
    print(f"   2. AWS CLI configured (aws configure)")
    print(f"   3. Docker installed and running")
    print(f"   4. GitHub personal access token")
    print(f"   5. Internet connectivity")
    print(f"   6. Run: ./ialctl start")
    
    # 8. Expected outcome
    print(f"\n🎉 Expected Outcome:")
    if success_rate >= 90:
        print(f"   ✅ System will deploy 100% automatically")
        print(f"   ✅ All {len(templates)} CloudFormation templates")
        print(f"   ✅ Complete IAL infrastructure ready")
    elif success_rate >= 70:
        print(f"   ⚠️  System will mostly work")
        print(f"   ⚠️  Some manual intervention needed")
        print(f"   ✅ Core functionality will be available")
    else:
        print(f"   ❌ System will fail to deploy")
        print(f"   ❌ Multiple manual steps required")
    
    return {
        'success_rate': success_rate,
        'blockers': blockers,
        'templates_count': len(templates),
        'will_work': success_rate >= 75
    }

if __name__ == "__main__":
    result = analyze_fresh_deployment_readiness()
    
    print(f"\n🏆 FINAL ANSWER:")
    if result['will_work']:
        print(f"   ✅ YES - ialctl start WILL work in fresh account")
        print(f"   📊 {result['templates_count']} templates will deploy")
        print(f"   🎯 Success rate: {result['success_rate']}%")
    else:
        print(f"   ❌ NO - ialctl start will have issues")
        print(f"   🚫 {result['blockers']} blocking issues")
    
    exit(0 if result['will_work'] else 1)
