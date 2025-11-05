import json
import boto3
import time
from typing import Dict, Any, List

# Import core components
import sys
import os
sys.path.append('/opt/python')  # Lambda layer path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.drift.drift_detector import DriftDetector
from core.drift.risk_classifier import RiskClassifier
from core.drift.auto_healer import AutoHealer
from core.drift.reverse_sync import ReverseSync
from core.decision_ledger import DecisionLedger
from core.drift_flag import DriftFlag, DriftState

def lambda_handler(event, context):
    """Main Lambda handler for drift detection and reconciliation"""
    
    start_time = time.time()
    
    try:
        # Initialize components
        drift_detector = DriftDetector()
        risk_classifier = RiskClassifier()
        auto_healer = AutoHealer()
        reverse_sync = ReverseSync()
        decision_ledger = DecisionLedger()
        drift_flag = DriftFlag()
        
        # Extract scope from event
        scope = event.get('scope', 'global')
        
        # Check drift control flag FIRST
        drift_state = drift_flag.get_drift_state(scope)
        
        print(f"Drift control state for {scope}: {drift_state.value}")
        
        if drift_state == DriftState.DISABLED:
            print(f"Drift detection DISABLED for {scope} - skipping completely")
            decision_ledger.log(
                phase="drift-reconciler",
                mcp="lambda",
                tool="drift_check",
                rationale=f"Drift detection disabled for {scope}",
                status="SKIPPED"
            )
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'status': 'skipped',
                    'reason': 'drift_disabled',
                    'scope': scope
                })
            }
        
        # Detect drift regardless of state (for visibility)
        print(f"Detecting drift for scope: {scope}")
        drift_findings = drift_detector.detect_drift(scope)
        
        if not drift_findings:
            print("No drift detected")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'status': 'no_drift',
                    'scope': scope,
                    'drift_state': drift_state.value
                })
            }
        
        print(f"Drift detected: {len(drift_findings)} findings")
        
        # Record findings in decision ledger
        decision_ledger.log(
            phase="drift-reconciler",
            mcp="lambda",
            tool="drift_detection",
            rationale=f"Detected {len(drift_findings)} drift findings for {scope}",
            status="DETECTED",
            metadata={
                'scope': scope,
                'findings_count': len(drift_findings),
                'drift_state': drift_state.value
            }
        )
        
        if drift_state == DriftState.PAUSED:
            print(f"Drift detection PAUSED for {scope} - detect only, no auto-reconcile")
            
            # Record findings but don't auto-reconcile
            for finding in drift_findings:
                decision_ledger.log(
                    phase="drift-reconciler",
                    mcp="lambda",
                    tool="drift_finding_paused",
                    rationale=f"Drift finding recorded (paused): {finding.get('resource_id')}",
                    status="PAUSED",
                    metadata=finding
                )
            
            # Generate reverse sync PR for manual review
            print("Generating reverse sync PR for manual review...")
            try:
                pr_result = reverse_sync.generate_pr_for_findings(drift_findings, scope)
                
                decision_ledger.log(
                    phase="drift-reconciler",
                    mcp="lambda",
                    tool="reverse_sync_pr",
                    rationale=f"Generated reverse sync PR for {scope} (drift paused)",
                    status="PR_CREATED",
                    metadata={
                        'pr_url': pr_result.get('pr_url'),
                        'findings_count': len(drift_findings)
                    }
                )
                
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'status': 'paused_pr_created',
                        'scope': scope,
                        'findings_count': len(drift_findings),
                        'pr_url': pr_result.get('pr_url'),
                        'drift_state': drift_state.value
                    })
                }
                
            except Exception as e:
                print(f"Failed to generate reverse sync PR: {e}")
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'status': 'paused_pr_failed',
                        'scope': scope,
                        'findings_count': len(drift_findings),
                        'error': str(e),
                        'drift_state': drift_state.value
                    })
                }
        
        # drift_state == DriftState.ENABLED - Normal auto-reconcile flow
        
        # Detect drift
        drift_items = drift_detector.detect_drift()
        
        if not drift_items:
            decision_ledger.log(
                phase="drift-detection",
                mcp="drift-reconciler",
                tool="detect_drift",
                rationale="No drift detected",
                status="NO_DRIFT"
            )
            
            publish_metrics(0, 0, 0)
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'status': 'no_drift',
                    'execution_time': time.time() - start_time
                })
            }
        
        # Process each drift item
        results = []
        safe_count = 0
        risky_count = 0
        critical_count = 0
        
        for drift_item in drift_items:
            # Classify risk
            risk_level = risk_classifier.classify_drift(drift_item)
            rationale = risk_classifier.get_rationale(drift_item, risk_level)
            
            drift_item['risk_level'] = risk_level
            drift_item['rationale'] = rationale
            
            # Take appropriate action
            if risk_level == 'safe':
                # Auto-heal safe drift
                heal_result = auto_healer.heal_drift(drift_item)
                drift_item['action'] = 'auto_healed'
                drift_item['heal_result'] = heal_result
                safe_count += 1
                
            elif risk_level in ['risky', 'critical']:
                # Create PR for risky/critical drift
                pr_result = reverse_sync.create_reverse_sync_pr(drift_item)
                drift_item['action'] = 'pr_created'
                drift_item['pr_result'] = pr_result
                
                if risk_level == 'risky':
                    risky_count += 1
                else:
                    critical_count += 1
            
            results.append(drift_item)
        
        # Log overall results
        decision_ledger.log(
            phase="drift-detection",
            mcp="drift-reconciler",
            tool="process_drift",
            rationale=f"Processed {len(drift_items)} drift items: {safe_count} safe, {risky_count} risky, {critical_count} critical",
            status="COMPLETED"
        )
        
        # Publish metrics
        publish_metrics(len(drift_items), safe_count, risky_count + critical_count)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'completed',
                'drift_items': len(drift_items),
                'safe_healed': safe_count,
                'prs_created': risky_count + critical_count,
                'execution_time': time.time() - start_time,
                'results': results
            })
        }
        
    except Exception as e:
        # Log error
        decision_ledger = DecisionLedger()
        decision_ledger.log(
            phase="drift-detection",
            mcp="drift-reconciler",
            tool="lambda_handler",
            rationale=f"Error in drift reconciliation: {str(e)}",
            status="ERROR"
        )
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'error': str(e),
                'execution_time': time.time() - start_time
            })
        }

def publish_metrics(total_drift: int, safe_healed: int, prs_created: int):
    """Publish drift metrics to CloudWatch"""
    
    try:
        cloudwatch = boto3.client('cloudwatch')
        
        metrics = [
            {
                'MetricName': 'Drift/Detected',
                'Value': total_drift,
                'Unit': 'Count'
            },
            {
                'MetricName': 'Drift/AutoHealed',
                'Value': safe_healed,
                'Unit': 'Count'
            },
            {
                'MetricName': 'Drift/PRsCreated',
                'Value': prs_created,
                'Unit': 'Count'
            }
        ]
        
        cloudwatch.put_metric_data(
            Namespace='IaL',
            MetricData=metrics
        )
        
    except Exception as e:
        print(f"Failed to publish metrics: {e}")

# For local testing
if __name__ == "__main__":
    test_event = {}
    test_context = type('Context', (), {'aws_request_id': 'test-request-id'})()
    
    result = lambda_handler(test_event, test_context)
    print(json.dumps(result, indent=2))
