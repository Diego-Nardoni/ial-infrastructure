#!/usr/bin/env python3
"""
Enhanced Desired State Builder - Support for Control Plane and Workloads separation
"""

import yaml
import json
import os
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import sys

# Add scripts directory to path for cf_yaml_loader
sys.path.append(str(Path(__file__).parent.parent / 'scripts'))

try:
    from cf_yaml_loader import CFYAMLLoader
    cf_loader = CFYAMLLoader()
    CF_LOADER_AVAILABLE = True
    print("✅ CF YAML Loader carregado")
except ImportError:
    CF_LOADER_AVAILABLE = False
    print("⚠️ CF YAML Loader not available, using standard YAML loader")

class EnhancedDesiredStateBuilder:
    def __init__(self, phases_dir: str = "./phases"):
        self.phases_dir = Path(phases_dir)
        self.reports_dir = Path("./reports")
        self.reports_dir.mkdir(exist_ok=True)
        
    def load_deployment_order(self, deployment_file: Optional[str] = None) -> Dict:
        """Load deployment order from specific file or default"""
        if deployment_file:
            deployment_path = Path(deployment_file)
        else:
            deployment_path = self.phases_dir / "deployment-order.yaml"
            
        if not deployment_path.exists():
            raise FileNotFoundError(f"Deployment file not found: {deployment_path}")
            
        with open(deployment_path, 'r') as f:
            return yaml.safe_load(f)
            
    def load_phases_by_order(self, deployment_order: Dict) -> List[Dict]:
        """Load phases based on deployment order"""
        phases = []
        execution_order = deployment_order.get('execution_order', [])
        
        print(f"🔍 Loading {len(execution_order)} phases from deployment order")
        
        for phase_path in execution_order:
            # Convert phase path to actual file path
            yaml_file = self.phases_dir / f"{phase_path}.yaml"
            
            if not yaml_file.exists():
                print(f"⚠️ Phase file not found: {yaml_file}")
                continue
                
            try:
                if CF_LOADER_AVAILABLE:
                    phase_data = load_cf_yaml(str(yaml_file))
                else:
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        phase_data = yaml.safe_load(f)
                
                if phase_data:
                    phase_data['_source_file'] = str(yaml_file)
                    phase_data['_phase_path'] = phase_path
                    phases.append(phase_data)
                    print(f"  ✅ Loaded: {phase_path}")
                else:
                    print(f"  ⚠️ Empty phase: {phase_path}")
                    
            except Exception as e:
                print(f"  ❌ Error loading {phase_path}: {e}")
                
        return phases
        
    def build_desired_spec(self, phases: List[Dict], deployment_type: str = "full") -> Dict:
        """Build desired specification from phases"""
        spec = {
            'metadata': {
                'version': '3.1',
                'deployment_type': deployment_type,
                'generated_at': datetime.now().isoformat(),
                'total_phases': len(phases),
                'builder': 'enhanced_desired_state_builder'
            },
            'domains': {},
            'resources': {},
            'dependencies': {},
            'tags': {
                'ial:deployment-type': deployment_type,
                'ial:generated-by': 'enhanced-desired-state-builder',
                'ial:version': '3.1'
            }
        }
        
        for phase in phases:
            phase_path = phase.get('_phase_path', 'unknown')
            domain = phase_path.split('/')[0] if '/' in phase_path else 'foundation'
            
            # Add domain info
            if domain not in spec['domains']:
                spec['domains'][domain] = {
                    'phases': [],
                    'resource_count': 0
                }
            
            spec['domains'][domain]['phases'].append(phase_path)
            
            # Process resources
            if 'Resources' in phase:
                for resource_name, resource_config in phase['Resources'].items():
                    full_resource_name = f"{phase_path}::{resource_name}"
                    spec['resources'][full_resource_name] = {
                        'type': resource_config.get('Type', 'Unknown'),
                        'properties': resource_config.get('Properties', {}),
                        'phase': phase_path,
                        'domain': domain
                    }
                    spec['domains'][domain]['resource_count'] += 1
                    
        return spec
        
    def save_desired_spec(self, spec: Dict, deployment_type: str) -> str:
        """Save desired specification with deployment type"""
        spec_hash = self.calculate_spec_hash(spec)
        spec['metadata']['spec_hash'] = spec_hash
        
        # Save current version
        current_file = self.reports_dir / f'desired_spec_{deployment_type}.json'
        with open(current_file, 'w') as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
            
        # Save versioned copy
        versioned_file = self.reports_dir / f'desired_spec_{deployment_type}_{spec_hash}.json'
        with open(versioned_file, 'w') as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
            
        print(f"💾 {deployment_type} spec saved:")
        print(f"  📄 Current: {current_file}")
        print(f"  📄 Versioned: {versioned_file}")
        print(f"  🔑 Hash: {spec_hash}")
        
        return spec_hash
        
    def calculate_spec_hash(self, spec: Dict) -> str:
        """Calculate specification hash for versioning"""
        spec_copy = spec.copy()
        if 'metadata' in spec_copy:
            spec_copy['metadata'] = {k: v for k, v in spec_copy['metadata'].items() 
                                   if k not in ['generated_at']}
        
        spec_str = json.dumps(spec_copy, sort_keys=True)
        return hashlib.sha256(spec_str.encode()).hexdigest()[:16]

def main():
    parser = argparse.ArgumentParser(description='Enhanced Desired State Builder')
    parser.add_argument('--deployment-file', 
                       help='Specific deployment order file to use')
    parser.add_argument('--deployment-type',
                       default='full',
                       help='Type of deployment (control_plane, workloads, full)')
    
    args = parser.parse_args()
    
    print(f"🚀 IAL Enhanced Desired State Builder v3.1")
    print(f"📋 Deployment Type: {args.deployment_type}")
    print("=" * 50)
    
    builder = EnhancedDesiredStateBuilder()
    
    try:
        # Load deployment order
        deployment_order = builder.load_deployment_order(args.deployment_file)
        deployment_type = deployment_order.get('metadata', {}).get('deployment_type', args.deployment_type)
        
        # Load phases based on deployment order
        phases = builder.load_phases_by_order(deployment_order)
        if not phases:
            print("❌ No phases found!")
            return 1
            
        # Build specification
        spec = builder.build_desired_spec(phases, deployment_type)
        
        # Save specification
        spec_hash = builder.save_desired_spec(spec, deployment_type)
        
        # Display statistics
        print(f"\n📈 STATISTICS ({deployment_type}):")
        print(f"  🏗️ Domains: {len(spec['domains'])}")
        print(f"  📦 Resources: {len(spec['resources'])}")
        print(f"  📋 Phases: {len(phases)}")
        
        print(f"\n✅ Enhanced Desired State Builder completed successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
