"""
Configuração global dos testes IAL
"""
import pytest
import os
import sys

# Adicionar path do IAL
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture(scope="session")
def ial_config():
    """Configuração base do IAL para testes"""
    return {
        'aws_region': 'us-east-1',
        'test_mode': True,
        'debug': True
    }

@pytest.fixture
def mock_aws():
    """Mock básico para AWS APIs"""
    from unittest.mock import MagicMock
    return MagicMock()
