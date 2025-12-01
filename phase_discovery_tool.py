#!/usr/bin/env python3
"""
Phase Discovery Tool - Integração com MCP GitHub Server + Fallback Filesystem
Resolve o problema de descoberta dinâmica de fases de deployment
"""

import json
import asyncio
import os
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class PhaseDiscoveryTool:
    """Ferramenta para descobrir fases disponíveis via MCP GitHub Server com fallback"""
    
    def __init__(self, mcp_client=None):
        self.mcp_client = mcp_client
        self.phases_cache = {}
        self.cache_ttl = 300  # 5 minutos
        
        # Detectar se está rodando no PyInstaller
        import sys
        if getattr(sys, 'frozen', False):
            # Rodando no PyInstaller
            self.phases_dir = os.path.join(sys._MEIPASS, 'phases')
        else:
            # Rodando em desenvolvimento
            self.phases_dir = "/home/ial/phases"
        
    def discover_phases(self, repo_path: str = "phases") -> List[Dict]:
        """Descobre fases disponíveis no repositório ou filesystem"""
        try:
            # Tentar via MCP GitHub Server primeiro
            if self.mcp_client:
                try:
                    import asyncio
                    phases = asyncio.run(self._discover_phases_via_mcp(repo_path))
                    if phases:
                        logger.info(f"✅ MCP: Descobertas {len(phases)} fases")
                        return phases
                except Exception as e:
                    logger.warning(f"⚠️ MCP falhou, usando filesystem: {e}")
            
            # Fallback para filesystem local
            phases = self._discover_phases_via_filesystem()
            if phases:
                logger.info(f"✅ Filesystem: Descobertas {len(phases)} fases")
                return phases
            
            logger.warning("⚠️ Nenhuma fase descoberta")
            return []
            
        except Exception as e:
            logger.error(f"Erro na descoberta de fases: {e}")
            return []
    
    async def _discover_phases_via_mcp(self, repo_path: str) -> List[Dict]:
        """Descobre fases via MCP GitHub Server"""
        try:
            # Lista diretórios de fases
            phase_dirs = await self._list_phase_directories_mcp(repo_path)
            
            phases = []
            for phase_dir in phase_dirs:
                # Lista templates YAML em cada fase
                templates = await self._list_phase_templates_mcp(f"{repo_path}/{phase_dir}")
                
                if templates:
                    phases.append({
                        "phase_id": phase_dir,
                        "phase_name": self._format_phase_name(phase_dir),
                        "template_count": len(templates),
                        "templates": templates,
                        "source": "mcp"
                    })
            
            return phases
            
        except Exception as e:
            logger.error(f"Erro na descoberta via MCP: {e}")
            return []
    
    async def _discover_phases_via_filesystem(self) -> List[Dict]:
        """Descobre fases via filesystem local"""
        try:
            if not os.path.exists(self.phases_dir):
                logger.warning(f"Diretório {self.phases_dir} não existe")
                return []
            
            phases = []
            
            # Lista diretórios no filesystem
            for item in os.listdir(self.phases_dir):
                item_path = os.path.join(self.phases_dir, item)
                
                if os.path.isdir(item_path) and self._is_phase_directory(item):
                    # Lista templates YAML na fase
                    templates = []
                    try:
                        for file in os.listdir(item_path):
                            if file.endswith((".yaml", ".yml")):
                                templates.append(file)
                    except Exception as e:
                        logger.warning(f"Erro listando templates em {item}: {e}")
                        continue
                    
                    if templates:
                        phases.append({
                            "phase_id": item,
                            "phase_name": self._format_phase_name(item),
                            "template_count": len(templates),
                            "templates": sorted(templates),
                            "source": "filesystem"
                        })
            
            return sorted(phases, key=lambda x: x["phase_id"])
            
        except Exception as e:
            logger.error(f"Erro na descoberta via filesystem: {e}")
            return []
    
    async def _list_phase_directories_mcp(self, repo_path: str) -> List[str]:
        """Lista diretórios de fases via MCP GitHub Server"""
        try:
            result = await self.mcp_client.call_tool("github-mcp-server", "list_repository_contents", {
                "path": repo_path,
                "type": "dir"
            })
            
            # Filtra apenas diretórios que seguem padrão XX-nome
            dirs = []
            for item in result.get("contents", []):
                if item.get("type") == "dir" and self._is_phase_directory(item.get("name", "")):
                    dirs.append(item["name"])
            
            return sorted(dirs)
            
        except Exception as e:
            logger.error(f"Erro listando diretórios via MCP: {e}")
            return []
    
    async def _list_phase_templates_mcp(self, phase_path: str) -> List[str]:
        """Lista templates YAML em uma fase específica via MCP"""
        try:
            result = await self.mcp_client.call_tool("github-mcp-server", "list_repository_contents", {
                "path": phase_path,
                "type": "file"
            })
            
            # Filtra apenas arquivos .yaml/.yml
            templates = []
            for item in result.get("contents", []):
                name = item.get("name", "")
                if name.endswith((".yaml", ".yml")):
                    templates.append(name)
            
            return sorted(templates)
            
        except Exception as e:
            logger.error(f"Erro listando templates via MCP em {phase_path}: {e}")
            return []
    
    def _is_phase_directory(self, dirname: str) -> bool:
        """Verifica se diretório segue padrão de fase (XX-nome)"""
        if len(dirname) < 3:
            return False
        return dirname[:2].isdigit() and dirname[2] == "-"
    
    def _format_phase_name(self, phase_dir: str) -> str:
        """Formata nome da fase para exibição"""
        if "-" in phase_dir:
            return phase_dir.split("-", 1)[1].replace("-", " ").title()
        return phase_dir

    def get_deployment_order(self) -> List[str]:
        """Retorna ordem recomendada de deployment das fases"""
        phases = self.discover_phases()
        return [phase["phase_id"] for phase in phases]

    def get_phase_summary(self, phases: List[Dict]) -> str:
        """Gera resumo das fases descobertas"""
        if not phases:
            return "❌ Nenhuma fase encontrada"
        
        total_templates = sum(p['template_count'] for p in phases)
        source = phases[0].get('source', 'unknown')
        
        summary = f"✅ {len(phases)} fases descobertas via {source}\n"
        summary += f"📄 {total_templates} templates totais\n\n"
        
        for phase in phases:
            summary += f"• **{phase['phase_id']}** - {phase['phase_name']} ({phase['template_count']} templates)\n"
        
        return summary
    
    async def get_phase_templates(self, phase_id: str) -> List[str]:
        """Obtém lista de templates de uma fase específica"""
        try:
            # Tentar via MCP GitHub Server primeiro
            if self.mcp_client:
                try:
                    templates = await self._list_phase_templates_mcp(f"phases/{phase_id}")
                    if templates:
                        return templates
                except Exception as e:
                    print(f"⚠️ MCP falhou para templates da fase {phase_id}: {e}")
            
            # Fallback para filesystem local
            phase_path = os.path.join(self.phases_dir, phase_id)
            if os.path.exists(phase_path):
                templates = [f for f in os.listdir(phase_path) 
                           if f.endswith(('.yaml', '.yml'))]
                return sorted(templates)
            
            return []
            
        except Exception as e:
            print(f"⚠️ Erro ao obter templates da fase {phase_id}: {e}")
            return []

# Integração com IAL Master Engine
async def integrate_phase_discovery(ial_engine):
    """Integra descoberta de fases no IAL Master Engine"""
    
    # Inicializa ferramenta com cliente MCP existente
    phase_tool = PhaseDiscoveryTool(ial_engine.mcp_client)
    
    # Descobre fases disponíveis
    available_phases = phase_tool.discover_phases()
    
    if available_phases:
        logger.info(f"✅ Descobertas {len(available_phases)} fases disponíveis")
        
        # Atualiza contexto do engine
        ial_engine.available_phases = available_phases
        ial_engine.deployment_order = phase_tool.get_deployment_order()
        
        return True
    else:
        logger.warning("⚠️ Nenhuma fase descoberta")
        return False

if __name__ == "__main__":
    # Teste standalone
    async def test_discovery():
        tool = PhaseDiscoveryTool()
        phases = await tool.discover_phases()
        print(tool.get_phase_summary(phases))
    
    asyncio.run(test_discovery())
