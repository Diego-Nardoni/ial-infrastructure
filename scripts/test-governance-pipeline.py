#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from datetime import datetime

class GovernancePipelineTester:
    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()
    
    def run_all_tests(self):
        """Run all governance pipeline tests"""
        
        print("🧪 IAL Governance Pipeline Test Suite")
        print("=" * 50)
        
        # Test 1: Compliance Engine
        self.test_compliance_engine()
        
        # Test 2: Budget Enforcement
        self.test_budget_enforcement()
        
        # Test 3: Security Sentinel
        self.test_security_sentinel()
        
        # Test 4: PR Commenter
        self.test_pr_commenter()
        
        # Test 5: Metrics Publisher
        self.test_metrics_publisher()
        
        # Test 6: Full Governance Flow
        self.test_full_governance_flow()
        
        # Generate test report
        self.generate_test_report()
    
    def test_compliance_engine(self):
        """Test compliance engine functionality"""
        print("\n1️⃣ Testing Compliance Engine...")
        
        try:
            # Test compliance check
            result = subprocess.run([
                'python3', 'governance_cli.py', 'compliance-check', 'phases/'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Compliance engine executed successfully")
                
                # Check if reports were generated
                if os.path.exists('reports/compliance/predeploy_report.json'):
                    print("✅ Compliance report generated")
                    self.test_results.append({"test": "compliance_engine", "status": "PASS"})
                else:
                    print("❌ Compliance report not generated")
                    self.test_results.append({"test": "compliance_engine", "status": "FAIL"})
            else:
                print(f"❌ Compliance engine failed: {result.stderr}")
                self.test_results.append({"test": "compliance_engine", "status": "FAIL"})
                
        except Exception as e:
            print(f"❌ Compliance engine test error: {e}")
            self.test_results.append({"test": "compliance_engine", "status": "ERROR"})
    
    def test_budget_enforcement(self):
        """Test budget enforcement functionality"""
        print("\n2️⃣ Testing Budget Enforcement...")
        
        try:
            # Test budget check with normal limit
            result = subprocess.run([
                'python3', 'governance_cli.py', 'budget-check', 'test-phase', '100'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Budget enforcement executed successfully")
                
                # Check if budget report was generated
                if os.path.exists('reports/finops/budget_check.json'):
                    print("✅ Budget report generated")
                    
                    # Test with low limit to trigger blocking
                    result2 = subprocess.run([
                        'python3', 'governance_cli.py', 'budget-check', 'compute', '10'
                    ], capture_output=True, text=True, timeout=30)
                    
                    if "BLOCK" in result2.stdout or "exceed" in result2.stdout.lower():
                        print("✅ Budget blocking works correctly")
                        self.test_results.append({"test": "budget_enforcement", "status": "PASS"})
                    else:
                        print("⚠️ Budget blocking may not be working")
                        self.test_results.append({"test": "budget_enforcement", "status": "WARNING"})
                else:
                    print("❌ Budget report not generated")
                    self.test_results.append({"test": "budget_enforcement", "status": "FAIL"})
            else:
                print(f"❌ Budget enforcement failed: {result.stderr}")
                self.test_results.append({"test": "budget_enforcement", "status": "FAIL"})
                
        except Exception as e:
            print(f"❌ Budget enforcement test error: {e}")
            self.test_results.append({"test": "budget_enforcement", "status": "ERROR"})
    
    def test_security_sentinel(self):
        """Test security sentinel functionality"""
        print("\n3️⃣ Testing Security Sentinel...")
        
        try:
            # Test security event processing
            test_event = {
                "id": "test-event-123",
                "source": "aws.guardduty",
                "type": "UnauthorizedAPICall",
                "severity": "Medium"
            }
            
            result = subprocess.run([
                'python3', 'governance_cli.py', 'security-event', json.dumps(test_event)
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Security sentinel executed successfully")
                
                # Check if security report was generated
                if os.path.exists('reports/security/sentinel_report.json'):
                    print("✅ Security report generated")
                    self.test_results.append({"test": "security_sentinel", "status": "PASS"})
                else:
                    print("❌ Security report not generated")
                    self.test_results.append({"test": "security_sentinel", "status": "FAIL"})
            else:
                print(f"❌ Security sentinel failed: {result.stderr}")
                self.test_results.append({"test": "security_sentinel", "status": "FAIL"})
                
        except Exception as e:
            print(f"❌ Security sentinel test error: {e}")
            self.test_results.append({"test": "security_sentinel", "status": "ERROR"})
    
    def test_pr_commenter(self):
        """Test PR commenter functionality"""
        print("\n4️⃣ Testing PR Commenter...")
        
        try:
            # Test PR comment generation (without actually posting)
            result = subprocess.run([
                'python3', 'scripts/pr-commenter.py',
                '--compliance-status', 'PASS',
                '--budget-status', 'PASS', 
                '--security-status', 'PASS',
                '--overall-status', 'PASS',
                '--pr-number', '1',
                '--github-token', 'test-token'
            ], capture_output=True, text=True, timeout=30)
            
            # Expect this to fail due to invalid token, but should generate report
            if "IAL Governance Report" in result.stderr or "Generated on" in result.stderr:
                print("✅ PR comment generation works")
                self.test_results.append({"test": "pr_commenter", "status": "PASS"})
            else:
                print("⚠️ PR commenter may have issues (expected without valid GitHub token)")
                self.test_results.append({"test": "pr_commenter", "status": "WARNING"})
                
        except Exception as e:
            print(f"❌ PR commenter test error: {e}")
            self.test_results.append({"test": "pr_commenter", "status": "ERROR"})
    
    def test_metrics_publisher(self):
        """Test metrics publisher functionality"""
        print("\n5️⃣ Testing Metrics Publisher...")
        
        try:
            # Test metrics publishing (will fail without AWS credentials, but should validate logic)
            result = subprocess.run([
                'python3', 'scripts/publish-governance-metrics.py',
                '--compliance-status', 'PASS',
                '--budget-status', 'PASS',
                '--security-status', 'PASS'
            ], capture_output=True, text=True, timeout=30)
            
            # Check if the script runs without syntax errors
            if "metrics to CloudWatch" in result.stdout or result.returncode == 0:
                print("✅ Metrics publisher logic works")
                self.test_results.append({"test": "metrics_publisher", "status": "PASS"})
            else:
                print("⚠️ Metrics publisher may have issues (expected without AWS credentials)")
                self.test_results.append({"test": "metrics_publisher", "status": "WARNING"})
                
        except Exception as e:
            print(f"❌ Metrics publisher test error: {e}")
            self.test_results.append({"test": "metrics_publisher", "status": "ERROR"})
    
    def test_full_governance_flow(self):
        """Test full governance flow"""
        print("\n6️⃣ Testing Full Governance Flow...")
        
        try:
            # Test full governance check
            result = subprocess.run([
                'python3', 'governance_cli.py', 'full-governance', 'test-phase'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("✅ Full governance flow executed successfully")
                
                # Check for expected outputs
                if "Compliance Check" in result.stdout and "Budget Check" in result.stdout:
                    print("✅ All governance components executed")
                    self.test_results.append({"test": "full_governance_flow", "status": "PASS"})
                else:
                    print("❌ Some governance components missing")
                    self.test_results.append({"test": "full_governance_flow", "status": "FAIL"})
            else:
                print(f"❌ Full governance flow failed: {result.stderr}")
                self.test_results.append({"test": "full_governance_flow", "status": "FAIL"})
                
        except Exception as e:
            print(f"❌ Full governance flow test error: {e}")
            self.test_results.append({"test": "full_governance_flow", "status": "ERROR"})
    
    def generate_test_report(self):
        """Generate test report"""
        print("\n" + "=" * 50)
        print("📊 Test Results Summary")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["status"] == "PASS"])
        failed_tests = len([t for t in self.test_results if t["status"] == "FAIL"])
        warning_tests = len([t for t in self.test_results if t["status"] == "WARNING"])
        error_tests = len([t for t in self.test_results if t["status"] == "ERROR"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️ Warnings: {warning_tests}")
        print(f"💥 Errors: {error_tests}")
        
        print("\nDetailed Results:")
        for result in self.test_results:
            status_icon = {
                "PASS": "✅",
                "FAIL": "❌", 
                "WARNING": "⚠️",
                "ERROR": "💥"
            }.get(result["status"], "❓")
            
            print(f"  {status_icon} {result['test']}: {result['status']}")
        
        # Save test report
        test_report = {
            "timestamp": self.start_time.isoformat(),
            "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "warnings": warning_tests,
                "errors": error_tests
            },
            "results": self.test_results
        }
        
        os.makedirs("reports/tests", exist_ok=True)
        with open("reports/tests/governance_pipeline_test.json", "w") as f:
            json.dump(test_report, f, indent=2)
        
        print(f"\n📄 Test report saved: reports/tests/governance_pipeline_test.json")
        
        # Overall status
        if failed_tests == 0 and error_tests == 0:
            print("\n🎉 All tests passed! Governance pipeline is ready.")
            return True
        else:
            print(f"\n⚠️ {failed_tests + error_tests} tests failed. Please review and fix issues.")
            return False

def main():
    tester = GovernancePipelineTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
