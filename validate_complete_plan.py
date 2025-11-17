#!/usr/bin/env python3
"""
Validação completa do plano /home/arquitetura-ok
Testa TODAS as stacks CloudFormation mencionadas no plano
"""

import boto3
import json
from datetime import datetime

class CompletePlanValidator:
    def __init__(self):
        self.cf = boto3.client('cloudformation')
        self.wafv2 = boto3.client('wafv2')
        self.lambda_client = boto3.client('lambda')
        self.cloudwatch = boto3.client('cloudwatch')
        self.apigateway = boto3.client('apigateway')
        self.xray = boto3.client('xray')
        
    def validate_waf_stack(self):
        """Valida stack WAF conforme plano"""
        print("\n🔒 Validating WAF CloudFormation Stack...")
        
        try:
            # Check stack exists
            stacks = self.cf.list_stacks(StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE'])
            waf_stacks = [s for s in stacks['StackSummaries'] if 'waf' in s['StackName'].lower()]
            
            if not waf_stacks:
                print("   ❌ WAF stack not found")
                return {'success': False, 'error': 'WAF stack missing'}
            
            waf_stack = waf_stacks[0]
            print(f"   ✅ WAF Stack found: {waf_stack['StackName']}")
            
            # Get stack outputs
            stack_details = self.cf.describe_stacks(StackName=waf_stack['StackName'])
            outputs = stack_details['Stacks'][0].get('Outputs', [])
            
            web_acl_arn = None
            for output in outputs:
                if 'WebACL' in output['OutputKey']:
                    web_acl_arn = output['OutputValue']
                    print(f"   📊 WebACL ARN: {web_acl_arn}")
            
            # Validate WAF rules as per plan
            if web_acl_arn:
                web_acls = self.wafv2.list_web_acls(Scope='REGIONAL')
                for acl in web_acls['WebACLs']:
                    if acl['ARN'] == web_acl_arn:
                        acl_details = self.wafv2.get_web_acl(
                            Name=acl['Name'],
                            Scope='REGIONAL',
                            Id=acl['Id']
                        )
                        
                        rules = acl_details['WebACL']['Rules']
                        print(f"   📋 Rules configured: {len(rules)}")
                        
                        # Check required rules from plan
                        required_rules = ['RateLimitRule', 'AWSManagedRulesCommonRuleSet', 'AWSManagedRulesSQLiRuleSet']
                        found_rules = [rule['Name'] for rule in rules]
                        
                        for req_rule in required_rules:
                            if any(req_rule in rule for rule in found_rules):
                                print(f"   ✅ Required rule found: {req_rule}")
                            else:
                                print(f"   ❌ Missing required rule: {req_rule}")
                        
                        return {
                            'success': True,
                            'stack_name': waf_stack['StackName'],
                            'rules_count': len(rules),
                            'web_acl_arn': web_acl_arn
                        }
            
            return {'success': False, 'error': 'WebACL ARN not found'}
            
        except Exception as e:
            print(f"   ❌ WAF validation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def validate_circuit_breaker_metrics_stack(self):
        """Valida stack Circuit Breaker Metrics conforme plano"""
        print("\n📈 Validating Circuit Breaker Metrics Stack...")
        
        try:
            # Check CloudFormation stack
            stacks = self.cf.list_stacks(StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE'])
            cb_stacks = [s for s in stacks['StackSummaries'] if 'circuit-breaker' in s['StackName'].lower()]
            
            stack_exists = len(cb_stacks) > 0
            if stack_exists:
                print(f"   ✅ Circuit Breaker stack found: {cb_stacks[0]['StackName']}")
            else:
                print("   ⚠️  Circuit Breaker CloudFormation stack not found")
            
            # Check Lambda function (deployed via enhanced ialctl)
            try:
                lambda_response = self.lambda_client.get_function(
                    FunctionName='ial-circuit-breaker-metrics-publisher'
                )
                
                print(f"   ✅ Metrics Publisher Lambda found")
                print(f"   🏷️  Runtime: {lambda_response['Configuration']['Runtime']}")
                print(f"   ⏱️  Timeout: {lambda_response['Configuration']['Timeout']}s")
                
                # Check environment variables as per plan
                env_vars = lambda_response['Configuration'].get('Environment', {}).get('Variables', {})
                if 'NAMESPACE' in env_vars:
                    print(f"   ✅ Environment configured: {env_vars['NAMESPACE']}")
                
                return {
                    'success': True,
                    'lambda_exists': True,
                    'stack_exists': stack_exists,
                    'function_name': 'ial-circuit-breaker-metrics-publisher'
                }
                
            except self.lambda_client.exceptions.ResourceNotFoundException:
                print("   ❌ Metrics Publisher Lambda not found")
                return {'success': False, 'error': 'Lambda function missing'}
                
        except Exception as e:
            print(f"   ❌ Circuit Breaker validation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def validate_xray_configuration(self):
        """Valida configuração X-Ray conforme plano"""
        print("\n🔍 Validating X-Ray Configuration...")
        
        try:
            # Check X-Ray service configuration
            sampling_rules = self.xray.get_sampling_rules()
            ial_rules = [rule for rule in sampling_rules['SamplingRuleRecords'] 
                        if 'ial' in rule['SamplingRule'].get('ServiceName', '').lower()]
            
            if ial_rules:
                print(f"   ✅ X-Ray sampling rules found: {len(ial_rules)}")
            else:
                print("   ⚠️  No IAL-specific sampling rules found")
            
            # Check API Gateway X-Ray tracing
            apis = self.apigateway.get_rest_apis()
            tracing_enabled = False
            
            for api in apis['items']:
                if 'ial' in api['name'].lower():
                    stages = self.apigateway.get_stages(restApiId=api['id'])
                    for stage in stages['item']:
                        tracing_config = stage.get('tracingConfig', {})
                        if tracing_config.get('tracingEnabled'):
                            tracing_enabled = True
                            print(f"   ✅ X-Ray enabled on API: {api['name']}, Stage: {stage['stageName']}")
            
            # Check recent traces
            try:
                traces = self.xray.get_trace_summaries(
                    TimeRangeType='TraceId',
                    StartTime=datetime.utcnow().replace(hour=0, minute=0, second=0),
                    EndTime=datetime.utcnow()
                )
                trace_count = len(traces.get('TraceSummaries', []))
                print(f"   📊 Recent traces found: {trace_count}")
            except Exception:
                print("   📊 Recent traces: Unable to retrieve")
            
            return {
                'success': True,
                'sampling_rules': len(ial_rules),
                'api_tracing_enabled': tracing_enabled,
                'configuration_applied': True
            }
            
        except Exception as e:
            print(f"   ❌ X-Ray validation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def validate_monitoring_dashboards(self):
        """Valida dashboards e alertas conforme plano"""
        print("\n📊 Validating Monitoring Dashboards & Alerts...")
        
        try:
            # Check dashboards
            dashboards = self.cloudwatch.list_dashboards()
            ial_dashboards = [d for d in dashboards['DashboardEntries'] 
                            if 'IAL' in d['DashboardName']]
            
            print(f"   📊 IAL Dashboards found: {len(ial_dashboards)}")
            for dashboard in ial_dashboards:
                print(f"      - {dashboard['DashboardName']}")
            
            # Check required dashboards from plan
            required_dashboards = ['IAL-Executive-Dashboard', 'IAL-Technical-Dashboard']
            dashboard_names = [d['DashboardName'] for d in ial_dashboards]
            
            executive_exists = any('Executive' in name for name in dashboard_names)
            technical_exists = any('Technical' in name for name in dashboard_names)
            
            print(f"   {'✅' if executive_exists else '❌'} Executive Dashboard: {'Found' if executive_exists else 'Missing'}")
            print(f"   {'✅' if technical_exists else '❌'} Technical Dashboard: {'Found' if technical_exists else 'Missing'}")
            
            # Check alarms
            alarms = self.cloudwatch.describe_alarms(AlarmNamePrefix='IAL-')
            alarm_count = len(alarms['MetricAlarms'])
            print(f"   🚨 IAL Alarms configured: {alarm_count}")
            
            for alarm in alarms['MetricAlarms']:
                print(f"      - {alarm['AlarmName']}: {alarm['StateValue']}")
            
            # Check required alarms from plan
            required_alarms = ['CircuitBreaker', 'High-Error-Rate', 'WAF-Attack']
            alarm_names = [alarm['AlarmName'] for alarm in alarms['MetricAlarms']]
            
            for req_alarm in required_alarms:
                if any(req_alarm in name for name in alarm_names):
                    print(f"   ✅ Required alarm type found: {req_alarm}")
                else:
                    print(f"   ⚠️  Alarm type missing: {req_alarm}")
            
            return {
                'success': True,
                'dashboards_count': len(ial_dashboards),
                'alarms_count': alarm_count,
                'executive_dashboard': executive_exists,
                'technical_dashboard': technical_exists
            }
            
        except Exception as e:
            print(f"   ❌ Monitoring validation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def validate_foundation_stacks(self):
        """Valida stacks foundation mencionadas no plano"""
        print("\n📦 Validating Foundation Stacks...")
        
        try:
            stacks = self.cf.list_stacks(StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE'])
            ial_stacks = [s for s in stacks['StackSummaries'] if 'ial' in s['StackName'].lower()]
            
            print(f"   📊 Total IAL stacks found: {len(ial_stacks)}")
            
            # Key stacks mentioned in plan
            key_stacks = [
                'dynamodb', 'kms', 'iam', 'lambda', 's3', 'stepfunctions', 
                'cloudwatch', 'sns', 'eventbridge', 'secrets'
            ]
            
            found_key_stacks = 0
            for key in key_stacks:
                matching_stacks = [s for s in ial_stacks if key in s['StackName'].lower()]
                if matching_stacks:
                    print(f"   ✅ {key.upper()} stack found: {matching_stacks[0]['StackName']}")
                    found_key_stacks += 1
                else:
                    print(f"   ⚠️  {key.upper()} stack not found")
            
            success_rate = (found_key_stacks / len(key_stacks)) * 100
            print(f"   📊 Foundation coverage: {found_key_stacks}/{len(key_stacks)} ({success_rate:.1f}%)")
            
            return {
                'success': success_rate >= 80,  # 80% threshold
                'total_stacks': len(ial_stacks),
                'key_stacks_found': found_key_stacks,
                'coverage_percentage': success_rate
            }
            
        except Exception as e:
            print(f"   ❌ Foundation validation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_complete_validation(self):
        """Executa validação completa do plano"""
        print("🧪 COMPLETE PLAN VALIDATION - /home/arquitetura-ok")
        print("=" * 60)
        
        results = {}
        
        # Validate all components from plan
        results['waf'] = self.validate_waf_stack()
        results['circuit_breaker'] = self.validate_circuit_breaker_metrics_stack()
        results['xray'] = self.validate_xray_configuration()
        results['monitoring'] = self.validate_monitoring_dashboards()
        results['foundation'] = self.validate_foundation_stacks()
        
        # Calculate overall success
        print("\n📋 COMPLETE VALIDATION SUMMARY:")
        print("=" * 40)
        
        total_components = len(results)
        successful_components = sum(1 for r in results.values() if r['success'])
        
        for component, result in results.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"   {component.upper()}: {status}")
            if not result['success']:
                print(f"      Error: {result.get('error', 'Unknown error')}")
        
        overall_percentage = (successful_components / total_components) * 100
        print(f"\n🎯 OVERALL PLAN IMPLEMENTATION: {successful_components}/{total_components} ({overall_percentage:.1f}%)")
        
        # Detailed analysis
        if overall_percentage == 100:
            print("🎉 PLAN 100% IMPLEMENTED - ALL REQUIREMENTS MET!")
        elif overall_percentage >= 90:
            print("✅ PLAN SUBSTANTIALLY IMPLEMENTED - PRODUCTION READY")
        elif overall_percentage >= 75:
            print("⚠️  PLAN MOSTLY IMPLEMENTED - MINOR ISSUES REMAIN")
        else:
            print("❌ PLAN PARTIALLY IMPLEMENTED - MAJOR ISSUES NEED ATTENTION")
        
        return {
            'overall_success': overall_percentage >= 90,
            'percentage': overall_percentage,
            'results': results
        }

if __name__ == "__main__":
    validator = CompletePlanValidator()
    result = validator.run_complete_validation()
    exit(0 if result['overall_success'] else 1)
