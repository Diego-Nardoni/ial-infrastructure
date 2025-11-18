#!/usr/bin/env python3
"""
MCP Mesh Loader - Carrega configuração do mcp-mesh.yaml
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from core.path_utils import get_config_path

class MCPMeshLoader:
    def __init__(self, config_path: str = None):
        # CORREÇÃO: Usar caminho dinâmico
        if config_path is None:
            config_path = get_config_path("mcp-mesh.yaml")
            
        self.config_path = config_path
        self.config = self._load_config()
        self.core_mcps = self.config.get('core_mcps', {}).get('always_active', [])
        self.domain_mcps = self.config.get('domain_mcps', {})
        self.settings = self.config.get('settings', {})
        self.architecture_patterns = self.config.get('architecture_patterns', {})
        
    def _load_config(self) -> Dict:
        """Load MCP mesh configuration"""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    return config
        except Exception as e:
            print(f"⚠️ Erro carregando MCP Mesh config: {e}")
        
        # Fallback configuration
        return {
            'core_mcps': {'always_active': []},
            'domain_mcps': {},
            'settings': {'lazy_loading': {'enabled': True}},
            'architecture_patterns': {}
        }
        
    def get_trigger_keywords(self, domain: str) -> List[str]:
        """Get trigger keywords for a domain"""
        if domain in self.domain_mcps:
            return self.domain_mcps[domain].get('trigger_keywords', [])
        return []
        
    def get_mcps_for_domain(self, domain: str) -> List[Dict]:
        """Get MCPs required for a domain"""
        if domain in self.domain_mcps:
            return self.domain_mcps[domain].get('mcps', [])
        return []
        
    def get_all_trigger_keywords(self) -> Dict[str, List[str]]:
        """Get all trigger keywords mapped by domain"""
        keywords_map = {}
        for domain, config in self.domain_mcps.items():
            keywords_map[domain] = config.get('trigger_keywords', [])
        return keywords_map
        
    def get_architecture_pattern_requirements(self, pattern: str) -> Dict:
        """Get requirements for an architecture pattern"""
        if pattern in self.architecture_patterns:
            return self.architecture_patterns[pattern]
        return {}
        
    def is_lazy_loading_enabled(self) -> bool:
        """Check if lazy loading is enabled"""
        return self.settings.get('lazy_loading', {}).get('enabled', True)
        
    def get_cache_settings(self) -> Dict:
        """Get cache configuration"""
        return self.settings.get('cache', {
            'enabled': True,
            'ttl_seconds': 300,
            'max_entries': 100
        })
        
    def get_health_check_settings(self) -> Dict:
        """Get health check configuration"""
        return self.settings.get('health_checks', {
            'enabled': True,
            'interval_seconds': 60,
            'timeout_seconds': 5,
            'max_failures': 3
        })
        
    def get_fallback_settings(self) -> Dict:
        """Get fallback configuration"""
        return self.settings.get('fallback', {
            'enabled': True,
            'use_cloudformation': True,
            'confidence_threshold': 0.3
        })
        
    def get_domain_description(self, domain: str) -> str:
        """Get description for a domain"""
        if domain in self.domain_mcps:
            return self.domain_mcps[domain].get('description', f'{domain} services')
        return f'{domain} services'
        
    def get_all_domains(self) -> List[str]:
        """Get all available domains"""
        return list(self.domain_mcps.keys())
        
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return status"""
        validation = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'stats': {}
        }
        
        # Count domains and MCPs
        total_domains = len(self.domain_mcps)
        total_mcps = sum(len(domain.get('mcps', [])) for domain in self.domain_mcps.values())
        total_keywords = sum(len(domain.get('trigger_keywords', [])) for domain in self.domain_mcps.values())
        
        validation['stats'] = {
            'total_domains': total_domains,
            'total_mcps': total_mcps,
            'total_keywords': total_keywords,
            'core_mcps': len(self.core_mcps)
        }
        
        # Validate required sections
        if not self.domain_mcps:
            validation['errors'].append("No domain MCPs configured")
            validation['valid'] = False
            
        if not self.core_mcps:
            validation['warnings'].append("No core MCPs configured")
            
        return validation
