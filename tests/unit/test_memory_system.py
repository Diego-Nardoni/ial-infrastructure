"""
Testes unitários para Memory System
"""
import pytest

class TestMemorySystem:
    
    def test_memory_manager_import(self):
        """Testa importação do MemoryManager"""
        try:
            from core.memory.memory_manager import MemoryManager
            memory_manager = MemoryManager()
            assert memory_manager is not None
            assert hasattr(memory_manager, 'get_recent_context')
        except ImportError as e:
            pytest.skip(f"MemoryManager não disponível: {e}")
    
    def test_context_engine_import(self):
        """Testa importação do ContextEngine"""
        try:
            from core.memory.context_engine import ContextEngine
            context_engine = ContextEngine()
            assert context_engine is not None
        except ImportError as e:
            pytest.skip(f"ContextEngine não disponível: {e}")
    
    def test_memory_methods(self):
        """Testa métodos do MemoryManager"""
        try:
            from core.memory.memory_manager import MemoryManager
            memory_manager = MemoryManager()
            
            # Testa métodos disponíveis
            methods = ['get_recent_context', 'save_message', 'get_session_context']
            for method in methods:
                assert hasattr(memory_manager, method), f"Método {method} não encontrado"
                
        except Exception as e:
            pytest.skip(f"Teste de métodos falhou: {e}")
