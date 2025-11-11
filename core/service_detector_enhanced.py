#!/usr/bin/env python3
"""
Enhanced Service Detector using MCP Mesh trigger keywords
"""

import re
from typing import Dict, List, Optional, Any
from core.mcp_mesh_loader import MCPMeshLoader

class ServiceDetectorEnhanced:
    def __init__(self, mesh_loader: MCPMeshLoader):
        self.mesh_loader = mesh_loader
        self.domain_keywords = self._build_keyword_map()
        self.architecture_patterns = mesh_loader.architecture_patterns
        
    def _build_keyword_map(self) -> Dict[str, List[str]]:
        """Build keyword map from MCP mesh configuration"""
        return self.mesh_loader.get_all_trigger_keywords()
        
    def detect_services(self, text: str) -> Dict[str, Any]:
        """Detect services using trigger keywords from MCP mesh"""
        text_lower = text.lower()
        detected_domains = []
        detected_services = []
        confidence_scores = {}
        
        # Check each domain's trigger keywords
        for domain, keywords in self.domain_keywords.items():
            matches = []
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    matches.append(keyword)
                    
            if matches:
                confidence = len(matches) / len(keywords)
                detected_domains.append(domain)
                confidence_scores[domain] = confidence
                detected_services.extend(matches)
                
        # Detect architecture pattern
        architecture_pattern = self.detect_architecture_pattern(detected_services)
        
        return {
            'detected_domains': detected_domains,
            'detected_services': list(set(detected_services)),
            'confidence_scores': confidence_scores,
            'architecture_pattern': architecture_pattern,
            'total_confidence': sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0
        }
        
    def detect_architecture_pattern(self, services: List[str]) -> Optional[str]:
        """Detect architecture pattern based on services"""
        services_lower = [s.lower() for s in services]
        
        # 3-tier pattern
        has_web = any(s in services_lower for s in ['elb', 'alb', 'load balancer', 'api gateway'])
        has_compute = any(s in services_lower for s in ['ec2', 'ecs', 'instance'])
        has_database = any(s in services_lower for s in ['rds', 'database', 'mysql', 'postgres'])
        
        if has_web and has_compute and has_database:
            return '3-tier'
            
        # Serverless pattern
        has_lambda = any(s in services_lower for s in ['lambda', 'function', 'serverless'])
        has_api_gateway = any(s in services_lower for s in ['api gateway', 'api', 'rest'])
        has_dynamodb = any(s in services_lower for s in ['dynamodb', 'nosql'])
        
        if has_lambda and (has_api_gateway or has_dynamodb):
            return 'serverless'
            
        # Microservices pattern
        has_containers = any(s in services_lower for s in ['ecs', 'eks', 'container', 'kubernetes'])
        has_service_mesh = any(s in services_lower for s in ['service mesh', 'istio'])
        
        if has_containers and len(services) > 3:
            return 'microservices'
            
        # Data pipeline pattern
        has_step_functions = any(s in services_lower for s in ['step functions', 'workflow'])
        has_data_services = any(s in services_lower for s in ['s3', 'glue', 'athena', 'redshift'])
        
        if has_step_functions and has_data_services:
            return 'data-pipeline'
            
        # CI/CD pattern
        has_github = any(s in services_lower for s in ['github', 'git', 'repository'])
        has_pipeline = any(s in services_lower for s in ['pipeline', 'ci/cd', 'deployment'])
        
        if has_github and has_pipeline:
            return 'ci-cd'
            
        return None
        
    def get_confidence_threshold(self) -> float:
        """Get confidence threshold from mesh settings"""
        fallback_settings = self.mesh_loader.get_fallback_settings()
        return fallback_settings.get('confidence_threshold', 0.3)
        
    def is_high_confidence(self, confidence: float) -> bool:
        """Check if confidence is above threshold"""
        return confidence >= self.get_confidence_threshold()
        
    def get_domain_description(self, domain: str) -> str:
        """Get description for detected domain"""
        return self.mesh_loader.get_domain_description(domain)
        
    def get_pattern_optimizations(self, pattern: str) -> Dict:
        """Get optimizations for detected architecture pattern"""
        return self.mesh_loader.get_architecture_pattern_requirements(pattern)
