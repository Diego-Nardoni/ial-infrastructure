#!/usr/bin/env python3
"""Bedrock-powered Test Execution and Analysis for IaL CI/CD"""

import json
import boto3
import subprocess
import os
import sys
from datetime import datetime

# AWS Clients
bedrock = boto3.client('bedrock-runtime')

def main():
    """Execute generated tests and analyze results with Bedrock"""
    
    print("🧪 Executing Bedrock-generated tests...")
    
    # 1. Execute pytest tests
    test_results = execute_pytest_tests()
    
    # 2. Analyze results with Bedrock
    analysis = analyze_results_with_bedrock(test_results)
    
    # 3. Generate intelligent report
    generate_intelligent_report(analysis)
    
    # 4. Take automated actions
    take_automated_actions(analysis)
    
    # 5. Exit with appropriate code
    exit_code = 0 if analysis['overall_health'] == 'HEALTHY' else 1
    sys.exit(exit_code)

def execute_pytest_tests():
    """Execute all generated pytest tests"""
    
    test_results = {
        'timestamp': datetime.utcnow().isoformat(),
        'categories': {},
        'summary': {}
    }
    
    test_dir = '/home/ial/tests/generated'
    
    if not os.path.exists(test_dir):
        print("⚠️ No generated tests found")
        return test_results
    
    # Execute tests by category
    for test_file in os.listdir(test_dir):
        if test_file.startswith('test_') and test_file.endswith('.py'):
            category = test_file.replace('test_', '').replace('_bedrock.py', '')
            
            print(f"🔍 Running {category} tests...")
            
            # Execute pytest with JSON output
            cmd = [
                'python3', '-m', 'pytest', 
                f'{test_dir}/{test_file}',
                '--json-report', '--json-report-file=/tmp/pytest_report.json',
                '-v'
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                # Parse pytest JSON report
                with open('/tmp/pytest_report.json', 'r') as f:
                    pytest_data = json.load(f)
                
                test_results['categories'][category] = {
                    'exit_code': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'pytest_data': pytest_data,
                    'passed': pytest_data['summary']['passed'],
                    'failed': pytest_data['summary']['failed'],
                    'total': pytest_data['summary']['total']
                }
                
                print(f"  ✅ {pytest_data['summary']['passed']} passed")
                print(f"  ❌ {pytest_data['summary']['failed']} failed")
                
            except subprocess.TimeoutExpired:
                test_results['categories'][category] = {
                    'exit_code': -1,
                    'error': 'Test execution timeout',
                    'passed': 0,
                    'failed': 1,
                    'total': 1
                }
                print(f"  ⏰ Tests timed out")
            
            except Exception as e:
                test_results['categories'][category] = {
                    'exit_code': -1,
                    'error': str(e),
                    'passed': 0,
                    'failed': 1,
                    'total': 1
                }
                print(f"  ❌ Error: {str(e)}")
    
    # Calculate summary
    total_passed = sum(cat.get('passed', 0) for cat in test_results['categories'].values())
    total_failed = sum(cat.get('failed', 0) for cat in test_results['categories'].values())
    total_tests = sum(cat.get('total', 0) for cat in test_results['categories'].values())
    
    test_results['summary'] = {
        'total_tests': total_tests,
        'total_passed': total_passed,
        'total_failed': total_failed,
        'success_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0
    }
    
    return test_results

def analyze_results_with_bedrock(test_results):
    """Use Bedrock to analyze test results intelligently"""
    
    # Select model based on complexity
    model_id = 'anthropic.claude-3-haiku-20240307-v1:0'  # Cost-effective for analysis
    
    prompt = create_analysis_prompt(test_results)
    
    try:
        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 2000,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        content = result['content'][0]['text']
        
        # Parse analysis from response
        analysis = parse_bedrock_analysis(content)
        
        # Log usage
        log_bedrock_usage(model_id, len(prompt), len(content), 'test_analysis')
        
        return analysis
        
    except Exception as e:
        print(f"❌ Bedrock analysis failed: {str(e)}")
        return generate_fallback_analysis(test_results)

def create_analysis_prompt(test_results):
    """Create prompt for Bedrock test analysis"""
    
    environment = os.environ.get('ENVIRONMENT', 'production')
    
    prompt = f"""You are an AWS infrastructure expert analyzing test results for a production deployment.

TEST EXECUTION RESULTS:
{json.dumps(test_results, indent=2)}

ENVIRONMENT: {environment}
PROJECT: IaL (Infrastructure as Language)

ANALYSIS REQUIRED:

1. OVERALL HEALTH ASSESSMENT:
   - HEALTHY: All critical tests pass, minor issues acceptable
   - DEGRADED: Some important tests fail, requires attention
   - CRITICAL: Critical tests fail, immediate action required

2. CRITICAL ISSUES IDENTIFICATION:
   - Security vulnerabilities
   - Service unavailability
   - Data integrity problems
   - Performance degradation

3. REMEDIATION RECOMMENDATIONS:
   - Immediate actions required
   - Auto-fixable issues
   - Manual intervention needed
   - Rollback recommendations

4. BUSINESS IMPACT ASSESSMENT:
   - User-facing impact
   - Service availability
   - Performance implications
   - Security risks

RESPONSE FORMAT (JSON only):
{{
  "overall_health": "HEALTHY|DEGRADED|CRITICAL",
  "health_score": 0-100,
  "critical_issues": [
    {{
      "category": "security|performance|availability|data",
      "severity": "critical|high|medium|low",
      "description": "Issue description",
      "impact": "Business impact",
      "remediation": "How to fix"
    }}
  ],
  "auto_fixable_issues": [
    {{
      "issue": "Description",
      "fix_command": "AWS CLI command to fix",
      "validation": "How to validate fix"
    }}
  ],
  "recommendations": [
    "Actionable recommendation 1",
    "Actionable recommendation 2"
  ],
  "rollback_required": true/false,
  "rollback_reason": "Why rollback is needed",
  "next_steps": [
    "Immediate action 1",
    "Follow-up action 2"
  ]
}}

DECISION CRITERIA:
- HEALTHY: >95% test pass rate, no critical failures
- DEGRADED: 80-95% pass rate, some important failures
- CRITICAL: <80% pass rate, critical system failures"""

    return prompt

def parse_bedrock_analysis(content):
    """Parse Bedrock analysis response"""
    
    try:
        # Extract JSON from response
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            raise ValueError("No JSON found in response")
        
        json_content = content[start_idx:end_idx]
        analysis = json.loads(json_content)
        
        return analysis
        
    except Exception as e:
        print(f"⚠️ Error parsing Bedrock analysis: {str(e)}")
        return generate_fallback_analysis({})

def generate_fallback_analysis(test_results):
    """Generate basic analysis if Bedrock fails"""
    
    summary = test_results.get('summary', {})
    success_rate = summary.get('success_rate', 0)
    
    if success_rate >= 95:
        health = 'HEALTHY'
    elif success_rate >= 80:
        health = 'DEGRADED'
    else:
        health = 'CRITICAL'
    
    return {
        'overall_health': health,
        'health_score': int(success_rate),
        'critical_issues': [],
        'auto_fixable_issues': [],
        'recommendations': ['Review failed tests manually'],
        'rollback_required': success_rate < 80,
        'rollback_reason': 'Low test success rate' if success_rate < 80 else None,
        'next_steps': ['Investigate test failures']
    }

def generate_intelligent_report(analysis):
    """Generate comprehensive test report"""
    
    report = {
        'timestamp': datetime.utcnow().isoformat(),
        'analysis': analysis,
        'deployment_recommendation': get_deployment_recommendation(analysis)
    }
    
    # Save detailed report
    with open('/home/ial/reports/test_analysis.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print(f"\n📊 TEST ANALYSIS SUMMARY")
    print(f"Overall Health: {analysis['overall_health']}")
    print(f"Health Score: {analysis['health_score']}/100")
    
    if analysis['critical_issues']:
        print(f"\n🚨 CRITICAL ISSUES ({len(analysis['critical_issues'])}):")
        for issue in analysis['critical_issues']:
            print(f"  - {issue['description']}")
    
    if analysis['auto_fixable_issues']:
        print(f"\n🤖 AUTO-FIXABLE ISSUES ({len(analysis['auto_fixable_issues'])}):")
        for issue in analysis['auto_fixable_issues']:
            print(f"  - {issue['issue']}")
    
    if analysis['recommendations']:
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in analysis['recommendations']:
            print(f"  - {rec}")

def take_automated_actions(analysis):
    """Take automated actions based on analysis"""
    
    # Execute auto-fixes
    if analysis.get('auto_fixable_issues'):
        print(f"\n🤖 Executing auto-fixes...")
        
        for issue in analysis['auto_fixable_issues']:
            try:
                cmd = issue['fix_command'].split()
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    print(f"  ✅ Fixed: {issue['issue']}")
                else:
                    print(f"  ❌ Failed to fix: {issue['issue']}")
                    
            except Exception as e:
                print(f"  ❌ Error fixing {issue['issue']}: {str(e)}")
    
    # Trigger rollback if required
    if analysis.get('rollback_required'):
        print(f"\n🔄 ROLLBACK REQUIRED: {analysis.get('rollback_reason')}")
        # Note: Actual rollback would be triggered by CI/CD pipeline

def get_deployment_recommendation(analysis):
    """Get deployment recommendation based on analysis"""
    
    health = analysis['overall_health']
    
    if health == 'HEALTHY':
        return 'PROCEED - Deployment is healthy and ready for production'
    elif health == 'DEGRADED':
        return 'CAUTION - Address issues before proceeding to production'
    else:
        return 'BLOCK - Critical issues must be resolved before deployment'

def log_bedrock_usage(model_id, input_tokens, output_tokens, operation):
    """Log Bedrock usage for cost tracking"""
    
    os.makedirs('/home/ial/logs', exist_ok=True)
    
    usage_log = {
        'timestamp': datetime.utcnow().isoformat(),
        'model_id': model_id,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'operation': operation,
        'project': os.environ.get('PROJECT_NAME', 'ial')
    }
    
    with open('/home/ial/logs/bedrock_usage.jsonl', 'a') as f:
        f.write(json.dumps(usage_log) + '\n')

if __name__ == "__main__":
    main()
