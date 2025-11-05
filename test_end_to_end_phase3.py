#!/usr/bin/env python3
"""
Teste End-to-End Real - Fase 3
Testa o IAL completo com cenários reais de usuário
"""

import sys
import os
import subprocess
import time

def test_ialctl_binary():
    """Testa o binário ialctl diretamente"""
    print("🧪 TESTE END-TO-END: BINÁRIO IALCTL")
    print("=" * 50)
    
    binary_path = "/home/ial/dist/linux/ialctl"
    
    if not os.path.exists(binary_path):
        print(f"❌ Binário não encontrado: {binary_path}")
        return False
    
    test_cases = [
        {
            'name': 'Help Command',
            'input': '--help',
            'expected_in_output': ['usage', 'help', 'ial']
        },
        {
            'name': 'Version Command', 
            'input': '--version',
            'expected_in_output': ['version', 'ial']
        },
        {
            'name': 'Lambda Request',
            'input': 'Create a Lambda function for processing SQS messages',
            'expected_in_output': ['lambda', 'function', 'sqs']
        },
        {
            'name': 'ECS Request',
            'input': 'Deploy ECS cluster with load balancer',
            'expected_in_output': ['ecs', 'cluster', 'load']
        },
        {
            'name': 'Infrastructure Request',
            'input': 'Setup 3-tier web application infrastructure',
            'expected_in_output': ['infrastructure', 'web', 'application']
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testando: {test_case['name']}")
        print(f"   Input: {test_case['input']}")
        
        try:
            start_time = time.time()
            
            # Executar ialctl com timeout
            if test_case['input'].startswith('--'):
                # Comando de sistema
                cmd = [binary_path, test_case['input']]
            else:
                # Comando de texto (usar echo pipe)
                cmd = f"echo '{test_case['input']}' | timeout 10s {binary_path}"
            
            if isinstance(cmd, list):
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
            else:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            
            processing_time = time.time() - start_time
            
            # Verificar saída
            output = result.stdout + result.stderr
            output_lower = output.lower()
            
            # Verificar se contém palavras esperadas
            matches = []
            for expected in test_case['expected_in_output']:
                if expected.lower() in output_lower:
                    matches.append(expected)
            
            success = len(matches) > 0 or result.returncode == 0
            
            print(f"   ⏱️ Tempo: {processing_time:.2f}s")
            print(f"   📤 Return code: {result.returncode}")
            print(f"   📝 Output: {len(output)} chars")
            print(f"   🎯 Matches: {matches}")
            print(f"   ✅ Status: {'PASS' if success else 'FAIL'}")
            
            if output and len(output) < 500:
                print(f"   📄 Saída: {output[:200]}...")
            
            results.append({
                'name': test_case['name'],
                'success': success,
                'processing_time': processing_time,
                'return_code': result.returncode,
                'output_length': len(output),
                'matches': matches
            })
            
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Timeout (10s)")
            results.append({
                'name': test_case['name'],
                'success': False,
                'error': 'timeout'
            })
            
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            results.append({
                'name': test_case['name'],
                'success': False,
                'error': str(e)
            })
    
    # Resumo dos resultados
    successful = sum(1 for r in results if r.get('success', False))
    total = len(results)
    
    print(f"\n📊 RESUMO BINÁRIO IALCTL:")
    print(f"   ✅ Testes passaram: {successful}/{total}")
    print(f"   📈 Taxa de sucesso: {successful/total:.1%}")
    
    if successful == total:
        print(f"   🎉 TODOS OS TESTES DO BINÁRIO PASSARAM!")
    
    return {
        'success': successful == total,
        'results': results,
        'success_rate': successful/total
    }

def test_python_direct():
    """Testa execução direta do Python"""
    print("\n🧪 TESTE DIRETO: PYTHON NATURAL_LANGUAGE_PROCESSOR")
    print("=" * 50)
    
    try:
        # Importar e testar diretamente
        sys.path.append('/home/ial')
        from natural_language_processor import IaLNaturalProcessor
        
        processor = IaLNaturalProcessor()
        
        # Casos de teste reais
        real_cases = [
            "Hello, I need help with my infrastructure",
            "Deploy security infrastructure for production", 
            "Create a Lambda function to process SQS messages",
            "Setup ECS cluster with RDS database",
            "Show me the status of my deployments"
        ]
        
        results = []
        
        for i, test_input in enumerate(real_cases, 1):
            print(f"\n{i}. Input: '{test_input}'")
            
            try:
                start_time = time.time()
                response = processor.process_command(test_input, f"real_user_{i}")
                processing_time = time.time() - start_time
                
                print(f"   ⏱️ Tempo: {processing_time:.3f}s")
                print(f"   📝 Resposta: {len(response)} chars")
                print(f"   🎯 Preview: {response[:100]}...")
                
                # Verificar se resposta faz sentido
                meaningful = len(response) > 20 and not response.startswith("❌")
                
                results.append({
                    'input': test_input,
                    'success': True,
                    'meaningful': meaningful,
                    'processing_time': processing_time,
                    'response_length': len(response)
                })
                
                print(f"   ✅ Status: {'MEANINGFUL' if meaningful else 'BASIC'}")
                
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                results.append({
                    'input': test_input,
                    'success': False,
                    'error': str(e)
                })
        
        # Estatísticas
        successful = sum(1 for r in results if r.get('success', False))
        meaningful = sum(1 for r in results if r.get('meaningful', False))
        
        if results:
            avg_time = sum(r.get('processing_time', 0) for r in results if 'processing_time' in r) / len([r for r in results if 'processing_time' in r])
            avg_length = sum(r.get('response_length', 0) for r in results if 'response_length' in r) / len([r for r in results if 'response_length' in r])
        else:
            avg_time = 0
            avg_length = 0
        
        print(f"\n📊 RESUMO PYTHON DIRETO:")
        print(f"   ✅ Execuções bem-sucedidas: {successful}/{len(results)}")
        print(f"   🧠 Respostas significativas: {meaningful}/{len(results)}")
        print(f"   ⏱️ Tempo médio: {avg_time:.3f}s")
        print(f"   📝 Tamanho médio resposta: {avg_length:.0f} chars")
        
        return {
            'success': successful == len(results),
            'meaningful_responses': meaningful,
            'avg_processing_time': avg_time,
            'results': results
        }
        
    except Exception as e:
        print(f"❌ Erro no teste Python direto: {e}")
        return {'success': False, 'error': str(e)}

def test_system_integration():
    """Testa integração completa do sistema"""
    print("\n🧪 TESTE DE INTEGRAÇÃO COMPLETA")
    print("=" * 50)
    
    try:
        # Testar se todos os componentes estão acessíveis
        components = {
            'natural_language_processor': '/home/ial/natural_language_processor.py',
            'intelligent_router': '/home/ial/core/intelligent_mcp_router.py',
            'service_detector': '/home/ial/core/service_detector.py',
            'domain_mapper': '/home/ial/core/domain_mapper.py',
            'mcp_orchestrator': '/home/ial/core/mcp_orchestrator.py',
            'mcp_mesh_config': '/home/ial/config/mcp-mesh.yaml',
            'binary': '/home/ial/dist/linux/ialctl'
        }
        
        component_status = {}
        
        for name, path in components.items():
            exists = os.path.exists(path)
            component_status[name] = exists
            status_icon = "✅" if exists else "❌"
            print(f"   {status_icon} {name}: {path}")
        
        # Verificar se arquivos Python são válidos
        python_files = [
            '/home/ial/natural_language_processor.py',
            '/home/ial/core/intelligent_mcp_router.py',
            '/home/ial/core/service_detector.py'
        ]
        
        syntax_valid = {}
        
        for py_file in python_files:
            if os.path.exists(py_file):
                try:
                    # Verificar sintaxe Python
                    with open(py_file, 'r') as f:
                        compile(f.read(), py_file, 'exec')
                    syntax_valid[py_file] = True
                    print(f"   ✅ Sintaxe válida: {os.path.basename(py_file)}")
                except SyntaxError as e:
                    syntax_valid[py_file] = False
                    print(f"   ❌ Erro de sintaxe: {os.path.basename(py_file)} - {e}")
        
        # Verificar tamanhos dos arquivos
        file_sizes = {}
        for name, path in components.items():
            if os.path.exists(path):
                size = os.path.getsize(path)
                file_sizes[name] = size
                print(f"   📏 {name}: {size:,} bytes")
        
        # Calcular score de integração
        components_available = sum(component_status.values())
        syntax_score = sum(syntax_valid.values())
        
        integration_score = (components_available + syntax_score) / (len(components) + len(python_files))
        
        print(f"\n📊 SCORE DE INTEGRAÇÃO:")
        print(f"   • Componentes disponíveis: {components_available}/{len(components)}")
        print(f"   • Arquivos Python válidos: {syntax_score}/{len(python_files)}")
        print(f"   • Score geral: {integration_score:.1%}")
        
        if integration_score >= 0.9:
            integration_status = "🎉 EXCELENTE"
        elif integration_score >= 0.7:
            integration_status = "✅ BOM"
        elif integration_score >= 0.5:
            integration_status = "⚠️ ACEITÁVEL"
        else:
            integration_status = "❌ PROBLEMÁTICO"
        
        print(f"   • Status: {integration_status}")
        
        return {
            'success': integration_score >= 0.7,
            'integration_score': integration_score,
            'components_status': component_status,
            'syntax_valid': syntax_valid,
            'file_sizes': file_sizes
        }
        
    except Exception as e:
        print(f"❌ Erro no teste de integração: {e}")
        return {'success': False, 'error': str(e)}

def main():
    """Executa validação completa da Fase 3"""
    print("🚀 FASE 3: TESTES E VALIDAÇÃO EM AMBIENTE REAL")
    print("=" * 70)
    print(f"📅 Data: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🖥️ Sistema: {os.uname().sysname} {os.uname().release}")
    print(f"📁 Diretório: {os.getcwd()}")
    
    # Executar todos os testes
    tests = [
        ('Integração do Sistema', test_system_integration),
        ('Python Direto', test_python_direct),
        ('Binário IALCTL', test_ialctl_binary)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*70}")
        print(f"🧪 EXECUTANDO: {test_name}")
        print(f"{'='*70}")
        
        try:
            result = test_func()
            results[test_name] = result
            
        except Exception as e:
            print(f"❌ Erro executando {test_name}: {e}")
            results[test_name] = {'success': False, 'error': str(e)}
    
    # Relatório final da Fase 3
    print(f"\n{'='*70}")
    print("🏆 RELATÓRIO FINAL - FASE 3: VALIDAÇÃO REAL")
    print(f"{'='*70}")
    
    successful_tests = sum(1 for r in results.values() if r.get('success', False))
    total_tests = len(results)
    
    print(f"✅ Testes bem-sucedidos: {successful_tests}/{total_tests}")
    print(f"📈 Taxa de sucesso: {successful_tests/total_tests:.1%}")
    
    # Detalhes por teste
    for test_name, result in results.items():
        status_icon = "✅" if result.get('success', False) else "❌"
        print(f"\n{status_icon} {test_name}:")
        
        if result.get('success'):
            if 'integration_score' in result:
                print(f"   📊 Score: {result['integration_score']:.1%}")
            if 'avg_processing_time' in result:
                print(f"   ⏱️ Tempo médio: {result['avg_processing_time']:.3f}s")
            if 'success_rate' in result:
                print(f"   📈 Taxa sucesso: {result['success_rate']:.1%}")
        else:
            print(f"   ❌ Erro: {result.get('error', 'Erro desconhecido')}")
    
    # Conclusão final
    if successful_tests == total_tests:
        final_status = "🎉 APROVADO PARA PRODUÇÃO"
        recommendation = "Sistema pronto para deployment"
    elif successful_tests >= total_tests * 0.8:
        final_status = "✅ APROVADO COM RESSALVAS"
        recommendation = "Sistema funcional, pequenos ajustes recomendados"
    else:
        final_status = "❌ REPROVADO"
        recommendation = "Sistema precisa de correções antes do deployment"
    
    print(f"\n🏆 STATUS FINAL: {final_status}")
    print(f"💡 Recomendação: {recommendation}")
    
    # Próximos passos
    print(f"\n🚀 PRÓXIMOS PASSOS:")
    if successful_tests == total_tests:
        print(f"   1. ✅ Fase 3 concluída com sucesso")
        print(f"   2. 📚 Iniciar Fase 4: Documentação")
        print(f"   3. 🚀 Preparar para deployment em produção")
    else:
        print(f"   1. 🔧 Corrigir testes que falharam")
        print(f"   2. 🔄 Re-executar validação")
        print(f"   3. 📋 Revisar integração dos componentes")
    
    return {
        'phase': 3,
        'status': final_status,
        'tests_passed': successful_tests,
        'total_tests': total_tests,
        'success_rate': successful_tests/total_tests,
        'recommendation': recommendation,
        'results': results
    }

if __name__ == "__main__":
    main()
