#!/usr/bin/env python3
"""
MCP Client - Conecta e gerencia servidores MCP
"""

import asyncio
import json
import subprocess
from typing import Dict, List, Any, Optional
from pathlib import Path

class MCPClient:
    """Cliente para conectar e usar servidores MCP"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "/home/ial/config/mcp-mesh.yaml"
        self.servers = {}
        self.tools_cache = {}
        
    async def initialize(self):
        """Inicializar conexões com servidores MCP"""
        try:
            # Usar MCP Server AWS oficial
            config_json = "/home/ial/mcp-aws-official.json"
            if Path(config_json).exists():
                with open(config_json, 'r') as f:
                    config = json.load(f)
                
                # Conectar ao servidor AWS oficial
                for name, server_config in config.get('mcpServers', {}).items():
                    await self._connect_server_json(name, server_config)
                    print(f"✅ MCP Server {name} conectado")
                    return
            
            print("⚠️ MCP Server config não encontrado, usando CLI fallback")
                
        except Exception as e:
            print(f"⚠️ Erro ao inicializar MCP Client: {e}")
    
    async def _connect_server_json(self, name: str, server_config: Dict):
        """Conectar a servidor MCP do formato JSON"""
        try:
            command = server_config.get('command')
            args = server_config.get('args', [])
            env = server_config.get('env', {})
            
            if not command:
                return
            
            # Iniciar processo do servidor MCP
            import os
            full_env = os.environ.copy()
            full_env.update(env)
            
            process = await asyncio.create_subprocess_exec(
                command,
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=full_env
            )
            
            self.servers[name] = {
                'process': process,
                'config': server_config
            }
            
            # Descobrir tools disponíveis
            await self._discover_tools(name)
            
        except Exception as e:
            print(f"⚠️ Erro ao conectar servidor {name}: {e}")
    
    async def _connect_server(self, server_config: Dict):
        """Conectar a um servidor MCP via stdio"""
        try:
            name = server_config.get('name')
            command = server_config.get('command')
            args = server_config.get('args', [])
            
            if not command:
                return
            
            # Iniciar processo do servidor MCP
            process = await asyncio.create_subprocess_exec(
                command,
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            self.servers[name] = {
                'process': process,
                'config': server_config
            }
            
            # Descobrir tools disponíveis
            await self._discover_tools(name)
            
        except Exception as e:
            print(f"⚠️ Erro ao conectar servidor {name}: {e}")
    
    async def _discover_tools(self, server_name: str):
        """Descobrir tools disponíveis no servidor"""
        try:
            server = self.servers.get(server_name)
            if not server:
                return
            
            # Enviar request para listar tools
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            }
            
            process = server['process']
            process.stdin.write((json.dumps(request) + '\n').encode())
            await process.stdin.drain()
            
            # Ler resposta
            response_line = await process.stdout.readline()
            response = json.loads(response_line.decode())
            
            if 'result' in response:
                tools = response['result'].get('tools', [])
                self.tools_cache[server_name] = tools
                print(f"✅ {len(tools)} tools descobertas em {server_name}")
            
        except Exception as e:
            print(f"⚠️ Erro ao descobrir tools: {e}")
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict) -> Dict:
        """Chamar tool em servidor MCP"""
        try:
            server = self.servers.get(server_name)
            if not server:
                return {'error': f'Servidor {server_name} não conectado'}
            
            # Enviar request para chamar tool
            request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            process = server['process']
            process.stdin.write((json.dumps(request) + '\n').encode())
            await process.stdin.drain()
            
            # Ler resposta
            response_line = await process.stdout.readline()
            response = json.loads(response_line.decode())
            
            if 'result' in response:
                return response['result']
            elif 'error' in response:
                return {'error': response['error']}
            
            return {'error': 'Resposta inválida'}
            
        except Exception as e:
            return {'error': f'Erro ao chamar tool: {str(e)}'}
    
    def get_available_tools(self, server_name: str = None) -> List[Dict]:
        """Retornar tools disponíveis"""
        if server_name:
            return self.tools_cache.get(server_name, [])
        
        # Retornar todas as tools de todos os servidores
        all_tools = []
        for tools in self.tools_cache.values():
            all_tools.extend(tools)
        return all_tools
    
    async def close(self):
        """Fechar conexões com servidores"""
        for name, server in self.servers.items():
            try:
                process = server['process']
                process.terminate()
                await process.wait()
            except:
                pass
