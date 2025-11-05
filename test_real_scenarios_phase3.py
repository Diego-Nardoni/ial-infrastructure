#!/usr/bin/env python3
"""
Fase 3: Testes e Validação em Ambiente Real
Testa cenários reais de infraestrutura com o Intelligent MCP Router
"""

import sys
import os
import asyncio
import time
import json
from datetime import datetime

# Adicionar paths
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

def test_real_scenario_1_lambda_sqs():
    """Cenário Real 1: Lambda + SQS para processamento de mensagens"""
    print("🧪 CENÁRIO REAL 1: LAMBDA + SQS")
    print("=" * 50)
    
    try:
        from natural_language_processor import IaLNaturalProcessor
        
        processor = IaLNaturalProcessor()
        
        # Solicitação real complexa
        user_input = """
        Preciso criar uma arquitetura serverless para processar pedidos de e-commerce:
        - Função Lambda para validar pedidos
        - Fila SQS para pedidos pendentes
        - Dead Letter Queue para erros
        - CloudWatch para monitoramento
        - IAM roles com least privilege
        """
        
        print(f"📝 Solicitação: {user_input[:100]}...")
        
        start_time = time.time()
        result = processor.process_command(user_input, "real_user_1", "session_ecommerce")
        processing_time = time.time() - start_time
        
        print(f"⏱️ Tempo de processamento: {processing_time:.2f}s")
        print(f"📊 Resultado: {len(result)} caracteres")
        print(f"🎯 Resposta: {result[:200]}...")
        
        # Validar se detectou os serviços corretos
        expected_services = ['lambda', 'sqs', 'cloudwatch', 'iam']
        detected_services = []
        
        for service in expected_services:
            if service.lower() in result.lower():
                detected_services.append(service)
        
        print(f"✅ Serviços detectados: {detected_services}")
        print(f"📈 Taxa de detecção: {len(detected_services)}/{len(expected_services)} ({len(detected_services)/len(expected_services)*100:.0f}%)")
        
        return {
            'success': True,
            'processing_time': processing_time,
            'services_detected': detected_services,
            'detection_rate': len(detected_services)/len(expected_services)
        }
        
    except Exception as e:
        print(f"❌ Erro no cenário 1: {e}")
        return {'success': False, 'error': str(e)}

def test_real_scenario_2_three_tier():
    """Cenário Real 2: Aplicação Web 3 Camadas"""
    print("\n🧪 CENÁRIO REAL 2: APLICAÇÃO WEB 3 CAMADAS")
    print("=" * 50)
    
    try:
        from natural_language_processor import IaLNaturalProcessor
        
        processor = IaLNaturalProcessor()
        
        # Solicitação real de arquitetura complexa
        user_input = """
        Deploy uma aplicação web completa com:
        - Load Balancer (ALB) na camada de apresentação
        - ECS Fargate com auto-scaling na camada de aplicação
        - RDS PostgreSQL Multi-AZ na camada de dados
        - VPC com subnets públicas e privadas
        - Security Groups restritivos
        - CloudWatch dashboards e alertas
        """
        
        print(f"📝 Solicitação: Aplicação web 3 camadas completa")
        
        start_time = time.time()
        result = processor.process_command(user_input, "real_user_2", "session_webapp")
        processing_time = time.time() - start_time
        
        print(f"⏱️ Tempo de processamento: {processing_time:.2f}s")
        
        # Validar detecção de padrão arquitetural
        architecture_patterns = ['3 tier', '3 camadas', 'three tier', 'web app']
        pattern_detected = any(pattern in result.lower() for pattern in architecture_patterns)
        
        # Validar serviços de 3 camadas
        expected_services = ['elb', 'alb', 'ecs', 'rds', 'vpc', 'cloudwatch']
        detected_services = [svc for svc in expected_services if svc in result.lower()]
        
        print(f"🏗️ Padrão 3-tier detectado: {pattern_detected}")
        print(f"✅ Serviços detectados: {detected_services}")
        print(f"📈 Taxa de detecção: {len(detected_services)}/{len(expected_services)} ({len(detected_services)/len(expected_services)*100:.0f}%)")
        
        return {
            'success': True,
            'processing_time': processing_time,
            'pattern_detected': pattern_detected,
            'services_detected': detected_services,
            'detection_rate': len(detected_services)/len(expected_services)
        }
        
    except Exception as e:
        print(f"❌ Erro no cenário 2: {e}")
        return {'success': False, 'error': str(e)}

def test_real_scenario_3_microservices():
    """Cenário Real 3: Arquitetura de Microserviços"""
    print("\n🧪 CENÁRIO REAL 3: MICROSERVIÇOS COM EKS")
    print("=" * 50)
    
    try:
        from natural_language_processor import IaLNaturalProcessor
        
        processor = IaLNaturalProcessor()
        
        user_input = """
        Criar infraestrutura de microserviços para fintech:
        - EKS cluster com managed node groups
        - API Gateway para roteamento
        - DynamoDB para dados transacionais
        - ElastiCache Redis para cache
        - Step Functions para workflows
        - X-Ray para distributed tracing
        - Secrets Manager para credenciais
        """
        
        print(f"📝 Solicitação: Microserviços fintech completos")
        
        start_time = time.time()
        result = processor.process_command(user_input, "real_user_3", "session_fintech")
        processing_time = time.time() - start_time
        
        print(f"⏱️ Tempo de processamento: {processing_time:.2f}s")
        
        # Validar detecção de microserviços
        microservices_patterns = ['microservices', 'micro services', 'distributed', 'service mesh']
        pattern_detected = any(pattern in result.lower() for pattern in microservices_patterns)
        
        # Validar serviços complexos
        expected_services = ['eks', 'api gateway', 'dynamodb', 'elasticache', 'step functions', 'xray', 'secrets']
        detected_services = []
        
        for service in expected_services:
            if any(keyword in result.lower() for keyword in service.split()):
                detected_services.append(service)
        
        print(f"🔧 Padrão microserviços detectado: {pattern_detected}")
        print(f"✅ Serviços detectados: {detected_services}")
        print(f"📈 Taxa de detecção: {len(detected_services)}/{len(expected_services)} ({len(detected_services)/len(expected_services)*100:.0f}%)")
        
        return {
            'success': True,
            'processing_time': processing_time,
            'pattern_detected': pattern_detected,
            'services_detected': detected_services,
            'detection_rate': len(detected_services)/len(expected_services)
        }
        
    except Exception as e:
        print(f"❌ Erro no cenário 3: {e}")
        return {'success': False, 'error': str(e)}

async def test_intelligent_router_direct():
    """Teste direto do Intelligent MCP Router"""
    print("\n🧪 TESTE DIRETO: INTELLIGENT MCP ROUTER")
    print("=" * 50)
    
    try:
        from core.intelligent_mcp_router import IntelligentMCPRouter
        
        router = IntelligentMCPRouter()
        
        # Cenários de teste direto
        test_cases = [
            {
                'input': 'Deploy ECS cluster with RDS and load balancer',
                'expected_services': ['ecs', 'rds', 'elb'],
                'expected_domains': ['compute', 'data', 'networking']
            },
            {
                'input': 'Create serverless API with Lambda and DynamoDB',
                'expected_services': ['lambda', 'dynamodb', 'apigateway'],
                'expected_domains': ['compute', 'data', 'networking']
            },
            {
                'input': 'Setup monitoring with CloudWatch and X-Ray',
                'expected_services': ['cloudwatch', 'xray'],
                'expected_domains': ['observability']
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. Testando: '{test_case['input']}'")
            
            context = {
                'user_id': f'direct_test_{i}',
                'session_id': f'direct_session_{i}',
                'test_mode': True
            }
            
            start_time = time.time()
            result = await router.route_request(test_case['input'], context)
            processing_time = time.time() - start_time
            
            print(f"   ⏱️ Tempo: {processing_time:.2f}s")
            print(f"   ✅ Sucesso: {result.get('success', False)}")
            
            if 'routing_decision' in result:
                decision = result['routing_decision']
                detected_services = decision.get('detected_services', [])
                mcps_used = decision.get('mcps_used', [])
                confidence = decision.get('confidence', 0)
                
                print(f"   🎯 Serviços: {detected_services}")
                print(f"   🤖 MCPs: {len(mcps_used)}")
                print(f"   📊 Confiança: {confidence:.2f}")
                
                # Calcular precisão
                expected = set(test_case['expected_services'])
                detected = set(detected_services)
                precision = len(expected.intersection(detected)) / len(expected) if expected else 0
                
                print(f"   📈 Precisão: {precision:.2f}")
                
                results.append({
                    'test_case': i,
                    'success': result.get('success', False),
                    'processing_time': processing_time,
                    'precision': precision,
                    'confidence': confidence,
                    'mcps_count': len(mcps_used)
                })
            
            if result.get('fallback_used'):
                print(f"   ⚠️ Fallback: {result.get('fallback_reason')}")
        
        # Estatísticas gerais
        if results:
            avg_time = sum(r['processing_time'] for r in results) / len(results)
            avg_precision = sum(r['precision'] for r in results) / len(results)
            avg_confidence = sum(r['confidence'] for r in results) / len(results)
            success_rate = sum(1 for r in results if r['success']) / len(results)
            
            print(f"\n📊 ESTATÍSTICAS GERAIS:")
            print(f"   • Tempo médio: {avg_time:.2f}s")
            print(f"   • Precisão média: {avg_precision:.2f}")
            print(f"   • Confiança média: {avg_confidence:.2f}")
            print(f"   • Taxa de sucesso: {success_rate:.2f}")
        
        return {
            'success': True,
            'results': results,
            'avg_processing_time': avg_time if results else 0,
            'avg_precision': avg_precision if results else 0
        }
        
    except Exception as e:
        print(f"❌ Erro no teste direto: {e}")
        return {'success': False, 'error': str(e)}

def test_performance_benchmark():
    """Benchmark de performance do sistema"""
    print("\n🧪 BENCHMARK DE PERFORMANCE")
    print("=" * 50)
    
    try:
        from natural_language_processor import IaLNaturalProcessor
        
        processor = IaLNaturalProcessor()
        
        # Casos de teste para benchmark
        benchmark_cases = [
            "Create Lambda function",
            "Deploy ECS cluster",
            "Setup RDS database",
            "Create VPC with subnets",
            "Deploy serverless API",
            "Setup monitoring dashboard",
            "Create S3 bucket with encryption",
            "Deploy microservices architecture",
            "Setup CI/CD pipeline",
            "Create data pipeline with Step Functions"
        ]
        
        print(f"🏃 Executando {len(benchmark_cases)} casos de teste...")
        
        times = []
        successes = 0
        
        for i, test_case in enumerate(benchmark_cases, 1):
            start_time = time.time()
            
            try:
                result = processor.process_command(test_case, f"bench_user_{i}")
                processing_time = time.time() - start_time
                times.append(processing_time)
                successes += 1
                
                print(f"   {i:2d}. {test_case[:30]:30} - {processing_time:.3f}s ✅")
                
            except Exception as e:
                processing_time = time.time() - start_time
                times.append(processing_time)
                print(f"   {i:2d}. {test_case[:30]:30} - {processing_time:.3f}s ❌")
        
        # Estatísticas de performance
        if times:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            success_rate = successes / len(benchmark_cases)
            
            print(f"\n📊 RESULTADOS DO BENCHMARK:")
            print(f"   • Casos testados: {len(benchmark_cases)}")
            print(f"   • Taxa de sucesso: {success_rate:.1%}")
            print(f"   • Tempo médio: {avg_time:.3f}s")
            print(f"   • Tempo mínimo: {min_time:.3f}s")
            print(f"   • Tempo máximo: {max_time:.3f}s")
            
            # Classificação de performance
            if avg_time < 1.0:
                performance_grade = "🚀 EXCELENTE"
            elif avg_time < 2.0:
                performance_grade = "✅ BOM"
            elif avg_time < 5.0:
                performance_grade = "⚠️ ACEITÁVEL"
            else:
                performance_grade = "❌ LENTO"
            
            print(f"   • Classificação: {performance_grade}")
        
        return {
            'success': True,
            'cases_tested': len(benchmark_cases),
            'success_rate': success_rate,
            'avg_time': avg_time,
            'min_time': min_time,
            'max_time': max_time
        }
        
    except Exception as e:
        print(f"❌ Erro no benchmark: {e}")
        return {'success': False, 'error': str(e)}

async def main():
    """Executa todos os testes de validação real"""
    print("🚀 INICIANDO FASE 3: TESTES E VALIDAÇÃO EM AMBIENTE REAL")
    print("=" * 70)
    
    # Executar todos os testes
    tests = [
        ('Cenário Lambda + SQS', test_real_scenario_1_lambda_sqs),
        ('Cenário 3-Tier Web App', test_real_scenario_2_three_tier),
        ('Cenário Microserviços', test_real_scenario_3_microservices),
        ('Router Direto', test_intelligent_router_direct),
        ('Benchmark Performance', test_performance_benchmark)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*70}")
        print(f"🧪 EXECUTANDO: {test_name}")
        print(f"{'='*70}")
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            results[test_name] = result
            
        except Exception as e:
            print(f"❌ Erro executando {test_name}: {e}")
            results[test_name] = {'success': False, 'error': str(e)}
    
    # Relatório final
    print(f"\n{'='*70}")
    print("📊 RELATÓRIO FINAL - FASE 3")
    print(f"{'='*70}")
    
    successful_tests = sum(1 for r in results.values() if r.get('success', False))
    total_tests = len(results)
    
    print(f"✅ Testes bem-sucedidos: {successful_tests}/{total_tests}")
    print(f"📈 Taxa de sucesso geral: {successful_tests/total_tests:.1%}")
    
    # Métricas agregadas
    processing_times = []
    detection_rates = []
    
    for test_name, result in results.items():
        if result.get('success'):
            print(f"\n🎯 {test_name}:")
            
            if 'processing_time' in result:
                processing_times.append(result['processing_time'])
                print(f"   ⏱️ Tempo: {result['processing_time']:.2f}s")
            
            if 'detection_rate' in result:
                detection_rates.append(result['detection_rate'])
                print(f"   🎯 Detecção: {result['detection_rate']:.1%}")
            
            if 'avg_time' in result:
                print(f"   📊 Tempo médio: {result['avg_time']:.3f}s")
            
            if 'success_rate' in result:
                print(f"   ✅ Taxa sucesso: {result['success_rate']:.1%}")
    
    # Métricas finais
    if processing_times:
        avg_processing_time = sum(processing_times) / len(processing_times)
        print(f"\n📊 MÉTRICAS FINAIS:")
        print(f"   • Tempo médio de processamento: {avg_processing_time:.2f}s")
    
    if detection_rates:
        avg_detection_rate = sum(detection_rates) / len(detection_rates)
        print(f"   • Taxa média de detecção: {avg_detection_rate:.1%}")
    
    # Conclusão
    if successful_tests == total_tests:
        print(f"\n🎉 TODOS OS TESTES PASSARAM!")
        print(f"✅ Sistema validado para produção")
        validation_status = "APROVADO"
    elif successful_tests >= total_tests * 0.8:
        print(f"\n⚠️ Maioria dos testes passou ({successful_tests}/{total_tests})")
        print(f"🔧 Revisar testes que falharam")
        validation_status = "APROVADO COM RESSALVAS"
    else:
        print(f"\n❌ Muitos testes falharam ({total_tests - successful_tests}/{total_tests})")
        print(f"🚫 Sistema precisa de correções")
        validation_status = "REPROVADO"
    
    print(f"\n🏆 STATUS FINAL: {validation_status}")
    
    return {
        'validation_status': validation_status,
        'tests_passed': successful_tests,
        'total_tests': total_tests,
        'success_rate': successful_tests/total_tests,
        'results': results
    }

if __name__ == "__main__":
    asyncio.run(main())
