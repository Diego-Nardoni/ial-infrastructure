#!/usr/bin/env python3
"""
Compatible Desired State Builder - Maintains backward compatibility while supporting new deployment types
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
    from cf_yaml_loader import load_cf_yaml
    CF_LOADER_AVAILABLE = True
except ImportError:
    CF_LOADER_AVAILABLE = False
    print("⚠️ CF YAML Loader not available, using standard YAML loader")

class CompatibleDesiredStateBuilder:
    def __init__(self, phases_dir: str = "./phases"):
        # Usar path absoluto baseado no diretório do projeto
        if not os.path.isabs(phases_dir):
            # Se for path relativo, usar baseado no diretório pai do core
            project_root = Path(__file__).parent.parent
            self.phases_dir = project_root / phases_dir.lstrip('./')
        else:
            self.phases_dir = Path(phases_dir)
            
        self.reports_dir = Path("./reports")
        self.reports_dir.mkdir(exist_ok=True)
        
    def load_phases(self, deployment_file: Optional[str] = None) -> List[Dict]:
        """Load phases - supports both old and new methods"""
        if deployment_file:
            return self.load_phases_by_deployment_file(deployment_file)
        else:
            return self.load_phases_legacy()
            
    def load_phases_by_deployment_file(self, deployment_file: str) -> List[Dict]:
        """Load phases based on deployment order file"""
        deployment_path = Path(deployment_file)
        if not deployment_path.exists():
            raise FileNotFoundError(f"Deployment file not found: {deployment_path}")
            
        with open(deployment_path, 'r') as f:
            deployment_order = yaml.safe_load(f)
            
        phases = []
        execution_order = deployment_order.get('execution_order', [])
        
        print(f"🔍 Loading {len(execution_order)} phases from {deployment_file}")
        
        for phase_path in execution_order:
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
                    
            except Exception as e:
                print(f"  ❌ Error loading {phase_path}: {e}")
                
        return phases
        
    def load_phases_legacy(self) -> List[Dict]:
        """Legacy method - load all phases from directory structure"""
        phases = []
        
        if not self.phases_dir.exists():
            print(f"❌ Phases directory not found: {self.phases_dir}")
            return phases
            
        print(f"🔍 Loading phases from: {self.phases_dir} (legacy mode)")
        
        for domain_dir in self.phases_dir.iterdir():
            if not domain_dir.is_dir() or domain_dir.name.startswith('.'):
                continue
                
            domain_name = domain_dir.name
            print(f"📁 Processing domain: {domain_name}")
            
            for yaml_file in domain_dir.glob('*.yaml'):
                if yaml_file.name in ['domain-metadata.yaml', 'deployment-order.yaml', 
                                     'deployment-control-plane.yaml', 'deployment-workloads.yaml']:
                    continue
                    
                try:
                    if CF_LOADER_AVAILABLE:
                        phase_data = load_cf_yaml(str(yaml_file))
                    else:
                        with open(yaml_file, 'r', encoding='utf-8') as f:
                            phase_data = yaml.safe_load(f)
                    
                    if phase_data:
                        phase_data['_source_file'] = str(yaml_file)
                        phase_data['_domain'] = domain_name
                        phases.append(phase_data)
                        print(f"  ✅ {yaml_file.name}")
                        
                except Exception as e:
                    print(f"  ❌ Error loading {yaml_file.name}: {e}")
                    
        return phases
        
    def build_desired_spec(self, phases: List[Dict]) -> Dict:
        """Build desired specification from phases"""
        spec = {
            'metadata': {
                'version': '3.1',
                'architecture': 'dag-cognitive',
                'generated_by': 'compatible_desired_state_builder',
                'generated_at': datetime.now().isoformat(),
                'total_phases': len(phases)
            },
            'domains': {},
            'resources': {},
            'dependencies': {},
            'tags': {
                'ial:version': '3.1',
                'ial:generated-by': 'compatible-desired-state-builder'
            }
        }
        
        for phase in phases:
            # Determine domain and phase path
            if '_phase_path' in phase:
                phase_path = phase['_phase_path']
                domain = phase_path.split('/')[0] if '/' in phase_path else 'foundation'
            else:
                domain = phase.get('_domain', 'unknown')
                phase_path = f"{domain}/{Path(phase['_source_file']).stem}"
            
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
        
    def calculate_spec_hash(self, spec: Dict) -> str:
        """Calculate hash of specification for versioning"""
        spec_copy = spec.copy()
        if 'metadata' in spec_copy:
            spec_copy['metadata'] = {k: v for k, v in spec_copy['metadata'].items() 
                                   if k not in ['generated_at']}
        
        spec_str = json.dumps(spec_copy, sort_keys=True)
        return hashlib.sha256(spec_str.encode()).hexdigest()[:16]
    
    def save_desired_spec(self, spec: Dict, version: Optional[str] = None) -> str:
        """Save desired specification with versioning"""
        spec_hash = self.calculate_spec_hash(spec)
        
        if not version:
            version = spec_hash
            
        spec['metadata']['spec_hash'] = spec_hash
        spec['metadata']['version'] = version
        
        # Save current version
        current_file = self.reports_dir / 'desired_spec.json'
        with open(current_file, 'w') as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
        
        # Save versioned copy
        versioned_file = self.reports_dir / f'desired_spec_{version}.json'
        with open(versioned_file, 'w') as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Desired spec saved:")
        print(f"  📄 Current: {current_file}")
        print(f"  📄 Versioned: {versioned_file}")
        print(f"  🔑 Hash: {spec_hash}")
        
        return spec_hash

def main():
    """Main function for standalone execution"""
    parser = argparse.ArgumentParser(description='Compatible Desired State Builder')
    parser.add_argument('--deployment-file', 
                       help='Specific deployment order file to use')
    
    args = parser.parse_args()
    
    print("🚀 IAL Compatible Desired State Builder v3.1")
    if args.deployment_file:
        print(f"📋 Using deployment file: {args.deployment_file}")
    else:
        #print("📋 Using legacy directory scan mode")
    print("=" * 50)
    
    builder = CompatibleDesiredStateBuilder()
    
    try:
        # Load phases
        phases = builder.load_phases(args.deployment_file)
        if not phases:
            print("❌ No phases found!")
            return 1
        
        # Build specification
        spec = builder.build_desired_spec(phases)
        
        # Save specification
        spec_hash = builder.save_desired_spec(spec)
        
        # Display statistics
        print(f"\n📈 STATISTICS:")
        print(f"  🏗️ Domains: {len(spec['domains'])}")
        print(f"  📦 Resources: {len(spec['resources'])}")
        print(f"  📋 Phases: {len(phases)}")
        
        print(f"\n✅ Compatible Desired State Builder completed successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
