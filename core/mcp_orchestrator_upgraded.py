#!/usr/bin/env python3
"""
Upgraded MCP Orchestrator with Async, Circuit Breakers, and Connection Pooling
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any, Optional
from core.mcp_mesh_loader import MCPMeshLoader
from core.circuit_breaker import CircuitBreaker
from core.mcp_connection_pool import MCPConnectionPool

class MCPOrchestratorUpgraded:
    def __init__(self, mesh_loader: MCPMeshLoader):
        self.mesh_loader = mesh_loader
        self.loaded_mcps = {}
        self.health_status = {}
        self.cache = {}
        self.connection_pool = MCPConnectionPool()
        self.circuit_breakers = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Get settings from mesh
        self.cache_settings = mesh_loader.get_cache_settings()
        self.health_settings = mesh_loader.get_health_check_settings()
        
    async def analyze_requirements(self, user_request: str) -> Dict[str, Any]:
        """Analyze user requirements using MCP capabilities to detect missing information"""
        try:
            # Get all available MCPs and their capabilities
            all_domains = self.mesh_loader.get_all_domains()
            
            # Detect which services are mentioned in the request
            request_lower = user_request.lower()
            detected_services = []
            
            # Service detection patterns
            service_patterns = {
                'ecs': ['ecs', 'container', 'fargate', 'task'],
                'rds': ['rds', 'database', 'mysql', 'postgres'],
                'lambda': ['lambda', 'function', 'serverless'],
                's3': ['s3', 'bucket', 'storage'],
                'api_gateway': ['api', 'gateway', 'rest', 'endpoint'],
                'vpc': ['vpc', 'network', 'subnet', 'security'],
                'ec2': ['ec2', 'instance', 'server', 'vm']
            }
            
            for service, patterns in service_patterns.items():
                if any(pattern in request_lower for pattern in patterns):
                    detected_services.append(service)
            
            if not detected_services:
                return {
                    'complete': False,
                    'missing_info': ['service_type'],
                    'detected_services': [],
                    'confidence': 0.1
                }
            
            # Analyze completeness based on detected services
            missing_info = []
            primary_service = detected_services[0]
            
            # Service-specific requirement analysis
            if primary_service == 'ecs':
                required_info = ['task_definition', 'networking', 'scaling']
                if 'task' not in request_lower and 'definition' not in request_lower:
                    missing_info.append('task_definition')
                if 'vpc' not in request_lower and 'subnet' not in request_lower:
                    missing_info.append('networking')
                if 'scale' not in request_lower and 'replica' not in request_lower:
                    missing_info.append('scaling')
            
            elif primary_service == 's3':
                # S3 + CloudFront para site precisa de informações específicas
                if 'cloudfront' in request_lower or 'site' in request_lower or 'website' in request_lower:
                    if 'domain' not in request_lower and 'dominio' not in request_lower:
                        missing_info.append('domain_name')
                    if 'ssl' not in request_lower and 'https' not in request_lower and 'certificate' not in request_lower:
                        missing_info.append('ssl_certificate')
                    if 'cache' not in request_lower and 'ttl' not in request_lower:
                        missing_info.append('cache_behavior')
            
            elif primary_service == 'rds':
                if not any(db in request_lower for db in ['mysql', 'postgres', 'aurora']):
                    missing_info.append('database_engine')
                if not any(size in request_lower for size in ['micro', 'small', 'medium', 'large']):
                    missing_info.append('instance_size')
                if 'multi-az' not in request_lower and 'availability' not in request_lower:
                    missing_info.append('availability')
            
            elif primary_service == 'lambda':
                if 'runtime' not in request_lower and not any(lang in request_lower for lang in ['python', 'node', 'java']):
                    missing_info.append('runtime')
                if 'memory' not in request_lower and 'timeout' not in request_lower:
                    missing_info.append('performance_config')
            
            # Calculate completeness
            is_complete = len(missing_info) == 0
            confidence = max(0.3, 1.0 - (len(missing_info) * 0.2))
            
            return {
                'complete': is_complete,
                'missing_info': missing_info,
                'detected_services': detected_services,
                'primary_service': primary_service,
                'confidence': confidence,
                'analysis_timestamp': time.time()
            }
            
        except Exception as e:
            print(f"⚠️ Erro na análise de requisitos MCP: {e}")
            return {
                'complete': False,
                'missing_info': ['analysis_error'],
                'detected_services': [],
                'confidence': 0.0,
                'error': str(e)
            }

    async def lazy_load_mcps_async(self, required_mcps: List[Dict]) -> Dict[str, Any]:
        """Async lazy loading with circuit breaker protection"""
        tasks = []
        
        for mcp_config in required_mcps:
            mcp_name = mcp_config['name']
            
            # Initialize circuit breaker if needed
            if mcp_name not in self.circuit_breakers:
                self.circuit_breakers[mcp_name] = CircuitBreaker(
                    failure_threshold=3,
                    timeout=30,
                    name=f"mcp-{mcp_name}"
                )
                
            circuit = self.circuit_breakers[mcp_name]
            
            if circuit.can_execute():
                task = self._load_mcp_async(mcp_config)
                tasks.append((mcp_name, task))
                
        # Execute all loading tasks concurrently
        if not tasks:
            return {}
            
        task_names, task_coroutines = zip(*tasks)
        results = await asyncio.gather(*task_coroutines, return_exceptions=True)
        
        loaded = {}
        for i, result in enumerate(results):
            mcp_name = task_names[i]
            circuit = self.circuit_breakers[mcp_name]
            
            if isinstance(result, Exception):
                circuit.record_failure()
                print(f"❌ Failed to load MCP {mcp_name}: {result}")
            else:
                circuit.record_success()
                loaded[mcp_name] = result
                self.loaded_mcps[mcp_name] = result
                
        return loaded
        
    async def _load_mcp_async(self, mcp_config: Dict) -> Any:
        """Async MCP loading with timeout and caching"""
        mcp_name = mcp_config['name']
        timeout = mcp_config.get('load_timeout', 5.0)
        
        # Check cache first
        if mcp_name in self.cache:
            cache_entry = self.cache[mcp_name]
            if not self._is_cache_expired(cache_entry):
                return cache_entry['mcp_instance']
                
        # Load MCP with timeout
        try:
            mcp_instance = await asyncio.wait_for(
                self._create_mcp_instance_async(mcp_config),
                timeout=timeout
            )
            
            # Cache the loaded MCP
            self.cache[mcp_name] = {
                'mcp_instance': mcp_instance,
                'loaded_at': time.time(),
                'ttl': self.cache_settings.get('ttl_seconds', 300)
            }
            
            return mcp_instance
            
        except asyncio.TimeoutError:
            raise Exception(f"MCP {mcp_name} loading timeout after {timeout}s")
            
    async def _create_mcp_instance_async(self, mcp_config: Dict) -> Any:
        """Create MCP instance asynchronously"""
        # Simulate MCP loading with connection pool
        mcp_name = mcp_config['name']
        
        async def load_operation(session):
            # Simulate async MCP initialization
            await asyncio.sleep(0.1)  # Simulate I/O
            return {
                'name': mcp_name,
                'type': mcp_config.get('type', 'unknown'),
                'capabilities': mcp_config.get('capabilities', []),
                'loaded_at': time.time(),
                'session': session
            }
            
        return await self.connection_pool.execute_with_connection(mcp_name, load_operation)
        
    def _is_cache_expired(self, cache_entry: Dict) -> bool:
        """Check if cache entry is expired"""
        loaded_at = cache_entry['loaded_at']
        ttl = cache_entry['ttl']
        return (time.time() - loaded_at) > ttl
        
    async def health_check_mcps_async(self):
        """Async health checking of all loaded MCPs"""
        if not self.loaded_mcps:
            return
            
        health_tasks = []
        for mcp_name, mcp_instance in self.loaded_mcps.items():
            task = self._health_check_mcp_async(mcp_name, mcp_instance)
            health_tasks.append((mcp_name, task))
            
        if not health_tasks:
            return
            
        task_names, task_coroutines = zip(*health_tasks)
        results = await asyncio.gather(*task_coroutines, return_exceptions=True)
        
        for i, result in enumerate(results):
            mcp_name = task_names[i]
            
            if isinstance(result, Exception):
                self.health_status[mcp_name] = {
                    'status': 'unhealthy',
                    'error': str(result),
                    'checked_at': time.time()
                }
                # Remove unhealthy MCP from cache
                if mcp_name in self.cache:
                    del self.cache[mcp_name]
            else:
                self.health_status[mcp_name] = {
                    'status': 'healthy',
                    'response_time': result.get('response_time', 0),
                    'checked_at': time.time()
                }
                
    async def _health_check_mcp_async(self, mcp_name: str, mcp_instance: Any) -> Dict:
        """Perform async health check on single MCP"""
        start_time = time.time()
        
        try:
            # Simulate health check
            await asyncio.sleep(0.05)  # Simulate health check latency
            
            response_time = time.time() - start_time
            return {
                'status': 'healthy',
                'response_time': response_time
            }
            
        except Exception as e:
            raise Exception(f"Health check failed: {e}")
            
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics"""
        circuit_metrics = {}
        for mcp_name, circuit in self.circuit_breakers.items():
            circuit_metrics[mcp_name] = circuit.get_metrics()
            
        return {
            'loaded_mcps': len(self.loaded_mcps),
            'cached_mcps': len(self.cache),
            'circuit_breakers': circuit_metrics,
            'health_status': self.health_status,
            'connection_pool': self.connection_pool.get_stats(),
            'cache_hit_rate': self._calculate_cache_hit_rate()
        }
        
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate (simplified)"""
        # This would be more sophisticated in production
        return 0.85  # Placeholder
        
    async def cleanup(self):
        """Cleanup resources"""
        await self.connection_pool.close_all()
        self.executor.shutdown(wait=True)
