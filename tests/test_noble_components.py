#!/usr/bin/env python3
"""
Testes Automatizados para Componentes Nobres do IAL
Cobertura das áreas críticas pós-AgentCore integration
"""

import unittest
import sys
import os
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock

# Adicionar path do IAL
sys.path.insert(0, '/home/ial')

class TestIntentParser(unittest.TestCase):
    """Testes para Intent Parser"""
    
    def setUp(self):
        from core.intent_validation.intent_parser import IntentParser
        self.parser = IntentParser()
    
    def test_parse_deployment_intent(self):
        """Testa parsing de intent de deployment"""
        intent = "deploy a web application with database"
        result = self.parser.parse_intent(intent)
        
        self.assertIsInstance(result, dict)
        self.assertIn('intent_type', result)
        self.assertIn('entities', result)
        self.assertEqual(result['intent_type'], 'deployment')
    
    def test_parse_cost_intent(self):
        """Testa parsing de intent de custo"""
        intent = "analyze costs for last month"
        result = self.parser.parse_intent(intent)
        
        self.assertEqual(result['intent_type'], 'cost_analysis')
        self.assertIn('time_period', result['entities'])
    
    def test_parse_security_intent(self):
        """Testa parsing de intent de segurança"""
        intent = "check security vulnerabilities"
        result = self.parser.parse_intent(intent)
        
        self.assertEqual(result['intent_type'], 'security_analysis')
    
    def test_invalid_intent(self):
        """Testa handling de intent inválido"""
        intent = ""
        result = self.parser.parse_intent(intent)
        
        self.assertEqual(result['intent_type'], 'unknown')

class TestRiskClassifier(unittest.TestCase):
    """Testes para Risk Classifier"""
    
    def setUp(self):
        from core.drift.risk_classifier import RiskClassifier
        self.classifier = RiskClassifier()
    
    def test_classify_low_risk(self):
        """Testa classificação de baixo risco"""
        change = {
            'resource_type': 'AWS::S3::Bucket',
            'change_type': 'tag_update',
            'impact_scope': 'single_resource'
        }
        
        risk = self.classifier.classify_risk(change)
        self.assertEqual(risk['level'], 'LOW')
    
    def test_classify_high_risk(self):
        """Testa classificação de alto risco"""
        change = {
            'resource_type': 'AWS::RDS::DBInstance',
            'change_type': 'deletion',
            'impact_scope': 'multi_resource'
        }
        
        risk = self.classifier.classify_risk(change)
        self.assertEqual(risk['level'], 'HIGH')
    
    def test_classify_critical_risk(self):
        """Testa classificação de risco crítico"""
        change = {
            'resource_type': 'AWS::IAM::Role',
            'change_type': 'policy_change',
            'impact_scope': 'account_wide'
        }
        
        risk = self.classifier.classify_risk(change)
        self.assertEqual(risk['level'], 'CRITICAL')

class TestCostGuardrails(unittest.TestCase):
    """Testes para Cost Guardrails"""
    
    def setUp(self):
        from core.cost_guardrails import CostGuardrails
        self.guardrails = CostGuardrails()
    
    def test_validate_within_budget(self):
        """Testa validação dentro do orçamento"""
        deployment = {
            'estimated_cost': 100.0,
            'resources': ['t3.micro', 's3.standard']
        }
        
        result = self.guardrails.validate_deployment(deployment)
        self.assertTrue(result['approved'])
    
    def test_validate_exceeds_budget(self):
        """Testa validação que excede orçamento"""
        deployment = {
            'estimated_cost': 10000.0,
            'resources': ['r5.24xlarge', 'rds.r5.24xlarge']
        }
        
        result = self.guardrails.validate_deployment(deployment)
        self.assertFalse(result['approved'])
        self.assertIn('budget_exceeded', result['reasons'])
    
    def test_validate_prohibited_resources(self):
        """Testa validação de recursos proibidos"""
        deployment = {
            'estimated_cost': 50.0,
            'resources': ['p3.16xlarge']  # GPU instance
        }
        
        result = self.guardrails.validate_deployment(deployment)
        self.assertFalse(result['approved'])
        self.assertIn('prohibited_resource', result['reasons'])

class TestDriftDetector(unittest.TestCase):
    """Testes para Drift Detector"""
    
    def setUp(self):
        from core.drift.drift_detector import DriftDetector
        self.detector = DriftDetector()
    
    @patch('boto3.client')
    def test_detect_no_drift(self, mock_boto):
        """Testa detecção sem drift"""
        # Mock AWS response
        mock_client = Mock()
        mock_client.describe_stacks.return_value = {
            'Stacks': [{
                'StackStatus': 'UPDATE_COMPLETE',
                'DriftInformation': {'StackDriftStatus': 'IN_SYNC'}
            }]
        }
        mock_boto.return_value = mock_client
        
        result = self.detector.detect_drift('test-stack')
        self.assertEqual(result['drift_status'], 'IN_SYNC')
    
    @patch('boto3.client')
    def test_detect_drift_present(self, mock_boto):
        """Testa detecção com drift"""
        mock_client = Mock()
        mock_client.describe_stacks.return_value = {
            'Stacks': [{
                'StackStatus': 'UPDATE_COMPLETE',
                'DriftInformation': {'StackDriftStatus': 'DRIFTED'}
            }]
        }
        mock_boto.return_value = mock_client
        
        result = self.detector.detect_drift('test-stack')
        self.assertEqual(result['drift_status'], 'DRIFTED')

class TestMCPOrchestrator(unittest.TestCase):
    """Testes para MCP Orchestrator (mockado)"""
    
    def setUp(self):
        from core.mcp_orchestrator import MCPOrchestrator
        self.orchestrator = MCPOrchestrator()
    
    @patch('core.mcp_orchestrator.MCPOrchestrator._execute_mcp_call')
    def test_orchestrate_single_mcp(self, mock_execute):
        """Testa orquestração de MCP único"""
        mock_execute.return_value = {'success': True, 'data': 'test'}
        
        result = self.orchestrator.orchestrate(['aws-api'], 'test command')
        self.assertTrue(result['success'])
    
    @patch('core.mcp_orchestrator.MCPOrchestrator._execute_mcp_call')
    def test_orchestrate_multiple_mcps(self, mock_execute):
        """Testa orquestração de múltiplos MCPs"""
        mock_execute.return_value = {'success': True, 'data': 'test'}
        
        result = self.orchestrator.orchestrate(['aws-api', 'cloudwatch'], 'test command')
        self.assertTrue(result['success'])
        self.assertEqual(len(result['mcp_results']), 2)
    
    @patch('core.mcp_orchestrator.MCPOrchestrator._execute_mcp_call')
    def test_orchestrate_with_failure(self, mock_execute):
        """Testa orquestração com falha"""
        mock_execute.side_effect = Exception("MCP connection failed")
        
        result = self.orchestrator.orchestrate(['aws-api'], 'test command')
        self.assertFalse(result['success'])
        self.assertIn('error', result)

class TestNLPFallback(unittest.TestCase):
    """Testes para NLP Fallback"""
    
    def setUp(self):
        from core.cognitive_engine import CognitiveEngine
        self.engine = CognitiveEngine()
    
    def test_process_simple_intent(self):
        """Testa processamento de intent simples"""
        result = self.engine.process_intent("create s3 bucket")
        
        self.assertIsInstance(result, dict)
        self.assertIn('intent_type', result)
        self.assertIn('response', result)
    
    def test_process_complex_intent(self):
        """Testa processamento de intent complexo"""
        intent = "deploy a web application with load balancer and database"
        result = self.engine.process_intent(intent)
        
        self.assertIsInstance(result, dict)
        self.assertTrue(len(result.get('phases', [])) > 1)
    
    def test_fallback_availability(self):
        """Testa disponibilidade do fallback"""
        self.assertTrue(self.engine.is_available())

class TestEnhancedFallbackSystem(unittest.TestCase):
    """Testes para Enhanced Fallback System"""
    
    def setUp(self):
        from core.enhanced_fallback_system import EnhancedFallbackSystem, ProcessingMode
        self.system = EnhancedFallbackSystem()
        self.ProcessingMode = ProcessingMode
    
    def test_determine_sandbox_mode(self):
        """Testa determinação do modo sandbox"""
        flags = {'sandbox': True}
        mode = self.system.determine_processing_mode("test", flags)
        self.assertEqual(mode, self.ProcessingMode.SANDBOX)
    
    def test_determine_offline_mode(self):
        """Testa determinação do modo offline"""
        flags = {'offline': True}
        mode = self.system.determine_processing_mode("test", flags)
        self.assertEqual(mode, self.ProcessingMode.FALLBACK_NLP)
    
    @patch.dict(os.environ, {'IAL_MODE': 'sandbox'})
    def test_sandbox_environment_variable(self):
        """Testa modo sandbox via variável de ambiente"""
        flags = {}
        mode = self.system.determine_processing_mode("test", flags)
        self.assertEqual(mode, self.ProcessingMode.SANDBOX)
    
    def test_telemetry_logging(self):
        """Testa logging de telemetria"""
        self.system._log_event("test_event", {"test": "data"})
        self.assertEqual(len(self.system.telemetry_events), 1)
        
        event = self.system.telemetry_events[0]
        self.assertEqual(event.event_type, "test_event")
        self.assertEqual(event.data["test"], "data")

class TestAgentCoreIntegration(unittest.TestCase):
    """Testes para integração com Agent Core"""
    
    def setUp(self):
        try:
            from core.bedrock_agent_core import BedrockAgentCore
            self.agent_available = True
        except ImportError:
            self.agent_available = False
    
    def test_agent_core_availability(self):
        """Testa disponibilidade do Agent Core"""
        if self.agent_available:
            from core.bedrock_agent_core import BedrockAgentCore
            agent = BedrockAgentCore()
            self.assertIsNotNone(agent)
    
    @unittest.skipIf(not os.environ.get('AWS_ACCESS_KEY_ID'), "AWS credentials not available")
    def test_agent_core_invocation(self):
        """Testa invocação do Agent Core (apenas se credenciais disponíveis)"""
        if self.agent_available:
            from core.bedrock_agent_core import BedrockAgentCore
            agent = BedrockAgentCore()
            
            # Teste básico de conectividade
            try:
                result = agent.invoke_agent("test connection", session_id="test-session")
                self.assertIsInstance(result, dict)
            except Exception as e:
                # Esperado se não houver agent configurado
                self.assertIn("agent", str(e).lower())

def run_noble_tests():
    """Executa todos os testes dos componentes nobres"""
    
    # Criar suite de testes
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Adicionar classes de teste
    test_classes = [
        TestIntentParser,
        TestRiskClassifier,
        TestCostGuardrails,
        TestDriftDetector,
        TestMCPOrchestrator,
        TestNLPFallback,
        TestEnhancedFallbackSystem,
        TestAgentCoreIntegration
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Executar testes
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Relatório final
    print("\n" + "="*60)
    print("🧪 RELATÓRIO DE TESTES DOS COMPONENTES NOBRES")
    print("="*60)
    print(f"✅ Testes executados: {result.testsRun}")
    print(f"❌ Falhas: {len(result.failures)}")
    print(f"⚠️  Erros: {len(result.errors)}")
    print(f"⏭️  Pulados: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\n❌ FALHAS:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\n⚠️  ERROS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100
    print(f"\n📊 Taxa de sucesso: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 COMPONENTES NOBRES VALIDADOS COM SUCESSO!")
    else:
        print("⚠️  ALGUNS COMPONENTES PRECISAM DE ATENÇÃO")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_noble_tests()
    sys.exit(0 if success else 1)
