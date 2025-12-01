#!/usr/bin/env python3
"""
Automated Tests for IAL Core Components
Tests for noble areas: IntentParser, RiskClassifier, CostGuardrails, DriftDetector, MCP Orchestrator
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, '/home/ial')

class TestIntentParser(unittest.TestCase):
    """Test Intent Parser functionality"""
    
    def setUp(self):
        try:
            from core.intent_parser import IntentParser
            self.parser = IntentParser()
        except ImportError:
            self.skipTest("IntentParser not available")
    
    def test_parse_infrastructure_intent(self):
        """Test parsing infrastructure intents"""
        intent = "criar uma aplicação web com banco de dados"
        result = self.parser.parse_intent(intent)
        
        self.assertIsInstance(result, dict)
        self.assertIn('intent_type', result)
        self.assertIn('confidence', result)
    
    def test_parse_drift_intent(self):
        """Test parsing drift-related intents"""
        intent = "verificar drift na infraestrutura"
        result = self.parser.parse_intent(intent)
        
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get('confidence', 0) > 0)

class TestRiskClassifier(unittest.TestCase):
    """Test Risk Classifier functionality"""
    
    def setUp(self):
        try:
            from core.intent_validation.risk_classifier import RiskClassifier
            self.classifier = RiskClassifier()
        except ImportError:
            self.skipTest("RiskClassifier not available")
    
    def test_classify_low_risk(self):
        """Test low risk classification"""
        intent = "listar buckets S3"
        result = self.classifier.classify_risk(intent)
        
        self.assertIsInstance(result, dict)
        self.assertIn('risk_level', result)
        self.assertIn(['low', 'medium', 'high'], result['risk_level'])
    
    def test_classify_high_risk(self):
        """Test high risk classification"""
        intent = "deletar todos os recursos da conta"
        result = self.classifier.classify_risk(intent)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('risk_level'), 'high')

class TestCostGuardrails(unittest.TestCase):
    """Test Cost Guardrails functionality"""
    
    def setUp(self):
        try:
            from core.intent_cost_guardrails import IntentCostGuardrails
            self.guardrails = IntentCostGuardrails()
        except ImportError:
            self.skipTest("IntentCostGuardrails not available")
    
    def test_validate_cost_simple(self):
        """Test cost validation for simple resources"""
        intent = "criar um bucket S3"
        result = self.guardrails.validate_cost(intent)
        
        self.assertIsInstance(result, dict)
        self.assertIn('cost_estimate', result)
        self.assertIn('monthly_cost', result)
    
    def test_validate_cost_complex(self):
        """Test cost validation for complex infrastructure"""
        intent = "criar cluster EKS com 10 nodes"
        result = self.guardrails.validate_cost(intent)
        
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get('monthly_cost', 0) > 0)

class TestDriftDetector(unittest.TestCase):
    """Test Drift Detector functionality"""
    
    def setUp(self):
        try:
            from core.drift.drift_detector import DriftDetector
            self.detector = DriftDetector()
        except ImportError:
            self.skipTest("DriftDetector not available")
    
    @patch('boto3.client')
    def test_detect_drift_no_changes(self, mock_boto):
        """Test drift detection with no changes"""
        # Mock AWS responses
        mock_boto.return_value.describe_stacks.return_value = {
            'Stacks': []
        }
        
        result = self.detector.detect_drift()
        
        self.assertIsInstance(result, list)
    
    def test_compare_states(self):
        """Test state comparison logic"""
        desired = {'resources': {'bucket1': {'type': 'S3::Bucket'}}}
        current = {'resources': {'bucket1': {'type': 'S3::Bucket'}}}
        
        result = self.detector._compare_states(desired, current)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)  # No drift

class TestMCPOrchestrator(unittest.TestCase):
    """Test MCP Orchestrator functionality"""
    
    def setUp(self):
        try:
            from mcp_orchestrator import MCPOrchestrator
            self.orchestrator = MCPOrchestrator()
        except ImportError:
            self.skipTest("MCPOrchestrator not available")
    
    def test_orchestrator_initialization(self):
        """Test orchestrator initializes correctly"""
        self.assertIsNotNone(self.orchestrator)
        self.assertTrue(hasattr(self.orchestrator, 'execute_coordinated'))
    
    @patch('asyncio.gather')
    async def test_execute_coordinated_mock(self, mock_gather):
        """Test coordinated execution with mocked MCPs"""
        mock_gather.return_value = [
            {'success': True, 'result': 'mocked'}
        ]
        
        mcps = ['aws-cloudformation-mcp']
        context = {'user_input': 'test'}
        
        result = await self.orchestrator.execute_coordinated(mcps, context, 'test')
        
        self.assertIsInstance(result, dict)
        self.assertIn('execution_id', result)

class TestEnhancedFallbackSystem(unittest.TestCase):
    """Test Enhanced Fallback System"""
    
    def setUp(self):
        try:
            from core.enhanced_fallback_system import EnhancedFallbackSystem, ProcessingMode
            self.fallback = EnhancedFallbackSystem()
            self.ProcessingMode = ProcessingMode
        except ImportError:
            self.skipTest("EnhancedFallbackSystem not available")
    
    def test_sandbox_mode(self):
        """Test sandbox mode processing"""
        result = self.fallback._process_sandbox_mode("criar bucket S3")
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('source'), 'sandbox')
        self.assertIn('preview_file', result)
    
    @patch('core.enhanced_fallback_system.IALCTLAgentIntegration')
    def test_agent_fallback_success(self, mock_integration):
        """Test successful agent processing"""
        mock_instance = Mock()
        mock_instance.process_message.return_value = {
            'success': True,
            'response': 'test response',
            'source': 'agent_core'
        }
        mock_integration.return_value = mock_instance
        
        result = self.fallback._process_with_agent_fallback("test message")
        
        self.assertTrue(result.get('success'))
        self.assertEqual(result.get('source'), 'agent_core')
    
    @patch('core.enhanced_fallback_system.IALCTLAgentIntegration')
    @patch('core.enhanced_fallback_system.CognitiveEngine')
    def test_agent_fallback_to_nlp(self, mock_cognitive, mock_integration):
        """Test fallback from agent to NLP"""
        # Mock agent failure
        mock_instance = Mock()
        mock_instance.process_message.return_value = {
            'success': False,
            'error': 'agent failed'
        }
        mock_integration.return_value = mock_instance
        
        # Mock cognitive success
        mock_cognitive_instance = Mock()
        mock_cognitive_instance.process_intent.return_value = "nlp response"
        mock_cognitive.return_value = mock_cognitive_instance
        
        result = self.fallback._process_with_agent_fallback("test message")
        
        self.assertTrue(result.get('success'))
        self.assertEqual(result.get('source'), 'fallback_cognitive')

def run_tests():
    """Run all tests"""
    print("🧪 Running IAL Core Components Tests")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestIntentParser,
        TestRiskClassifier,
        TestCostGuardrails,
        TestDriftDetector,
        TestMCPOrchestrator,
        TestEnhancedFallbackSystem
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Tests run: {result.testsRun}")
    print(f"✅ Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failures: {len(result.failures)}")
    print(f"💥 Errors: {len(result.errors)}")
    print(f"⏭️ Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    return len(result.failures) + len(result.errors) == 0

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
