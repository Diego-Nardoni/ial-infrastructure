import json
import yaml
import os
from typing import Dict, Any, List
from core.decision_ledger import DecisionLedger
from core.mcp_router import MCPRouter

# Knowledge Graph integration
try:
    from core.graph.dependency_graph import DependencyGraph
    from core.graph.graph_query_api import GraphQueryAPI
    GRAPH_AVAILABLE = True
except ImportError:
    GRAPH_AVAILABLE = False
    print("⚠️ Knowledge Graph não disponível no ReverseSync")

class ReverseSync:
    def __init__(self):
        self.decision_ledger = DecisionLedger()
        self.mcp_router = MCPRouter()
        
        # Initialize Knowledge Graph integration
        if GRAPH_AVAILABLE:
            try:
                self.dependency_graph = DependencyGraph(enable_persistence=True)
                self.graph_api = GraphQueryAPI(self.dependency_graph)
                self.graph_enabled = True
                print("✅ ReverseSync: Knowledge Graph habilitado")
            except Exception as e:
                print(f"⚠️ ReverseSync: Erro inicializando grafo: {e}")
                self.graph_enabled = False
        else:
            self.graph_enabled = False
        
    def generate_pr_for_findings(self, drift_findings: List[Dict[str, Any]], scope: str) -> Dict[str, Any]:
        """Generate PR for multiple drift findings with impact analysis"""
        
        print(f"Generating reverse sync PR for {len(drift_findings)} findings in scope {scope}")
        
        try:
            # Perform impact analysis if graph is available
            impact_analysis = None
            if self.graph_enabled:
                impact_analysis = self._analyze_drift_impact(drift_findings)
                
                # Group findings by dependency chains
                grouped_findings = self._group_by_dependency_chains(drift_findings)
                print(f"📊 Agrupados em {len(grouped_findings)} cadeias de dependência")
            else:
                grouped_findings = {'default': drift_findings}
            
            # Create PR for each dependency chain
            pr_results = []
            for chain_name, chain_findings in grouped_findings.items():
                pr_content = self._create_pr_for_chain(chain_name, chain_findings, scope, impact_analysis)
                pr_result = self._create_github_pr(pr_content)
                pr_results.append(pr_result)
            
            return {
                "status": "success",
                "prs_created": len(pr_results),
                "pr_results": pr_results,
                "impact_analysis": impact_analysis
            }
            
        except Exception as e:
            print(f"❌ Erro gerando PR: {e}")
            return {"status": "error", "message": str(e)}
    
    def _analyze_drift_impact(self, drift_findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analisa impacto dos drifts usando Knowledge Graph"""
        if not self.graph_enabled:
            return {}
        
        try:
            impact_summary = {
                'total_resources': len(drift_findings),
                'high_impact_resources': [],
                'dependency_chains_affected': 0,
                'cascade_risk_score': 0,
                'recommendations': []
            }
            
            total_risk = 0
            chains_affected = set()
            
            for finding in drift_findings:
                resource_id = finding.get('resource_id')
                if not resource_id:
                    continue
                
                # Análise de impacto para cada recurso
                impact = self.graph_api.get_impacted_resources(resource_id)
                
                # Recursos de alto impacto
                if impact.cascade_risk_score > 50:
                    impact_summary['high_impact_resources'].append({
                        'resource_id': resource_id,
                        'risk_score': impact.cascade_risk_score,
                        'affected_services': impact.affected_services
                    })
                
                total_risk += impact.cascade_risk_score
                
                # Cadeias de dependência afetadas
                chains = self.graph_api.get_dependency_chain(resource_id)
                for chain in chains:
                    chains_affected.add(chain.root_resource)
            
            impact_summary['cascade_risk_score'] = total_risk / len(drift_findings) if drift_findings else 0
            impact_summary['dependency_chains_affected'] = len(chains_affected)
            
            # Gerar recomendações
            if impact_summary['cascade_risk_score'] > 70:
                impact_summary['recommendations'].append("⚠️ ALTO RISCO: Aplicar mudanças durante janela de manutenção")
            
            if len(impact_summary['high_impact_resources']) > 0:
                impact_summary['recommendations'].append(f"🔍 {len(impact_summary['high_impact_resources'])} recursos de alto impacto identificados")
            
            return impact_summary
            
        except Exception as e:
            print(f"⚠️ Erro na análise de impacto: {e}")
            return {}
    
    def _group_by_dependency_chains(self, drift_findings: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Agrupa findings por cadeias de dependência"""
        if not self.graph_enabled:
            return {'default': drift_findings}
        
        try:
            chains = {}
            processed_resources = set()
            
            for finding in drift_findings:
                resource_id = finding.get('resource_id')
                if not resource_id or resource_id in processed_resources:
                    continue
                
                # Obter cadeia de dependências
                dependency_chains = self.graph_api.get_dependency_chain(resource_id)
                
                if dependency_chains:
                    # Usar a cadeia mais crítica como chave
                    critical_chain = next((c for c in dependency_chains if c.critical_path), dependency_chains[0])
                    chain_key = f"chain_{critical_chain.root_resource}"
                else:
                    chain_key = f"isolated_{resource_id}"
                
                # Agrupar finding na cadeia
                if chain_key not in chains:
                    chains[chain_key] = []
                
                chains[chain_key].append(finding)
                processed_resources.add(resource_id)
            
            return chains
            
        except Exception as e:
            print(f"⚠️ Erro agrupando por cadeias: {e}")
            return {'default': drift_findings}
    
    def _create_pr_for_chain(self, chain_name: str, findings: List[Dict[str, Any]], 
                           scope: str, impact_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Cria PR para uma cadeia específica de dependências"""
        
        pr_content = {
            "title": f"[DRIFT-CHAIN] {chain_name} - Reverse Sync for {scope}",
            "description": f"Reverse sync for dependency chain {chain_name} with {len(findings)} findings",
            "files": []
        }
        
        return pr_content
    
    def _create_github_pr(self, pr_content: Dict[str, Any]) -> Dict[str, Any]:
        """Create GitHub PR (simulated)"""
        return {
            "status": "success",
            "pr_number": 123,
            "pr_url": "https://github.com/example/repo/pull/123"
        }
