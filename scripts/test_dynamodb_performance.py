#!/usr/bin/env python3
"""
Performance testing para otimizações DynamoDB
Compara performance antes/depois das otimizações
"""

import time
import asyncio
import statistics
from typing import List, Dict
import sys
import os

# Add path for imports
sys.path.append('/home/ial')

class DynamoDBPerformanceTester:
    def __init__(self):
        self.test_user_id = "test-user-performance"
        self.test_session_id = "test-session-123"
        
        # Initialize engines
        self.old_engine = None
        self.new_engine = None
        
        self._init_engines()
    
    def _init_engines(self):
        """Initialize old and new context engines"""
        
        # Old engine
        try:
            from core.memory.context_engine import ContextEngine
            self.old_engine = ContextEngine()
            print("✅ Old ContextEngine initialized")
        except Exception as e:
            print(f"⚠️ Old engine not available: {e}")
        
        # New optimized engine
        try:
            from core.memory.context_engine_optimized import OptimizedContextEngine
            self.new_engine = OptimizedContextEngine()
            print("✅ Optimized ContextEngine initialized")
        except Exception as e:
            print(f"⚠️ Optimized engine not available: {e}")
    
    def benchmark_context_retrieval(self, engine, engine_name: str, iterations: int = 10) -> Dict:
        """Benchmark context retrieval performance"""
        
        print(f"\n🔍 Testing {engine_name} - Context Retrieval ({iterations} iterations)")
        
        times = []
        
        for i in range(iterations):
            start_time = time.time()
            
            try:
                if hasattr(engine, 'build_context_for_query_optimized'):
                    # New optimized method
                    context = engine.build_context_for_query_optimized(
                        f"Test query {i}", self.test_user_id, self.test_session_id
                    )
                else:
                    # Old method
                    context = engine.build_context_for_query(f"Test query {i}")
                
                end_time = time.time()
                query_time = (end_time - start_time) * 1000  # Convert to ms
                times.append(query_time)
                
                print(f"  Query {i+1}: {query_time:.1f}ms")
                
            except Exception as e:
                print(f"  ❌ Query {i+1} failed: {e}")
                continue
        
        if times:
            results = {
                'engine': engine_name,
                'iterations': len(times),
                'avg_time_ms': statistics.mean(times),
                'min_time_ms': min(times),
                'max_time_ms': max(times),
                'median_time_ms': statistics.median(times),
                'std_dev_ms': statistics.stdev(times) if len(times) > 1 else 0
            }
        else:
            results = {
                'engine': engine_name,
                'error': 'All queries failed'
            }
        
        return results
    
    def benchmark_embedding_search(self, iterations: int = 5) -> Dict:
        """Benchmark embedding search performance"""
        
        print(f"\n🔍 Testing Embedding Search ({iterations} iterations)")
        
        if not self.new_engine:
            return {'error': 'Optimized engine not available'}
        
        times = []
        
        for i in range(iterations):
            start_time = time.time()
            
            try:
                # Test embedding search
                results = self.new_engine.embeddings.find_similar_conversations_optimized(
                    f"Test embedding query {i}", self.test_user_id, limit=3
                )
                
                end_time = time.time()
                search_time = (end_time - start_time) * 1000
                times.append(search_time)
                
                print(f"  Search {i+1}: {search_time:.1f}ms ({len(results)} results)")
                
            except Exception as e:
                print(f"  ❌ Search {i+1} failed: {e}")
                continue
        
        if times:
            return {
                'test': 'embedding_search',
                'iterations': len(times),
                'avg_time_ms': statistics.mean(times),
                'min_time_ms': min(times),
                'max_time_ms': max(times)
            }
        else:
            return {'test': 'embedding_search', 'error': 'All searches failed'}
    
    def benchmark_memory_operations(self, iterations: int = 5) -> Dict:
        """Benchmark memory save/load operations"""
        
        print(f"\n🔍 Testing Memory Operations ({iterations} iterations)")
        
        if not self.new_engine:
            return {'error': 'Optimized engine not available'}
        
        save_times = []
        load_times = []
        
        for i in range(iterations):
            # Test save operation
            start_time = time.time()
            
            try:
                self.new_engine.save_interaction_optimized(
                    f"Test user input {i}",
                    f"Test assistant response {i}",
                    self.test_user_id,
                    self.test_session_id,
                    {'test': True, 'iteration': i}
                )
                
                save_time = (time.time() - start_time) * 1000
                save_times.append(save_time)
                
                # Test load operation
                start_time = time.time()
                
                context = self.new_engine.memory.get_recent_context_optimized(limit=5)
                
                load_time = (time.time() - start_time) * 1000
                load_times.append(load_time)
                
                print(f"  Operation {i+1}: Save {save_time:.1f}ms, Load {load_time:.1f}ms")
                
            except Exception as e:
                print(f"  ❌ Operation {i+1} failed: {e}")
                continue
        
        return {
            'test': 'memory_operations',
            'save_avg_ms': statistics.mean(save_times) if save_times else 0,
            'load_avg_ms': statistics.mean(load_times) if load_times else 0,
            'iterations': len(save_times)
        }
    
    def run_comprehensive_benchmark(self) -> Dict:
        """Run comprehensive performance benchmark"""
        
        print("🚀 Starting DynamoDB Performance Benchmark")
        print("=" * 50)
        
        results = {
            'timestamp': time.time(),
            'test_user_id': self.test_user_id,
            'benchmarks': {}
        }
        
        # Test old engine (if available)
        if self.old_engine:
            old_results = self.benchmark_context_retrieval(self.old_engine, "Original Engine", 5)
            results['benchmarks']['original_engine'] = old_results
        
        # Test new optimized engine
        if self.new_engine:
            new_results = self.benchmark_context_retrieval(self.new_engine, "Optimized Engine", 10)
            results['benchmarks']['optimized_engine'] = new_results
            
            # Additional optimized tests
            embedding_results = self.benchmark_embedding_search(5)
            results['benchmarks']['embedding_search'] = embedding_results
            
            memory_results = self.benchmark_memory_operations(5)
            results['benchmarks']['memory_operations'] = memory_results
            
            # Get performance metrics from engine
            if hasattr(self.new_engine, 'get_performance_metrics'):
                engine_metrics = self.new_engine.get_performance_metrics()
                results['engine_metrics'] = engine_metrics
        
        # Calculate improvements
        if 'original_engine' in results['benchmarks'] and 'optimized_engine' in results['benchmarks']:
            old_avg = results['benchmarks']['original_engine'].get('avg_time_ms', 0)
            new_avg = results['benchmarks']['optimized_engine'].get('avg_time_ms', 0)
            
            if old_avg > 0 and new_avg > 0:
                improvement = ((old_avg - new_avg) / old_avg) * 100
                results['performance_improvement'] = {
                    'old_avg_ms': old_avg,
                    'new_avg_ms': new_avg,
                    'improvement_percent': improvement,
                    'speedup_factor': old_avg / new_avg
                }
        
        return results
    
    def print_benchmark_report(self, results: Dict):
        """Print formatted benchmark report"""
        
        print("\n" + "=" * 60)
        print("📊 DYNAMODB PERFORMANCE BENCHMARK REPORT")
        print("=" * 60)
        
        # Performance improvement summary
        if 'performance_improvement' in results:
            improvement = results['performance_improvement']
            print(f"\n🚀 PERFORMANCE IMPROVEMENT:")
            print(f"   Original Engine: {improvement['old_avg_ms']:.1f}ms average")
            print(f"   Optimized Engine: {improvement['new_avg_ms']:.1f}ms average")
            print(f"   Improvement: {improvement['improvement_percent']:.1f}% faster")
            print(f"   Speedup Factor: {improvement['speedup_factor']:.1f}x")
        
        # Individual benchmark results
        print(f"\n📋 DETAILED RESULTS:")
        
        for test_name, test_results in results['benchmarks'].items():
            if 'error' in test_results:
                print(f"\n❌ {test_name}: {test_results['error']}")
                continue
            
            print(f"\n✅ {test_name}:")
            if 'avg_time_ms' in test_results:
                print(f"   Average: {test_results['avg_time_ms']:.1f}ms")
                print(f"   Min: {test_results['min_time_ms']:.1f}ms")
                print(f"   Max: {test_results['max_time_ms']:.1f}ms")
                print(f"   Iterations: {test_results['iterations']}")
            
            if test_name == 'memory_operations':
                print(f"   Save Avg: {test_results['save_avg_ms']:.1f}ms")
                print(f"   Load Avg: {test_results['load_avg_ms']:.1f}ms")
        
        # Engine metrics
        if 'engine_metrics' in results:
            metrics = results['engine_metrics']
            print(f"\n📈 ENGINE METRICS:")
            for metric_name, value in metrics.items():
                print(f"   {metric_name}: {value}")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    tester = DynamoDBPerformanceTester()
    results = tester.run_comprehensive_benchmark()
    tester.print_benchmark_report(results)
    
    # Save results to file
    import json
    with open('/home/ial/reports/dynamodb_performance_benchmark.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: /home/ial/reports/dynamodb_performance_benchmark.json")
