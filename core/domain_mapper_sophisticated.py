#!/usr/bin/env python3
"""
Sophisticated Domain Mapper using MCP Mesh configuration
"""

from typing import Dict, List, Optional, Any
from core.mcp_mesh_loader import MCPMeshLoader

class DomainMapperSophisticated:
    def __init__(self, mesh_loader: MCPMeshLoader):
        self.mesh_loader = mesh_loader
        self.architecture_patterns = mesh_loader.architecture_patterns
        
    def map_to_domains(self, detected_services: List[str]) -> List[str]:
        """Map detected services to domains"""
        domains = set()
        
        # Map services to domains using trigger keywords
        for domain, keywords in self.mesh_loader.get_all_trigger_keywords().items():
            for service in detected_services:
                if service.lower() in [k.lower() for k in keywords]:
                    domains.add(domain)
                    
        return list(domains)
        
    def get_required_mcps(self, domains: List[str]) -> List[Dict]:
        """Get MCPs required for domains"""
        required_mcps = []
        
        # Always include core MCPs
        for core_mcp in self.mesh_loader.core_mcps:
            required_mcps.append({
                'name': core_mcp['name'],
                'priority': core_mcp.get('priority', 1),
                'load_timeout': core_mcp.get('load_timeout', 5.0),
                'type': 'core',
                'description': core_mcp.get('description', 'Core MCP')
            })
            
        # Add domain-specific MCPs
        for domain in domains:
            domain_mcps = self.mesh_loader.get_mcps_for_domain(domain)
            for mcp in domain_mcps:
                required_mcps.append({
                    'name': mcp['name'],
                    'priority': mcp.get('priority', 2),
                    'load_timeout': mcp.get('load_timeout', 5.0),
                    'type': 'domain',
                    'domain': domain,
                    'capabilities': mcp.get('capabilities', []),
                    'description': f"{domain} domain MCP"
                })
                
        # Sort by priority (lower number = higher priority)
        required_mcps.sort(key=lambda x: x['priority'])
        
        return required_mcps
        
    def apply_optimizations(self, pattern: str, mcps: List[Dict]) -> List[Dict]:
        """Apply optimizations based on architecture pattern"""
        if pattern not in self.architecture_patterns:
            return mcps
            
        pattern_config = self.architecture_patterns[pattern]
        optimizations = pattern_config.get('optimizations', {})
        required_domains = pattern_config.get('required_domains', [])
        
        optimized_mcps = mcps.copy()
        
        # Add required domains if missing
        current_domains = set(mcp.get('domain') for mcp in mcps if mcp.get('domain'))
        missing_domains = set(required_domains) - current_domains
        
        for domain in missing_domains:
            domain_mcps = self.mesh_loader.get_mcps_for_domain(domain)
            for mcp in domain_mcps:
                optimized_mcps.append({
                    'name': mcp['name'],
                    'priority': mcp.get('priority', 3),  # Lower priority for auto-added
                    'load_timeout': mcp.get('load_timeout', 5.0),
                    'type': 'pattern_required',
                    'domain': domain,
                    'capabilities': mcp.get('capabilities', []),
                    'description': f"Required by {pattern} pattern"
                })
                
        # Apply pattern-specific optimizations
        for mcp in optimized_mcps:
            if mcp.get('domain') in required_domains:
                # Increase priority for pattern-critical MCPs
                mcp['priority'] = max(1, mcp['priority'] - 1)
                
                # Apply specific optimizations
                if optimizations.get('enable_auto_scaling') and 'auto_scaling' in mcp.get('capabilities', []):
                    mcp['auto_scaling_enabled'] = True
                    
                if optimizations.get('multi_az_deployment') and 'multi_az' in mcp.get('capabilities', []):
                    mcp['multi_az_enabled'] = True
                    
        # Re-sort by priority
        optimized_mcps.sort(key=lambda x: x['priority'])
        
        return optimized_mcps
        
    def get_load_strategy(self, mcps: List[Dict]) -> Dict[str, Any]:
        """Get loading strategy based on MCP priorities and settings"""
        lazy_loading = self.mesh_loader.is_lazy_loading_enabled()
        
        if not lazy_loading:
            return {
                'strategy': 'eager',
                'load_all': True,
                'parallel': True
            }
            
        # Group MCPs by priority
        priority_groups = {}
        for mcp in mcps:
            priority = mcp['priority']
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(mcp)
            
        return {
            'strategy': 'lazy',
            'priority_groups': priority_groups,
            'load_order': sorted(priority_groups.keys()),
            'parallel_within_priority': True
        }
        
    def estimate_resource_requirements(self, mcps: List[Dict]) -> Dict[str, Any]:
        """Estimate resource requirements for MCPs"""
        total_mcps = len(mcps)
        core_mcps = len([mcp for mcp in mcps if mcp.get('type') == 'core'])
        domain_mcps = len([mcp for mcp in mcps if mcp.get('type') == 'domain'])
        
        # Estimate based on MCP count and types
        estimated_memory = core_mcps * 50 + domain_mcps * 30  # MB
        estimated_load_time = max(mcp.get('load_timeout', 5.0) for mcp in mcps)
        
        return {
            'total_mcps': total_mcps,
            'core_mcps': core_mcps,
            'domain_mcps': domain_mcps,
            'estimated_memory_mb': estimated_memory,
            'estimated_load_time_seconds': estimated_load_time,
            'parallel_loading_recommended': total_mcps > 3
        }
