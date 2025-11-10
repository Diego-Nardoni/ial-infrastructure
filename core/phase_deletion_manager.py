#!/usr/bin/env python3
"""
Phase Deletion Manager - Exclusão completa de phases com dependências
"""

import boto3
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import yaml

try:
    from graph.dependency_graph import DependencyGraph
    from resource_catalog import ResourceCatalog
    GRAPH_AVAILABLE = True
except ImportError:
    GRAPH_AVAILABLE = False

class PhaseDeletionManager:
    """Gerencia exclusão completa de phases"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.cf_client = boto3.client('cloudformation', region_name=region)
        self.phases_dir = Path("phases")
        
        if GRAPH_AVAILABLE:
            self.dependency_graph = DependencyGraph(region=region)
            self.resource_catalog = ResourceCatalog()
        else:
            self.dependency_graph = None
            self.resource_catalog = None
    
    def delete_phase(self, phase_name: str, force: bool = False) -> Dict[str, Any]:
        """Delete complete phase with all resources"""
        
        print(f"🗑️ Iniciando exclusão da phase: {phase_name}")
        
        # 1. Discover phase resources
        resources = self._discover_phase_resources(phase_name)
        if not resources:
            return {'success': False, 'error': f'Phase {phase_name} not found or no resources'}
        
        # 2. Check dependencies
        if not force:
            dependency_check = self._check_dependencies(resources)
            if not dependency_check['safe']:
                return {
                    'success': False,
                    'error': 'Phase has dependencies',
                    'dependencies': dependency_check['blocking_dependencies'],
                    'suggestion': 'Use force=True to override or delete dependent phases first'
                }
        
        # 3. Calculate deletion order
        deletion_order = self._calculate_deletion_order(resources)
        
        # 4. Execute deletion
        results = []
        for resource in deletion_order:
            result = self._delete_resource(resource)
            results.append(result)
            if not result['success'] and not force:
                return {
                    'success': False,
                    'error': f'Failed to delete {resource["id"]}',
                    'partial_results': results
                }
        
        # 5. Cleanup phase directory
        self._cleanup_phase_directory(phase_name)
        
        print(f"✅ Phase {phase_name} deletada com sucesso")
        
        return {
            'success': True,
            'phase': phase_name,
            'deleted_resources': len(results),
            'results': results
        }
    
    def _discover_phase_resources(self, phase_name: str) -> List[Dict[str, Any]]:
        """Discover all resources in a phase"""
        resources = []
        
        # 1. From CloudFormation stacks
        try:
            stacks = self.cf_client.list_stacks(
                StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE']
            )
            
            for stack in stacks['StackSummaries']:
                stack_name = stack['StackName']
                if phase_name in stack_name or stack_name.startswith(f"ial-{phase_name}"):
                    resources.append({
                        'id': stack_name,
                        'type': 'CloudFormation::Stack',
                        'phase': phase_name,
                        'arn': stack['StackId']
                    })
        except Exception as e:
            print(f"⚠️ Error discovering CF stacks: {e}")
        
        # 2. From phase YAML files
        phase_dir = self.phases_dir / phase_name
        if phase_dir.exists():
            for yaml_file in phase_dir.glob("*.yaml"):
                try:
                    with open(yaml_file, 'r') as f:
                        template = yaml.safe_load(f)
                    
                    if 'Resources' in template:
                        for res_name, res_config in template['Resources'].items():
                            resources.append({
                                'id': f"{phase_name}-{res_name}",
                                'type': res_config.get('Type', 'Unknown'),
                                'phase': phase_name,
                                'template_file': str(yaml_file)
                            })
                except Exception as e:
                    print(f"⚠️ Error parsing {yaml_file}: {e}")
        
        return resources
    
    def _check_dependencies(self, resources: List[Dict]) -> Dict[str, Any]:
        """Check if resources have dependencies"""
        if not self.dependency_graph:
            return {'safe': True, 'blocking_dependencies': []}
        
        blocking_deps = []
        
        for resource in resources:
            resource_id = resource['id']
            if resource_id in self.dependency_graph.nodes:
                dependents = self.dependency_graph.nodes[resource_id].dependents
                if dependents:
                    blocking_deps.extend(dependents)
        
        return {
            'safe': len(blocking_deps) == 0,
            'blocking_dependencies': list(set(blocking_deps))
        }
    
    def _calculate_deletion_order(self, resources: List[Dict]) -> List[Dict]:
        """Calculate safe deletion order (reverse dependency order)"""
        if not self.dependency_graph:
            return resources
        
        # Simple reverse order for now
        return list(reversed(resources))
    
    def _delete_resource(self, resource: Dict) -> Dict[str, Any]:
        """Delete individual resource"""
        resource_id = resource['id']
        resource_type = resource['type']
        
        try:
            if resource_type == 'CloudFormation::Stack':
                # Delete CloudFormation stack
                self.cf_client.delete_stack(StackName=resource_id)
                
                # Wait for deletion
                waiter = self.cf_client.get_waiter('stack_delete_complete')
                waiter.wait(StackName=resource_id, WaiterConfig={'Delay': 10, 'MaxAttempts': 30})
                
                print(f"✅ Stack {resource_id} deleted")
            
            # Remove from dependency graph
            if self.dependency_graph:
                self.dependency_graph.remove_resource(resource_id)
            
            return {'success': True, 'resource': resource_id, 'type': resource_type}
            
        except Exception as e:
            print(f"❌ Failed to delete {resource_id}: {e}")
            return {'success': False, 'resource': resource_id, 'error': str(e)}
    
    def _cleanup_phase_directory(self, phase_name: str):
        """Remove phase directory and files"""
        phase_dir = self.phases_dir / phase_name
        if phase_dir.exists():
            import shutil
            shutil.rmtree(phase_dir)
            print(f"🗑️ Phase directory {phase_dir} removed")
    
    def list_phases(self) -> List[str]:
        """List all available phases"""
        phases = []
        
        if self.phases_dir.exists():
            for item in self.phases_dir.iterdir():
                if item.is_dir():
                    phases.append(item.name)
        
        return sorted(phases)
    
    def get_phase_info(self, phase_name: str) -> Dict[str, Any]:
        """Get detailed information about a phase"""
        resources = self._discover_phase_resources(phase_name)
        dependency_check = self._check_dependencies(resources)
        
        return {
            'phase': phase_name,
            'resources': resources,
            'resource_count': len(resources),
            'has_dependencies': not dependency_check['safe'],
            'blocking_dependencies': dependency_check.get('blocking_dependencies', []),
            'safe_to_delete': dependency_check['safe']
        }
