#!/usr/bin/env python3
"""
Intelligent MCP Router Sophisticated - Complete Integration
LLM + MCP Mesh + Circuit Breakers + Async/Await
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from core.llm_provider import LLMProvider
from core.mcp_mesh_loader import MCPMeshLoader
from core.service_detector_enhanced import ServiceDetectorEnhanced
from core.domain_mapper_sophisticated import DomainMapperSophisticated
from core.mcp_orchestrator_upgraded import MCPOrchestratorUpgraded
from core.circuit_breaker import CircuitBreaker

class IntelligentMCPRouterSophisticated:
    def __init__(self):
        # Initialize all components
        self.llm_provider = LLMProvider()
        self.mesh_loader = MCPMeshLoader()
        self.service_detector = ServiceDetectorEnhanced(self.mesh_loader)
        self.domain_mapper = DomainMapperSophisticated(self.mesh_loader)
        self.orchestrator = MCPOrchestratorUpgraded(self.mesh_loader)
        
        # Circuit breaker for overall routing
        self.routing_circuit = CircuitBreaker(
            failure_threshold=10,
            timeout=120,
            name="routing"
        )
        
        print("🧠 Intelligent MCP Router Sophisticated inicializado")
        print(f"✅ LLM Provider: {self.llm_provider.current_provider}")
        print(f"✅ MCP Domains: {len(self.mesh_loader.get_all_domains())}")
        print(f"✅ Circuit Breakers: Ativo")
        
    async def route_request_async(self, request: str) -> Dict[str, Any]:
        """Main async routing method with circuit breaker"""
        start_time = time.time()
        
        if not self.routing_circuit.can_execute():
            return self._fallback_response("Circuit breaker open", start_time)
            
        try:
            # Step 1: LLM Processing (async)
            llm_start = time.time()
            llm_result = await self.llm_provider.process_natural_language_async(request)
            llm_time = time.time() - llm_start
            
            # Step 2: Service Detection (sync, fast)
            detection_start = time.time()
            processed_text = llm_result.get('processed_text', request)
            detection_result = self.service_detector.detect_services(processed_text)
            detection_time = time.time() - detection_start
            
            # Step 3: Domain Mapping (sync, fast)
            mapping_start = time.time()
            domains = self.domain_mapper.map_to_domains(detection_result['detected_services'])
            required_mcps = self.domain_mapper.get_required_mcps(domains)
            
            # Apply pattern optimizations
            pattern = detection_result.get('architecture_pattern')
            if pattern:
                required_mcps = self.domain_mapper.apply_optimizations(pattern, required_mcps)
                
            mapping_time = time.time() - mapping_start
            
            # Step 4: MCP Loading (async, parallel)
            loading_start = time.time()
            loaded_mcps = await self.orchestrator.lazy_load_mcps_async(required_mcps)
            loading_time = time.time() - loading_start
            
            # Step 5: Execution (async, parallel)
            execution_start = time.time()
            execution_results = await self._execute_mcps_async(loaded_mcps, request)
            execution_time = time.time() - execution_start
            
            total_time = time.time() - start_time
            
            self.routing_circuit.record_success()
            
            return {
                'status': 'success',
                'request': request,
                'llm_result': {
                    'provider': llm_result['provider'],
                    'confidence': llm_result['confidence'],
                    'entities': llm_result['entities']
                },
                'detection_result': {
                    'domains': detection_result['detected_domains'],
                    'services': detection_result['detected_services'],
                    'pattern': detection_result['architecture_pattern'],
                    'confidence': detection_result['total_confidence']
                },
                'mapping_result': {
                    'required_mcps': len(required_mcps),
                    'loaded_mcps': list(loaded_mcps.keys()),
                    'load_strategy': self.domain_mapper.get_load_strategy(required_mcps)
                },
                'execution_results': execution_results,
                'performance_metrics': {
                    'total_time': round(total_time * 1000, 2),  # ms
                    'llm_time': round(llm_time * 1000, 2),
                    'detection_time': round(detection_time * 1000, 2),
                    'mapping_time': round(mapping_time * 1000, 2),
                    'loading_time': round(loading_time * 1000, 2),
                    'execution_time': round(execution_time * 1000, 2)
                },
                'circuit_breaker_metrics': self._get_circuit_breaker_metrics()
            }
            
        except Exception as e:
            self.routing_circuit.record_failure()
            return self._fallback_response(f"Routing failed: {str(e)}", start_time)
            
    async def _execute_mcps_async(self, loaded_mcps: Dict, request: str) -> Dict:
        """Execute MCPs in parallel"""
        if not loaded_mcps:
            return {'status': 'no_mcps_loaded'}
            
        execution_tasks = []
        
        for mcp_name, mcp_instance in loaded_mcps.items():
            task = self._execute_single_mcp_async(mcp_name, mcp_instance, request)
            execution_tasks.append((mcp_name, task))
            
        if not execution_tasks:
            return {'status': 'no_tasks_created'}
            
        task_names, task_coroutines = zip(*execution_tasks)
        results = await asyncio.gather(*task_coroutines, return_exceptions=True)
        
        execution_results = {}
        for i, result in enumerate(results):
            mcp_name = task_names[i]
            
            if isinstance(result, Exception):
                execution_results[mcp_name] = {
                    'status': 'failed',
                    'error': str(result)
                }
            else:
                execution_results[mcp_name] = {
                    'status': 'success',
                    'result': result
                }
                
        return execution_results
        
    async def _execute_single_mcp_async(self, mcp_name: str, mcp_instance: Any, request: str) -> Dict:
        """Execute single MCP async"""
        try:
            # Simulate MCP execution
            await asyncio.sleep(0.1)  # Simulate execution time
            
            return {
                'mcp_name': mcp_name,
                'request_processed': request,
                'capabilities_used': mcp_instance.get('capabilities', []),
                'execution_time': 0.1,
                'resources_created': f"simulated_{mcp_name}_resources"
            }
            
        except Exception as e:
            raise Exception(f"MCP {mcp_name} execution failed: {e}")
            
    def _fallback_response(self, error_message: str, start_time: float) -> Dict[str, Any]:
        """Generate fallback response"""
        return {
            'status': 'fallback',
            'error': error_message,
            'fallback_used': True,
            'performance_metrics': {
                'total_time': round((time.time() - start_time) * 1000, 2)
            },
            'circuit_breaker_metrics': self._get_circuit_breaker_metrics()
        }
        
    def _get_circuit_breaker_metrics(self) -> Dict:
        """Get performance metrics from all circuit breakers"""
        metrics = {
            'routing_circuit': self.routing_circuit.get_metrics(),
            'llm_circuits': {},
            'mcp_circuits': {}
        }
        
        # LLM circuit breaker metrics
        for provider, circuit in self.llm_provider.circuit_breakers.items():
            metrics['llm_circuits'][provider] = circuit.get_metrics()
            
        # MCP circuit breaker metrics
        for mcp_name, circuit in self.orchestrator.circuit_breakers.items():
            metrics['mcp_circuits'][mcp_name] = circuit.get_metrics()
            
        return metrics
        
    def route_request(self, request: str) -> Dict[str, Any]:
        """Sync wrapper for backward compatibility"""
        try:
            # Run async method in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.route_request_async(request))
            loop.close()
            return result
        except Exception as e:
            return self._fallback_response(f"Sync wrapper failed: {str(e)}", time.time())
            
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        health_status = {
            'overall_status': 'healthy',
            'components': {},
            'timestamp': time.time()
        }
        
        # Check LLM provider
        try:
            llm_metrics = self.llm_provider.get_metrics()
            health_status['components']['llm_provider'] = {
                'status': 'healthy',
                'metrics': llm_metrics
            }
        except Exception as e:
            health_status['components']['llm_provider'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['overall_status'] = 'degraded'
            
        # Check MCP orchestrator
        try:
            await self.orchestrator.health_check_mcps_async()
            orchestrator_metrics = self.orchestrator.get_metrics()
            health_status['components']['mcp_orchestrator'] = {
                'status': 'healthy',
                'metrics': orchestrator_metrics
            }
        except Exception as e:
            health_status['components']['mcp_orchestrator'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['overall_status'] = 'degraded'
            
        return health_status
        
    async def cleanup(self):
        """Cleanup all resources"""
        await self.orchestrator.cleanup()
        print("✅ Router cleanup completed")
