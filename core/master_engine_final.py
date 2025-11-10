#!/usr/bin/env python3
"""
Master Engine Final - Integração CORE + USER Paths
Entrada única que decide entre Bootstrap CORE ou Pipeline USER
"""

import sys
import os
from typing import Dict, Any
from datetime import datetime

class MasterEngineFinal:
    def __init__(self):
        """Inicializar Resource Router e engines"""
        
        try:
            from core.resource_router import ResourceRouter
            self.resource_router = ResourceRouter()
            print("✅ Resource Router carregado")
        except ImportError as e:
            print(f"❌ Resource Router não disponível: {e}")
            self.resource_router = None
        
        try:
            from core.cognitive_engine import CognitiveEngine
            self.cognitive_engine = CognitiveEngine()
            print("✅ Cognitive Engine carregado")
        except ImportError as e:
            print(f"❌ Cognitive Engine não disponível: {e}")
            self.cognitive_engine = None
        
        try:
            from core.mcp_infrastructure_manager import MCPInfrastructureManager
            from core.intelligent_mcp_router import IntelligentMCPRouter
            router = IntelligentMCPRouter()
            self.mcp_infrastructure_manager = MCPInfrastructureManager(router)
            print("✅ MCP Infrastructure Manager carregado")
        except ImportError as e:
            print(f"❌ MCP Infrastructure Manager não disponível: {e}")
            self.mcp_infrastructure_manager = None
    
    def process_request(self, nl_intent: str, config: Dict = None) -> Dict[str, Any]:
        """
        ÚNICO ENTRY POINT - TODOS os requests passam pelo Cognitive Engine (GitOps obrigatório)
        """
        
        print(f"🎯 Master Engine processando: '{nl_intent[:50]}...'")
        print("🧠 FORÇANDO Cognitive Engine para TODOS os requests (GitOps obrigatório)")
        
        # TODOS os requests passam pelo Cognitive Engine
        return self.process_cognitive_engine_path(nl_intent)
    
    def process_cognitive_engine_path(self, nl_intent: str) -> Dict[str, Any]:
        """
        COGNITIVE ENGINE PATH: Todos os recursos via GitOps pipeline completo
        """
        
        print("🧠 Executando COGNITIVE ENGINE PATH - Pipeline completo")
        
        if not self.cognitive_engine:
            return {
                'error': 'Cognitive Engine não disponível',
                'status': 'error',
                'path': 'COGNITIVE_ENGINE_PATH'
            }
        
        try:
            # PIPELINE COMPLETO: IAS → Cost → Phase Builder → GitHub → CI/CD → Audit
            result = self.cognitive_engine.process_intent(nl_intent)
            
            return {
                'status': 'success',
                'path': 'COGNITIVE_ENGINE_PATH',
                'pipeline_steps': result.get('pipeline_steps', []),
                'github_pr': result.get('github_pr_url'),
                'message': 'Request processed via complete GitOps pipeline',
                'result': result
            }
            
        except Exception as e:
            return {
                'error': f'Cognitive Engine error: {str(e)}',
                'status': 'error',
                'path': 'COGNITIVE_ENGINE_PATH'
            }
    
    def _is_deletion_request(self, nl_intent: str) -> bool:
        """Check if request is for deletion"""
        deletion_keywords = ['delete', 'remove', 'destroy', 'cleanup', 'exclude', 'drop']
        return any(keyword in nl_intent.lower() for keyword in deletion_keywords)
    
    def process_deletion_request(self, nl_intent: str) -> Dict[str, Any]:
        """Process deletion requests - phases or individual resources"""
        print("🗑️ Processando solicitação de exclusão")
        
        # Try phase deletion first
        phase_name = self._extract_phase_name(nl_intent)
        if phase_name:
            return self._process_phase_deletion(phase_name)
        
        # Try individual resource deletion
        resource_info = self._extract_resource_info(nl_intent)
        if resource_info:
            return self._process_resource_deletion(resource_info[1], resource_info[0])
        
        return {
            'error': 'Could not identify what to delete',
            'status': 'error',
            'suggestion': 'Specify "delete phase <name>" or "delete bucket <name>"'
        }
    
    def _process_phase_deletion(self, phase_name: str) -> Dict[str, Any]:
        """Process phase deletion"""
        try:
            from phase_deletion_manager import PhaseDeletionManager
            deletion_manager = PhaseDeletionManager()
            
            # Get phase info
            phase_info = deletion_manager.get_phase_info(phase_name)
            if not phase_info['resources']:
                return {
                    'error': f'Phase {phase_name} not found',
                    'status': 'error'
                }
            
            # Check if safe to delete
            if not phase_info['safe_to_delete']:
                return {
                    'error': f'Phase {phase_name} has dependencies',
                    'status': 'blocked',
                    'dependencies': phase_info['blocking_dependencies'],
                    'suggestion': 'Delete dependent phases first or use force option'
                }
            
            # Execute deletion
            result = deletion_manager.delete_phase(phase_name, force=False)
            
            if result['success']:
                return {
                    'status': 'success',
                    'action': 'phase_deletion',
                    'phase': phase_name,
                    'deleted_resources': result['deleted_resources'],
                    'message': f'Phase {phase_name} deleted successfully'
                }
            else:
                return {
                    'error': result['error'],
                    'status': 'error',
                    'phase': phase_name
                }
                
        except ImportError:
            return {
                'error': 'Phase deletion not available',
                'status': 'error',
                'suggestion': 'Phase deletion manager not installed'
            }
        except Exception as e:
            return {
                'error': f'Phase deletion failed: {str(e)}',
                'status': 'error'
            }
    
    def _process_resource_deletion(self, resource_id: str, resource_type: str) -> Dict[str, Any]:
        """Process individual resource deletion"""
        try:
            from resource_deletion_manager import ResourceDeletionManager
            deletion_manager = ResourceDeletionManager()
            
            print(f"🗑️ Deletando recurso individual: {resource_id} ({resource_type})")
            
            # Execute deletion with complete cleanup
            result = deletion_manager.delete_resource(resource_id, force=False)
            
            if result['success']:
                return {
                    'status': 'success',
                    'action': 'resource_deletion',
                    'resource': resource_id,
                    'type': result['type'],
                    'cleanup_performed': result['cleanup_performed'],
                    'dependencies_removed': result['dependencies_removed'],
                    'message': f'{resource_type.upper()} {resource_id} deleted with complete cleanup'
                }
            else:
                return {
                    'error': result['error'],
                    'status': 'error',
                    'resource': resource_id,
                    'suggestion': result.get('suggestion', 'Check resource exists and permissions')
                }
                
        except ImportError:
            return {
                'error': 'Resource deletion not available',
                'status': 'error',
                'suggestion': 'Resource deletion manager not installed'
            }
        except Exception as e:
            return {
                'error': f'Resource deletion failed: {str(e)}',
                'status': 'error'
            }
    
    def _extract_phase_name(self, nl_intent: str) -> Optional[str]:
        """Extract phase name from natural language"""
        import re
        
        # Common patterns for phases
        phase_patterns = [
            r'delete\s+phase\s+(\w+)',
            r'remove\s+phase\s+(\w+)',
            r'destroy\s+phase\s+(\w+)',
            r'phase\s+(\w+)\s+delete',
            r'(\w+)\s+phase.*delete'
        ]
        
        for pattern in phase_patterns:
            match = re.search(pattern, nl_intent.lower())
            if match:
                return match.group(1)
        
        return None
    
    def _extract_resource_info(self, nl_intent: str) -> Optional[Tuple[str, str]]:
        """Extract resource type and name from natural language"""
        import re
        
        # Resource patterns: (type, identifier_pattern)
        resource_patterns = [
            (r'bucket\s+([a-z0-9\-]+)', 's3'),
            (r'lambda\s+([a-zA-Z0-9\-_]+)', 'lambda'),
            (r'function\s+([a-zA-Z0-9\-_]+)', 'lambda'),
            (r'table\s+([a-zA-Z0-9\-_.]+)', 'dynamodb'),
            (r'database\s+([a-zA-Z0-9\-]+)', 'rds'),
            (r'instance\s+([a-zA-Z0-9\-]+)', 'ec2')
        ]
        
        for pattern, resource_type in resource_patterns:
            match = re.search(pattern, nl_intent.lower())
            if match:
                return (resource_type, match.group(1))
        
        return None
    
    def process_core_path(self, nl_intent: str, config: Dict) -> Dict[str, Any]:
        """
        CORE PATH: Bootstrap CORE resources via MCP Infrastructure Manager
        """
        
        print("🔧 Executando CORE PATH - Bootstrap IAL Foundation")
        
        if not self.mcp_infrastructure_manager:
            return {
                'error': 'MCP Infrastructure Manager não disponível',
                'status': 'error',
                'path': 'CORE_PATH'
            }
        
        try:
            # Deploy via MCP Infrastructure Manager (42 componentes)
            import asyncio
            result = asyncio.run(
                self.mcp_infrastructure_manager.deploy_ial_infrastructure(config)
            )
            
            return {
                'status': 'success',
                'path': 'CORE_PATH',
                'method': 'mcp_infrastructure_manager',
                'components_created': result.get('deployment_summary', {}).get('foundation_components', 0),
                'details': result,
                'processing_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ CORE PATH error: {str(e)}")
            return {
                'status': 'error',
                'path': 'CORE_PATH',
                'error': str(e),
                'method': 'mcp_infrastructure_manager'
            }
    
    def process_user_path(self, nl_intent: str) -> Dict[str, Any]:
        """
        USER PATH: Arquitetura de referência completa via Cognitive Engine
        """
        
        print("👤 Executando USER PATH - Arquitetura de Referência")
        
        if not self.cognitive_engine:
            return {
                'error': 'Cognitive Engine não disponível',
                'status': 'error',
                'path': 'USER_PATH'
            }
        
        try:
            # Pipeline completo: NL → IAS → Cost → Phase Builder → GitHub PR → CI/CD → Audit → Auto-Heal
            result = self.cognitive_engine.process_user_request(nl_intent)
            
            result['path'] = 'USER_PATH'
            return result
            
        except Exception as e:
            print(f"❌ USER PATH error: {str(e)}")
            return {
                'status': 'error',
                'path': 'USER_PATH',
                'error': str(e),
                'method': 'cognitive_engine'
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Verificar status do sistema"""
        
        return {
            'master_engine': 'active',
            'resource_router': self.resource_router is not None,
            'cognitive_engine': self.cognitive_engine is not None,
            'mcp_infrastructure_manager': self.mcp_infrastructure_manager is not None,
            'timestamp': datetime.now().isoformat()
        }
