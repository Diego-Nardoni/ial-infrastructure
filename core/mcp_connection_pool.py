#!/usr/bin/env python3
"""
MCP Connection Pool for async operations
"""

import asyncio
import aiohttp
import time
from typing import Dict, Any, Optional, Callable

class MCPConnectionPool:
    def __init__(self, max_connections: int = 10, timeout: int = 30):
        self.max_connections = max_connections
        self.timeout = timeout
        self.pools = {}
        self.semaphore = asyncio.Semaphore(max_connections)
        
    async def get_connection(self, mcp_name: str) -> aiohttp.ClientSession:
        """Get or create connection for MCP"""
        if mcp_name not in self.pools:
            connector = aiohttp.TCPConnector(
                limit=self.max_connections,
                limit_per_host=5,
                ttl_dns_cache=300,
                use_dns_cache=True
            )
            
            timeout_config = aiohttp.ClientTimeout(total=self.timeout)
            
            self.pools[mcp_name] = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout_config
            )
            
        return self.pools[mcp_name]
        
    async def execute_with_connection(self, mcp_name: str, operation: Callable) -> Any:
        """Execute operation with connection pooling and semaphore"""
        async with self.semaphore:
            session = await self.get_connection(mcp_name)
            return await operation(session)
            
    async def close_all(self):
        """Close all connection pools"""
        for session in self.pools.values():
            await session.close()
        self.pools.clear()
        
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        return {
            'active_pools': len(self.pools),
            'max_connections': self.max_connections,
            'timeout': self.timeout,
            'semaphore_available': self.semaphore._value
        }
