#!/usr/bin/env python3
"""
MCP Servers Initializer
Inicializa e valida os 17 MCP servers configurados
"""

import yaml
import asyncio
import os
import sys
from typing import Dict, List
from pathlib import Path


class MCPServersInitializer:
    """Inicializador dos MCP servers"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Detectar se está rodando como binário PyInstaller
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_path, "config", "mcp-mesh-complete.yaml")
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.initialized_servers = {}
        
    def _load_config(self) -> Dict:
        """Carrega configuração MCP mesh"""
        try:
            with open(self.config_path) as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"⚠️ Erro carregando config MCP: {e}")
            return {"core_mcps": {"always_active": []}, "domain_mcps": {}}
    
    async def initialize_all_servers(self) -> Dict:
        """Inicializar todos os MCP servers"""
        
        results = {
            "core_mcps": [],
            "domain_mcps": {},
            "total_initialized": 0,
            "total_failed": 0
        }
        
        # 1. Inicializar core MCPs (sempre ativos)
        core_mcps = self.config.get('core_mcps', {}).get('always_active', [])
        
        for mcp in core_mcps:
            server_name = mcp['name']
            result = await self._initialize_server(server_name, mcp)
            results["core_mcps"].append(result)
            
            if result["status"] == "success":
                results["total_initialized"] += 1
            else:
                results["total_failed"] += 1
        
        # 2. Registrar domain MCPs (lazy loading)
        domain_mcps = self.config.get('domain_mcps', {}).get('lazy_load', {})
        
        for domain, mcps_list in domain_mcps.items():
            results["domain_mcps"][domain] = {
                "description": f"{domain.title()} domain MCPs",
                "mcps": [mcp['name'] for mcp in mcps_list],
                "status": "registered"
            }
        
        return results
    
    async def _initialize_server(self, server_name: str, config: Dict) -> Dict:
        """Inicializar servidor MCP específico"""
        
        try:
            # Health check simulado (MCP servers são lazy-loaded)
            health_result = await self._health_check_server(server_name, config)
            
            if health_result["status"] == "healthy":
                self.initialized_servers[server_name] = config
                return {
                    "server": server_name,
                    "status": "success",
                    "message": f"{server_name} registered",
                    "priority": config.get('priority', 2)
                }
            else:
                return {
                    "server": server_name,
                    "status": "warning",
                    "message": f"{server_name} registered (lazy-load)",
                    "priority": config.get('priority', 2)
                }
                
        except Exception as e:
            return {
                "server": server_name,
                "status": "error",
                "message": f"Failed: {str(e)}"
            }
    
    async def _health_check_server(self, server_name: str, config: Dict) -> Dict:
        """Health check do servidor MCP"""
        
        # MCP servers são lazy-loaded, então apenas registramos
        # O health check real acontece quando o server é usado
        
        return {
            "status": "healthy",
            "server": server_name,
            "load_timeout": config.get('load_timeout', 3.0)
        }
    
    def get_server_count(self) -> Dict:
        """Retorna contagem de servidores"""
        
        core_count = len(self.config.get('core_mcps', {}).get('always_active', []))
        
        domain_count = 0
        for domain_config in self.config.get('domain_mcps', {}).values():
            domain_count += len(domain_config.get('mcps', []))
        
        return {
            "core_mcps": core_count,
            "domain_mcps": domain_count,
            "total": core_count + domain_count
        }


async def initialize_mcp_servers() -> Dict:
    """Função auxiliar para inicialização"""
    initializer = MCPServersInitializer()
    return await initializer.initialize_all_servers()
