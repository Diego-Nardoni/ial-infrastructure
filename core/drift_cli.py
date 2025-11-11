#!/usr/bin/env python3
import sys
import json
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.drift.drift_detector import DriftDetector
from core.drift.risk_classifier import RiskClassifier
from core.drift.auto_healer import AutoHealer
from core.drift.reverse_sync import ReverseSync

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 drift_cli.py <command> [args]")
        print("Commands:")
        print("  detect - Detect drift between Git and AWS")
        print("  classify <drift_item_json> - Classify drift risk")
        print("  heal <drift_item_json> - Auto-heal safe drift")
        print("  sync <drift_item_json> - Create reverse sync PR")
        print("  simulate - Simulate drift detection")
        return
    
    command = sys.argv[1]
    
    if command == "detect":
        print("🔍 Detecting drift between Git and AWS...")
        
        detector = DriftDetector()
        drift_items = detector.detect_drift()
        
        if not drift_items:
            #print("✅ No drift detected - infrastructure is in sync")
        else:
            print(f"⚠️ Found {len(drift_items)} drift items:")
            for i, item in enumerate(drift_items, 1):
                print(f"  {i}. {item['resource_id']} - {item['drift_type']} ({item['severity']})")
        
        # Save results for other commands
        with open('/tmp/drift_results.json', 'w') as f:
            json.dump(drift_items, f, indent=2)
        
    elif command == "classify":
        if len(sys.argv) < 3:
            print("Usage: python3 drift_cli.py classify <drift_item_json>")
            return
        
        drift_item = json.loads(sys.argv[2])
        classifier = RiskClassifier()
        
        risk_level = classifier.classify_drift(drift_item)
        rationale = classifier.get_rationale(drift_item, risk_level)
        
        print(f"🎯 Risk Classification: {risk_level.upper()}")
        print(f"📝 Rationale: {rationale}")
        
    elif command == "heal":
        if len(sys.argv) < 3:
            print("Usage: python3 drift_cli.py heal <drift_item_json>")
            return
        
        drift_item = json.loads(sys.argv[2])
        healer = AutoHealer()
        
        print(f"🔧 Attempting to heal drift for {drift_item.get('resource_id')}...")
        result = healer.heal_drift(drift_item)
        
        print(f"📊 Heal Result: {json.dumps(result, indent=2)}")
        
    elif command == "sync":
        if len(sys.argv) < 3:
            print("Usage: python3 drift_cli.py sync <drift_item_json>")
            return
        
        drift_item = json.loads(sys.argv[2])
        reverse_sync = ReverseSync()
        
        print(f"🔄 Creating reverse sync PR for {drift_item.get('resource_id')}...")
        result = reverse_sync.create_reverse_sync_pr(drift_item)
        
        print(f"📊 Sync Result: {json.dumps(result, indent=2)}")
        
    elif command == "simulate":
        print("🧪 Simulating drift detection...")
        
        # Create sample drift items for testing
        sample_drift = [
            {
                "resource_id": "ial-security-stack::SecurityGroup",
                "drift_type": "configuration_drift",
                "desired": {"tags": {"Environment": "prod"}},
                "current": {"tags": {"Environment": "dev"}},
                "differences": [
                    {
                        "property": "tags.Environment",
                        "desired": "prod",
                        "current": "dev",
                        "type": "tag_drift"
                    }
                ],
                "severity": "low"
            },
            {
                "resource_id": "manual-ec2-instance",
                "drift_type": "extra_resource",
                "desired": None,
                "current": {
                    "type": "AWS::EC2::Instance",
                    "properties": {"InstanceType": "t3.micro"}
                },
                "severity": "medium"
            }
        ]
        
        classifier = RiskClassifier()
        
        for drift_item in sample_drift:
            resource_id = drift_item['resource_id']
            risk_level = classifier.classify_drift(drift_item)
            rationale = classifier.get_rationale(drift_item, risk_level)
            
            print(f"\n📋 Resource: {resource_id}")
            print(f"🎯 Risk: {risk_level.upper()}")
            print(f"📝 Action: {'Auto-heal' if risk_level == 'safe' else 'Create PR'}")
            print(f"💭 Rationale: {rationale}")
        
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
