#!/usr/bin/env python3
"""
Testes para Feature Flags
"""

import pytest
from unittest.mock import Mock, patch
from core.feature_flags_manager import FeatureFlagsManager, is_feature_enabled
from core.integrations.drift_integration import DriftIntegration

class TestFeatureFlagsManager:
    
    def setup_method(self):
        self.manager = FeatureFlagsManager()
    
    def test_default_states(self):
        """Teste: Estados padrão das features"""
        # Core features should be enabled by default
        assert self.manager._get_default_state("drift_detection") == True
        assert self.manager._get_default_state("auto_healing") == True
        
        # Advanced features should be disabled by default
        assert self.manager._get_default_state("llm_prioritization") == False
        assert self.manager._get_default_state("experimental_features") == False
    
    def test_is_enabled_fallback(self):
        """Teste: Fallback quando DynamoDB não disponível"""
        # Simulate no table available
        manager = FeatureFlagsManager()
        manager.table = None
        
        # Should return default states
        assert manager.is_enabled("drift_detection") == True
        assert manager.is_enabled("experimental_features") == False
    
    @patch('boto3.resource')
    def test_set_flag(self, mock_boto):
        """Teste: Definir feature flag"""
        mock_table = Mock()
        mock_boto.return_value.Table.return_value = mock_table
        
        manager = FeatureFlagsManager()
        manager.table = mock_table
        
        result = manager.set_flag("test_feature", True, "test_scope", "test reason")
        
        assert result["flag_name"] == "test_feature"
        assert result["state"] == "enabled"
        assert result["scope"] == "test_scope"
        mock_table.put_item.assert_called_once()

class TestDriftIntegration:
    
    def setup_method(self):
        self.integration = DriftIntegration()
    
    def test_should_detect_drift(self):
        """Teste: Verificação se deve detectar drift"""
        # Mock feature flags
        self.integration.feature_flags.is_enabled = Mock(return_value=True)
        self.integration.feature_flags.is_drift_enabled = Mock(return_value=True)
        
        result = self.integration.should_detect_drift("test_scope")
        assert result == True
    
    def test_should_not_detect_drift_global_disabled(self):
        """Teste: Não deve detectar drift se globalmente desabilitado"""
        self.integration.feature_flags.is_enabled = Mock(return_value=False)
        
        result = self.integration.should_detect_drift("test_scope")
        assert result == False
    
    def test_get_drift_config(self):
        """Teste: Obter configuração de drift"""
        # Mock methods
        self.integration.should_detect_drift = Mock(return_value=True)
        self.integration.should_auto_heal = Mock(return_value=False)
        
        mock_state = Mock()
        mock_state.value = "PAUSED"
        self.integration.feature_flags.drift_flag.get_drift_state = Mock(return_value=mock_state)
        
        config = self.integration.get_drift_config("test_scope")
        
        assert config["detect_enabled"] == True
        assert config["auto_heal_enabled"] == False
        assert config["drift_state"] == "PAUSED"
        assert config["scope"] == "test_scope"

def test_convenience_functions():
    """Teste: Funções de conveniência"""
    with patch('core.feature_flags_manager.get_feature_flags') as mock_get:
        mock_manager = Mock()
        mock_manager.is_enabled.return_value = True
        mock_get.return_value = mock_manager
        
        result = is_feature_enabled("test_feature")
        assert result == True
        mock_manager.is_enabled.assert_called_with("test_feature", "global")

if __name__ == '__main__':
    pytest.main([__file__])
