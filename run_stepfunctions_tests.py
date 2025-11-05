#!/usr/bin/env python3
"""
Run all Step Functions tests and generate report
"""

import subprocess
import sys
from pathlib import Path

def run_tests():
    """Run all Step Functions related tests"""
    
    test_files = [
        "tests/test_stepfunctions_integration.py",
        "tests/test_stepfunctions_complete.py"
    ]
    
    print("🧪 Running Step Functions Integration Tests...")
    print("=" * 60)
    
    all_passed = True
    
    for test_file in test_files:
        if Path(test_file).exists():
            print(f"\n📋 Running {test_file}...")
            
            try:
                result = subprocess.run([
                    sys.executable, "-m", "pytest", 
                    test_file, "-v", "--tb=short"
                ], capture_output=True, text=True, cwd="/home/ial")
                
                if result.returncode == 0:
                    print(f"✅ {test_file} - PASSED")
                    print(result.stdout)
                else:
                    print(f"❌ {test_file} - FAILED")
                    print(result.stdout)
                    print(result.stderr)
                    all_passed = False
                    
            except Exception as e:
                print(f"❌ Error running {test_file}: {e}")
                all_passed = False
        else:
            print(f"⚠️ Test file not found: {test_file}")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Step Functions migration is ready for deployment")
    else:
        print("❌ Some tests failed. Please review and fix issues.")
    
    return all_passed

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
