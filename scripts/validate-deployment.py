#!/usr/bin/env python3
"""Deployment Validation - Ensure All Resources Are Created"""

import boto3
import yaml
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Import CloudFormation YAML loader
sys.path.append(str(Path(__file__).parent))
from cf_yaml_loader import load_cf_yaml

# Get project root directory dynamically
PROJECT_ROOT = Path(__file__).parent.parent
PHASES_DIR = PROJECT_ROOT / 'phases'
REPORTS_DIR = PROJECT_ROOT / 'reports'
VALIDATION_DIR = PROJECT_ROOT / 'validation'

dynamodb = boto3.client('dynamodb')

def main():
    """Validate complete deployment"""
    
    print("🔍 Validating deployment completeness...")
    
    # 1. Count expected resources from phases
    expected_resources = count_expected_resources()
    
    # 2. Count created resources in DynamoDB
    created_resources = count_created_resources()
    
    # 3. Validate completeness
    validation_result = validate_completeness(expected_resources, created_resources)
    
    # 4. Generate report
    generate_validation_report(validation_result)
    
    # 5. Exit with appropriate code
    if validation_result['status'] == 'COMPLETE':
        print("✅ Deployment validation PASSED")
        sys.exit(0)
    else:
        print("❌ Deployment validation FAILED")
        sys.exit(1)

def count_expected_resources():
    """Count all resources defined in phases"""
    
    phases_dir = PHASES_DIR
    total_resources = 0
    phase_details = {}
    
    for phase_file in phases_dir.glob('*.yaml'):
        try:
            phase_data = load_cf_yaml(phase_file)
            if phase_data is None:
                continue
            
            phase_name = phase_file.stem
            
            # Count from explicit resource_count
            explicit_count = phase_data.get('resource_count', 0)
            
            # Count from Resources section
            resources_section = phase_data.get('Resources', {})
            resources_count = len(resources_section) if resources_section else 0
            
            # Count from DynamoDB items (for phases that create DynamoDB entries)
            dynamodb_items = count_dynamodb_items_in_phase(phase_data)
            
            # Use the highest count (most accurate)
            phase_count = max(explicit_count, resources_count, dynamodb_items)
            
            if phase_count > 0:
                total_resources += phase_count
                phase_details[phase_name] = {
                    'expected_count': phase_count,
                    'explicit_count': explicit_count,
                    'resources_section': resources_count,
                    'dynamodb_items': dynamodb_items
                }
                
        except Exception as e:
            print(f"⚠️ Error processing {phase_file}: {e}")
            phase_details[phase_name] = {'error': str(e)}
    
    return {
        'total': total_resources,
        'phases': phase_details
    }

def count_dynamodb_items_in_phase(phase_data):
    """Count DynamoDB items that would be created by this phase"""
    
    count = 0
    
    # Look for DynamoDB put_item operations
    if 'Resources' in phase_data:
        for resource_name, resource_config in phase_data['Resources'].items():
            if isinstance(resource_config, dict):
                # Check for DynamoDB item creation patterns
                if 'Properties' in resource_config:
                    props = resource_config['Properties']
                    if isinstance(props, dict) and 'Item' in props:
                        count += 1
                # Check for explicit resource type
                if resource_config.get('Type', '').startswith('AWS::'):
                    count += 1
    
    return count

def count_created_resources():
    """Count resources marked as Created in DynamoDB"""
    
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
                ':p': {'S': 'ial'},
                ':status': {'S': 'Created'}
            }
        )
        
        resources_by_phase = {}
        total_created = 0
        
        for item in response.get('Items', []):
            resource_name = item['ResourceName']['S']
            phase = item.get('Phase', {}).get('S', 'unknown')
            
            if phase not in resources_by_phase:
                resources_by_phase[phase] = []
            
            resources_by_phase[phase].append({
                'name': resource_name,
                'type': item.get('ResourceType', {}).get('S', 'Unknown'),
                'timestamp': item.get('Timestamp', {}).get('S', 'Unknown')
            })
            total_created += 1
        
        return {
            'total': total_created,
            'by_phase': resources_by_phase
        }
        
    except Exception as e:
        print(f"❌ Error counting created resources: {e}")
        return {'total': 0, 'by_phase': {}}

def validate_completeness(expected, created):
    """Validate deployment completeness"""
    
    validation = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'expected_total': expected['total'],
        'created_total': created['total'],
        'completion_rate': 0,
        'status': 'INCOMPLETE',
        'missing_resources': [],
        'phase_analysis': {},
        'issues': []
    }
    
    # Calculate completion rate
    if expected['total'] > 0:
        validation['completion_rate'] = (created['total'] / expected['total']) * 100
    
    # Determine status
    if created['total'] >= expected['total']:
        validation['status'] = 'COMPLETE'
    elif validation['completion_rate'] >= 95:
        validation['status'] = 'NEARLY_COMPLETE'
    elif validation['completion_rate'] >= 80:
        validation['status'] = 'MOSTLY_COMPLETE'
    else:
        validation['status'] = 'INCOMPLETE'
    
    # Analyze by phase
    for phase_name, phase_info in expected['phases'].items():
        expected_count = phase_info['expected_count']
        created_in_phase = len(created['by_phase'].get(phase_name, []))
        
        phase_status = 'COMPLETE' if created_in_phase >= expected_count else 'INCOMPLETE'
        
        validation['phase_analysis'][phase_name] = {
            'expected': expected_count,
            'created': created_in_phase,
            'status': phase_status,
            'completion_rate': (created_in_phase / expected_count * 100) if expected_count > 0 else 0
        }
        
        # Track missing resources
        if created_in_phase < expected_count:
            missing_count = expected_count - created_in_phase
            validation['missing_resources'].append({
                'phase': phase_name,
                'missing_count': missing_count,
                'expected': expected_count,
                'created': created_in_phase
            })
    
    # Identify issues
    if validation['completion_rate'] < 100:
        validation['issues'].append(f"Deployment incomplete: {validation['completion_rate']:.1f}% complete")
    
    if validation['missing_resources']:
        validation['issues'].append(f"{len(validation['missing_resources'])} phases have missing resources")
    
    return validation

def generate_validation_report(validation):
    """Generate comprehensive validation report"""
    
    # Save detailed report
    REPORTS_DIR.mkdir(exist_ok=True)
    
    with open(REPORTS_DIR / 'deployment_validation.json', 'w') as f:
        json.dump(validation, f, indent=2)
    
    # Print summary
    print(f"\n📊 DEPLOYMENT VALIDATION REPORT")
    print(f"Status: {validation['status']}")
    print(f"Completion Rate: {validation['completion_rate']:.1f}%")
    print(f"Expected Resources: {validation['expected_total']}")
    print(f"Created Resources: {validation['created_total']}")
    
    if validation['missing_resources']:
        print(f"\n🚨 MISSING RESOURCES ({len(validation['missing_resources'])} phases):")
        for missing in validation['missing_resources']:
            print(f"  - {missing['phase']}: {missing['missing_count']} missing ({missing['created']}/{missing['expected']})")
    
    if validation['issues']:
        print(f"\n⚠️ ISSUES:")
        for issue in validation['issues']:
            print(f"  - {issue}")
    
    # Phase-by-phase analysis
    print(f"\n📋 PHASE ANALYSIS:")
    for phase, analysis in validation['phase_analysis'].items():
        status_icon = "✅" if analysis['status'] == 'COMPLETE' else "❌"
        print(f"  {status_icon} {phase}: {analysis['created']}/{analysis['expected']} ({analysis['completion_rate']:.0f}%)")

def update_validation_metadata():
    """Update validation metadata with current counts"""
    
    expected = count_expected_resources()
    
    # Update checklist.yaml
    checklist_path = VALIDATION_DIR / 'checklist.yaml'
    
    try:
        with open(checklist_path, 'r') as f:
            content = f.read()
        
        # Update total_resources
        updated_content = content.replace(
            'total_resources: 61',
            f'total_resources: {expected["total"]}'
        )
        
        # Update validation_type
        updated_content = updated_content.replace(
            'validation_type: "Manual"',
            'validation_type: "Automated"'
        )
        
        with open(checklist_path, 'w') as f:
            f.write(updated_content)
        
        print(f"✅ Updated validation metadata: {expected['total']} resources")
        
    except Exception as e:
        print(f"⚠️ Could not update metadata: {e}")

if __name__ == "__main__":
    # Update metadata first
    update_validation_metadata()
    
    # Run validation
    main()
