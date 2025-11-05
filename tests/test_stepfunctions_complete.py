#!/usr/bin/env python3
"""
Complete Step Functions Integration Tests
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from core.stepfunctions_integration import IALStepFunctionsIntegration

class TestIALStepFunctionsIntegration:
    
    def test_initialization_with_all_features_enabled(self):
        """Test initialization with all Step Functions features enabled"""
        mock_config = {
            "migration": {
                "feature_flags": {
                    "healing_orchestrator_sf": True,
                    "phase_manager_sf": True,
                    "audit_validator_sf": True
                }
            }
        }
        
        with patch.object(IALStepFunctionsIntegration, '_load_config', return_value=mock_config):
            with patch('core.graph.healing_orchestrator_stepfunctions.StepFunctionsHealingOrchestrator'):
                with patch('scripts.phase_manager_stepfunctions.StepFunctionsPhaseManager'):
                    with patch('core.audit_validator_stepfunctions.StepFunctionsAuditValidator'):
                        integration = IALStepFunctionsIntegration()
                        
                        assert integration.healing_orchestrator is not None
                        assert integration.phase_manager is not None
                        assert integration.audit_validator is not None
    
    def test_initialization_with_features_disabled(self):
        """Test initialization with Step Functions features disabled"""
        mock_config = {
            "migration": {
                "feature_flags": {
                    "healing_orchestrator_sf": False,
                    "phase_manager_sf": False,
                    "audit_validator_sf": False
                }
            }
        }
        
        with patch.object(IALStepFunctionsIntegration, '_load_config', return_value=mock_config):
            integration = IALStepFunctionsIntegration()
            
            assert integration.healing_orchestrator is None
            assert integration.phase_manager is None
            assert integration.audit_validator is None
    
    def test_orchestrate_healing_stepfunctions(self):
        """Test healing orchestration using Step Functions"""
        mock_config = {
            "migration": {
                "feature_flags": {
                    "healing_orchestrator_sf": True,
                    "phase_manager_sf": False,
                    "audit_validator_sf": False
                }
            }
        }
        
        with patch.object(IALStepFunctionsIntegration, '_load_config', return_value=mock_config):
            with patch('core.graph.healing_orchestrator_stepfunctions.StepFunctionsHealingOrchestrator') as mock_class:
                mock_orchestrator = Mock()
                mock_orchestrator.orchestrate_healing.return_value = {
                    "status": "started",
                    "execution_arn": "test-arn"
                }
                mock_class.return_value = mock_orchestrator
                
                integration = IALStepFunctionsIntegration()
                result = integration.orchestrate_healing(["resource-1"])
                
                assert result["status"] == "started"
                assert "execution_arn" in result
                mock_orchestrator.orchestrate_healing.assert_called_once_with(["resource-1"])
    
    def test_orchestrate_healing_fallback(self):
        """Test healing orchestration fallback to legacy"""
        mock_config = {
            "migration": {
                "feature_flags": {
                    "healing_orchestrator_sf": False,
                    "phase_manager_sf": False,
                    "audit_validator_sf": False
                }
            }
        }
        
        with patch.object(IALStepFunctionsIntegration, '_load_config', return_value=mock_config):
            with patch('core.graph.healing_orchestrator.GraphBasedHealingOrchestrator') as mock_class:
                mock_orchestrator = Mock()
                mock_orchestrator.orchestrate_healing.return_value = {
                    "status": "completed",
                    "healed_resources": []
                }
                mock_class.return_value = mock_orchestrator
                
                integration = IALStepFunctionsIntegration()
                result = integration.orchestrate_healing(["resource-1"])
                
                assert result["status"] == "completed"
                mock_orchestrator.orchestrate_healing.assert_called_once_with(["resource-1"])
    
    def test_execute_phases_stepfunctions(self):
        """Test phase execution using Step Functions"""
        mock_config = {
            "migration": {
                "feature_flags": {
                    "healing_orchestrator_sf": False,
                    "phase_manager_sf": True,
                    "audit_validator_sf": False
                }
            }
        }
        
        with patch.object(IALStepFunctionsIntegration, '_load_config', return_value=mock_config):
            with patch('scripts.phase_manager_stepfunctions.StepFunctionsPhaseManager') as mock_class:
                mock_manager = Mock()
                mock_manager.execute_phases.return_value = {
                    "status": "started",
                    "execution_arn": "test-arn"
                }
                mock_class.return_value = mock_manager
                
                integration = IALStepFunctionsIntegration()
                result = integration.execute_phases()
                
                assert result["status"] == "started"
                mock_manager.execute_phases.assert_called_once()
    
    def test_validate_audit_stepfunctions(self):
        """Test audit validation using Step Functions"""
        mock_config = {
            "migration": {
                "feature_flags": {
                    "healing_orchestrator_sf": False,
                    "phase_manager_sf": False,
                    "audit_validator_sf": True
                }
            }
        }
        
        with patch.object(IALStepFunctionsIntegration, '_load_config', return_value=mock_config):
            with patch('core.audit_validator_stepfunctions.StepFunctionsAuditValidator') as mock_class:
                mock_validator = Mock()
                mock_validator.validate_completeness_with_enforcement.return_value = {
                    "status": "started",
                    "execution_arn": "test-arn"
                }
                mock_class.return_value = mock_validator
                
                integration = IALStepFunctionsIntegration()
                result = integration.validate_audit()
                
                assert result["status"] == "started"
                mock_validator.validate_completeness_with_enforcement.assert_called_once()
    
    def test_get_execution_status(self):
        """Test execution status retrieval"""
        with patch('boto3.client') as mock_boto:
            mock_sf = Mock()
            mock_sf.describe_execution.return_value = {
                "status": "SUCCEEDED",
                "startDate": "2023-01-01T00:00:00Z",
                "output": '{"result": "success"}'
            }
            mock_boto.return_value = mock_sf
            
            integration = IALStepFunctionsIntegration()
            result = integration.get_execution_status("test-arn")
            
            assert result["status"] == "SUCCEEDED"
            assert "start_date" in result
    
    def test_health_check_all_enabled(self):
        """Test health check with all components enabled"""
        mock_config = {
            "migration": {
                "feature_flags": {
                    "healing_orchestrator_sf": True,
                    "phase_manager_sf": True,
                    "audit_validator_sf": True
                }
            }
        }
        
        with patch.object(IALStepFunctionsIntegration, '_load_config', return_value=mock_config):
            with patch('core.graph.healing_orchestrator_stepfunctions.StepFunctionsHealingOrchestrator'):
                with patch('scripts.phase_manager_stepfunctions.StepFunctionsPhaseManager'):
                    with patch('core.audit_validator_stepfunctions.StepFunctionsAuditValidator'):
                        integration = IALStepFunctionsIntegration()
                        health = integration.health_check()
                        
                        assert health["overall_status"] == "healthy"
                        assert health["components"]["healing_orchestrator"]["status"] == "enabled"
                        assert health["components"]["phase_manager"]["status"] == "enabled"
                        assert health["components"]["audit_validator"]["status"] == "enabled"
    
    def test_health_check_all_disabled(self):
        """Test health check with all components disabled"""
        mock_config = {
            "migration": {
                "feature_flags": {
                    "healing_orchestrator_sf": False,
                    "phase_manager_sf": False,
                    "audit_validator_sf": False
                }
            }
        }
        
        with patch.object(IALStepFunctionsIntegration, '_load_config', return_value=mock_config):
            integration = IALStepFunctionsIntegration()
            health = integration.health_check()
            
            assert health["overall_status"] == "healthy"
            assert health["components"]["healing_orchestrator"]["status"] == "disabled"
            assert health["components"]["phase_manager"]["status"] == "disabled"
            assert health["components"]["audit_validator"]["status"] == "disabled"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
