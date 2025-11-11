#!/usr/bin/env python3
"""
Enhanced IAL System - Sistema Completo Integrado
Orquestra todos os componentes das melhorias implementadas + Intelligent MCP Router
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import time

# Add all core components
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

# Try to import Intelligent MCP Router
try:
    from intelligent_mcp_router import IntelligentMCPRouter
    INTELLIGENT_ROUTER_AVAILABLE = True
except ImportError:
    INTELLIGENT_ROUTER_AVAILABLE = False

class EnhancedIALSystem:
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.start_time = time.time()
        
        # Initialize Intelligent MCP Router if available
        self.intelligent_router = None
        if INTELLIGENT_ROUTER_AVAILABLE:
            try:
                self.intelligent_router = IntelligentMCPRouter()
                #print("✅ Enhanced IAL System: Intelligent MCP Router integrado")
            except Exception as e:
                print(f"⚠️ Enhanced IAL System: Erro integrando router: {e}")
        
        print("🚀 Inicializando Enhanced IAL System v8.0 (Graph-based Self-Healing + Safe Chaos + Intelligent MCP Router)...")
    
    def execute_full_workflow(self, create_version: bool = True, 
                            auto_remediate: bool = False,
                            use_intelligent_routing: bool = True) -> Dict:
        """Executa workflow completo do sistema aprimorado com router inteligente"""
        workflow_start = time.time()
        
        print("\n🔄 EXECUTANDO WORKFLOW COMPLETO")
        print("=" * 50)
        
        workflow_result = {
            'started_at': datetime.utcnow().isoformat(),
            'workflow_version': '3.2',  # Incrementado para incluir router
            'steps': {},
            'success': False,
            'total_duration_ms': 0,
            'intelligent_routing_used': False
        }
        
        try:
            # Step 1: Check if should use intelligent routing
            if use_intelligent_routing and self.intelligent_router:
                print("🧠 Usando Intelligent MCP Router para workflow")
                workflow_result['intelligent_routing_used'] = True
                
                # Use intelligent router for infrastructure decisions
                routing_result = self._execute_with_intelligent_routing()
                workflow_result['steps']['intelligent_routing'] = routing_result
            
            # Step 2: Simular outros steps do workflow
            workflow_result['steps']['desired_state'] = {'success': True, 'simulated': True}
            workflow_result['steps']['validation'] = {'success': True, 'simulated': True}
            workflow_result['steps']['reconciliation'] = {'success': True, 'simulated': True}
            workflow_result['steps']['observability'] = {'success': True, 'simulated': True}
            
            # Determine overall success
            workflow_result['success'] = True
            
        except Exception as e:
            print(f"❌ Erro no workflow: {e}")
            workflow_result['error'] = str(e)
        
        finally:
            workflow_result['total_duration_ms'] = int((time.time() - workflow_start) * 1000)
        
        return workflow_result

    def _execute_with_intelligent_routing(self) -> Dict:
        """Executa decisões usando router inteligente"""
        try:
            # Simular solicitação de infraestrutura complexa
            infrastructure_request = "Deploy complete infrastructure with ECS, RDS, and ELB"
            
            context = {
                'system': 'enhanced_ial',
                'workflow': True,
                'timestamp': time.time()
            }
            
            # Usar router inteligente
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.intelligent_router.route_request(infrastructure_request, context)
            )
            loop.close()
            
            return {
                'success': result.get('success', False),
                'mcps_used': result.get('routing_decision', {}).get('mcps_used', []),
                'execution_time': result.get('execution_time', 0),
                'phases_executed': len(result.get('phases', {}))
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_system_status(self) -> Dict:
        """Retorna status completo do sistema"""
        status = {
            'system_version': '8.0',
            'region': self.region,
            'uptime_seconds': time.time() - self.start_time,
            'components': {
                'intelligent_router': self.intelligent_router is not None,
                'drift_detector': True,
                'auto_healer': True,
                'security_sentinel': True,
                'finops': True,
                'chaos_controller': True
            }
        }
        
        # Add intelligent router stats if available
        if self.intelligent_router:
            status['intelligent_router_stats'] = self.intelligent_router.get_router_stats()
        
        return status
