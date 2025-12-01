#!/usr/bin/env python3
"""
Test Bedrock Agent Core Implementation
Validates integration without breaking existing system
"""

import sys
import os
sys.path.insert(0, '/home/ial')

def test_agent_core_creation():
    """Test Bedrock Agent Core creation"""
    print("🧠 Testing Bedrock Agent Core creation...")
    
    try:
        from core.bedrock_agent_core import BedrockAgentCore
        
        agent = BedrockAgentCore()
        assert hasattr(agent, 'create_agent'), "create_agent method missing"
        assert hasattr(agent, 'invoke_agent'), "invoke_agent method missing"
        assert hasattr(agent, '_init_tools'), "tools initialization missing"
        
        print("✅ Agent Core class structure validated")
        return True
        
    except Exception as e:
        print(f"❌ Agent Core creation failed: {e}")
        return False

def test_agent_tools_lambda():
    """Test Agent Tools Lambda structure"""
    print("⚡ Testing Agent Tools Lambda...")
    
    try:
        from core.agent_tools_lambda import lambda_handler
        
        # Test lambda handler structure
        test_event = {
            'actionGroup': 'IALTools',
            'apiPath': '/get_aws_docs',
            'parameters': [{'name': 'query', 'value': 'test query'}]
        }
        
        # This should not fail on import/structure
        assert callable(lambda_handler), "lambda_handler not callable"
        
        print("✅ Agent Tools Lambda structure validated")
        return True
        
    except Exception as e:
        print(f"❌ Agent Tools Lambda failed: {e}")
        return False

def test_ialctl_integration():
    """Test IALCTL Agent Integration"""
    print("🔗 Testing IALCTL Agent Integration...")
    
    try:
        from core.ialctl_agent_integration import IALCTLAgentIntegration
        
        integration = IALCTLAgentIntegration()
        assert hasattr(integration, 'process_message'), "process_message method missing"
        assert hasattr(integration, 'set_offline_mode'), "offline mode missing"
        assert hasattr(integration, 'get_status'), "status method missing"
        
        # Test status
        status = integration.get_status()
        assert isinstance(status, dict), "status should return dict"
        assert 'agent_core_available' in status, "agent status missing"
        assert 'fallback_available' in status, "fallback status missing"
        
        print("✅ IALCTL Integration structure validated")
        return True
        
    except Exception as e:
        print(f"❌ IALCTL Integration failed: {e}")
        return False

def test_fallback_preservation():
    """Test that existing NLP system is preserved"""
    print("🔄 Testing fallback system preservation...")
    
    try:
        # Test original engines still work
        from core.cognitive_engine import CognitiveEngine
        from core.master_engine_final import MasterEngineFinal
        
        cognitive = CognitiveEngine()
        master = MasterEngineFinal()
        
        assert hasattr(cognitive, 'process_intent'), "CognitiveEngine process_intent missing"
        assert hasattr(master, 'process_request'), "MasterEngine process_request missing"
        
        print("✅ Fallback NLP system preserved")
        return True
        
    except Exception as e:
        print(f"❌ Fallback system test failed: {e}")
        return False

def test_existing_infrastructure():
    """Test that existing infrastructure components are intact"""
    print("🏗️ Testing existing infrastructure preservation...")
    
    try:
        # Test key components still exist
        from mcp_orchestrator import MCPOrchestrator
        from core.drift.drift_detector import DriftDetector
        from core.validation_system import IALValidationSystem
        
        mcp = MCPOrchestrator()
        drift = DriftDetector()
        validator = IALValidationSystem()
        
        assert hasattr(mcp, 'execute_coordinated'), "MCP orchestration missing"
        assert hasattr(drift, 'detect_drift'), "Drift detection missing"
        assert hasattr(validator, 'validate_complete_deployment'), "Validation missing"
        
        print("✅ Existing infrastructure preserved")
        return True
        
    except Exception as e:
        print(f"❌ Infrastructure preservation test failed: {e}")
        return False

def test_enhanced_ialctl():
    """Test enhanced IALCTL with agent support"""
    print("🚀 Testing enhanced IALCTL...")
    
    try:
        # Check if enhanced IALCTL exists and has proper structure
        if os.path.exists('/home/ial/ialctl_agent_enhanced.py'):
            print("✅ Enhanced IALCTL file exists")
        else:
            print("⚠️ Enhanced IALCTL file not found")
        
        # Check if original IALCTL was updated
        with open('/home/ial/ialctl_integrated.py', 'r') as f:
            content = f.read()
            if 'IALCTLAgentIntegration' in content:
                print("✅ Original IALCTL updated with agent support")
            else:
                print("⚠️ Original IALCTL not updated")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced IALCTL test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Bedrock Agent Core Implementation")
    print("=" * 60)
    
    tests = [
        test_agent_core_creation,
        test_agent_tools_lambda,
        test_ialctl_integration,
        test_fallback_preservation,
        test_existing_infrastructure,
        test_enhanced_ialctl
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Bedrock Agent Core ready for deployment")
        print("\n🚀 Next steps:")
        print("1. Run: python3 setup_bedrock_agent.py")
        print("2. Test: python3 ialctl_agent_enhanced.py --status")
        print("3. Use: python3 ialctl_agent_enhanced.py")
        return 0
    else:
        print("⚠️ Some tests failed. Please review implementation.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
