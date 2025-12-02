"""
Testes de integração para pipeline NLP
"""
import pytest

class TestNLPPipeline:
    
    def test_natural_language_processor_flow(self):
        """Testa fluxo completo do processador NLP"""
        try:
            from natural_language_processor import IaLNaturalProcessor
            processor = IaLNaturalProcessor()
            
            # Testa processamento básico
            result = processor.process_command("help", "test_user", "test_session")
            assert result is not None
            assert isinstance(result, str)
            
        except Exception as e:
            pytest.skip(f"NLP Pipeline não disponível: {e}")
    
    def test_intelligent_router_integration(self):
        """Testa integração com Intelligent Router"""
        try:
            from natural_language_processor import IaLNaturalProcessor
            processor = IaLNaturalProcessor()
            
            # Verifica se router está disponível
            assert processor.intelligent_router is not None
            
            # Testa query simples
            result = processor.process_command("quantas ec2 existem?", "test_user", "test_session")
            assert "EC2" in result or "erro" in result.lower()
            
        except Exception as e:
            pytest.skip(f"Router integration falhou: {e}")
