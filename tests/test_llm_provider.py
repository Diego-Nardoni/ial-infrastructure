#!/usr/bin/env python3
"""
Testes para LLMProvider
"""

import sys
import asyncio
sys.path.append('/home/ial')

async def test_llm_provider_basic():
    """Testa carregamento básico do LLMProvider"""
    try:
        from core.llm_provider import LLMProvider
        provider = LLMProvider()
        print(f"✅ LLMProvider carregado: {provider.current_provider}")
        print(f"✅ Fallback order: {provider.fallback_order}")
        print(f"✅ Circuit breakers: {list(provider.circuit_breakers.keys())}")
        return True
    except Exception as e:
        print(f"❌ LLMProvider falhou: {e}")
        return False

async def test_llm_async_processing():
    """Testa processamento async"""
    try:
        from core.llm_provider import LLMProvider
        provider = LLMProvider()
        
        result = await provider.process_natural_language_async("Create ECS cluster with RDS")
        print(f"✅ Processamento async OK: {result['provider']}")
        print(f"✅ Entities detectadas: {result['entities']}")
        print(f"✅ Confidence: {result['confidence']}")
        return True
    except Exception as e:
        print(f"❌ Processamento async falhou: {e}")
        return False

async def test_circuit_breaker():
    """Testa circuit breaker"""
    try:
        from core.circuit_breaker import CircuitBreaker
        cb = CircuitBreaker(failure_threshold=2, timeout=1, name="test")
        
        # Test normal operation
        assert cb.can_execute() == True
        cb.record_success()
        
        # Test failure
        cb.record_failure()
        cb.record_failure()  # Should open circuit
        
        metrics = cb.get_metrics()
        print(f"✅ Circuit breaker OK: {metrics['state']}")
        return True
    except Exception as e:
        print(f"❌ Circuit breaker falhou: {e}")
        return False

async def main():
    print("🧪 TESTANDO LLMProvider...")
    
    tests = [
        test_llm_provider_basic,
        test_llm_async_processing,
        test_circuit_breaker
    ]
    
    passed = 0
    for test in tests:
        if await test():
            passed += 1
    
    print(f"\n📊 RESULTADO: {passed}/{len(tests)} testes passaram")
    
    if passed == len(tests):
        print("✅ LLMProvider VALIDADO - FASE 2.1 COMPLETA")
    else:
        print("❌ LLMProvider COM PROBLEMAS")

if __name__ == "__main__":
    asyncio.run(main())
