import json
import os
import sys
import time
from typing import Dict, List, Optional
from enum import Enum

class MCPStatus(Enum):
    CONFIGURED = "configured"
    LOADING = "loading"
    ACTIVE = "active"
    ERROR = "error"
    INACTIVE = "inactive"

class MCPRegistry:
    def __init__(self, config_path="mcp-server-config.json"):
        # Detectar se está executando como binário PyInstaller
        if hasattr(sys, '_MEIPASS'):
            # Executando como binário - usar recursos empacotados
            self.config_path = os.path.join(sys._MEIPASS, config_path)
        else:
            # Executando como script - usar caminho relativo
            self.config_path = config_path
            
        self.servers = {}
        self.active_servers = {}
        self.load_history = {}
        self._load()

    def _load(self):
        """Carrega configuração dos MCPs"""
        if not os.path.exists(self.config_path):
            # Usar configuração padrão embarcada (silencioso)
            self._load_default_config()
            return
        
        try:
            with open(self.config_path) as f:
                cfg = json.load(f)
            
            # Carregar servidores configurados
            for s in cfg.get("servers", []):
                self.servers[s["name"]] = {
                    **s,
                    'status': MCPStatus.CONFIGURED,
                    'configured_at': time.time()
                }
        except Exception as e:
            print(f"⚠️ Erro carregando MCP config: {e}")
            self._load_default_config()
    
    def _load_default_config(self):
        """Carrega configuração padrão quando arquivo não existe"""
        print("✅ Usando configuração MCP padrão embarcada")
        default_config = {
            "mcpServers": {
                "aws-real-executor": {
                    "command": "python",
                    "args": ["-m", "mcp_aws_real_executor"],
                    "env": {}
                },
                "aws-cloudformation": {
                    "command": "python", 
                    "args": ["-m", "mcp_aws_cloudformation"],
                    "env": {}
                },
                "aws-cloud-control-api": {
                    "command": "python",
                    "args": ["-m", "mcp_aws_cloud_control_api"],
                    "env": {}
                },
                "aws-cli": {
                    "command": "python",
                    "args": ["-m", "mcp_aws_cli"],
                    "env": {}
                },
                "aws-core": {
                    "command": "python",
                    "args": ["-m", "mcp_aws_core"],
                    "env": {}
                }
            }
        }
        
        # Processar configuração padrão
        for name, config in default_config.get("mcpServers", {}).items():
            self.servers[name] = {
                "name": name,
                **config,
                'status': MCPStatus.CONFIGURED,
                'configured_at': time.time()
            }
            
        print(f"📋 {len(self.servers)} MCPs configurados")

    def list(self) -> List[str]:
        """Lista todos os MCPs configurados"""
        return list(self.servers.keys())

    def list_active(self) -> List[str]:
        """Lista apenas MCPs ativos"""
        return [
            name for name, info in self.active_servers.items()
            if info.get('status') == MCPStatus.ACTIVE
        ]

    def get(self, name: str) -> Optional[Dict]:
        """Obtém configuração de um MCP"""
        return self.servers.get(name)

    def get_active(self, name: str) -> Optional[Dict]:
        """Obtém MCP ativo"""
        return self.active_servers.get(name)

    def list_tools(self, name: str) -> List[str]:
        """Lista ferramentas de um MCP"""
        server = self.servers.get(name, {})
        return server.get("tools", [])

    async def ensure_loaded(self, mcp_names: List[str]) -> Dict[str, bool]:
        """Garante que MCPs estão carregados (lazy loading)"""
        results = {}
        
        for name in mcp_names:
            if name in self.active_servers:
                results[name] = True
                continue
            
            if name not in self.servers:
                print(f"⚠️ MCP {name} não configurado")
                results[name] = False
                continue
            
            # Tentar carregar MCP
            success = await self._load_mcp(name)
            results[name] = success
        
        return results

    async def _load_mcp(self, name: str) -> bool:
        """Carrega um MCP específico"""
        if name not in self.servers:
            return False
        
        config = self.servers[name]
        
        try:
            print(f"📦 Carregando MCP: {name}")
            
            # Marcar como carregando
            self.active_servers[name] = {
                **config,
                'status': MCPStatus.LOADING,
                'load_started': time.time()
            }
            
            # Simular carregamento (substituir por implementação real)
            import asyncio
            await asyncio.sleep(0.5)  # Simular latência de carregamento
            
            # Marcar como ativo
            self.active_servers[name].update({
                'status': MCPStatus.ACTIVE,
                'loaded_at': time.time(),
                'load_time': time.time() - self.active_servers[name]['load_started']
            })
            
            # Registrar no histórico
            self.load_history[name] = {
                'last_load': time.time(),
                'load_count': self.load_history.get(name, {}).get('load_count', 0) + 1,
                'success': True
            }
            
            print(f"✅ MCP {name} carregado com sucesso")
            return True
            
        except Exception as e:
            print(f"❌ Erro carregando MCP {name}: {e}")
            
            # Marcar como erro
            if name in self.active_servers:
                self.active_servers[name].update({
                    'status': MCPStatus.ERROR,
                    'error': str(e),
                    'error_time': time.time()
                })
            
            # Registrar erro no histórico
            self.load_history[name] = {
                'last_load': time.time(),
                'load_count': self.load_history.get(name, {}).get('load_count', 0) + 1,
                'success': False,
                'error': str(e)
            }
            
            return False

    def unload_mcp(self, name: str) -> bool:
        """Descarrega um MCP"""
        if name in self.active_servers:
            self.active_servers[name]['status'] = MCPStatus.INACTIVE
            print(f"📤 MCP {name} descarregado")
            return True
        return False

    def get_status(self, name: str) -> MCPStatus:
        """Obtém status de um MCP"""
        if name in self.active_servers:
            return self.active_servers[name]['status']
        elif name in self.servers:
            return MCPStatus.CONFIGURED
        else:
            return MCPStatus.INACTIVE

    def health_check(self, name: str) -> Dict:
        """Verifica saúde de um MCP"""
        if name not in self.active_servers:
            return {'healthy': False, 'reason': 'MCP não ativo'}
        
        server_info = self.active_servers[name]
        
        if server_info['status'] != MCPStatus.ACTIVE:
            return {'healthy': False, 'reason': f"Status: {server_info['status'].value}"}
        
        # Verificar se não está muito antigo (mais de 1 hora)
        load_time = server_info.get('loaded_at', 0)
        if time.time() - load_time > 3600:
            return {'healthy': False, 'reason': 'MCP muito antigo, precisa recarregar'}
        
        return {'healthy': True, 'load_time': load_time}

    def get_registry_stats(self) -> Dict:
        """Retorna estatísticas do registry"""
        total_configured = len(self.servers)
        total_active = len([s for s in self.active_servers.values() if s['status'] == MCPStatus.ACTIVE])
        total_errors = len([s for s in self.active_servers.values() if s['status'] == MCPStatus.ERROR])
        
        return {
            'total_configured': total_configured,
            'total_active': total_active,
            'total_errors': total_errors,
            'load_success_rate': (total_active / max(total_configured, 1)) * 100,
            'active_mcps': self.list_active(),
            'error_mcps': [
                name for name, info in self.active_servers.items()
                if info['status'] == MCPStatus.ERROR
            ]
        }
