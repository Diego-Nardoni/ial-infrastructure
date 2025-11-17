#!/usr/bin/env python3
"""
Phase Discovery Tool - Lista fases disponíveis via MCP GitHub Server
"""

import json
import time
from typing import Dict, List, Optional

class PhaseDiscoveryTool:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.repo_owner = "Diego-Nardoni"
        self.repo_name = "ial-infrastructure"
        
    async def list_available_phases(self) -> Dict:
        """Lista todas as fases disponíveis via GitHub"""
        
        # Check cache first
        cache_key = "available_phases"
        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']
        
        try:
            # Use MCP GitHub Server
            from core.mcp_client import MCPClient
            mcp_client = MCPClient()
            
            # List phases directory
            phases_result = await mcp_client.call_tool(
                "github-mcp",
                "list_repository_contents",
                {
                    "owner": self.repo_owner,
                    "repo": self.repo_name,
                    "path": "phases"
                }
            )
            
            if not phases_result.get('success', False):
                return self._fallback_phases_list()
            
            # Parse directory contents
            contents = phases_result.get('contents', [])
            phases = []
            
            for item in contents:
                if item.get('type') == 'dir' and item.get('name', '').startswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')):
                    phase_info = await self._get_phase_details(item['name'])
                    phases.append(phase_info)
            
            # Get deployment order
            deployment_order = await self._get_deployment_order()
            
            result = {
                'total_phases': len(phases),
                'phases': sorted(phases, key=lambda x: x['number']),
                'deployment_order': deployment_order,
                'source': 'github',
                'timestamp': time.time()
            }
            
            # Cache result
            self._cache_result(cache_key, result)
            return result
            
        except Exception as e:
            print(f"⚠️ GitHub query failed: {e}")
            return self._fallback_phases_list()
    
    async def _get_phase_details(self, phase_name: str) -> Dict:
        """Get details for a specific phase"""
        
        try:
            from core.mcp_client import MCPClient
            mcp_client = MCPClient()
            
            # List phase contents
            phase_contents = await mcp_client.call_tool(
                "github-mcp",
                "list_repository_contents",
                {
                    "owner": self.repo_owner,
                    "repo": self.repo_name,
                    "path": f"phases/{phase_name}"
                }
            )
            
            templates = []
            if phase_contents.get('success', False):
                for item in phase_contents.get('contents', []):
                    if item.get('name', '').endswith('.yaml') and not item.get('name', '').startswith('domain-metadata'):
                        templates.append(item['name'])
            
            # Extract phase number and domain
            phase_number = int(phase_name.split('-')[0])
            domain = '-'.join(phase_name.split('-')[1:]) if '-' in phase_name else 'unknown'
            
            return {
                'name': phase_name,
                'number': phase_number,
                'domain': domain,
                'templates': sorted(templates),
                'template_count': len(templates)
            }
            
        except Exception as e:
            return {
                'name': phase_name,
                'number': int(phase_name.split('-')[0]) if '-' in phase_name else 99,
                'domain': 'unknown',
                'templates': [],
                'template_count': 0,
                'error': str(e)
            }
    
    async def _get_deployment_order(self) -> List[str]:
        """Get deployment order from GitHub"""
        
        try:
            from core.mcp_client import MCPClient
            mcp_client = MCPClient()
            
            # Get deployment-order.yaml
            order_file = await mcp_client.call_tool(
                "github-mcp",
                "get_file_contents",
                {
                    "owner": self.repo_owner,
                    "repo": self.repo_name,
                    "path": "phases/deployment-order.yaml"
                }
            )
            
            if order_file.get('success', False):
                import yaml
                content = order_file.get('content', '')
                order_data = yaml.safe_load(content)
                return order_data.get('execution_order', [])
            
        except Exception as e:
            print(f"⚠️ Could not get deployment order: {e}")
        
        return []
    
    def _fallback_phases_list(self) -> Dict:
        """Fallback list when GitHub is unavailable"""
        
        fallback_phases = [
            {'name': '00-foundation', 'number': 0, 'domain': 'foundation', 'templates': ['~40 templates'], 'template_count': 40},
            {'name': '10-security', 'number': 10, 'domain': 'security', 'templates': ['~6 templates'], 'template_count': 6},
            {'name': '20-network', 'number': 20, 'domain': 'network', 'templates': ['~3 templates'], 'template_count': 3},
            {'name': '30-compute', 'number': 30, 'domain': 'compute', 'templates': ['~6 templates'], 'template_count': 6},
            {'name': '40-data', 'number': 40, 'domain': 'data', 'templates': ['~4 templates'], 'template_count': 4},
            {'name': '50-application', 'number': 50, 'domain': 'application', 'templates': ['~3 templates'], 'template_count': 3},
            {'name': '60-observability', 'number': 60, 'domain': 'observability', 'templates': ['~2 templates'], 'template_count': 2},
            {'name': '70-ai-ml', 'number': 70, 'domain': 'ai-ml', 'templates': ['~1 template'], 'template_count': 1},
            {'name': '90-governance', 'number': 90, 'domain': 'governance', 'templates': ['~5 templates'], 'template_count': 5}
        ]
        
        return {
            'total_phases': len(fallback_phases),
            'phases': fallback_phases,
            'deployment_order': [],
            'source': 'fallback',
            'timestamp': time.time(),
            'note': 'GitHub unavailable, using cached phase list'
        }
    
    def _is_cached(self, key: str) -> bool:
        """Check if result is cached and valid"""
        if key not in self.cache:
            return False
        
        cached_time = self.cache[key]['timestamp']
        return (time.time() - cached_time) < self.cache_ttl
    
    def _cache_result(self, key: str, data: Dict):
        """Cache result with timestamp"""
        self.cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def format_phases_response(self, phases_data: Dict) -> str:
        """Format phases data for user display"""
        
        if not phases_data.get('phases'):
            return "❌ Nenhuma fase encontrada"
        
        response = f"📦 **{phases_data['total_phases']} Fases Disponíveis** (fonte: {phases_data['source']})\n\n"
        
        for phase in phases_data['phases']:
            response += f"**{phase['name']}** - {phase['domain']}\n"
            response += f"   📋 {phase['template_count']} templates\n"
            if phase.get('templates') and len(phase['templates']) <= 5:
                response += f"   📄 {', '.join(phase['templates'])}\n"
            response += "\n"
        
        if phases_data.get('deployment_order'):
            response += f"🔄 **Ordem de Deployment**: {len(phases_data['deployment_order'])} steps definidos\n"
        
        return response
