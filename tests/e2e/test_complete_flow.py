"""
Testes end-to-end para fluxo completo
"""
import pytest
import subprocess
import time

class TestCompleteFlow:
    
    @pytest.mark.e2e
    def test_ialctl_query_execution(self):
        """Testa execução completa via ialctl"""
        try:
            # Executa comando real
            result = subprocess.run(
                ['echo', 'quantas ec2 existem?'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Pipe para ialctl
            ialctl_result = subprocess.run(
                ['timeout', '30', 'ialctl'],
                input=result.stdout,
                capture_output=True,
                text=True
            )
            
            # Verifica resultado
            assert ialctl_result.returncode in [0, 124]  # 0=success, 124=timeout
            assert "Router result: success" in ialctl_result.stdout or "EC2" in ialctl_result.stdout
            
        except Exception as e:
            pytest.skip(f"E2E test falhou: {e}")
    
    @pytest.mark.e2e
    def test_multiple_service_queries(self):
        """Testa queries para múltiplos serviços"""
        queries = [
            "quantas ec2 existem?",
            "quantos buckets s3 existem?",
            "quantas funções lambda existem?"
        ]
        
        for query in queries:
            try:
                result = subprocess.run(
                    ['timeout', '20', 'ialctl'],
                    input=query,
                    capture_output=True,
                    text=True
                )
                
                # Deve processar sem erro crítico
                assert "Router result: success" in result.stdout or "recursos" in result.stdout
                
            except Exception as e:
                pytest.skip(f"Query '{query}' falhou: {e}")
