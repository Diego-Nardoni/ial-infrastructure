#!/usr/bin/env python3
"""
Tests for Step Functions integration
"""

import pytest
import json
from unittest.mock import Mock, patch
from core.graph.healing_orchestrator_stepfunctions import StepFunctionsHealingOrchestrator, HealingInitializer
from scripts.phase_manager_stepfunctions import StepFunctionsPhaseManager, PhaseDiscoverer

class TestStepFunctionsHealingOrchestrator:
    
    def test_orchestrate_healing_success(self):
        """Test successful healing orchestration"""
        with patch('boto3.client') as mock_boto:
            mock_sf = Mock()
            mock_sf.start_execution.return_value = {
                "executionArn": "arn:aws:states:us-east-1:123456789012:execution:test"
            }
            mock_boto.return_value = mock_sf
            
            orchestrator = StepFunctionsHealingOrchestrator()
            result = orchestrator.orchestrate_healing(["resource-1", "resource-2"])
            
            assert result["status"] == "started"
            assert "execution_arn" in result
            assert "correlation_id" in result
            mock_sf.start_execution.assert_called_once()
    
    def test_get_execution_status(self):
        """Test execution status retrieval"""
        with patch('boto3.client') as mock_boto:
            mock_sf = Mock()
            mock_sf.describe_execution.return_value = {
                "status": "SUCCEEDED",
                "output": '{"status": "completed"}',
                "startDate": "2023-01-01T00:00:00Z"
            }
            mock_boto.return_value = mock_sf
            
            orchestrator = StepFunctionsHealingOrchestrator()
            result = orchestrator.get_execution_status("test-arn")
            
            assert result["status"] == "SUCCEEDED"
            assert result["output"]["status"] == "completed"

class TestHealingInitializer:
    
    def test_lambda_handler_with_resources(self):
        """Test healing initializer with resources"""
        with patch('core.graph.dependency_graph.DependencyGraph') as mock_graph:
            mock_instance = Mock()
            mock_instance.nodes = {"resource-1": Mock()}
            mock_instance.get_healing_order.return_value = ["resource-1", "resource-2"]
            mock_graph.return_value = mock_instance
            
            initializer = HealingInitializer()
            event = {"failed_resources": ["resource-1"]}
            
            result = initializer.lambda_handler(event, None)
            
            assert result["has_resources"] is True
            assert len(result["healing_batches"]) > 0
            assert result["total_resources"] == 2
    
    def test_lambda_handler_no_resources(self):
        """Test healing initializer with no resources"""
        with patch('core.graph.dependency_graph.DependencyGraph') as mock_graph:
            mock_instance = Mock()
            mock_instance.get_healing_order.return_value = []
            mock_graph.return_value = mock_instance
            
            initializer = HealingInitializer()
            event = {"failed_resources": []}
            
            result = initializer.lambda_handler(event, None)
            
            assert result["has_resources"] is False
            assert result["total_resources"] == 0

class TestStepFunctionsPhaseManager:
    
    def test_execute_phases_success(self):
        """Test successful phase execution"""
        with patch('boto3.client') as mock_boto:
            mock_sf = Mock()
            mock_sf.start_execution.return_value = {
                "executionArn": "arn:aws:states:us-east-1:123456789012:execution:test"
            }
            mock_boto.return_value = mock_sf
            
            manager = StepFunctionsPhaseManager()
            result = manager.execute_phases()
            
            assert result["status"] == "started"
            assert "execution_arn" in result
            mock_sf.start_execution.assert_called_once()

class TestPhaseDiscoverer:
    
    def test_lambda_handler(self):
        """Test phase discovery"""
        with patch('pathlib.Path') as mock_path:
            # Mock directory structure
            mock_phases_dir = Mock()
            mock_domain_dir = Mock()
            mock_domain_dir.is_dir.return_value = True
            mock_domain_dir.name = "00-foundation"
            
            mock_yaml_file = Mock()
            mock_yaml_file.stem = "test-phase"
            mock_yaml_file.name = "test-phase.yaml"
            
            mock_domain_dir.glob.return_value = [mock_yaml_file]
            mock_phases_dir.iterdir.return_value = [mock_domain_dir]
            
            mock_path.return_value = mock_phases_dir
            
            discoverer = PhaseDiscoverer()
            result = discoverer.lambda_handler({}, None)
            
            assert "discovered_phases" in result
            assert "00-foundation" in result["discovered_phases"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
