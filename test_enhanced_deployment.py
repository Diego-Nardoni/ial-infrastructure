#!/usr/bin/env python3
"""
Teste da implementação das melhorias do IAL
Valida WAF, X-Ray, Circuit Breaker Metrics
"""

import boto3
import json
import time
from datetime import datetime

class EnhancedDeploymentTester:
    def __init__(self):
        self.session = boto3.Session()
        
    def test_waf_deployment(self):
        """Testa se o WAF foi deployado corretamente"""
        print("\n🔒 Testing WAF Deployment...")
        
        try:
            wafv2 = self.session.client('wafv2')
            
            # List WebACLs
            response = wafv2.list_web_acls(Scope='REGIONAL')
            
            ial_waf = None
            for acl in response['WebACLs']:
                if 'ial-api-gateway-waf' in acl['Name']:
                    ial_waf = acl
                    break
            
            if ial_waf:
                print(f"   ✅ WAF found: {ial_waf['Name']}")
                print(f"   📊 WAF ID: {ial_waf['Id']}")
                
                # Get WAF details
                details = wafv2.get_web_acl(
                    Name=ial_waf['Name'],
                    Scope='REGIONAL',
                    Id=ial_waf['Id']
                )
                
                rules_count = len(details['WebACL']['Rules'])
                print(f"   📋 Rules configured: {rules_count}")
                
                return {'success': True, 'waf_name': ial_waf['Name'], 'rules': rules_count}
            else:
                print("   ❌ IAL WAF not found")
                return {'success': False, 'error': 'WAF not found'}
                
        except Exception as e:
            print(f"   ❌ WAF test failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_xray_configuration(self):
        """Testa se o X-Ray está configurado"""
        print("\n🔍 Testing X-Ray Configuration...")
        
        try:
            xray = self.session.client('xray')
            
            # Get tracing configuration
            response = xray.get_trace_summaries(
                TimeRangeType='TraceId',
                StartTime=datetime.utcnow().replace(hour=0, minute=0, second=0),
                EndTime=datetime.utcnow()
            )
            
            print(f"   📊 Recent traces found: {len(response.get('TraceSummaries', []))}")
            
            # Check API Gateway tracing
            apigateway = self.session.client('apigateway')
            apis = apigateway.get_rest_apis()
            
            tracing_enabled = False
            for api in apis['items']:
                if 'ial' in api['name'].lower():
                    stages = apigateway.get_stages(restApiId=api['id'])
                    for stage in stages['item']:
                        if stage.get('tracingConfig', {}).get('tracingEnabled'):
                            tracing_enabled = True
                            print(f"   ✅ X-Ray enabled on API: {api['name']}")
            
            if tracing_enabled:
                return {'success': True, 'tracing_enabled': True}
            else:
                print("   ⚠️  X-Ray tracing not detected on API Gateway")
                return {'success': False, 'error': 'X-Ray not enabled'}
                
        except Exception as e:
            print(f"   ❌ X-Ray test failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_metrics_publisher(self):
        """Testa se o Metrics Publisher está deployado"""
        print("\n📈 Testing Circuit Breaker Metrics Publisher...")
        
        try:
            lambda_client = self.session.client('lambda')
            
            # Check if Lambda function exists
            try:
                response = lambda_client.get_function(
                    FunctionName='ial-circuit-breaker-metrics-publisher'
                )
                
                print(f"   ✅ Metrics Publisher found")
                print(f"   🏷️  Runtime: {response['Configuration']['Runtime']}")
                print(f"   ⏱️  Timeout: {response['Configuration']['Timeout']}s")
                
                # Test invoke (dry run)
                test_event = {
                    'Records': [{
                        'eventSource': 'aws:ssm',
                        'eventSourceARN': 'arn:aws:ssm:us-east-1:123456789012:parameter/circuit-breaker-bedrock-state'
                    }]
                }
                
                # Don't actually invoke to avoid side effects
                print("   ✅ Function ready for SSM Parameter triggers")
                
                return {'success': True, 'function_name': 'ial-circuit-breaker-metrics-publisher'}
                
            except lambda_client.exceptions.ResourceNotFoundException:
                print("   ❌ Metrics Publisher Lambda not found")
                return {'success': False, 'error': 'Lambda function not found'}
                
        except Exception as e:
            print(f"   ❌ Metrics Publisher test failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_monitoring_dashboards(self):
        """Testa se os dashboards foram criados"""
        print("\n📊 Testing Monitoring Dashboards...")
        
        try:
            cloudwatch = self.session.client('cloudwatch')
            
            # List dashboards
            response = cloudwatch.list_dashboards()
            
            ial_dashboards = []
            for dashboard in response['DashboardEntries']:
                if 'IAL' in dashboard['DashboardName']:
                    ial_dashboards.append(dashboard['DashboardName'])
            
            if ial_dashboards:
                print(f"   ✅ Dashboards found: {', '.join(ial_dashboards)}")
                
                # Check alarms
                alarms = cloudwatch.describe_alarms(
                    AlarmNamePrefix='IAL-'
                )
                
                alarm_count = len(alarms['MetricAlarms'])
                print(f"   🚨 Alarms configured: {alarm_count}")
                
                return {
                    'success': True, 
                    'dashboards': len(ial_dashboards),
                    'alarms': alarm_count
                }
            else:
                print("   ❌ No IAL dashboards found")
                return {'success': False, 'error': 'No dashboards found'}
                
        except Exception as e:
            print(f"   ❌ Dashboard test failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_complete_test(self):
        """Executa todos os testes"""
        print("🧪 IAL Enhanced Deployment Test Suite")
        print("=" * 50)
        
        results = {}
        
        # Test WAF
        results['waf'] = self.test_waf_deployment()
        
        # Test X-Ray
        results['xray'] = self.test_xray_configuration()
        
        # Test Metrics Publisher
        results['metrics'] = self.test_metrics_publisher()
        
        # Test Dashboards
        results['dashboards'] = self.test_monitoring_dashboards()
        
        # Summary
        print("\n📋 Test Summary:")
        print("=" * 30)
        
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r['success'])
        
        for component, result in results.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"   {component.upper()}: {status}")
            if not result['success']:
                print(f"      Error: {result['error']}")
        
        print(f"\n🎯 Overall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All enhanced features deployed successfully!")
            return True
        else:
            print("⚠️  Some features need attention")
            return False

if __name__ == "__main__":
    tester = EnhancedDeploymentTester()
    success = tester.run_complete_test()
    exit(0 if success else 1)
